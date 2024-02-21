#!/usr/bin/env ptpython
from build_spectra import *
from models import *

from webapp import test_file_gen

import requests

def test_tile_zcat():
    fibers = [10, 234, 2761, 3951]
    params = TileParameters(tile=80605, fibers=fibers)
    req = ApiRequest(
        requested_data=RequestedData.ZCAT,
        command=Command.DOWNLOAD,
        endpoint=Endpoint.TILE,
        release="fuji",
        params=params,
        filters=dict(),
    )
    result = handle_zcat(req)
    print(result)



def test_tile():
    fibers = [10, 234, 2761, 3951]
    params = TileParameters(tile=80605, fibers=fibers)
    req = ApiRequest(
        command=Command.DOWNLOAD,
        endpoint=Endpoint.TILE,
        release="fuji",
        params=params,
        filters=dict(),
    )
    result = handle_spectra(req)
    print(result)
    print(result.fibermap["FIBER", "TARGETID"])
    assert sorted(result.fibermap["FIBER"]) == sorted(fibers)
    return result


def test_target():
    targets = [
        39628473198710603,
        39632946386177593,
        39632956452508085,
        39632971434560784,
    ]
    params = TargetParameters(target_ids=targets)
    req = ApiRequest(
        command=Command.DOWNLOAD,
        endpoint=Endpoint.TARGETS,
        release="fuji",
        params=params,
        filters=dict(),
    )
    result = handle(req)
    print(result)
    print(result.fibermap["TARGETID"])
    assert sorted(result.fibermap["TARGETID"]) == sorted(targets)
    return result


def test_target_zcat():
    targets = [
        39628473198710603,
        39632946386177593,
        39632956452508085,
        39632971434560784,
    ]
    params = TargetParameters(target_ids=targets)
    req = ApiRequest(
        requested_data=RequestedData.ZCAT,
        command=Command.DOWNLOAD,
        endpoint=Endpoint.TARGETS,
        release="fuji",
        params=params,
        filters=dict(),
    )
    result = handle_zcat(req)
    print(result)
    # print(result.fibermap["TARGETID"])
    # assert sorted(result.fibermap["TARGETID"]) == sorted(targets)
    return result

def test_target_filters():
    target_data = [
        (39628473198710603, "cmx", "other", 2152, 23.76486248, 29.83237896, True),
        (39632946386177593, "special", "dark", 9161, 224.43884348, 33.20396119, True),
        (39632956452508085, "special", "dark", 9185, 222.58404957, 33.84867304, True),
        (39632971434560784, "sv3", "bright", 9150, 218.99193255, 34.45646842, True),
    ]
    dark = [39632946386177593, 39632956452508085]

    targets = [
        39628473198710603,
        39632946386177593,
        39632956452508085,
        39632971434560784,
    ]
    params = TargetParameters(target_ids=targets)
    req = ApiRequest(
        requested_data=RequestedData.SPECTRA,
        command=Command.DOWNLOAD,
        endpoint=Endpoint.TARGETS,
        release="fuji",
        params=params,
        filters={"PROGRAM":"=dark"},
    )
    result = handle(req)
    print(result)
    print(result.fibermap["TARGETID"])
    assert sorted(result.fibermap["TARGETID"]) == sorted(dark)
    return result


# Webapp mocking
def test_app_tile():
    x = test_file_gen("plot/fuji/tile/80605/10,234,2761,3951")
    print(x)
    return x


def test_app_target():
    x = test_file_gen(
        "download/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784?survey=main"
    )
    print(x)
    return x


# Webapp testing


def test_get_targets():
    return requests.get(
        "http://127.0.0.1:5000/api/v1/download/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784?survey=main",
    )


def test_get_tile():
    return requests.get(
        "http://127.0.0.1:5000/api/v1/plot/fuji/tile/80605/10,234,2761,3951"
    )


def test_post_targets():
    data = {
        "command": "download",
        "release": "fuji",
        "endpoint": "targets",
        "params": "39628473198710603,39632946386177593,39632956452508085,39632971434560784",
        "survey": "main",
    }
    resp = requests.post("http://127.0.0.1:5000/api/v1/post", data=data)
    return resp

    # requests.get("http://127.0.0.1:5000/api/v1/plot/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784?survey=main", )


test_tile_zcat()
test_target_zcat()
