#!/usr/bin/env ptpython
from build_spectra import *
from models import *

from webapp import test_file_gen

import requests


def test_tile():
    fibers = [10, 234, 2761, 3951]
    params = TileParameters(tile=80605, fibers=fibers)
    req = ApiRequest(
        command=Command.DOWNLOAD,
        endpoint=Endpoint.TILE,
        release="fuji",
        params=params,
    )
    result = handle(req)
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
    )
    result = handle(req)
    print(result)
    print(result.fibermap["TARGETID"])
    assert sorted(result.fibermap["TARGETID"]) == sorted(targets)
    return result



# Webapp mocking
def test_app_tile():
    x= test_file_gen("plot/fuji/tile/80605/10,234,2761,3951")
    print(x)
    return x

def test_app_target():
    x= test_file_gen("download/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784?survey=main")
    print(x)
    return x


# Webapp testing

def test_get_targets():
     return requests.get("http://127.0.0.1:5000/api/v1/download/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784?survey=main", )

def test_get_tile():
    return requests.get("http://127.0.0.1:5000/api/v1/plot/fuji/tile/80605/10,234,2761,3951")

def test_post_targets():
    data = {"command":"download", "release":"fuji","endpoint":"targets","params":"39628473198710603,39632946386177593,39632956452508085,39632971434560784", "survey":"main"}
    resp = requests.post("http://127.0.0.1:5000/api/v1/post", data=data)
    return resp


     # requests.get("http://127.0.0.1:5000/api/v1/plot/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784?survey=main", )
# test_post_targets()
