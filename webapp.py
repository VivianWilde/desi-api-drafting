#!/usr/bin/env ipython3

from flask import Flask, send_file, render_template
from typing import List
from build_spectra import handle
import datetime as dt
from models import *
import desispec.io, desispec.spectra
from desispec.spectra import Spectra
from prospect.viewer import plotspectra


import os



@app.route("/api/v1/<path:params>")
def top_level(params: str):
    """Entrypoint. Accepts an arbitrary path (via a URL), translates it into an API request, builds the response as a file, and serves it over the network

    :param params: Query params/URL string/whatever
    :returns: None, but either renders HTML or sends a file as a response

    """
    req = build_request(params)
    response_file = build_response_file(req, dt.datetime.now())
    if mimetype(response_file) == "html":
        return render_template(response_file)
    return send_file(response_file, download_name=f"{req.get_cache_path()}.fits")

def test_file_gen(params: str) -> str:
    req = build_request(params)
    response_file = build_response_file(req, dt.datetime.now())
    return response_file


def build_request(request: str) -> ApiRequest:
    """Parse an API request path into an ApiRequest object

    :param request: The slash-separated string representing the raw path of the API request
    :returns: A parsed ApiRequest object.
    """

    command, release_name, req_type, *params = request.split("/")

    command_enum = Command[command.upper()]
    req_type_enum = RequestType[req_type.upper()]
    release_canonised = release_name.lower()

    formal_params = build_params(req_type_enum, params)

    return ApiRequest(
        command=command_enum,
        release=release_canonised,
        request_type=req_type_enum,
        params=formal_params,
    )


def build_params(req_type: RequestType, params: List[str]) -> Parameters:
    """Build a Parameters object out of the API parameters (a list of arguments)

    :param req_type: The type of the API request as an enum: One of Tile/Target/Radec
    :param params: A list of strings representing parameters in the API request, such as ['80605', '10,234,2761,3951']
    :returns: A Parameters object representing the parameters specified in the request.
    """

    if req_type == RequestType.RADEC:
        ra, dec, radius = parse_list(params[0])
        return RadecParameters(ra, dec, radius)
    elif req_type == RequestType.TARGETS:
        return TargetParameters(parse_list(params[0]))
    elif req_type == RequestType.TILE:
        return TileParameters(int(params[0]), parse_list(params[1]))


def build_response_file(
    req: ApiRequest, request_time: dt.datetime = dt.datetime.now()
) -> str:
    """Build the file asked for by REQ, or reuse an existing one if it is sufficiently recent, and return the path to it

    :param req: An ApiRequest object
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
            print("Used cache")
            return os.path.join(cache_path, most_recent)
    print("Rebuilding")
    spectra = handle(req)
    resp_file_path = create_file(req.command, spectra, cache_path, request_time.isoformat())
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
        desispec.io.write_spectra(target_file, spectra)
        return target_file
    elif cmd == Command.PLOT:
        target_file = f"{save_dir}/{file_name}.html"
        return write_html(spectra, save_dir, file_name)
    return ""


def write_html(spectra: Spectra, save_dir: str, file_name: str)->str:
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


# File utilities for readability
def mimetype(path: str) -> str:
    """Returns the extension of the file"""
    return os.path.splitext(path)[1].lower()


def filename(path: str) -> str:
    """Return the file name and extension (no path info)"""
    return os.path.split(path)[0]


def basename(path: str):
    """Return the file name without extension or path info"""
    return os.path.splitext(path)[0]


def parse_list(lst: str) -> List[int]:
    """Takes in a string representing a comma-separated list of integers (no spaces) and returns the list"""
    return [int(i) for i in lst.split(",")]


def main():
    """Start a server running the webapp"""
    DEBUG = True
    app = Flask(__name__)
    app.config.from_object(__name__)
    app.config["SECRET_KEY"] = "7d441f27d441f27567d441f2b6176a"


    app.run()


if __name__ == "__main__":
    main()
