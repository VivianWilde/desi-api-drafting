#!/usr/bin/env ptpython
from build_spectra import *
from models import *
from webapp import *

def test_tile():
    params = TileParameters(tile=80605, fibers=[10, 234, 2761, 3951])
    req = ApiRequest(
        command=Command.DOWNLOAD,
        request_type=RequestType.TILE,
        release="fuji",
        params=params,
    )
    result = handle(req)
    assert sorted(result['FIBER'])=[10,234,2761,3951]
    return result
