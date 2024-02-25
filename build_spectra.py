#!/usr/bin/env ipython3
import operator
import os
from typing import List, Tuple

import desispec.io
import desispec.spectra
import fitsio
import numpy as np
from astropy.table import Table
from desispec.spectra import Spectra

from models import *
from utils import log

# TODO: Consider doing this go-style, with liberal use of dataclasses to prevent type errors.
# Use types rigorously. I have learned that they are good.

# TODO params and datarelease should be dfs as well


def handle_spectra(req: ApiRequest) -> Spectra:
    """
    Interpret an API Request, construct and return the relevant spectra. Basic entry point of this module.

    :param req: A parsed/structured API Request constructing from a network request
    :returns: Spectra object from which to construct a response
    """

    canonised = canonise_release_name(req.release)
    release = DataRelease(canonised)
    log("release: ", release)
    params = req.params
    if req.endpoint == Endpoint.TILE:
        return get_tile_spectra(release, params.tile, params.fibers, req.filters)
    elif req.endpoint == Endpoint.TARGETS:
        return get_target_spectra(release, params.target_ids, req.filters)
    elif req.endpoint == Endpoint.RADEC:
        return get_radec_spectra(
            release, params.ra, params.dec, params.radius, req.filters
        )
    else:
        raise DesiApiException("Invalid Endpoint")


def handle_zcatalog(req: ApiRequest) -> Zcatalog:
    """
    Interpret an API Request, construct and return the relevant Zcatalog (metadata). Basic entry point of this module.

    :param req: A parsed/structured API Request constructing from a network request
    :returns: Zcatalog object from which to construct a response
    """

    canonised = canonise_release_name(req.release)
    release = DataRelease(canonised)
    log("release: ", release)
    params = req.params
    if req.endpoint == Endpoint.TILE:
        return get_tile_zcatalog(release, params.tile, params.fibers, req.filters)
    elif req.endpoint == Endpoint.TARGETS:
        return get_target_zcatalog(release, params.target_ids, req.filters)
    elif req.endpoint == Endpoint.RADEC:
        return get_radec_zcatalog(
            release, params.ra, params.dec, params.radius, req.filters
        )
    else:
        raise DesiApiException("Invalid Endpoint")


def get_radec_spectra(
    release: DataRelease, ra: float, dec: float, radius: float, filters: Filter
) -> Spectra:
    """
    Find all objects within RADIUS of the point (RA, DEC), combine and return their spectra

    :param release: The data release to use as a data source
    :param ra: Right Ascension of the target point
    :param dec: Declination of the target point
    :param radius: Radius (in arcseconds) around the target point to search. Capped at 60 arcsec for now
    :returns: A combined Spectra of all such objects in the data release
    """
    relevant_targets = get_radec_zcatalog(release, ra, dec, radius, filters)
    log(f"Retrieving {len(relevant_targets)} targets")
    spectra = get_populated_target_spectra(release, relevant_targets)
    return desispec.spectra.stack(spectra)


def get_tile_spectra(
    release: DataRelease, tile: int, fibers: List[int], filters: Filter
) -> Spectra:
    """
    Combine spectra from specified FIBERS within a TILE and return it

    :param release: The data release to use as a data source
    :param tile: Index of tile to access
    :param fibers: Fibers within the tile being requested
    :returns: A combined Spectra containing the spectra of all specified fibers
    """
    folder = f"{release.tile_dir}/{tile}"
    log("reading tile info from: ", folder)
    latest = max(os.listdir(folder))
    log(latest)

    try:
        spectra = desispec.io.read_tile_spectra(
            latest,
            tile,
            fibers=fibers,
            coadd=True,
            redrock=True,
            specprod=release.name,
            group="cumulative",
        )
    except:
        raise DesiApiException("unable to locate tiles or fibers")
        # TODO: Figure out read_tile_spectra errors and use those
    log("read spectra")
    if isinstance(spectra, Tuple):
        # spectra, redrock = spectra
        # keep = np.isin(redrock["FIBER_ID"], fibers) & redrock["TILE"]==tile
        # spectra.extra_catalog = redrock[keep]
        return spectra[0]
    else:
        return spectra


def get_target_spectra(
    release: DataRelease, target_ids: List[int], filters: Filter
) -> Spectra:
    """
    Combine spectra of all target objects with the specified TARGET_IDs and return the result

    :param release: The data release to use as a data source
    :param target_ids: The list of target identifiers to search for
    :returns: A Spectra object combining individual spectra for all targets
    """

    target_objects = get_target_zcatalog(release, target_ids, filters)
    return desispec.spectra.stack(get_populated_target_spectra(release, target_objects))


def get_radec_zcatalog(
    release: DataRelease, ra: float, dec: float, radius: float, filters: Filter
) -> Zcatalog:
    """

    :param release:
    :param ra:
    :param dec:
    :param radius:
    :param filters:
    :returns:

    """
    targets = get_target_zcatalog(release, filters=filters)

    distfilter = (ra - targets["TARGET_RA"]) ** 2 + (
        dec - targets["TARGET_DEC"]
    ) ** 2 <= radius
    # TODO test this.
    return targets[distfilter]


def get_tile_zcatalog(
    release: DataRelease, tile: int, fibers: List[int], filters: Filter
):
    desired_columns = [
        "TARGETID",
        "TILEID",
        "FIBER",
        "SURVEY",
        "PROGRAM",
        "ZCAT_PRIMARY",
        "TARGET_RA",
        "TARGET_DEC",
    ]  # TODO
    for k in filters.keys():
        desired_columns.append(k)

    zcatfile = release.tile_fits
    log("reading target zcatalog info from: ", zcatfile)
    try:
        zcatalog = fitsio.read(
            zcatfile,
            "ZCATALOG",
            columns=desired_columns,
        )
    except:
        raise DesiApiException("unable to read tile information")

    keep = (zcatalog["TILEID"] == tile & np.isin(zcatalog["FIBER"], fibers))
    zcatalog = zcatalog[keep]
    return filter_zcatalog(zcatalog, filters)


def get_target_zcatalog(
    release: DataRelease, target_ids: List[int] = [], filters: Filter = dict()
) -> List[Target]:
    """
    For each TARGET_ID, read the corresponding target metadata into a Target object.

    :param release: The data release to use as a data source
    :param target_ids: The list of target identifiers to build objects for. If this list is empty, blindly reads all targets
    :returns: A list of target objects, each containing metadata for a target with a specified target_id
    """
    desired_columns = [
        "TARGETID",
        "HEALPIX",
        "SURVEY",
        "PROGRAM",
        "ZCAT_PRIMARY",
        "TARGET_RA",
        "TARGET_DEC",
    ]

    # Also read in metadata we want to filter on
    for k in filters.keys():
        desired_columns.append(k)

    zcatfile = release.healpix_fits
    log("reading target zcatalog info from: ", zcatfile)
    try:
        zcatalog = fitsio.read(
            zcatfile,
            "ZCATALOG",
            columns=desired_columns,
        )
    except:
        raise DesiApiException("unable to read target information")

    keep = (
        ((zcatalog["ZCAT_PRIMARY"] == True) & np.isin(zcatalog["TARGETID"], target_ids))
        if len(target_ids)
        else (zcatalog["ZCAT_PRIMARY"] == True)
    )

    zcatalog = zcatalog[keep]

    # Check for missing IDs
    missing_ids = []
    found_ids = set(zcatalog["TARGETID"])
    for i in target_ids:
        if i not in found_ids:
            missing_ids.append(i)
    if len(missing_ids):
        raise DesiApiException("unable to find targets:", target_ids)

    return filter_zcatalog(zcatalog, filters)


# TODO needs a better name
def get_populated_target_spectra(
    release: DataRelease, targets: List[Target]
) -> List[Spectra]:
    """
    Given a list of TARGETS with populated metadata, retrieve each of their spectra as a list.

    :param release: The data release to use as a data source
    :param targets: A list of Target objects
    :returns: A list of Spectra objects, one for each target passed in
    """
    # Unoptimised: Reads one file per target, no grouping of targets, so may read same file several times.
    # TODO: Optimise, logging
    target_spectra = []
    failures = []
    for target in targets:
        try:
            source_file = desispec.io.findfile(
                "coadd",
                survey=target["SURVEY"],
                faprogram=target["PROGRAM"],
                groupname="healpix",
                healpix=target["HEALPIX"],
                specprod_dir=release.directory,
            )
            redrock_file = desispec.io.findfile(
                "redrock",
                survey=target["SURVEY"],
                faprogram=target["PROGRAM"],
                groupname="healpix",
                healpix=target["HEALPIX"],
                specprod_dir=release.directory,
            )
            spectra = desispec.io.read_spectra(
                source_file, targetids=[target["TARGETID"]]
            )
            zcatalog = Table.read(redrock_file, "REDSHIFTS")
            keep = zcatalog["TARGETID"] == target["TARGETID"]
            zcatalog = zcatalog[keep]
            spectra.extra_catalog = zcatalog
            target_spectra.append(spectra)
        except:
            failures.append(target["TARGETID"])
    if len(failures):
        raise DesiApiException("unable to locate spectra for targets", failures)
    return target_spectra


def clause_from_filter(key: str, value: str, targets: Dataframe):
    operator_fns = {
        ">": operator.gt,
        "=": operator.eq,
        "<": operator.lt,
        "?": lambda x, y: True,
    }
    op = value[0]
    func = operator_fns[op]
    if op == "?":
        value = ""
    else:
        value = value[1:]  # Actual value. TODO: Handle casting when appropriate

    return func(targets[key], value)


def filter_spectra(spectra: Spectra, options: Filter) -> Spectra:
    # TODO
    return spectra


def filter_zcatalog(zcatalog: Zcatalog, filters: Filter):
    filtered_keep = np.full(zcatalog.shape, True, dtype=bool)
    for k, v in filters.items():
        clause = clause_from_filter(k, v, zcatalog)
        filtered_keep = np.logical_and(filtered_keep, clause)
    return zcatalog[filtered_keep]
