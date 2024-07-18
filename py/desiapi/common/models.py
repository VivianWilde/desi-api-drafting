#!/usr/bin/env ipython3
import os
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import List, Mapping, Tuple

from .utils import list_directories

from numpy import ndarray

from .errors import MalformedRequestException

from astropy.table import Table


from desispec.spectra import Spectra as DesiSpectra


# Type aliases my beloved
DataFrame = ndarray
Target = DataFrame
Filter = Mapping[str, str]
Zcatalog = Table
Clause = List[bool]  # A boolean mask, used in filtering Zcatalogs
Spectra = DesiSpectra

PRELOAD_RELEASES = ("fujilite", "jura", "iron")
# PRELOAD_RELEASES = ("fujilite",)
MEMMAP_DIR = os.path.expandvars("$SCRATCH/memmap") # FIXME shouldn't be scratch
HDF5_DIR = os.path.expandvars("$SCRATCH/hdf5")
DTYPES_DIR = os.path.expandvars("$SCRATCH/dtypes")
SPECTRO_REDUX = os.getenv("DESI_SPECTRO_REDUX")
# CACHE = "/cache" # Where we mount cache
DEFAULT_CONF = "/config/default.toml"
USER_CONF = "/config/config.toml"
# DEFAULT_FILETYPE = "fits"  # The default filetype for zcat files
DEFAULT_FILETYPE = "json"  # The default filetype for zcat files
SPECIAL_QUERY_PARAMS = [
    "filetype"
]  # Query params that don't correspond to data filters

DESIRED_COLUMNS = [
    "TARGETID",
    "SURVEY",
    "PROGRAM",
    "ZCAT_PRIMARY",
    "TARGET_RA",
    "TARGET_DEC",
    # "COEFF"
]
DESIRED_COLUMNS_TILE = DESIRED_COLUMNS + ["TILEID","FIBER"]
DESIRED_COLUMNS_TARGET = DESIRED_COLUMNS + ["HEALPIX"]


def canonise_release_name(release: str) -> str:
    """
    Helper function to canonise the release name and error if a release name is invalid.

    :param release: Not-necessarily-canonical name of a Data Release
    :returns: Canonised name which maps to a directory

    """
    # TODO This is kind of gross, we should really have this live outside the code in a json or something, or pulled directly?
    allowed = ["fuji", "iron", "daily", "fujilite"]
    translations = {"edr": "fuji", "dr1": "iron"}
    if release in translations.keys():
        return translations[release]
    if release.isidentifier():
        return release
    raise MalformedRequestException(
        f"release must be alphanumeric, cannot be {release}"
    )


class RequestedData(Enum):
    UNSPECIFIED = 0
    ZCAT = 1
    SPECTRA = 2

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class ResponseType(Enum):
    UNSPECIFIED = 0
    DOWNLOAD = 1
    PLOT = 2

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class Endpoint(Enum):
    UNSPECIFIED = 0
    TILE = 1
    TARGETS = 2
    RADEC = 3

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class Parameters:
    @property
    def canonical(self) -> Tuple:
        return ()


@dataclass
class RadecParameters(Parameters):
    ra: float
    dec: float
    radius: float

    @property
    def canonical(self) -> Tuple:
        return (float(self.ra), float(self.dec), float(self.radius))

    def __str__(self) -> str:
        return str(
            {
                "Right Ascension": float(self.ra),
                "Declination": float(self.dec),
                "Radius": float(self.radius),
            }
        )


@dataclass
class TileParameters(Parameters):
    tile: int
    fibers: List[int]

    @property
    def canonical(self) -> Tuple:
        return (self.tile, sorted(self.fibers))

    def __str__(self) -> str:
        return str({"Tile ID": self.tile, "Fibers": sorted(self.fibers)})


@dataclass
class TargetParameters(Parameters):
    target_ids: List[int]

    @property
    def canonical(self) -> Tuple:
        return tuple(sorted(self.target_ids))

    def __str__(self) -> str:
        return str({"Target IDs": sorted(self.target_ids)})


@dataclass()
class ApiRequest:
    requested_data: RequestedData  # zcat/spectra
    response_type: ResponseType
    release: str
    endpoint: Endpoint  # tile/target/radec
    params: Parameters
    filters: Filter = field(default_factory=lambda: dict())

    def get_cache_path(self) -> str:
        """Return the path (relative to cache dir) to write this request to
        :returns:
        """
        return self.replace_for_fitsio(
            f"{self.requested_data.name}-{self.response_type.name}-{canonise_release_name(self.release)}-{self.endpoint.name}-params-{self.params.canonical}-{self.filters}"
        )

    @staticmethod
    def replace_for_fitsio(s: str):
        """FitsIO has weird quirks regarding file names it allows, we try to work around them here"""
        return (
            s.replace(" ", "")
            .replace("(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .replace("{", "")
            .replace("}", "")
        )

    def validate(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"""

        Requested Data: {self.requested_data.name.capitalize()}

        Response Type: {self.response_type.name.capitalize()}

        Endpoint: {self.endpoint.name.capitalize()}

        Parameters: {self.params}

        Filters: {self.filters}
        """

    def to_post_payload(self) -> dict:
        payload = {
            "requested_data": self.requested_data.name,
            "response_type": self.response_type.name,
            "release": self.release,
            "endpoint": self.endpoint.name,
            "params": asdict(self.params),
        }
        payload.update(self.filters)
        return payload


@dataclass
class DataRelease:
    name: str
    directory: str
    tile_dir: str
    tile_fits: str
    healpix_fits: str
    # sqlite_file: str

    def __init__(self, name: str) -> None:
        self.name = name.lower()
        self.directory = f"{SPECTRO_REDUX}/{self.name}"

        self.tile_fits = f"{self.zcat_dir}/zall-tilecumulative-{self.name}.fits"
        self.tile_dir = f"{self.directory}/tiles/cumulative"

        self.healpix_fits = f"{self.zcat_dir}/zall-pix-{self.name}.fits"

        self.healpix_hdf5 = f"{HDF5_DIR}/zall-pix-{self.name}.hdf5"
        self.tile_hdf5 = f"{HDF5_DIR}/zall-tilecumulative-{self.name}.hdf5"
        # self.sqlite_file = f"{SQL_DIR}/{self.name}.sqlite"

    @property
    def zcat_dir(self) -> str:
        guess = f"{self.directory}/zcatalog"
        if os.path.exists(f"{guess}/zall-pix-{self.name}.fits") and os.path.exists(
            f"{guess}/zall-tilecumulative-{self.name}.fits"
        ):
            return guess
        else:
            dirs = list_directories(guess)
            versions = [int(d.replace("v", "")) for d in dirs]
            latest = max(versions)
            return f"{guess}/v{latest}"

    @property
    def tile_memmap(self) -> str:
        return os.path.expandvars(
            f"{MEMMAP_DIR}/zall-tilecumulative-{self.name}.npy"
        )

    @property
    def tile_dtype(self) -> str:
        return os.path.expandvars(
            f"{DTYPES_DIR}/zall-tilecumulative-{self.name}.pickle"
        )

    @property
    def healpix_memmap(self) -> str:
        return os.path.expandvars(f"{MEMMAP_DIR}/zall-pix-{self.name}.npy")

    @property
    def healpix_dtype(self) -> str:
        return os.path.expandvars(f"{DTYPES_DIR}/zall-pix-{self.name}.pickle")
