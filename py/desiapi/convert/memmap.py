import os,sys
import fitsio
import datetime as dt
import numpy as np
import pickle
from typing import List

import logging

from ..common.models import DESIRED_COLUMNS_TILE, DESIRED_COLUMNS_TARGET, DataRelease

logging.basicConfig(format="%(asctime)s: %(message)s")
logger = logging.getLogger("hdf5_converter")
logger.setLevel(logging.INFO)

MEMMAP_DIR = os.path.expandvars("$SCRATCH/memmap")
COEFF_COLUMN = "COEFF"
DATASET = "zall-tilecumulative-jura"

# FITS_FILE = os.path.expandvars("/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits")
FITS_FILE = os.path.expandvars(
    "$DESIROOT/fujilite/zcatalog/zall-tilecumulative-fujilite.fits"
)
outfile = f"{MEMMAP_DIR}/{DATASET}.dat"
outfile_dtype = f"{MEMMAP_DIR}/dtype.pickle"


def create_memmaps(release_name: str):
    release = DataRelease(release_name)
    tile = fitsio.read(release.tile_fits, columns=DESIRED_COLUMNS_TILE)
    with open(release.tile_dtype, "wb") as f:
        pickle.dump(tile.dtype, f)
    write = np.memmap(
        release.tile_memmap, mode="w+", dtype=tile.dtype, shape=tile.shape
    )
    write[:] = tile
    del write
    healpix = fitsio.read(release.healpix_fits, columns = DESIRED_COLUMNS_TARGET)
    with open(release.healpix_dtype, "wb") as f:
        pickle.dump(healpix.dtype, f)
    write = np.memmap(
        release.healpix_memmap, mode="w+", dtype=healpix.dtype, shape=healpix.shape
    )
    write[:] = healpix
    del write

def read_memmap(numpy_file: str, dtype_file: str, desired_columns: List[str]):
    with open(dtype_file, "rb") as f:
        dtype = pickle.load(f)
    read = np.memmap(numpy_file, mode="r", dtype=dtype)
    return read



def main():
    create_memmaps("jura")
    create_memmaps("fuji")

if __name__ == "__main__":
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
