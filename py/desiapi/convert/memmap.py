import os, sys
import fitsio
import datetime as dt
import numpy as np
import pickle
from typing import Tuple
from functools import lru_cache

import logging

from ..common.models import (
    DESIRED_COLUMNS_TILE,
    DESIRED_COLUMNS_TARGET,
    DataRelease,
    PRELOAD_RELEASES,
    MEMMAP_DIR,
    DTYPES_DIR,
)

from ..common.utils import log


def create_memmap(release_name: str):
    release = DataRelease(release_name)
    tile = fitsio.read(release.tile_fits, columns=DESIRED_COLUMNS_TILE)
    with open(release.tile_dtype, "wb") as f:
        pickle.dump(tile.dtype, f)
    write = np.memmap(
        release.tile_memmap, mode="w+", dtype=tile.dtype, shape=tile.shape
    )
    write[:] = tile
    del write
    healpix = fitsio.read(release.healpix_fits, columns=DESIRED_COLUMNS_TARGET)
    with open(release.healpix_dtype, "wb") as f:
        pickle.dump(healpix.dtype, f)
    write = np.memmap(
        release.healpix_memmap, mode="w+", dtype=healpix.dtype, shape=healpix.shape
    )
    write[:] = healpix
    del write


def read_memmap(numpy_file: str, dtype_file: str):
    with open(dtype_file, "rb") as f:
        dtype = pickle.load(f)
    read = np.memmap(numpy_file, mode="r", dtype=dtype)
    return read


@lru_cache(maxsize=1)
def preload_memmaps(release_names: Tuple[str]):
    preloads = dict()
    for r in release_names:
        log("reading memmap for:", r)
        release = DataRelease(r)
        preloads[release.healpix_memmap] = read_memmap(
            release.healpix_memmap, release.healpix_dtype
        )
        preloads[release.tile_memmap] = read_memmap(
            release.tile_memmap, release.tile_dtype
        )
    return preloads


def main():
    for release in PRELOAD_RELEASES:
        create_memmap(release)


def test_run():
    logging.basicConfig(format="%(asctime)s: %(message)s")
    logger = logging.getLogger("hdf5_converter")
    logger.setLevel(logging.INFO)
    DATASET = "zall-tilecumulative-jura"
    # FITS_FILE = os.path.expandvars("/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits")
    FITS_FILE = os.path.expandvars(
        "$DESIROOT/fujilite/zcatalog/zall-tilecumulative-fujilite.fits"
    )
    outfile = f"{MEMMAP_DIR}/{DATASET}.npy"
    outfile_dtype = f"{DTYPES_DIR}/{DATASET}.pickle"
    logger.info("starting")
    orig = fitsio.read(FITS_FILE, columns=COLS)
    logger.info("read fits")
    with open(outfile_dtype, "wb") as f:
        pickle.dump(orig.dtype, f)
    write = np.memmap(outfile, mode="w+", dtype=orig.dtype, shape=orig.shape)
    write[:] = orig
    print(write.dtype)
    print(write.shape)
    logger.info("wrote numpy")
    del write
    with open(outfile_dtype, "rb") as f:
        read_dtype = pickle.load(f)
    read = np.memmap(outfile, mode="r", dtype=read_dtype)
    print(read.dtype.fields)
    print(read.shape)
    logger.info("read numpy")


if __name__ == "__main__":
    main()
