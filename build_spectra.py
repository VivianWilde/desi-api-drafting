#!/usr/bin/env ipython3
import os
import desispec.io, desispec.spectra
from math import sqrt
from typing import List, Tuple
from models import *
from desispec.spectra import Spectra
import fitsio
import numpy as np

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
        return tile(release, params.tile , params.fibers)
    elif req.request_type == RequestType.TARGETS:
        return targets(release, params.target_ids)
    elif req.request_type == RequestType.RADEC:
        return radec(release, params.ra, params.dec, params.radius)


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
    targets = retrieve_targets(release)

    def distfilter(target: Target) -> bool:
        return sqrt((ra - target.ra) ** 2 + (dec - target.dec) ** 2) <= radius

    relevant_targets = [t for t in targets if distfilter(t)] # TODO probably inefficient
    spectra = retrieve_target_spectra(release, relevant_targets)
    return desispec.spectra.stack(spectra)


def tile(release: DataRelease, tile: int, fibers: List[int]) -> Spectra:
    """Combine spectra from specified FIBERS within a TILE and return it

    :param tile: Index of tile to access
    :param fibers: Fibers within the tile being requested
    :returns: The result of reading Spectra from all of those fibers
    """
    folder = f"{release.directory}/tiles/cumulative/{tile}"  # TODO Consider abstracting these?
    latest = max(os.listdir(folder))

    spectra = desispec.io.read_tile_spectra(
        tile,
        latest,
        fibers=fibers,
        coadd=True,
        redrock=False,
        specprod=release.name,
        group="cumulative",
    )
    if isinstance(spectra, Tuple):
        return spectra[0]
    else:
        return spectra


def targets(release: DataRelease, target_ids: List[int]) -> Spectra:
    target_objects = retrieve_targets(release, target_ids)
    return desispec.spectra.stack(retrieve_target_spectra(release, target_objects))


def retrieve_targets(release: DataRelease, target_ids: List[int] = []) -> List[Target]:
    # If the list of target_ids is empty, return all targets
    zcatfile = release.healpix_fits
    # desispec.io.read_table(database)
    zcat = fitsio.read(
        zcatfile,
        "ZCATALOG",
        columns=[
            "TARGETID",
            "HEALPIX",
            "SURVEY",
            "PROGRAM",
            "ZCAT_PRIMARY",
            "TARGET_RA", # We don't always need these, but save them so we can reuse this function. Maybe make it optional if this has high overhead.
            "TARGET_DEC",
        ],
    )
    keep = ((zcat["ZCAT_PRIMARY"] == True) &  np.isin(zcat["TARGETID"],target_ids)) if len(target_ids) else (zcat["ZCAT_PRIMARY"] == True)
    zcat = zcat[keep]
    targets = []
    for target in zcat:
        targets.append(
            Target(
                target_id=target["TARGETID"],
                healpix=target["HEALPIX"],
                survey=target["SURVEY"],
                program=target["PROGRAM"],
                zcat_primary=target["ZCAT_PRIMARY"],
                ra=target["TARGET_RA"],
                dec=target["TARGET_DEC"],
            )
        )
    print(targets)
    return targets



def retrieve_target_spectra(
        # Unoptimised: Reads one file per target, no grouping of targets, so may read same file several times.
    release: DataRelease, targets: List[Target]
) -> List[Spectra]:
    target_spectra = []
    for target in targets:
        source_file = desispec.io.findfile(
            "coadd",
            survey=target.survey,
            faprogram=target.program,
            groupname="healpix",
            healpix=target.healpix,
            specprod_dir=release.directory,
        )
        # print(source_file)
        print(type(target.target_id))
        spectra = desispec.io.read_spectra(source_file, targetids=[target.target_id])
        target_spectra.append(spectra)
    return target_spectra
