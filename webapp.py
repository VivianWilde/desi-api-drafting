#!/usr/bin/env ipython3

from flask import Flask, send_file, render_template
from pathlib import Path
from typing import List
import build_spectra as builder
import datetime as dt
from models import *




DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "7d441f27d441f27567d441f2b6176a"


def parse_list(lst: str) -> List[int]:
    """Takes in a string representing a comma-separated list of integers (no spaces) and returns the list

    :param lst:
    :returns:
    """
    return [int(i) for i in lst.split(",")]


@app.route("<path: params>")
def top_level(params: str):
    req = build_request(params)
    response_file = build_response_file(req)
    # TODO: logic for return html vs send file
    # Make it dumb. Just check if
    if mimetype(response_file) == "HTML":
        return render_template(response_file)
    return send_file(response_file, attachment_filename=req.get_cache_path())


def build_request(params: str) -> ApiRequest:
    return ApiRequest()


def build_response_file(
    req: ApiRequest, request_time: dt.datetime = dt.datetime.now()
) -> str:
    """Build the file asked for by request, and return the path to it

    :param req:
    :returns:

    """
    # TODO: Extract into cache utils
    path = req.get_cache_path()
    cached_responses = os.listdir(path)
    most_recent = max(cached_responses, key=int)
    # TODO: Convert most_recent to time, do TimeDelta
    age = most_recent_time - request_time
    if age < CUTOFF:
        return most_recent  # TODO: make it back into a path, adjoin to get_cache_path()?
    spectra = builder.handle(req)
    resp_file = build_file(req.command, spectra)
    path = concat_path(path, request_time)
    save_file(resp_file, path)
    return path


def build_file(cmd: Command, spectra: Spectra):
    if cmd == Command.DOWNLOAD:
        desispec.io.write_spectra()  # TODO
    elif cmd == Command.PLOT:
        # TODO plotting - use matpolotlib example from demo for now
        pass


# def concat_path

def main():
    # start a server
    app.run()
