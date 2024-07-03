#!/usr/bin/env ipython3

import datetime as dt
import json
from typing import List

from flask import Flask, Response, abort, redirect, request, send_file
from json import loads

from ..convert.memmap import preload_memmaps

from ..common.errors import DesiApiException, MalformedRequestException
from ..common.models import *
from ..common.utils import *
from .response_file import build_response

DEBUG = True
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
app = Flask("DESI API Server", template_folder=TEMPLATE_DIR)
# app.config.from_object(__name__)

DOC_URL = (
    "https://github.com/VivianWilde/desi-api-drafting/blob/main/doc/user/userdoc.md"
)


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
    data = loads(request.json)
    log("request: ", data)
    param_keys = ["requested_data", "response_type", "release", "endpoint", "params"]
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
        raise MalformedRequestException(
            f"requested_data must be one of ZCAT or SPECTRA, not {requested_data}"
        )

    try:
        response_type_enum = ResponseType[response_type.upper()]
    except KeyError:
        raise MalformedRequestException(
            f"response_type must be one of DOWNLOAD or PLOT, not {response_type}"
        )

    try:
        endpoint_enum = Endpoint[endpoint.upper()]
    except KeyError:
        raise MalformedRequestException(
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
        raise MalformedRequestException("invalid endpoint")


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
            }, indent=4
        )
        log(e)
        abort(Response(info, status=500))


def exec_request(req: ApiRequest) -> Response:
    """Processes an ApiRequest and returns the corresponding file, either HTML or FITS.

    :param req: An ApiRequest object
    :returns: An HTML or FITS file wrapped in Flask's send_file function.
    """
    req_time = dt.datetime.now()
    log("request: ", req.__repr__())
    response_file = build_response(
        req,
        req_time,
        cache_root=app.config["cache"]["path"],
        cache_max_age=app.config["cache"]["max_age"],
    )
    # log("response file: ", response_file)

    if mimetype(response_file) == ".html":
        return send_file(response_file)
    else:
        ext = mimetype(response_file)
        requested_data = req.requested_data.name.lower()
        return send_file(
            response_file,
            download_name=f"desi_api_{req_time.isoformat()}.{requested_data}.{ext}",  # .spectra.fits or .zcat.fits
        )


# Validation Functions/Rules:


def validate_radec(params: RadecParameters):
    if params.radius > 60:
        raise MalformedRequestException("radius must be <= 60 arcseconds")


def validate_tile(params: TileParameters):
    if len(params.fibers) > 500:
        raise MalformedRequestException("cannot have more than 500 fiber IDs")


def validate_target(params: TargetParameters):
    if len(params.target_ids) > 500:
        raise MalformedRequestException("cannot have more than 500 target IDs")


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
            return TargetParameters(params["target_ids"])
        elif endpoint == Endpoint.TILE:
            return TileParameters(int(params["tile"]), params["fibers"])
    except:
        raise MalformedRequestException(f"invalid endpoint parameters for {endpoint}")


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
        raise MalformedRequestException(f"invalid endpoint parameters for {endpoint}")


def invalid_request_error(e: Exception) -> Response:
    """Take an error resulting from an invalid request, and wrap it in a Flask response"""
    info = json.dumps(
        {"Error": str(e), "Help": f"See {DOC_URL} for an overview of request syntax"}, indent=4
    )
    return Response(info, status=400)


def run_app(config: dict):
    """Load the configuration values from CONFIG into the app's internal config and start the server

    :param config:
    :returns:

    """
    app.config.update(config)
    # Doesn't save the results anywhere, but calling it should cause the value to be cached if functools does its job
    preload_memmaps(PRELOAD_RELEASES)
    app.run(host="0.0.0", debug=True)


# For testing the pipeline from request -> build file, for testing on NERSC pre web-app
def test_file_gen(request_args: str) -> str:
    requested_data, response_type, release, endpoint, *params = request_args.split("/")
    req = build_request(
        requested_data, response_type, release, endpoint, "/".join(params), {}
    )
    response_file = response_file_gen.build_response(
        req, dt.datetime.now(), app.config["cache"]
    )
    return response_file
