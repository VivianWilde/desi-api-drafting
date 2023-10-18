#!/usr/bin/env ipython3
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
import datetime as dt
from typing import List
import os

# Models and constants

SQL_DIR = "/home/vivien/desi-sql"
DESIROOT= os.getenv("DESIROOT") or "/global/cfs/cdirs/desi/spectro/redux"


CUTOFF = dt.timedelta(
    hours=1
)  # if age > cutoff, a response is considered stale and we recompute


class InvalidReleaseException(Exception):
    pass


class Command(Enum):
    UNSPECIFIED = 0
    DOWNLOAD = 1
    PLOT = 2


class RequestType(Enum):
    UNSPECIFIED = 0
    TILE = 1
    TARGETS = 2
    RADEC = 3

class Parameters:
    pass


@dataclass
class RadecParameters(Parameters):
    ra: float
    dec: float
    radius: float


@dataclass
class TileParameters(Parameters):
    tile: int
    fibers: List[int]


@dataclass
class TargetParameters(Parameters):
    target_ids: List[int]



@dataclass()
class ApiRequest:
    command: Command  # should be enum really
    release: str
    request_type: RequestType  # tile/target/radec
    params: Parameters

    def get_cache_path(self) -> str:
        """Return the path (relative to cache dir) to write this request to
        :returns:
        """
        return ""

    def validate(self) -> bool:
        return True


@dataclass()
class Target:
    target_id: int
    healpix: int
    survey: str
    program: str
    zcat_primary: bool
    ra: float
    dec: float
    # This works well. So we can populate the target objects in a separate function, and then just have our functions use them.

    @property
    def healpix_group(self) -> int:
        return self.healpix // 100


@dataclass
class DataRelease:
    name: str
    directory: str
    tile_fits: str
    healpix_fits: str
    sqlite_file: str

    # NOTE: the fits for tiles vs for healpix are different, so capture that fact.
    def __init__(self, name: str) -> None:
        self.name = name
        self.directory = f"{DESIROOT}/{self.name}"
        self.tile_fits = f"{self.directory}/zcatalog/zall-tilecumulative-{self.name}.fits"
        self.healpix_fits = f"{self.directory}/zcatalog/zall-pix-{self.name}.fits"
        self.sqlite_file = f"{SQL_DIR}/{self.name}.sqlite"


