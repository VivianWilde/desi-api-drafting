from os.path import basename
import h5py
import os
import fitsio
import datetime as dt
import numpy as np
from typing import List
import numpy.lib.recfunctions as rfn

from astropy.table import Table

DESIRED_COLUMNS = [
    "TARGETID",
    "SURVEY",
    "PROGRAM",
    "ZCAT_PRIMARY",
    "TARGET_RA",
    "TARGET_DEC",
    # "COEFF"
]
DESIRED_COLUMNS_TILE = DESIRED_COLUMNS + ["TILEID", "FIBER"]
DESIRED_COLUMNS_TARGET = DESIRED_COLUMNS + ["HEALPIX"]
PRELOAD_RELEASES = ("jura", "iron")


def log(*args):
    print(*args)


# from ..common.models import (
#     DataRelease,
# )


def filename(path: str) -> str:
    """Return the file name and extension (no path info)"""
    return os.path.split(path)[1]


def basename(path: str):
    """Return the file name without extension or path info"""
    return os.path.splitext(filename(path))[0].split(".")[0]


# spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits


def replace_type(old_type, new_type_label):
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


def to_hdf5(arr: np.recarray, outfile: str):
    new_type = strings_to_bytes(arr.dtype)
    arr = arr.astype(np.dtype(new_type))
    log(basename(outfile))
    with h5py.File(outfile, "w") as f:
        f.create_dataset(basename(outfile), data=arr)


def from_hdf5(infile: str, columns: List[str]):
    with h5py.File(infile, "r") as f:
        data = f[basename(infile)].fields(columns)[:]
    new_type = bytes_to_strings(data.dtype)
    return data.astype(np.dtype(new_type))


def create_hdf5(release_name: str):
    release = DataRelease(release_name)
    log(release.tile_fits)
    tile = fitsio.read(release.tile_fits, "ZCATALOG")
    to_hdf5_datasets(tile, release.tile_hdf5)
    log(release.healpix_fits)
    healpix = fitsio.read(release.healpix_fits, "ZCATALOG")
    to_hdf5_datasets(healpix, release.healpix_hdf5)


def read_hdf5s(release_name: str):
    release = DataRelease(release_name)
    tile = from_hdf5_datasets(release.tile_hdf5, columns=DESIRED_COLUMNS_TILE)
    healpix = from_hdf5_datasets(release.healpix_hdf5, columns=DESIRED_COLUMNS_TARGET)
    return tile, healpix


def to_hdf5_datasets(arr: np.recarray, outfile: str):
    with h5py.File(outfile, "w") as f:
        for col, type_tuple in arr.dtype.fields.items():
            log("column: ", col)
            dtype = type_tuple[0]
            if dtype.type == np.str_:
                byte_type = ("S", dtype.itemsize)
                new_type = (col, byte_type)
                f.create_dataset(col, data=arr[col].astype(byte_type))
            else:
                f.create_dataset(col, data=arr[col])


def from_hdf5_datasets(infile: str, columns: List[str]):
    table = Table()
    with h5py.File(infile, "r") as f:
        # arr = np.recarray(
        #     f[columns[0]].shape, dtype=[("idx", int)]
        # )  # TODO better way to get size?
        for col in columns:
            data = f[col][:]
            dtype = data.dtype
            if dtype.type == np.bytes_:
                string_type = ("U", dtype.itemsize)
                # new_type = (col, string_type)
                table[col] = data.astype(string_type)
            else:
                table[col] = data
    return table


def get_dataset_keys(f):
    keys = []
    f.visit(lambda key: keys.append(key) if isinstance(f[key], h5py.Dataset) else None)
    return keys


def main():
    for release in PRELOAD_RELEASES:
        log(release)
        try:
            create_hdf5(release)
            # tile, healpix = read_hdf5s(release)
        except FileNotFoundError as e:
            log(e)


if __name__ == "__main__":
    fits_file = os.path.expandvars(
        "/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits"
    )
    orig = fitsio.read(fits_file, "ZCATALOG")
    hdf5_file = os.path.expandvars("$SCRATCH/hdf5/zall-tilecumulative-jura.hdf5")
    to_hdf5_datasets(orig, hdf5_file)
    rebuilt = from_hdf5_datasets(hdf5_file, DESIRED_COLUMNS_TILE)
