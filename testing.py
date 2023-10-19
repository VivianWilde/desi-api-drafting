#!/usr/bin/env ptpython
from build_spectra import *
from models import *

# from webapp import *


def test_tile():
    fibers = [10, 234, 2761, 3951]
    params = TileParameters(tile=80605, fibers=fibers)
    req = ApiRequest(
        command=Command.DOWNLOAD,
        request_type=RequestType.TILE,
        release="fuji",
        params=params,
    )
    result = handle(req)
    print(result.fibermap["FIBER", "TARGETID"])
    assert sorted(result.fibermap["FIBER"]) == sorted(fibers)


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
        request_type=RequestType.TARGETS,
        release="fuji",
        params=params,
    )
    result = handle(req)
    print(result.fibermap["TARGETID"])
    assert sorted(result.fibermap["TARGETID"]) == sorted(targets)


test_target()
