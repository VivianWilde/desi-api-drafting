#!/usr/bin/env ipython3
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import os
import desispec
from math import sqrt
from typing import List


# TODO: Consider doing this go-style, with liberal use of dataclasses to prevent type errors.
# Use types rigorously. I have learned that they are good.

SQL_DIR = Path() # Where we store the sqlite database for a release, if we have one


class Command(Enum):
    UNSPECIFIED = 0
    DOWNLOAD = 1
    PLOT = 2


class RequestType(Enum):
    UNSPECIFIED = 0
    TILE = 1
    TARGETS = 2
    RADEC = 3


@dataclass()
class ApiRequest:
    command: Command  # should be enum really
    release: str
    request_type: RequestType  # tile/target/radec
    params: dict  # should be something cleverer


class Spectra:
    # TODO: Import desi stuff
    pass


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


def handle(req: ApiRequest) -> Spectra:
    # ignore command
    # select relevant folder based on release
    # switch-case on request_type
    # dispatch to function accordingly
    canonised = canonise_release_name(req.release)
    release = DataRelease(canonised)
    # TODO: Ask about setup details, like language version so if I can use match/case


def canonise_release_name(release: str) -> str:
    """
    # Other options for "fuji" would be "daily" or "iron", and as special cases map data release names to production names "edr" -> "fuji" and "dr1" -> "iron".
    """
    allowed = ["fuji", "iron", "daily"]
    translations = {"edr": "fuji", "dr1": "iron"}
    if release in allowed:
        return release
    if release in translations.keys():
        return translations[release]
    raise InvalidReleaseException



class DataRelease:
    name: str
    directory: Path
    tile_fits: Path
    healpix_fits: Path
    sqlite_file: Path

    # NOTE: the fits for tiles vs for healpix are different, so capture that fact.
    def __init__(self, name: str) -> None:
        self.name = name
        self.directory = Path()
        self.tile_fits = self.directory / Path()
        self.healpix_fits = self.directory / Path()
        self.sqlite_file = SQL_DIR / Path(f"{name}.sqlite")

    def radec(self, ra: float, dec: float, radius: float) -> Spectra:
        """
        Find all objects within RADIUS of the point (RA, DEC), combine and return their spectra

        :param ra: Right Ascension of the target point
        :param dec: Declination of the target point
        :param radius: Radius (in arcseconds) around the target point to search. Capped at 60 arcsec for now
        :returns: A combined Spectra of all such objects in the data release
        """
        all_targets = self.read_targets()

        def distfilter(target: Target) -> bool:
            # TODO units
            return sqrt((ra - target.ra) ** 2 + (dec - target.dec) ** 2) <= radius
        relevant_targets = [target for target in all_targets if distfilter(target)] # TODO numpy syntax
        spectra = self.retrieve_target_spectra(relevant_targets)
        return desispec.spectra.stack(spectra)

    def tile(self, tile: int, fibers: List[int]) -> Spectra:
        """Combine spectra from specified FIBERS within a TILE and return it

        :param tile: Index of tile to access
        :param fibers: Fibers within the tile being requested
        :returns: The result of reading Spectra from all of those fibers
        """
        path = self.directory / Path("tiles", "cumulative", str(tile))

        dates = [int(i) for i in os.listdir(path.as_posix())]
        latest = str(max(dates))

        path = path / Path(latest)

        petals = [fiber // 500 for fiber in fibers]

        petal_files = [Path(f"coadd-{petal}-{self.name}.fits") for petal in petals]

        # TODO: Review file slicing/dicing rules
        # TODO: replace path stuff with desi utilities

    def targets(self, target_ids: List[int]) -> Spectra:
        target_objects = self.retrieve_targets(target_ids)
        return desispec.spectra.stack(self.retrieve_target_spectra(target_objects))

    def retrieve_targets(self, target_ids: List[int]) -> List[Target]:
        return []

    def retrieve_target_spectra(self, targets: List[Target]) -> List[Spectra]:
        target_spectra=[]
        for target in targets:
            target_file = self.directory / Path(
                f"healpix/{target.healpix_group}/{target.healpix}/{target.survey}/{target.program}/coadd-{target.survey}-{target.program}-{target.healpix}.fits"
            )
            target_spectra.append(desispec.io.read_spectra(target_file.as_posix()))
            # TODO use desi utils
        return target_spectra



    def read_targets(self) -> List[Target]:
        # TODO: Something with fits-ing the self.healpix file
        pass


# IDEA: Make all endpoints methods of a class DataRelease. So then our `handle` func defines a Release, and then calls the appropriate method on that release.
# Then we can store stuff like which file to access as Release attrs rather than passing them in to every func, which seems satisfying to me.
# This actually works great because we can encapsulate edge cases like how to access zall-fits and stuff in the Release class. So more liberty on moving between sqlite/raw fits.


