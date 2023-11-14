#!/usr/bin/env ipython3
import os
import desispec.io, desispec.spectra
from math import sqrt
from typing import List, Tuple
from models import *
from desispec.spectra import Spectra
import fitsio
from astropy.table import Table
import numpy as np

# TODO: Consider doing this go-style, with liberal use of dataclasses to prevent type errors.
# Use types rigorously. I have learned that they are good.


def handle(req: ApiRequest) -> Spectra:
    """
    Interpret an API Request, construct and return the relevant spectra. Basic entry point of this module.

    :param req: A parsed/structured API Request constructing from a network request
    :returns: Spectra object from which to construct a response
    """

    canonised = canonise_release_name(req.release)
    release = DataRelease(canonised)
    params = req.params
    if req.request_type == RequestType.TILE:
        return tile(release, params.tile, params.fibers)
    elif req.request_type == RequestType.TARGETS:
        return targets(release, params.target_ids)
    elif req.request_type == RequestType.RADEC:
        return radec(release, params.ra, params.dec, params.radius)
    else:
        raise InvalidReleaseException


def radec(release: DataRelease, ra: float, dec: float, radius: float) -> Spectra:
    """
    Find all objects within RADIUS of the point (RA, DEC), combine and return their spectra

    :param release: The data release to use as a data source
    :param ra: Right Ascension of the target point
    :param dec: Declination of the target point
    :param radius: Radius (in arcseconds) around the target point to search. Capped at 60 arcsec for now
    :returns: A combined Spectra of all such objects in the data release
    """
    targets = retrieve_targets(release)

    def distfilter(target: Target) -> bool:
        return sqrt((ra - target.ra) ** 2 + (dec - target.dec) ** 2) <= radius

    relevant_targets = [
        t for t in targets if distfilter(t)
    ]  # TODO probably inefficient
    spectra = retrieve_target_spectra(release, relevant_targets)
    return desispec.spectra.stack(spectra)


def tile(release: DataRelease, tile: int, fibers: List[int]) -> Spectra:
    """
    Combine spectra from specified FIBERS within a TILE and return it

    :param release: The data release to use as a data source
    :param tile: Index of tile to access
    :param fibers: Fibers within the tile being requested
    :returns: A combined Spectra containing the spectra of all specified fibers
    """
    folder = f"{release.tile_dir}/{tile}"
    latest = max(os.listdir(folder))

    spectra = desispec.io.read_tile_spectra(
        tile,
        latest,
        fibers=fibers,
        coadd=True,
        redrock=True,
        specprod=release.name,
        group="cumulative",
    )
    if isinstance(spectra, Tuple):
        result = spectra[0]
        result.extra_catalog = result[1]
        return result
    else:
        return spectra


def targets(release: DataRelease, target_ids: List[int]) -> Spectra:
    """
    Combine spectra of all target objects with the specified TARGET_IDs and return the result

    :param release: The data release to use as a data source
    :param target_ids: The list of target identifiers to search for
    :returns: A Spectra object combining individual spectra for all targets
    """

    target_objects = retrieve_targets(release, target_ids)
    return desispec.spectra.stack(retrieve_target_spectra(release, target_objects))


def retrieve_targets(release: DataRelease, target_ids: List[int] = []) -> List[Target]:
    """
    For each TARGET_ID, read the corresponding target metadata into a Target object.

    :param release: The data release to use as a data source
    :param target_ids: The list of target identifiers to build objects for. If this list is empty, blindly reads all targets
    :returns: A list of target objects, each containing metadata for a target with a specified target_id
    """
    zcatfile = release.healpix_fits
    zcat = fitsio.read(
        zcatfile,
        "ZCATALOG",
        columns=[
            "TARGETID",
            "HEALPIX",
            "SURVEY",
            "PROGRAM",
            "ZCAT_PRIMARY",
            # We don't always need these, but save them so we can reuse this function. Maybe make it optional if this has high overhead.
            "TARGET_RA",
            "TARGET_DEC",
        ],
    )
    keep = (
        ((zcat["ZCAT_PRIMARY"] == True) & np.isin(zcat["TARGETID"], target_ids))
        if len(target_ids)
        else (zcat["ZCAT_PRIMARY"] == True)
    )
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
    return targets


def retrieve_target_spectra(
    release: DataRelease, targets: List[Target]
) -> List[Spectra]:
    """
    Given a list of TARGETS with populated metadata, retrieve each of their spectra as a list.

    :param release: The data release to use as a data source
    :param targets: A list of Target objects
    :returns: A list of Spectra objects, one for each target passed in
    """
    # Unoptimised: Reads one file per target, no grouping of targets, so may read same file several times.
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
        redrock_file = desispec.io.findfile(
            "redrock",
            survey=target.survey,
            faprogram=target.program,
            groupname="healpix",
            healpix=target.healpix,
            specprod_dir=release.directory,
        )
        spectra = desispec.io.read_spectra(source_file, targetids=[target.target_id])
        zcat = Table.read(redrock_file, "REDSHIFTS")
        spectra.extra_catalog = zcat
        target_spectra.append(spectra)
    return target_spectra
