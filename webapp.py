#!/usr/bin/env ipython3

from flask import Flask, send_file, send_from_directory
from typing import List

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


@app.route("/api/v1/<command>/<release>/<endpoint>/<path:params>")
def top_level(command: str, release: str, endpoint: str, params: str):
    """Entrypoint. Accepts an arbitrary path (via a URL), translates it into an API request, builds the response as a file, and serves it over the network

    :param command: One of Download/Plot, specifies whether to return raw FITS data or an interactive HTML plot.
    :param release: The DESI release from which to draw data.
    :param endpoint: One of Tile/Target/Radec, the endpoint to query.
    :param params: Endpoint-specific parameters, such as a tile ID and list of fibers, a list of target IDs, or a (ra, dec) point and radius.
    :returns: None, but either renders HTML or sends a file as a response.
    """
    req_time = dt.datetime.now()
    log("params: ", params)
    req = build_request(command, release, endpoint, params)
    log("request: ", req)

    response_file = build_response_file(req, req_time)
    log("response file: ", response_file)
    if req.command == Command.PLOT:
        return send_file(response_file)
    else:
        return send_file(
            response_file, download_name=f"desi_api_{req_time.isoformat()}.fits"
        )


def validate(req: ApiRequest):
    # switch case on req type
    pass


def validate_radec(params: RadecParameters):
    pass


def validate_tile(params: TileParameters):
    pass


def validate_target(params: TargetParameters):
    pass


def build_request(command: str, release: str, endpoint: str, params: str) -> ApiRequest:
    """Parse an API request path into an ApiRequest object. The parameters represent the components of the request URL.

    :returns: A parsed ApiRequest object.
    """
    command_enum = Command[command.upper()]
    endpoint_enum = Endpoint[endpoint.upper()]
    release_canonised = release.lower()

    formal_params = build_params(endpoint_enum, params.split("/"))

    return ApiRequest(
        command=command_enum,
        release=release_canonised,
        endpoint=endpoint_enum,
        params=formal_params,
    )


def build_params(endpoint: Endpoint, params: List[str]) -> Parameters:
    """Build a Parameters object out of the API parameters (a list of arguments)

    :param endpoint: The type of the API request as an enum: One of Tile/Target/Radec
    :param params: A list of strings representing parameters in the API request, such as ['80605', '10,234,2761,3951']
    :returns: A Parameters object representing the parameters specified in the request.
    """

    if endpoint == Endpoint.RADEC:
        ra, dec, radius = parse_list_float(params[0])
        return RadecParameters(ra, dec, radius)
    elif endpoint == Endpoint.TARGETS:
        return TargetParameters(parse_list_int(params[0]))
    elif endpoint == Endpoint.TILE:
        return TileParameters(int(params[0]), parse_list_int(params[1]))


def build_response_file(
    req: ApiRequest, request_time: dt.datetime 
) -> str:
    """Build the file asked for by REQ, or reuse an existing one if it is sufficiently recent, and return the path to it

    :param req: An ApiRequest object
    :param request_time: The time the request was made, used for cache checks, etc.
    :returns: A complete path (including the file extension) to a created file that should be sent back as the response
    """
    cache_path = f"{CACHE_DIR}/{req.get_cache_path()}"
    if os.path.isdir(cache_path):
        cached_responses = os.listdir(cache_path)
        most_recent = max(cached_responses, key=basename)
        # Filenames are of the form <timestamp>.<ext>, the key filters out extension
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
            raise DesiApiException(e)
    elif cmd == Command.PLOT:
        target_file = f"{save_dir}/{file_name}.html"
        return write_html(spectra, save_dir, file_name)
    else:
        raise DesiApiException("Invalid Command (must be PLOT or DOWNLOAD)")


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
        raise DesiApiException(e)


# For testing the pipeline from request -> build file, for testing on NERSC pre web-app
def test_file_gen(request_args: str) -> str:
    command, release, endpoint, *params = request_args.split("/")
    req = build_request(command, release, endpoint, "/".join(params))
    response_file = build_response_file(req, dt.datetime.now())
    return response_file


if __name__ == "__main__":
    app.run()
