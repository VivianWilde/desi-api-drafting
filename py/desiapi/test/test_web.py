#!/usr/bin/env python
import requests

from ..common.build_spectra import *
from ..common.models import *
from ..web.server import test_file_gen

# Build_spectra tests: Test it gets the right data in our internal python format


def test_tile_zcat():
    fibers = [10, 234, 2761, 3951]
    params = TileParameters(tile=80605, fibers=fibers)
    req = ApiRequest(
        requested_data=RequestedData.ZCAT,
        response_type=ResponseType.DOWNLOAD,
        endpoint=Endpoint.TILE,
        release="fuji",
        params=params,
        filters=dict(),
    )
    result = handle_zcatalog(req)
    print(result)
    return result


def test_tile():
    fibers = [10, 234, 2761, 3951]
    params = TileParameters(tile=80605, fibers=fibers)
    req = ApiRequest(
        requested_data=RequestedData.SPECTRA,
        response_type=ResponseType.DOWNLOAD,
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


# test_tile()


def test_target():
    targets = [
        39628473198710603,
        39632946386177593,
        39632956452508085,
        39632971434560784,
    ]
    params = TargetParameters(target_ids=targets)
    req = ApiRequest(
        response_type=ResponseType.DOWNLOAD,
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
        response_type=ResponseType.DOWNLOAD,
        endpoint=Endpoint.TARGETS,
        release="fuji",
        params=params,
        filters={"PROGRAM": "=dark"},
    )
    result = handle_zcatalog(req)
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
        response_type=ResponseType.DOWNLOAD,
        endpoint=Endpoint.TARGETS,
        release="fuji",
        params=params,
        filters={"PROGRAM": "=dark"},
    )
    result = handle(req)
    print(result)
    print(result.fibermap["TARGETID"])
    assert sorted(result.fibermap["TARGETID"]) == sorted(dark)
    return result


# App tests: Given an endpoint string, build and return response file for it
def meta_test_app(req: str):
    x = test_file_gen(req)
    print(x)
    return x


def test_app_tile():
    return meta_test_app("spectra/plot/fuji/tile/80605/10,234,2761,3951")


def test_app_target():
    return meta_test_app(
        "spectra/download/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784?survey=main"
    )


# Webapp testing
vi_endpoint = {
    "targets": "zcat/download/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784?program=dark",
    "tile": "spectra/plot/fuji/tile/80605/10,234,2761,3951",
}


def test_get(req: str):
    resp = requests.get("http://127.0.0.1:5000/api/v1/" + req)
    print(req)
    print(resp.status_code)
    assert resp.status_code == 200
    assert resp.content != ""
    return resp


def test_post(req: str, args: dict):
    resp = requests.post("http://127.0.0.1:5000/api/v1/post", data=args)
    assert resp.status_code == 200
    assert resp.content != ""
    return resp


def test_get_targets():
    return test_get(vi_endpoint["targets"])


def test_get_tile():
    return test_get(vi_endpoint["tile"])


def test_post_targets():
    data = {
        "requested_data": "ZCAT",
        "response_type": "DOWNLOAD",
        "release": "fujilite",
        "endpoint": "TARGETS",
        "params": "39628473198710603,39632946386177593,39632956452508085,39632971434560784",
        "survey": "main",
    }
    return test_post("http://127.0.0.1:5000/api/v1/post", data)


# Fujilite

spectra_plot_endpoints = [
    "spectra/plot/fujilite/radec/210.9,24.8,180",  # FIXME
    "spectra/plot/fujilite/tile/80858/600,900,1000",  # FIXME
    "spectra/plot/fujilite/targets/39628368387245557,39628368404022902",  # Works
]

fujilite_endpoints = [
    "spectra/download/fujilite/radec/210.9,24.8,180",  # Works
    "spectra/download/fujilite/tile/80858/600,900,1000",
    "spectra/download/fujilite/radec/210.9,24.8,180",  # Works
    "zcat/download/fujilite/radec/210.9,24.8,180",  # Works
    "zcat/download/fujilite/tile/80858/600,900,1000",  # Works
    "zcat/download/fujilite/targets/39628368387245557,39628368404022902",  # Works
]

zcat_plot_endpoints = [
    "zcat/plot/fujilite/radec/210.9,24.8,180",
    "zcat/plot/fujilite/tile/80858/600,900,1000",
    "zcat/plot/fujilite/targets/39628368387245557,39628368404022902",
]

filter_endpoints = [
    # "spectra/download/fujilite/radec/210.9,24.8,180?healpix=>8939",
    "zcat/download/fujilite/radec/210.9,24.8,180?healpix=>8939",
    "zcat/download/fujilite/tile/80858/600,900,1000?fiber=<950",
    # "zcat/plot/fujilite/targets/39628368387245557,39628368404022902?survey==sv2",
    "zcat/download/fujilite/targets/39628368387245557,39628368404022902?survey==sv2",
]


def test_fujilite(endpoints: List[str]):
    resps = dict()
    for endpoint in endpoints:
        resps[endpoint] = test_get(endpoint)
    return resps
    # resps = [test_get(endpoint) for endpoint in fujilite_endpoints]


def test_fujilite_filegen():
    resps = dict()
    for endpoint in fujilite_endpoints:
        resps[endpoint] = test_file_gen(endpoint)
    return resps

if __name__ == "__main__":
    # test_fujilite(spectra_plot_endpoints)
    test_fujilite(fujilite_endpoints)
    test_fujilite(zcat_plot_endpoints)
# test_fujilite(filter_endpoints)
# test_post_targets()
