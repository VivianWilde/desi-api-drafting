from build_spectra import handle_spectra, handle_zcatalog
from cache import check_cache
from errors import DataNotFoundException, DesiApiException
from typing import List
from models import *
from response_file_gen import build_response
from desispec.io import read_spectra

import datetime, requests, os


def default_cache_dir() -> str:
    return os.path.expanduser("~/tmp/desi-api-cache")
    # TODO magic


def default_release():
    return "fuji"
    # TODO if running at NERSC, use the latest private, else latest public


DEFAULT_SERVER = "http://0.0.0:5000"  # possibly change this
DEFAULT_MAX_AGE = 60


def deserialize(path: str) -> Zcatalog | Spectra:
    base = os.path.basename(path)
    requested_data = base.split(".")[1]
    match requested_data:
        case "zcat":
            return Table.read(path)
        case "spectra":
            return read_spectra(path)
        case _:
            raise DesiApiException()


def guess_ext(req: ApiRequest) -> str:
    if "filetype" in req.filters.keys():
        return req.filters["filetype"]
    if req.response_type == ResponseType.PLOT:
        return "html"
    if req.requested_data == RequestedData.SPECTRA:
        return "fits"
    if req.requested_data == RequestedData.ZCAT:
        return DEFAULT_FILETYPE
    return DEFAULT_FILETYPE  # as good a guess as any


def make_request(
    requested_data: RequestedData,
    endpoint: Endpoint,
    params: Parameters,
    filters: Filter,
) -> ApiRequest:
    return ApiRequest(
        requested_data=requested_data,
        endpoint=endpoint,
        params=params,
        filters=filters,
        response_type=ResponseType.DOWNLOAD,
        release="",
    )


class DesiApiClient:
    def __init__(
        self, release=None, server_url=None, cache_root=None, cache_max_age=None
    ) -> None:
        self.release = release or default_release()
        self.server_url = server_url or DEFAULT_SERVER
        self.cache_root = cache_root or default_cache_dir()
        self.cache_max_age = 0  # i.e infinity

    def get_data_with_fallback(self, req: ApiRequest) -> Zcatalog | Spectra:
        req.release = self.release
        try:
            match req.requested_data:
                case RequestedData.ZCAT:
                    return handle_zcatalog(req)
                case RequestedData.SPECTRA:
                    return handle_spectra(req)
                case _:
                    raise MalformedRequestException("Ok what the actual hell")
        except DataNotFoundException:
            req_time = datetime.datetime.now()
            cached = check_cache(req, req_time, self.cache_root, self.cache_max_age)
            if cached:
                return deserialize(cached)
            return deserialize(self.fallback_to_web(req, req_time))

    def fallback_to_web(self, req: ApiRequest, req_time: datetime.datetime) -> str:
        extension = guess_ext(req)
        payload = req.to_post_payload()
        resp = requests.post(f"{self.server_url}/api/v1/post", data=payload)
        file_bytes = resp.content
        requested_data = req.requested_data.name.lower()
        cache_path = f"{self.cache_root}/{req.get_cache_path()}/{req_time.isoformat()}.{requested_data}.{extension}"
        with open(cache_path, "wb") as resp_file:
            resp_file.write(file_bytes)
        return cache_path

    # user facing class methods
    def get_zcat_radec(self, ra: float, dec: float, radius: float, **filters):
        req = make_request(
            RequestedData.ZCAT,
            Endpoint.RADEC,
            RadecParameters(ra, dec, radius),
            filters,
        )
        return self.get_data_with_fallback(req)

    def get_zcat_tile(self, tile: int, fibers: List[int], **filters):
        req = make_request(
            RequestedData.ZCAT, Endpoint.TILE, TileParameters(tile, fibers), filters
        )
        return self.get_data_with_fallback(req)

    def get_zcat_targets(self, target_ids: List[int], **filters):
        req = make_request(
            RequestedData.ZCAT, Endpoint.TARGETS, TargetParameters(target_ids), filters
        )
        return self.get_data_with_fallback(req)

    def get_spectra_radec(self, ra: float, dec: float, radius: float, **filters):
        req = make_request(
            RequestedData.SPECTRA,
            Endpoint.RADEC,
            RadecParameters(ra, dec, radius),
            filters,
        )
        return self.get_data_with_fallback(req)

    def get_spectra_tile(self, tile: int, fibers: List[int], **filters):
        req = make_request(
            RequestedData.SPECTRA, Endpoint.TILE, TileParameters(tile, fibers), filters
        )
        return self.get_data_with_fallback(req)

    def get_spectra_targets(self, target_ids: List[int], **filters):
        req = make_request(
            RequestedData.SPECTRA,
            Endpoint.TARGETS,
            TargetParameters(target_ids),
            filters,
        )
        return self.get_data_with_fallback(req)


# User-facing functions


def get_zcat_radec(
    ra: float,
    dec: float,
    radius: float,
    release: str,
    server_url=None,
    cache_root=None,
    **filters,
):
    return DesiApiClient(release, server_url, cache_root).get_zcat_radec(
        ra, dec, radius, **filters
    )


def get_zcat_tile(
    tile: int,
    fibers: List[int],
    release: str,
    server_url=None,
    cache_root=None,
    **filters,
):
    return DesiApiClient(release, server_url, cache_root).get_zcat_tile(
        tile, fibers, **filters
    )


def get_zcat_targets(
    target_ids: List[int], release: str, server_url=None, cache_root=None, **filters
):
    return DesiApiClient(release, server_url, cache_root).get_zcat_targets(
        target_ids, **filters
    )


def get_spectra_radec(
    ra: float,
    dec: float,
    radius: float,
    release: str,
    server_url=None,
    cache_root=None,
    **filters,
):
    return DesiApiClient(release, server_url, cache_root).get_spectra_radec(
        ra, dec, radius, **filters
    )


def get_spectra_tile(
    tile: int,
    fibers: List[int],
    release: str,
    server_url=None,
    cache_root=None,
    **filters,
):
    return DesiApiClient(release, server_url, cache_root).get_spectra_tile(
        tile, fibers, **filters
    )


def get_spectra_targets(
    target_ids: List[int], release: str, server_url=None, cache_root=None, **filters
):
    return DesiApiClient(release, server_url, cache_root).get_spectra_targets(
        target_ids, **filters
    )
