#!/usr/bin/env ipython3

from flask import (
    Flask,
    Response,
    redirect,
    send_file,
    request,
    abort,
)
from typing import List

from json import dumps

from build_spectra import handle
import datetime as dt
from models import *
import desispec.io, desispec.spectra
from desispec.spectra import Spectra
from prospect.viewer import plotspectra
from utils import *


import os

DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "7d441f27d441f27567d441f2b6176a"

DOC_URL = "https://github.com/VivianWilde/desi-api-drafting/blob/main/userdoc.org"


@app.route("/")
@app.route("/api")
@app.route("/api/v1")
def show_doc():
    return redirect(DOC_URL)


@app.route(
    "/api/v1/spectra/<command>/<release>/<endpoint>/<path:endpoint_params>", methods=["GET"]
)
def handle_get_spectra(command: str, release: str, endpoint: str, endpoint_params: str):
    """Entrypoint. Accepts an arbitrary path (via a URL), translates it into an API request, builds the response as a file, and serves it over the network

    :param command: One of Download/Plot, specifies whether to return raw FITS data or an interactive HTML plot.
    :param release: The DESI release from which to draw data.
    :param endpoint: One of Tile/Target/Radec, the endpoint to query.
    :param params: Endpoint-specific parameters, such as a tile ID and list of fibers, a list of target IDs, or a (ra, dec) point and radius.
    :returns: None, but either renders HTML or sends a file as a response.
    """
    log("params: ", endpoint_params)
    try:
        req = build_request(
            command, release, endpoint, endpoint_params, request.args.to_dict()
        )
        validate(req)
    except (DesiApiException, KeyError) as e:
        invalid_request_error(e)
    else:
        return process_request(req)


@app.route("/api/v1/post", methods=["POST"])
def handle_post():
    """Handle a post request with API call parameters and optionally filters defined in the form data as key-value pairs

    :returns: None, but either renders HTML or sends a file as response

    """
    # TODO: Handle sensible ways to do paths for params, so no <tileid>/<fiberids>
    data = request.form
    log("request: ", data)
    param_keys = ["command", "release", "endpoint", "params"]
    filters = {k: v for (k, v) in data.items() if k not in param_keys}
    try:
        req = build_request(
            data["command"], data["release"], data["endpoint"], data["params"], filters
        )
        validate(req)
    except (DesiApiException, KeyError) as e:
        invalid_request_error(e)
    else:
        return process_request(req)


def build_request(
    command: str, release: str, endpoint: str, params: str | Dict, filters: Dict
) -> ApiRequest:
    """Parse an API request path into an ApiRequest object. The parameters represent the components of the request URL.

    :returns: A parsed ApiRequest object.
    """
    # TODO: Descriptive error feedback

    try:
        command_enum = Command[command.upper()]
    except KeyError:
        raise DesiApiException(
            f"command must be one of DOWNLOAD or PLOT, not {command}"
        )

    try:
        endpoint_enum = Endpoint[endpoint.upper()]
    except KeyError:
        raise DesiApiException(
            f"endpoint must be one of TILE, TARGETS, RADEC, not {endpoint}"
        )

    release_canonised = release.lower()

    formal_params = (
        build_params_from_strings(endpoint_enum, params.split("/"))
        if isinstance(params, str)
        else build_params_from_dict(endpoint_enum, params)
    )

    return ApiRequest(
        command=command_enum,
        release=release_canonised,
        endpoint=endpoint_enum,
        params=formal_params,
        filters=filters,
    )


def build_params_from_dict(endpoint: Endpoint, params: Dict) -> Parameters:
    # TODO: Replace keys with consts, Kapstan style.
    try:
        if endpoint == Endpoint.RADEC:
            ra, dec, radius = [float(params[key]) for key in ["ra", "dec", "radius"]]
            return RadecParameters(ra, dec, radius)
        elif endpoint == Endpoint.TARGETS:
            return TargetParameters(parse_list_int(params["target_ids"]))
        elif endpoint == Endpoint.TILE:
            return TileParameters(
                int(params["tile_id"]), parse_list_int(params["fiber_ids"])
            )
    except:
        raise DesiApiException(f"invalid endpoint parameters for {endpoint}")


def build_params_from_strings(endpoint: Endpoint, params: List[str]) -> Parameters:
    """Build a Parameters object out of the API parameters (a list of arguments)

    :param endpoint: The type of the API request as an enum: One of Tile/Target/Radec
    :param params: A list of strings representing parameters in the API request, such as ['80605', '10,234,2761,3951']
    :returns: A Parameters object representing the parameters specified in the request.
    """
    try:
        if endpoint == Endpoint.RADEC:
            ra, dec, radius = parse_list_float(params[0])
            return RadecParameters(ra, dec, radius)
        elif endpoint == Endpoint.TARGETS:
            return TargetParameters(parse_list_int(params[0]))
        elif endpoint == Endpoint.TILE:
            return TileParameters(int(params[0]), parse_list_int(params[1]))
    except:
        raise DesiApiException(f"invalid endpoint parameters for {endpoint}")


def validate(req: ApiRequest):
    params = req.params
    if req.endpoint == Endpoint.RADEC:
        validate_radec(params)
    elif req.endpoint == Endpoint.TARGETS:
        validate_target(params)
    elif req.endpoint == Endpoint.TILE:
        validate_tile(params)
    else:
        raise DesiApiException("invalid endpoint")


def validate_radec(params: RadecParameters):
    if params.radius > 60:
        raise DesiApiException("radius must be <= 60 arcseconds")


def validate_tile(params: TileParameters):
    if len(params.fibers) > 500:
        raise DesiApiException("cannot have more than 500 fiber IDs")


def validate_target(params: TargetParameters):
    if len(params.target_ids) > 500:
        raise DesiApiException("cannot have more than 500 target IDs")


def invalid_request_error(e: Exception):
    """Take an error resulting from an invalid request, and wrap it in a Flask response"""
    info = dumps(
        {"Error": str(e), "Help": f"See {DOC_URL} for an overview of request syntax"}
    )
    abort(Response(info), 400)


def process_request(req: ApiRequest):
    """A simple wrapper around handle_request that does some error-handling"""
    try:
        return handle_request(req)
    except DesiApiException as e:
        info = dumps(
            {
                "Request": repr(req),
                "Error": str(e),
                "Help": f"See {DOC_URL} for an overview of request syntax",
            }
        )
        abort(Response(info), 500)


def handle_request(req: ApiRequest):
    """Processes an ApiRequest and returns the corresponding file, either HTML or FITS.

    :param req: An ApiRequest object
    :returns: An HTML or FITS file wrapped in Flask's send_file function.

    """

    req_time = dt.datetime.now()
    log("request: ", req)
    response_file = build_response_file(req, req_time)
    log("response file: ", response_file)
    if req.command == Command.PLOT:
        return send_file(response_file)
    else:
        return send_file(
            response_file, download_name=f"desi_api_{req_time.isoformat()}.fits"
        )


def build_response_file(req: ApiRequest, request_time: dt.datetime) -> str:
    """Build the file asked for by REQ, or reuse an existing one if it is sufficiently recent, and return the path to it

    :param req: An ApiRequest object
    :param request_time: The time the request was made, used for cache checks, etc.
    :returns: A complete path (including the file extension) to a created file that should be sent back as the response
    """
    cache_path = f"{CACHE_DIR}/{req.get_cache_path()}"
    if os.path.isdir(cache_path):
        cached_responses = os.listdir(cache_path)
        most_recent = (
            max(cached_responses, key=basename)
            if len(cached_responses)
            else dt.datetime.utcfromtimestamp(0).isoformat()
        )
        # Filenames are of the form <timestamp>.<ext>, the key filters out extension
        # If there are no cached responses, use 1970 as the time so it doesn't get selected.
        print("recent", basename(most_recent))
        age = request_time - dt.datetime.fromisoformat(basename(most_recent))
        print("age", age)
        if age < CUTOFF:
            log("using cache")
            return os.path.join(cache_path, most_recent)
    log("rebuilding")
    spectra = handle(req)
    resp_file_path = create_file(
        req.command, spectra, cache_path, request_time.isoformat()
    )
    return resp_file_path


def create_file(cmd: Command, spectra: Spectra, save_dir: str, file_name: str) -> str:
    """Creates a file at SAVE_PATH.<ext> generated from data in SPECTRA. The type of file (FITS vs HTML currently) is determined by CMD.

    :param cmd: Command from the request, one of DOWNLOAD or PLOT, defines whether the output is raw data or an HTML plot.
    :param spectra: The Spectra object to draw our data from
    :param save_path: The path (without an extension) to which we should save our file.
    :returns: The full path (including extension) to the file created
    """
    os.makedirs(save_dir, exist_ok=True)
    if cmd == Command.DOWNLOAD:
        target_file = f"{save_dir}/{file_name}.fits"
        try:
            desispec.io.write_spectra(target_file, spectra)
            return target_file
        except Exception as e:
            raise DesiApiException("unable to create spectra file")
    elif cmd == Command.PLOT:
        target_file = f"{save_dir}/{file_name}.html"
        return write_html(spectra, save_dir, file_name)
    else:
        raise DesiApiException("invalid command (must be PLOT or DOWNLOAD)")


def write_html(spectra: Spectra, save_dir: str, file_name: str) -> str:
    try:
        plotspectra(
            spectra,
            zcatalog=spectra.extra_catalog,
            html_dir=save_dir,
            title=file_name,
            with_vi_widgets=False,
            with_full_2ndfit=False,
            num_approx_fits=0,
        )
        return f"{save_dir}/{file_name}.html"
    except Exception as e:
        raise DesiApiException("unable to produce plot")


# For testing the pipeline from request -> build file, for testing on NERSC pre web-app
def test_file_gen(request_args: str) -> str:
    command, release, endpoint, *params = request_args.split("/")
    req = build_request(command, release, endpoint, "/".join(params), {})
    response_file = build_response_file(req, dt.datetime.now())
    return response_file


if __name__ == "__main__":
    app.run()
