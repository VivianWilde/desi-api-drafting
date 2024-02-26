#!/usr/bin/env ipython3
import datetime as dt
import os
import tomllib
from dataclasses import dataclass
from enum import Enum
from typing import List, Mapping, Tuple

from numpy import ndarray

# Models and constants

# Unused for now
# TODO: Fix for docker edition
# CONFIG_FILE = f"{os.getenv('HOME')}/.config/desi-api.toml"
CONFIG_FILE="/home/vivien/d/urap/desi-api/docker-utilities/default.toml"
with open(CONFIG_FILE, "rb") as conf:
    CONFIG = tomllib.load(conf)


def get_dir(key: str):
    return os.path.expanduser(CONFIG["paths"][key])

CACHE = get_dir("cache")
SPECTRO_REDUX = get_dir("spectro_redux") or os.getenv("DESI_SPECTRO_REDUX")
SQL_DIR = get_dir("sql")
CUTOFF = dt.timedelta(minutes=CONFIG["cutoff"])

# Type aliases my beloved
Dataframe = ndarray
Target = Dataframe
Filter = Mapping[str, str]
Zcatalog = Dataframe


def canonise_release_name(release: str) -> str:
    """
    Helper function to canonise the release name and error if a release name is invalid.

    :param release: Not-necessarily-canonical name of a Data Release
    :returns: Canonised name which maps to a directory

    """
    # TODO This is kind of gross, we should really have this live outside the code in a json or something, or pulled directly?
    allowed = ["fuji", "iron", "daily"]
    translations = {"edr": "fuji", "dr1": "iron"}
    if release in allowed:
        return release
    if release in translations.keys():
        return translations[release]
    raise DesiApiException(f"release must be one of FUJI or IRON, not {release}")


class DesiApiException(Exception):
    pass


class RequestedData(Enum):
    UNSPECIFIED = 0
    ZCAT = 1
    SPECTRA = 2


class Command(Enum):
    UNSPECIFIED = 0
    DOWNLOAD = 1
    PLOT = 2


class Endpoint(Enum):
    UNSPECIFIED = 0
    TILE = 1
    TARGETS = 2
    RADEC = 3


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
        return (self.ra, self.dec, self.radius)


@dataclass
class TileParameters(Parameters):
    tile: int
    fibers: List[int]

    @property
    def canonical(self) -> Tuple:
        return (self.tile, sorted(self.fibers))


@dataclass
class TargetParameters(Parameters):
    target_ids: List[int]

    @property
    def canonical(self) -> Tuple:
        return tuple(sorted(self.target_ids))


@dataclass()
class ApiRequest:
    requested_data: RequestedData  # zcat/spectra
    command: Command
    release: str
    endpoint: Endpoint  # tile/target/radec
    params: Parameters
    filters: Filter

    def get_cache_path(self) -> str:
        """Return the path (relative to cache dir) to write this request to
        :returns:
        """
        # Fitsio doesn't like parentheses in file names
        return f"{self.command}-{canonise_release_name(self.release)}-{self.endpoint}-params-{self.params.canonical}".replace("(","<").replace(")",">")


    def validate(self) -> bool:
        return True


@dataclass
class DataRelease:
    name: str
    directory: str
    tile_dir: str
    tile_fits: str
    healpix_fits: str
    sqlite_file: str

    def __init__(self, name: str) -> None:
        self.name = name.lower()
        self.directory = f"{SPECTRO_REDUX}/{self.name}"
        self.tile_fits = (
            f"{self.directory}/zcatalog/zall-tilecumulative-{self.name}.fits"
        )
        self.tile_dir = f"{self.directory}/tiles/cumulative"
        self.healpix_fits = f"{self.directory}/zcatalog/zall-pix-{self.name}.fits"
        self.sqlite_file = f"{SQL_DIR}/{self.name}.sqlite"
