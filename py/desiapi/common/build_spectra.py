#!/usr/bin/env ipython3
import operator
import os
from typing import List, Tuple

import desispec.io
import desispec.spectra
import fitsio
import numpy as np
from astropy.table import Table, vstack

from .models import *
from .utils import log, invert
from .errors import DataNotFoundException, MalformedRequestException, SqlException
# from ..sql import convert as sqlconvert
from ..convert import memmap 


# Consider doing this go-style, with liberal use of dataclasses to prevent type errors.
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
        raise MalformedRequestException("Invalid Endpoint")


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
        raise MalformedRequestException("Invalid Endpoint")


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
    return get_populated_target_spectra(release, relevant_targets)
    # return desispec.spectra.stack(spectra)


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
            tile,
            latest,
            specprod=release.name,
            coadd=True,
            fibers=fibers,
            redrock=True,
            group="cumulative",
        )
    except:
        raise DataNotFoundException("unable to locate tiles or fibers")
        # TODO: Figure out read_tile_spectra errors and use those
    log("read spectra")
    if isinstance(spectra, Tuple):
        spectra_data, redrock = spectra
        # keep = np.isin(redrock["FIBERID"], fibers) & redrock["TILE"]==tile
        spectra_data.extra_catalog = redrock
        return spectra_data
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
    return targets[distfilter]


def get_tile_zcatalog(
    release: DataRelease, tile: int, fibers: List[int], filters: Filter
):
    desired_columns = DESIRED_COLUMNS[:]
    for k in filters.keys():
        desired_columns.append(k)

        # TODO: SQL stuff
    try:
        zcatalog = unfiltered_zcatalog(
            release.tile_memmap, release.tile_dtype, release.tile_fits, desired_columns
        )
    except Exception as e:
        raise DataNotFoundException("unable to read tile information")
    keep = (zcatalog["TILEID"] == tile) & np.isin(zcatalog["FIBER"], fibers)
    zcatalog = zcatalog[keep]
    return filter_zcatalog(zcatalog, filters)


def get_target_zcatalog(
    release: DataRelease, target_ids: List[int] = [], filters: Filter = dict()
) -> Zcatalog:
    """
    For each TARGET_ID, read the corresponding target metadata into a Target object.

    :param release: The data release to use as a data source
    :param target_ids: The list of target identifiers to build objects for. If this list is empty, blindly reads all targets
    :returns: A list of target objects, each containing metadata for a target with a specified target_id
    """
    desired_columns = DESIRED_COLUMNS[:]

    # Also read in metadata we want to filter on
    for k in filters.keys():
        if k not in SPECIAL_QUERY_PARAMS:
            desired_columns.append(k)

    try:
        zcatalog = unfiltered_zcatalog(
            release.healpix_memmap, release.healpix_dtype, release.healpix_fits, desired_columns
        )
    except:
        raise DataNotFoundException("unable to read target information")

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
        raise DataNotFoundException("unable to find targets:", target_ids)
    return filter_zcatalog(zcatalog, filters)


def unfiltered_zcatalog(numpy_file: str, dtype_file: str, fits_file: str, desired_columns: List[str]):
    """Attempt to read zcat info from the memory-mapped numpy file, else fall back to fits file

    :param fits_file:
    :param sql_file:
    :param desired_columns:
    :returns:

    """

    try:
        log("reading zcatalog info from", numpy_file)
        # zcatalog = sqlconvert.sql_to_numpy(sql_file, columns=desired_columns)
        return memmap.read_memmap(numpy_file, dtype_file, desired_columns)
        # log("zcatalog: ", zcatalog)
    except Exception as e:
        # log(e)
        log("reading zcatalog info from: ", fits_file)
        return fitsio.read(
            fits_file,
            "ZCATALOG",
            columns=desired_columns,
        )
    # FitsIO errors are caught by the calling get_target_zcatalog


# TODO needs a better name
def get_populated_target_spectra(
    release: DataRelease, targets: Zcatalog
) -> Spectra:
    """
    Given a list of TARGETS with populated metadata, retrieve each of their spectra as a list.

    :param release: The data release to use as a data source
    :param targets: A list of Target objects
    :returns: A list of Spectra objects, one for each target passed in
    """
    redrock_to_targets = dict()
    target_spectra = desispec.io.read_spectra_parallel(targets, specprod=release.name)
    for target in targets:
        redrock_file = desispec.io.findfile(
            "redrock",
            survey=target["SURVEY"],
            faprogram=target["PROGRAM"],
            groupname="healpix",
            healpix=target["HEALPIX"],
            specprod_dir=release.directory,
        )
        redrock_to_targets[redrock_file] = redrock_to_targets.get(redrock_file, [])+[target["TARGETID"]]
    zcatalog = Table.read(redrock_file, "REDSHIFTS")
    zcatalog.remove_rows(slice(0,len(zcatalog)))
    total_kept=0
    for redrock, redrock_targets in redrock_to_targets.items():
        new = Table.read(redrock, "REDSHIFTS")
        keep = np.isin(new["TARGETID"], redrock_targets)
        new = new[keep]
        zcatalog = vstack([zcatalog,new])
        total_kept += len(new)
    zcatalog = sort_zcat(zcatalog, targets)
    target_spectra.extra_catalog = zcatalog
    return target_spectra


def clause_from_filter(key: str, value: str, targets: Zcatalog) -> Clause:
    """Given a column name KEY and a filter string VALUE of the form '<operation><value>' and a ZCATALOG of target metadata, create a boolean array where Arr[i] is true iff the i^th record satisfies the filter.

    :param key:
    :param value:
    :param targets:
    :returns:

    """

    operator_fns = {
        ">": operator.gt,
        "=": operator.eq,
        "<": operator.lt,
        "*": lambda x, y: True,
    }
    key = key.upper()
    op = value[0]
    if op not in operator_fns.keys():
        func = operator_fns["="]
        return func(targets[key], value)

    func = operator_fns[op]
    if op == "*":
        value = ""
    else:
        value = value[1:]
        try:
            value = float(value)
        except ValueError:
            pass

    return func(targets[key], value)


def filter_spectra(spectra: Spectra, options: Filter) -> Spectra:
    # TODO
    return spectra


def filter_zcatalog(zcatalog: Zcatalog, filters: Filter) -> Zcatalog:
    """Given a collection of FILTERS of the form {column_name: "<test><value>"}, filter the ZCAT to only include records which satisfy all of those filters and return that filtered copy.

    :param zcatalog:
    :param filters:
    :returns:

    """

    filtered_keep = np.full(zcatalog.shape, True, dtype=bool)
    for k, v in filters.items():
        if k in SPECIAL_QUERY_PARAMS:
            pass
        else:
            clause = clause_from_filter(k, v, zcatalog)
            filtered_keep = np.logical_and(filtered_keep, clause)
    return zcatalog[filtered_keep]



# Permutation Functions
def sort_zcat(zcat: Zcatalog, target_ids: Zcatalog):
    sorted_zcat = np.argsort(zcat, order="TARGETID")
    sorted_input = np.argsort(target_ids)
    # zcat->sorted, and then reverse input->sorted, so we end up with zcat->sorted->input
    return zcat[sorted_zcat][invert(sorted_input)]
