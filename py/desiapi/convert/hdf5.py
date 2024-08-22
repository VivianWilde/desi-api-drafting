from os.path import basename
import h5py
import os
import fitsio
import datetime as dt
import numpy as np
from typing import List, Tuple
import numpy.lib.recfunctions as rfn

from astropy.table import Table

from ..common.models import (
    PRELOAD_RELEASES,
    DataRelease,
    DESIRED_COLUMNS_TARGET,
    DESIRED_COLUMNS_TILE,
)
from ..common.utils import log, basename


def replace_type(old_type, new_type_label):
    """HDF5 doesn't support string fields, only bytes. This function constructs `replacers` which take in a recarray and cast one type to another type

    :param old_type: The old numpy type, such as `np.str_` or `np.bytes_`
    :param new_type_label: The label numpy uses, such as `S` (str), `I` (int), `U` (bytes), for the new type
    :returns: A function that given a recarray dtype (as returned by `arr.dtype`) constructs a new dtype with instances of OLD_TYPE replaced with NEW_TYPE

    """

    def replacer(recarray_type):
        new_type = []
        for column, type_tuple in recarray_type.fields.items():
            dtype = type_tuple[0]
            if dtype.type == old_type:
                byte_type = (new_type_label, dtype.itemsize)
                new_type.append((column, byte_type))
            else:
                new_type.append((column, dtype))
        return new_type

    return replacer


strings_to_bytes = replace_type(np.str_, "S")
bytes_to_strings = replace_type(np.bytes_, "U")


def create_hdf5(release_name: str):
    release = DataRelease(release_name)
    log(release.tile_fits)
    tile = fitsio.read(release.tile_fits, "ZCATALOG")
    to_hdf5_datasets(tile, release.tile_hdf5)
    log(release.healpix_fits)
    healpix = fitsio.read(release.healpix_fits, "ZCATALOG")
    to_hdf5_datasets(healpix, release.healpix_hdf5)


def read_hdf5s(release_name: str) -> Tuple[Table, Table]:
    release = DataRelease(release_name)
    tile = from_hdf5_datasets(release.tile_hdf5, columns=DESIRED_COLUMNS_TILE)
    healpix = from_hdf5_datasets(release.healpix_hdf5, columns=DESIRED_COLUMNS_TARGET)
    return tile, healpix


def to_hdf5_datasets(arr: np.recarray, outfile: str):
    with h5py.File(outfile, "w") as f:
        for col, type_tuple in arr.dtype.fields.items():
            dtype = type_tuple[0]
            if dtype.type == np.str_:
                byte_type = ("S", dtype.itemsize)
                new_type = (col, byte_type)
                f.create_dataset(col, data=arr[col].astype(byte_type))
            else:
                f.create_dataset(col, data=arr[col])


def from_hdf5_datasets(infile: str, columns: List[str]) -> Table:
    table = Table()
    with h5py.File(infile, "r") as f:
        for col in columns:
            data = f[col][:]
            dtype = data.dtype
            if dtype.type == np.bytes_:
                string_type = ("U", dtype.itemsize)
                table[col] = data.astype(string_type)
            else:
                table[col] = data
    return table


def main():
    for release in PRELOAD_RELEASES:
        log(release)
        try:
            create_hdf5(release)
        except FileNotFoundError as e:
            log(e)


if __name__ == "__main__":
    main()
