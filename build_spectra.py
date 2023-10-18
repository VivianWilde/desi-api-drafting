#!/usr/bin/env ipython3
import os
import desispec.io, desispec.spectra
from math import sqrt
from typing import List, Tuple
from models import *
from desispec.spectra import Spectra

# TODO: Consider doing this go-style, with liberal use of dataclasses to prevent type errors.
# Use types rigorously. I have learned that they are good.


def handle(req: ApiRequest) -> Spectra:
    # ignore command
    # select relevant folder based on release
    # switch-case on request_type
    # dispatch to function accordingly
    canonised = canonise_release_name(req.release)
    release = DataRelease(canonised)
    params = req.params
    if req.request_type == RequestType.TILE:
        return tile(release, params.tile, params.fibers)
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



def radec(release: DataRelease, ra: float, dec: float, radius: float) -> Spectra:
    """
    Find all objects within RADIUS of the point (RA, DEC), combine and return their spectra

    :param ra: Right Ascension of the target point
    :param dec: Declination of the target point
    :param radius: Radius (in arcseconds) around the target point to search. Capped at 60 arcsec for now
    :returns: A combined Spectra of all such objects in the data release
    """
    all_targets = read_targets(release)

    def distfilter(target: Target) -> bool:
        # TODO units
        return sqrt((ra - target.ra) ** 2 + (dec - target.dec) ** 2) <= radius

    relevant_targets = [
        target for target in all_targets if distfilter(target)
    ]  # TODO numpy syntax
    spectra = retrieve_target_spectra(release, relevant_targets)
    return desispec.spectra.stack(spectra)


def tile(release: DataRelease, tile: int, fibers: List[int]) -> Spectra:
    """Combine spectra from specified FIBERS within a TILE and return it

    :param tile: Index of tile to access
    :param fibers: Fibers within the tile being requested
    :returns: The result of reading Spectra from all of those fibers
    """
    folder = f"{release.directory}/tiles/cumulative/{tile}" # TODO Consider abstracting these?
    latest = max(os.listdir(folder))
    print(folder)
    print(latest)

    spectra = desispec.io.read_tile_spectra(tile, latest, fibers=fibers, coadd=True, redrock=False, specprod=release.name, group='cumulative')
    if isinstance(spectra, Tuple):
        return spectra[0]
    else:
        return spectra
    # Read all into a single spectra.
    # Filter: Where FIBERID in List
    # TODO: Review file slicing/dicing rules
    # TODO: replace path stuff with desi utilities


def targets(release: DataRelease, target_ids: List[int]) -> Spectra:
    target_objects = retrieve_targets(release, target_ids)
    return desispec.spectra.stack(retrieve_target_spectra(release, target_objects))


def retrieve_targets(release: DataRelease, target_ids: List[int]) -> List[Target]:
    return []


def retrieve_target_spectra(
    release: DataRelease, targets: List[Target]
) -> List[Spectra]:
    target_spectra = []
    for target in targets:
        target_file = release.directory / Path(
            f"healpix/{target.healpix_group}/{target.healpix}/{target.survey}/{target.program}/coadd-{target.survey}-{target.program}-{target.healpix}.fits"
        )
        target_spectra.append(desispec.io.read_spectra(target_file.as_posix()))
        # TODO use desi utils
    return target_spectra


def read_targets(release: DataRelease) -> List[Target]:
    # TODO: Something with fits-ing the self.healpix file
    pass

def main():
    params=TileParameters(tile=80605, fibers=[10,234,2761,3951])
    req = ApiRequest(command=Command.DOWNLOAD, request_type=RequestType.TILE, release="fuji", params=params)
    result = handle(req)
    return result


result=main()
