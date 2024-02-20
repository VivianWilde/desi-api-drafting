#!/usr/bin/env ipython3
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple, Mapping
import os

from werkzeug.datastructures import ImmutableMultiDict

# Models and constants

# Unused for now
# TODO: Fix for docker edition
SQL_DIR = f"{os.getenv('home')}/desi-sql"
SPECTRO_REDUX = os.getenv("DESI_SPECTRO_REDUX")
CACHE_DIR = os.path.expanduser("~/tmp/desi-api-cache")


CUTOFF = dt.timedelta(
    hours=1
)  # if age > cutoff, a response is considered stale and we recompute


# Type aliases my beloved
DataFrame = Mapping[str, Any]  # Type alias
Target = DataFrame
Filter = Mapping[str, str]
Zcat = DataFrame


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
    UNSPECIFIED=0
    ZCAT=1
    SPECTRA=2

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
    requested_data: RequestedData # zcat/spectra
    command: Command
    release: str
    endpoint: Endpoint  # tile/target/radec
    params: Parameters
    filters: Filter

    def get_cache_path(self) -> str:
        """Return the path (relative to cache dir) to write this request to
        :returns:
        """
        return f"{self.command}-{canonise_release_name(self.release)}-{self.endpoint}-params-{self.params.canonical}"

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
