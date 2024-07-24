import os
import pickle
import sys
from datetime import datetime as dt

import fitsio
import h5py
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

MEMMAP_DIR = os.path.expandvars("$SCRATCH/memmap")
DTYPE_DIR = os.path.expandvars("$SCRATCH/dtype")
HDF5_DIR = os.path.expandvars("$SCRATCH/hdf5")

FITS_FILE = os.path.expandvars(
    "/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-pix-jura.fits"
)
DATASET = "zall-pix-jura"


def memmap_write(fits_file, dataset):
    outfile = f"{MEMMAP_DIR}/{dataset}.npy"
    outfile_dtype = f"{DTYPE_DIR}/{dataset}.pickle"
    log("starting")
    orig = fitsio.read(fits_file, "ZCATALOG")
    log("read fits")
    with open(outfile_dtype, "wb") as f:
        pickle.dump(orig.dtype, f)
    write = np.memmap(outfile, mode="w+", dtype=orig.dtype, shape=orig.shape)
    write[:] = orig
    print(write.dtype)
    print(write.shape)
    log("wrote numpy")
    del write


def memmap_read(dataset, columns):
    numpy_file = f"{MEMMAP_DIR}/{dataset}.npy"
    dtype_file = f"{DTYPE_DIR}/{dataset}.pickle"
    with open(dtype_file, "rb") as f:
        dtype = pickle.load(f)
    read = np.memmap(numpy_file, mode="r", dtype=dtype)
    return read


def hdf5_write(fits_file, dataset):
    arr = fitsio.read(fits_file, "ZCATALOG")
    outfile = f"{HDF5_DIR}/{dataset}.hdf5"
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


def hdf5_read(dataset, columns):
    table = Table()
    infile = f"{HDF5_DIR}/{dataset}.hdf5"
    with h5py.File(infile, "r") as f:
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


# Testing testing
all_fields=['TARGETID', 'SURVEY', 'PROGRAM', 'HEALPIX', 'SPGRPVAL', 'Z', 'ZERR', 'ZWARN', 'CHI2', 'COEFF', 'NPIXELS', 'SPECTYPE', 'SUBTYPE', 'NCOEFF', 'DELTACHI2', 'COADD_FIBERSTATUS', 'TARGET_RA', 'TARGET_DEC', 'PMRA', 'PMDEC', 'REF_EPOCH', 'FA_TARGET', 'FA_TYPE', 'OBJTYPE', 'SUBPRIORITY', 'OBSCONDITIONS', 'RELEASE', 'BRICKNAME', 'BRICKID', 'BRICK_OBJID', 'MORPHTYPE', 'EBV', 'FLUX_G', 'FLUX_R', 'FLUX_Z', 'FLUX_W1', 'FLUX_W2', 'FLUX_IVAR_G', 'FLUX_IVAR_R', 'FLUX_IVAR_Z', 'FLUX_IVAR_W1', 'FLUX_IVAR_W2', 'FIBERFLUX_G', 'FIBERFLUX_R', 'FIBERFLUX_Z', 'FIBERTOTFLUX_G', 'FIBERTOTFLUX_R', 'FIBERTOTFLUX_Z', 'MASKBITS', 'SERSIC', 'SHAPE_R', 'SHAPE_E1', 'SHAPE_E2', 'REF_ID', 'REF_CAT', 'GAIA_PHOT_G_MEAN_MAG', 'GAIA_PHOT_BP_MEAN_MAG', 'GAIA_PHOT_RP_MEAN_MAG', 'PARALLAX', 'PHOTSYS', 'PRIORITY_INIT', 'NUMOBS_INIT', 'CMX_TARGET', 'DESI_TARGET', 'BGS_TARGET', 'MWS_TARGET', 'SCND_TARGET', 'SV1_DESI_TARGET', 'SV1_BGS_TARGET', 'SV1_MWS_TARGET', 'SV1_SCND_TARGET', 'SV2_DESI_TARGET', 'SV2_BGS_TARGET', 'SV2_MWS_TARGET', 'SV2_SCND_TARGET', 'SV3_DESI_TARGET', 'SV3_BGS_TARGET', 'SV3_MWS_TARGET', 'SV3_SCND_TARGET', 'PLATE_RA', 'PLATE_DEC', 'COADD_NUMEXP', 'COADD_EXPTIME', 'COADD_NUMNIGHT', 'COADD_NUMTILE', 'MEAN_DELTA_X', 'RMS_DELTA_X', 'MEAN_DELTA_Y', 'RMS_DELTA_Y', 'MEAN_FIBER_RA', 'STD_FIBER_RA', 'MEAN_FIBER_DEC', 'STD_FIBER_DEC', 'MEAN_PSF_TO_FIBER_SPECFLUX', 'TSNR2_GPBDARK_B', 'TSNR2_ELG_B', 'TSNR2_GPBBRIGHT_B', 'TSNR2_LYA_B', 'TSNR2_BGS_B', 'TSNR2_GPBBACKUP_B', 'TSNR2_QSO_B', 'TSNR2_LRG_B', 'TSNR2_GPBDARK_R', 'TSNR2_ELG_R', 'TSNR2_GPBBRIGHT_R', 'TSNR2_LYA_R', 'TSNR2_BGS_R', 'TSNR2_GPBBACKUP_R', 'TSNR2_QSO_R', 'TSNR2_LRG_R', 'TSNR2_GPBDARK_Z', 'TSNR2_ELG_Z', 'TSNR2_GPBBRIGHT_Z', 'TSNR2_LYA_Z', 'TSNR2_BGS_Z', 'TSNR2_GPBBACKUP_Z', 'TSNR2_QSO_Z', 'TSNR2_LRG_Z', 'TSNR2_GPBDARK', 'TSNR2_ELG', 'TSNR2_GPBBRIGHT', 'TSNR2_LYA', 'TSNR2_BGS', 'TSNR2_GPBBACKUP', 'TSNR2_QSO', 'TSNR2_LRG', 'SV_NSPEC', 'SV_PRIMARY', 'ZCAT_NSPEC', 'ZCAT_PRIMARY']
TEN_COLS = all_fields[:10]
TWENTY_COLS = all_fields[:20]
FIFTY_COLS = all_fields[:50]


def write():
    hdf5_write(FITS_FILE, DATASET)
    memmap_write(FITS_FILE, DATASET)


def test_read(cols):
    log("starting hdf5")
    hdf = hdf5_read(DATASET, cols)
    hdf = radec_filter(210.9,24.8,5, hdf)
    log("finished hdf5")

    log("starting memmap")
    memmap = memmap_read(DATASET, cols)
    memmap = radec_filter(210.9,24.8,5, memmap)
    log("finished memmap")

def main():
    if sys.argv[1]=="write":
        write()
        return
    for cols in (TEN_COLS, TWENTY_COLS, FIFTY_COLS):
        test_read(cols)

# Utilities
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


def log(*args):
    print(dt.now(), ": ", *args)


def radec_filter(ra,dec,radius, targets):
    ctargets = SkyCoord(
        targets["TARGET_RA"] * u.degree, targets["TARGET_DEC"] * u.degree
    )
    center = SkyCoord(ra * u.degree, dec * u.degree)

    ii = center.separation(ctargets) <= radius * u.degree

    return targets[ii]
