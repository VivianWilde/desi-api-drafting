import h5py
import os
import fitsio
import datetime as dt

import logging
logging.basicConfig(format="%(asctime)s: %(message)s")
logger = logging.getLogger("hdf5_converter")



SQL_DIR = os.path.expandvars("$SCRATCH/sql")
HDF5_DIR = os.path.expandvars("$SCRATCH/hdf5")
COEFF_COLUMN = "COEFF"
DATASET = "zall-tilecumulative-jura"
COLS = ["TARGETID", "TILEID", "FIBER", "SURVEY", "PROGRAM", "ZCAT_PRIMARY", "TARGET_RA", "TARGET_DEC"]

FITS_FILE = os.path.expandvars("/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits")


def log(msg):
    print(dt.datetime.now(), ": ", msg)

if __name__ == "__main__":
    logger.info("starting")
    orig = fitsio.read(FITS_FILE, columns=COLS)
    logger.info("read fits")
    with h5py.File(f"{HDF5_DIR}/{DATASET}.hdf5") as f:
        f.create_dataset(DATASET,data=orig)
    logger.info("wrote hdf5")
    with h5py.File(f"{HDF5_DIR}/{DATASET}.hdf5") as f:
        dset = f[DATASET]
    logger.info("read hdf5")
