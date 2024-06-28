import os
import fitsio
import datetime as dt
import numpy as np
import pickle

import logging

logging.basicConfig(format="%(asctime)s: %(message)s")
logger = logging.getLogger("hdf5_converter")
logger.setLevel(logging.INFO)

MEMMAP_DIR = os.path.expandvars("$SCRATCH/memmap")
COEFF_COLUMN = "COEFF"
DATASET = "zall-tilecumulative-jura"
COLS = [
    "TARGETID",
    "TILEID",
    "FIBER",
    "SURVEY",
    "PROGRAM",
    "ZCAT_PRIMARY",
    "TARGET_RA",
    "TARGET_DEC",
]

# FITS_FILE = os.path.expandvars("/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits")
FITS_FILE = os.path.expandvars(
    "$DESIROOT/fujilite/zcatalog/zall-tilecumulative-fujilite.fits"
)


outfile = f"{MEMMAP_DIR}/{DATASET}.dat"
outfile_dtype = f"{MEMMAP_DIR}/dtype.pickle"
if __name__ == "__main__":
    logger.info("starting")
    orig = fitsio.read(FITS_FILE, columns=COLS)
    logger.info("read fits")
    with open(outfile_dtype, "wb") as f:
        pickle.dump(orig.dtype, f)
    write = np.memmap(outfile, mode="w+", dtype=orig.dtype, shape=orig.shape)
    write[:]=orig
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
