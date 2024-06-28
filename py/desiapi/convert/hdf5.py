import h5py
import os
import fitsio
import datetime as dt
import numpy as np

import logging

logging.basicConfig(format="%(asctime)s: %(message)s")
logger = logging.getLogger("hdf5_converter")
logger.setLevel(logging.INFO)



SQL_DIR = os.path.expandvars("$SCRATCH/sql")
HDF5_DIR = os.path.expandvars("$SCRATCH/hdf5")
COEFF_COLUMN = "COEFF"
DATASET = "zall-tilecumulative-jura"
COLS = ["TARGETID", "TILEID", "FIBER", "SURVEY", "PROGRAM", "ZCAT_PRIMARY", "TARGET_RA", "TARGET_DEC"]

# FITS_FILE = os.path.expandvars("/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits")
FITS_FILE = os.path.expandvars("$DESIROOT/fujilite/zcatalog/zall-tilecumulative-fujilite.fits")


def log(msg):
    print(dt.datetime.now(), ": ", msg)


def to_hdf5(arr: np.recarray, outfile: str):

    for column, type_tuple in orig.dtype.fields.items():
        dtype = type_tuple[0]
        print(column, dtype)
        if dtype.type==np.str_:
            print("converting")
            new_type = np.dtype("<S", dtype.itemsize)
            orig[column]=orig[column].astype(new_type)
            print(orig[column].dtype)
    print(orig.dtype.fields)
    with h5py.File(outfile,"w") as f:
        f.create_dataset(DATASET,data=orig)

def from_hdf5(infile: str):
    with h5py.File(infile, "r") as f:
        dset = f[DATASET]


outfile = f"{HDF5_DIR}/{DATASET}.hdf5"
if __name__ == "__main__":
    logger.info("starting")
    orig = fitsio.read(FITS_FILE, columns=COLS)
    logger.info("read fits")
    logger.info("wrote hdf5")
    with h5py.File(f"{HDF5_DIR}/{DATASET}.hdf5", "r") as f:
        dset = f[DATASET]
    logger.info("read hdf5")
