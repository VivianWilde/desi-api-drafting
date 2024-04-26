#!/usr/bin/env ipython3

import datetime as dt
import os
import json
from typing import List

import desispec.io
import desispec.spectra
import fitsio
from desispec.spectra import Spectra
from flask import (
    Config,
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    send_file,
)
from prospect.viewer import plotspectra
import pandas as pd

from numpyencoder import NumpyEncoder


import build_spectra
from models import *
from utils import *
from cache import check_cache

DEBUG = True
app = Flask("DESI API Server")
# app.config.from_object(__name__)

DOC_URL = "https://github.com/VivianWilde/desi-api-drafting/blob/main/userdoc.org"


@app.route("/")
@app.route("/api")
@app.route("/api/v1")
def show_doc():
    return redirect(DOC_URL)


@app.route(
    "/api/v1/<requested_data>/<response_type>/<release>/<endpoint>/<path:endpoint_params>",
    methods=["GET"],
)
def handle_get(
    requested_data: str,
    response_type: str,
    release: str,
    endpoint: str,
    endpoint_params: str,
) -> Response:
    """Entrypoint. Accepts an arbitrary path (via a URL), translates it into an API request, builds the response as a file, and serves it over the network

    :param response_type: One of Download/Plot, specifies whether to return raw FITS data or an interactive HTML plot.
    :param release: The DESI release from which to draw data.
    :param endpoint: One of Tile/Target/Radec, the endpoint to query.
    :param params: Endpoint-specific parameters, such as a tile ID and list of fibers, a list of target IDs, or a (ra, dec) point and radius.
    :returns: None, but either renders HTML or sends a file as a response.
    """
    log("params: ", endpoint_params)
    try:
        req = build_request(
            requested_data,
            response_type,
            release,
            endpoint,
            endpoint_params,
            request.args.to_dict(),
        )
        validate(req)
    except (DesiApiException, KeyError) as e:
        return invalid_request_error(e)
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
    param_keys = ["requested_data" "response_type", "release", "endpoint", "params"]
    filters = {k: v for (k, v) in data.items() if k not in param_keys}
    try:
        # TODO data re
        req = build_request(
            data["requested_data"],
            data["response_type"],
            data["release"],
            data["endpoint"],
            data["params"],
            filters,
        )
        validate(req)
    except (DesiApiException, KeyError) as e:
        return invalid_request_error(e)
    else:
        return process_request(req)


def build_request(
    requested_data: str,
    response_type: str,
    release: str,
    endpoint: str,
    params: str | dict,
    filters: dict,
) -> ApiRequest:
    """Parse an API request path into an ApiRequest object. The parameters represent the components of the request URL.

    :returns: A parsed ApiRequest object.
    """
    try:
        requested_data_enum = RequestedData[requested_data.upper()]
    except KeyError:
        raise DesiApiException(
            f"requested_data must be one of ZCAT or SPECTRA, not {requested_data}"
        )

    try:
        response_type_enum = ResponseType[response_type.upper()]
    except KeyError:
        raise DesiApiException(
            f"response_type must be one of DOWNLOAD or PLOT, not {response_type}"
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
        requested_data=requested_data_enum,
        response_type=response_type_enum,
        release=release_canonised,
        endpoint=endpoint_enum,
        params=formal_params,
        filters=filters,
    )


def validate(req: ApiRequest):
    return True  # FIXME kept for testing
    params = req.params
    if req.requested_data == RequestedData.ZCAT:
        return True  # no restrictions on zcat endpoint (for now)
    if req.endpoint == Endpoint.RADEC:
        validate_radec(params)
    elif req.endpoint == Endpoint.TARGETS:
        validate_target(params)
    elif req.endpoint == Endpoint.TILE:
        validate_tile(params)
    else:
        raise DesiApiException("invalid endpoint")


def process_request(req: ApiRequest) -> Response:
    """A simple wrapper around handle_request that does some error-handling"""
    try:
        return exec_request(req)
    except DesiApiException as e:
        info = json.dumps(
            {
                "Request": repr(req),
                "Error": str(e),
                "Help": f"See {DOC_URL} for an overview of request syntax",
            }
        )
        log(e)
        abort(Response(info, status=500))


def exec_request(req: ApiRequest) -> Response:
    """Processes an ApiRequest and returns the corresponding file, either HTML or FITS.

    :param req: An ApiRequest object
    :returns: An HTML or FITS file wrapped in Flask's send_file function.
    """
    req_time = dt.datetime.now()
    log("request: ", req)
    response_file = build_response(req, req_time)
    log("response file: ", response_file)

    if mimetype(response_file) == ".html":
        return send_file(response_file)
    else:
        ext = mimetype(response_file)
        return send_file(
            response_file,
            download_name=f"desi_api_{req_time.isoformat()}.{ext}",  # TODO: FIlename may not be fits
        )


def build_response(req: ApiRequest, request_time: dt.datetime) -> str:
    """Build the file asked for by REQ, or reuse an existing one if it is sufficiently recent, and return the path to it

    :param req: An ApiRequest object
    :param request_time: The time the request was made, used for cache checks, etc.
    :returns: A complete path (including the file extension) to a created file that should be sent back as the response
    """
    cached = check_cache(req, request_time, app.config["cache"])
    if cached:
        return cached
    cache_path = f"{app.config['cache']['path']}/{req.get_cache_path()}"

    if req.requested_data == RequestedData.SPECTRA:
        spectra = build_spectra.handle_spectra(req)
        resp_file_path = create_spectra_file(
            req.response_type, spectra, cache_path, request_time.isoformat()
        )
        return resp_file_path
    else:
        zcatalog = build_spectra.handle_zcatalog(
            req
        )  # object returned by fitsio.read + slicing/dicing
        resp_file_path = create_zcat_file(
            req.response_type,
            zcatalog,
            cache_path,
            request_time.isoformat(),
            req.filters,
        )
        return resp_file_path


def create_zcat_file(
    response_type: ResponseType,
    zcat: Zcatalog,
    save_dir: str,
    file_name: str,
    filters: Filter,
) -> str:
    """Write a collection of zcatalog metadata to either an Html or Fits file, cache that file, and return the path to it.

    :param response_type: One of download/plot
    :param zcat: Data to be written to a file
    :param save_dir: Path to the cache dir to save the file
    :param file_name:
    :param filters: A collection of key-value pairs. Mainly used to indicate the desired file format
    :returns: Path to a file containing the Zcat info
    """

    os.makedirs(save_dir, exist_ok=True)

    if response_type == ResponseType.PLOT:
        # We want an html table
        return zcat_to_html(zcat, save_dir, file_name)
    else:
        filetype = filters.get("filetype", DEFAULT_FILETYPE).lower()
        # Do the complex figuring.
        # For now, just do FITS.
        target_file = f"{save_dir}/{file_name}.{filetype}"
        try:
            write_zcat_to_file(target_file, zcat, filetype)
            return target_file
        except Exception as e:
            raise DesiApiException(
                "unable to create spectra file - fitsio failed to write to "
                + target_file
            )

def write_zcat_to_file(target_file: str, zcat: Zcatalog, filetype:str):
    log("requested filetype: ", filetype)
    match filetype:
        case "fits":
            fitsio.write(target_file, zcat)
        case "json":
            with open(target_file, "w") as f:
                f.write(zcat_to_json_str(zcat))
        case _:
            raise DesiApiException("invalid filetype requested")


def zcat_to_json_str(zcat: Zcatalog) -> str:
    """Jsonify the data in the Zcatalog object ZCAT and return the raw Json data."""

    keys = zcat.dtype.names
    return json.dumps([dict(zip(keys, record)) for record in zcat], cls=NumpyEncoder)


def create_spectra_file(
    response_type: ResponseType, spectra: Spectra, save_dir: str, file_name: str
) -> str:
    """Creates a file at SAVE_PATH.<ext> generated from data in SPECTRA. The type of file (FITS vs HTML currently) is determined by RESPONSE_TYPE.

    :param response_type: Response type from the request, one of DOWNLOAD or PLOT, defines whether the output is raw data or an HTML plot.
    :param spectra: The Spectra object to draw our data from
    :param save_path: The path (without an extension) to which we should save our file.
    :returns: The full path (including extension) to the file created
    """
    os.makedirs(save_dir, exist_ok=True)
    if response_type == ResponseType.DOWNLOAD:
        target_file = f"{save_dir}/{file_name}.fits"
        try:
            desispec.io.write_spectra(target_file, spectra)
            return target_file
        except Exception as e:
            raise DesiApiException("unable to create spectra file")
    elif response_type == ResponseType.PLOT:
        return spectra_to_html(spectra, save_dir, file_name)
    else:
        raise DesiApiException("invalid response_type (must be PLOT or DOWNLOAD)")


def zcat_to_html(zcat: Zcatalog, save_dir: str, file_name: str) -> str:
    """Render ZCAT data to an interactive html table based on a template, and return the path to the filled-in html file

    :param zcat: The Zcatalog metadata to generate a table from
    :param save_dir:
    :param file_name:
    :returns:

    """

    html_file = f"{save_dir}/{file_name}.html"
    json_data = zcat_to_json_str(zcat)
    with open(html_file, "w") as out:
        out.write(
            render_template("table.html", columns=zcat.dtype.names, json_data=json_data)
        )
    return html_file


def spectra_to_html(spectra: Spectra, save_dir: str, file_name: str) -> str:
    """Render Spectra data to an interactive html plot using the DESI Prosect library, and return the path to the html file.

    :param spectra:
    :param save_dir:
    :param file_name:
    :returns:

    """

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
        raise e
        # raise DesiApiException("unable to produce plot")


# Validation Functions/Rules:


def validate_radec(params: RadecParameters):
    if params.radius > 60:
        raise DesiApiException("radius must be <= 60 arcseconds")


def validate_tile(params: TileParameters):
    if len(params.fibers) > 500:
        raise DesiApiException("cannot have more than 500 fiber IDs")


def validate_target(params: TargetParameters):
    if len(params.target_ids) > 500:
        raise DesiApiException("cannot have more than 500 target IDs")


# Helper Functions:


def build_params_from_dict(endpoint: Endpoint, params: dict) -> Parameters:
    """Given a dictionary of endpoint params, parse that into a params object

    :param endpoint: The endpoint these params correspond to (tells us what structure the params object has)
    :param params: The formal endpoint parameters and their values
    :returns: A parsed Parameters object

    """

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


def invalid_request_error(e: Exception) -> Response:
    """Take an error resulting from an invalid request, and wrap it in a Flask response"""
    info = json.dumps(
        {"Error": str(e), "Help": f"See {DOC_URL} for an overview of request syntax"}
    )
    return Response(info, status=400)


# For testing the pipeline from request -> build file, for testing on NERSC pre web-app
def test_file_gen(request_args: str) -> str:
    requested_data, response_type, release, endpoint, *params = request_args.split("/")
    req = build_request(
        requested_data, response_type, release, endpoint, "/".join(params), {}
    )
    response_file = build_response(req, dt.datetime.now())
    return response_file


def run_app(config: dict):
    """Load the configuration values from CONFIG into the app's internal config and start the server

    :param config:
    :returns:

    """

    # app.config["SECRET_KEY"] = "7d441f27d441f27567d441f2b6176a"
    app.config.update(config)
    app.run(host="0.0.0", debug=True)


# if __name__ == "__main__":
#     main()
