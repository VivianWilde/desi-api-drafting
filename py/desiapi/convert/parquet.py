import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.feather as feather
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
PARQUET_DIR=os.path.expandvars("$SCRATCH/parquet")
FEATHER_DIR=os.path.expandvars("$SCRATCH/feather")
COEFF_COLUMN = "COEFF"
DATASET = "zall-tilecumulative-jura"
COLS = ["TARGETID", "TILEID", "FIBER", "SURVEY", "PROGRAM", "ZCAT_PRIMARY", "TARGET_RA", "TARGET_DEC"]

# FITS_FILE = os.path.expandvars("/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits")
FITS_FILE = os.path.expandvars("$DESIROOT/fujilite/zcatalog/zall-tilecumulative-fujilite.fits")


def to_table(recarray):
    return pa.Table.from_pydict({k:recarray[k] for k in recarray.dtype.fields.keys()})

if __name__=="__main__":
    logger.info("starting")
    orig = fitsio.read(FITS_FILE, columns=COLS)
    logger.info("read fits")
    # table = pa.table(orig)
    table= to_table(orig)
    logger.info("built table")
    feather.write_feather(table, f"{FEATHER_DIR}/{DATASET}.feather")
    logger.info("wrote feather")
    read = feather.read_table(f"{FEATHER_DIR}/{DATASET}.feather")
    logger.info("read feather")
