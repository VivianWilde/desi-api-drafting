#!/usr/bin/env ipython3

from flask import Flask, send_file
from pathlib import Path
from typing import List
import build_spectra as builder


def parse_list(lst: str) -> List[int]:
    """ Takes in a string representing a comma-separated list of integers (no spaces) and returns the list

    :param lst:
    :returns:
    """
    return [int(i) for i in lst.split(",")]

@app.route('<path: params>')
def top_level(params: str):
    req = build_request(params)
    response_file = handle(req)
    # TODO: logic for return html vs send file
	return send_file(response_file, attachment_filename=req.get_cache_path())




def build_request(params: str) -> builder.ApiRequest:
    return builder.ApiRequest()


def handle(req: builder.ApiRequest) -> str:
    """ Build the file asked for by request, and return the path to it

    :param req:
    :returns:

    """
    # TODO: Extract into cache utils
    path = req.get_cache_path()
    cached_responses = os.listdir(path)
    most_recent = max(cached_responses, key= lambda i: int(i))
    # TODO: Convert most_recent to time, do TimeDelta

    if age < cutoff:
        return most_recent # TODO: make it back into a path

    request_time = time.now()
    spectra = builder.handle(req)
    resp_file =  build_file(req.command, spectra)
    path = concat_path(path, request_time)
    save_file(resp_file, path)
    return path

def build_file(cmd: builder.Command, spectra: builder.Spectra):
    if cmd == builder.Command.DOWNLOAD:
        desispec.io.write_spectra() # TODO
    elif cmd == builder.Command.PLOT:
        # TODO plotting - use matpolotlib example from demo for now
