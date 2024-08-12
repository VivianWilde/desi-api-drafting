#!/usr/bin/env ipython3
import operator
import os
from typing import List, Tuple

import desispec.io
import desispec.spectra
import fitsio
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table, vstack

from ..convert import hdf5, memmap
from .errors import DataNotFoundException, MalformedRequestException
from .models import *
from .utils import invert, log

# TODO params and datarelease should be dfs as well


def handle_spectra(req: ApiRequest) -> Spectra:
    """
    Interpret an API Request, construct and return the relevant spectra. Basic entry point of this module.

    :param req: A parsed/structured API Request constructing from a network request
    :returns: Spectra object from which to construct a response
    """

    canonised = canonise_release_name(req.release)
    release = DataRelease(canonised)
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
    :param filters: A dictionary of filters to restrict the objects retrieved
    :returns: A combined Spectra of all such objects in the data release
    """
    relevant_targets = get_radec_zcatalog(release, ra, dec, radius, filters)
    log(f"Retrieving {len(relevant_targets)} targets")
    return get_target_spectra_from_metadata(release, relevant_targets)


def get_tile_spectra(
    release: DataRelease, tile: int, fibers: List[int], filters: Filter
) -> Spectra:
    """
    Combine spectra from specified FIBERS within a TILE and return it

    :param release: The data release to use as a data source
    :param tile: Index of tile to access
    :param fibers: Fibers within the tile being requested
    :param filter: Currently ignored
    :returns: A combined Spectra containing the spectra of all specified fibers
    """
    folder = f"{release.tile_dir}/{tile}"
    log("reading tile info from: ", folder)
    latest = max(os.listdir(folder))

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
    :param filters: The set of filters that restricts which targets are selected
    :returns: A Spectra object combining individual spectra for all targets
    """

    target_objects = get_target_zcatalog(release, target_ids, filters)
    return get_target_spectra_from_metadata(release, target_objects)


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
    # TODO doc
    targets = get_target_zcatalog(release, filters=filters)
    print(targets.dtype)
    ctargets = SkyCoord(
        targets["TARGET_RA"] * u.degree, targets["TARGET_DEC"] * u.degree
    )
    center = SkyCoord(ra * u.degree, dec * u.degree)

    ii = center.separation(ctargets) <= radius * u.degree

    return targets[ii]


def get_tile_zcatalog(
    # TODO doc
    release: DataRelease,
    tile: int,
    fibers: List[int],
    filters: Filter,
):
    desired_columns = DESIRED_COLUMNS_TILE[:]
    for k in filters.keys():
        desired_columns.append(k)
    try:
        zcatalog = unfiltered_zcatalog(
            desired_columns,
            release.tile_hdf5,
            release.tile_memmap,
            release.tile_dtype,
            release.tile_fits,
        )
    except Exception as e:
        raise DataNotFoundException("unable to read tile information")
    log("read unfiltered zcatalog")
    keep = (zcatalog["TILEID"] == tile) & np.isin(zcatalog["FIBER"], fibers)
    zcatalog = zcatalog[keep]
    return filter_zcatalog(zcatalog, filters)


def get_target_zcatalog(
    # TODO doc
    release: DataRelease,
    target_ids: List[int] = [],
    filters: Filter = dict(),
) -> Zcatalog:
    """
    For each TARGET_ID, read the corresponding target metadata into a Target object.

    :param release: The data release to use as a data source
    :param target_ids: The list of target identifiers to build objects for. If this list is empty, blindly reads all targets
    :returns: A list of target objects, each containing metadata for a target with a specified target_id
    """
    desired_columns = DESIRED_COLUMNS_TARGET[:]

    # Also read in metadata we want to filter on
    for k in filters.keys():
        if k not in SPECIAL_QUERY_PARAMS:
            desired_columns.append(k)

    try:
        zcatalog = unfiltered_zcatalog(
            desired_columns,
            release.healpix_hdf5,
            release.healpix_memmap,
            release.healpix_dtype,
            release.healpix_fits,
        )

    except Exception as e:
        log(e)
        raise DataNotFoundException("unable to read target information")
    log("computing keep indices")
    keep = (
        ((zcatalog["ZCAT_PRIMARY"] == True) & np.isin(zcatalog["TARGETID"], target_ids))
        if len(target_ids)
        else (zcatalog["ZCAT_PRIMARY"] == True)
    )

    zcatalog = zcatalog[keep]
    log("computed keep indices")

    # Check for missing IDs
    missing_ids = []
    found_ids = set(zcatalog["TARGETID"])
    for i in target_ids:
        if i not in found_ids:
            missing_ids.append(i)
    if len(missing_ids):
        raise DataNotFoundException("unable to find targets:", target_ids)
    return filter_zcatalog(zcatalog, filters)


def unfiltered_zcatalog(
    desired_columns: List[str],
    hdf5_file: str,
    numpy_file: str,
    dtype_file: str,
    fits_file: str,
) -> Zcatalog:
    """Attempt to read zcat info from several sources, starting with the most performant and falling back to other methods if necessary.
    Order is:
    1. Preloaded/cached data (contains a limited set of columns)
    2. Numpy memmapped file (contains the full set of columns)
    3. FITS file (if the other methods fail)

    :param desired_columns: List of columns to read from the file
    :param numpy_file: Data file from which to read a thing
    :param dtype_file: File containing the pickled datatype for the numpy array
    :param fits_file: Original fits file where the data is stored
    :param hdf5_file: TODO
    :returns:
    """

    if (
        desired_columns == DESIRED_COLUMNS_TARGET
        or desired_columns == DESIRED_COLUMNS_TILE
    ):
        log("checking preloaded fits")
        preloaded_fits = memmap.preload_fits()
        log("preload accessed")
        if fits_file in preloaded_fits.keys():
            log("used preloaded fits")
            return preloaded_fits.get(fits_file)

    try:
        log("reading zcatalog info from", numpy_file)
        return memmap.read_memmap(numpy_file, dtype_file)
    except Exception as e:
        log(e)

    try:
        log("reading zcatalog info from", hdf5_file)
        return hdf5.from_hdf5_datasets(hdf5_file, desired_columns)
    except Exception as e:
        log(e)

    log("reading zcatalog info from: ", fits_file)
    return fitsio.read(
        fits_file,
        "ZCATALOG",
        columns=desired_columns,
    )


def get_target_spectra_from_metadata(
    release: DataRelease, targets: Zcatalog
) -> Spectra:
    """
    Given a list of TARGETS with populated metadata, retrieve each of their spectra as a list. Uses some trickery to ensure that the constructed Zcatalog has the target IDs in the original order specified

    :param release: The data release to use as a data source
    :param targets: A list of Target objects
    :returns: A list of Spectra objects, one for each target passed in
    """
    target_spectra = desispec.io.read_spectra_parallel(targets, specprod=release.name)
    redrock_to_targets = dict()
    for target in targets:
        redrock_file = desispec.io.findfile(
            "redrock",
            survey=target["SURVEY"],
            faprogram=target["PROGRAM"],
            groupname="healpix",
            healpix=target["HEALPIX"],
            specprod_dir=release.directory,
        )
        redrock_to_targets[redrock_file] = redrock_to_targets.get(redrock_file, []) + [
            target["TARGETID"]
        ]
    zcatalog = Table.read(redrock_file, "REDSHIFTS")
    zcatalog.remove_rows(slice(0, len(zcatalog)))
    total_kept = 0
    for redrock, redrock_targets in redrock_to_targets.items():
        new = Table.read(redrock, "REDSHIFTS")
        keep = np.isin(new["TARGETID"], redrock_targets)
        new = new[keep]
        zcatalog = vstack([zcatalog, new])
        total_kept += len(new)
    zcatalog = sort_zcat(zcatalog, targets)
    target_spectra.extra_catalog = zcatalog
    return target_spectra


def clause_from_filter(key: str, value: str, targets: Zcatalog) -> Clause:
    """Given a column name KEY and a filter string VALUE of the form '<operation><value>' and a ZCATALOG of target metadata, create a boolean array where Arr[i] is true iff the i^th record satisfies the filter.

    :param key: The name of the column to filter on
    :param value: The value of the filter, a string containing a comparison (one of >,<,=) and a value to compare against
    :param targets: The Zcatalog data from which to filter out targets
    :returns: A boolean mask that can be applied to the Zcatalog to remove anything that doesn't apply the filter
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


def filter_zcatalog(zcatalog: Zcatalog, filters: Filter) -> Zcatalog:
    """Given a collection of FILTERS of the form {column_name: "<test><value>"}, filter the ZCAT to only include records which satisfy all of those filters and return that filtered copy.

    :param zcatalog: TODO
    :param filters: TODO
    :returns:

    """
    # Speed trick for when there are no filters
    if filters == dict():
        return zcatalog
    filtered_keep = np.full(zcatalog.shape, True, dtype=bool)
    for k, v in filters.items():
        if k in SPECIAL_QUERY_PARAMS:
            pass
        else:
            clause = clause_from_filter(k, v, zcatalog)
            filtered_keep = np.logical_and(filtered_keep, clause)
    return zcatalog[filtered_keep]


# Permutation Functions
def sort_zcat(zcat: Zcatalog, target_ids: Zcatalog) -> Zcatalog:
    """Given a Zcatalog of targets in arbitrary order, and a set of target IDs in order, reorder the entries in ZCAT according to the order of IDs in TARGET_IDs

    :param zcat: Zcatalog table of targets and their metadata
    :param target_ids: A 1-d array of target IDs, representing the desired order for the Zcatalog
    :returns: The original Zcatalog, permuted so that the order lines up with the order of target_ids.
    """
    sorted_zcat = np.argsort(zcat, order="TARGETID")
    sorted_input = np.argsort(target_ids)
    # zcat->sorted, and then reverse input->sorted, so we end up with zcat->sorted->input
    return zcat[sorted_zcat][invert(sorted_input)]
