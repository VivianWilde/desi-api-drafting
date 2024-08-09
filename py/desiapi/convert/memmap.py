import fitsio
import datetime as dt
import numpy as np
import pickle
from typing import Tuple
from functools import lru_cache


from ..common.models import (
    DataRelease,
    PRELOAD_RELEASES,
    Zcatalog,
)

from ..common.utils import log


def create_memmap(release_name: str):
    """Read the tilecumulative and zpix metadata for a release and create memmap

    :param release_name:
    :returns:

    """

    release = DataRelease(release_name)
    tile = fitsio.read(release.tile_fits, "ZCATALOG")
    with open(release.tile_dtype, "wb") as f:
        pickle.dump(tile.dtype, f)
    write = np.memmap(
        release.tile_memmap, mode="w+", dtype=tile.dtype, shape=tile.shape
    )
    write[:] = tile
    del write
    healpix = fitsio.read(release.healpix_fits, "ZCATALOG")
    with open(release.healpix_dtype, "wb") as f:
        pickle.dump(healpix.dtype, f)
    write = np.memmap(
        release.healpix_memmap, mode="w+", dtype=healpix.dtype, shape=healpix.shape
    )
    write[:] = healpix
    del write


def read_memmap(numpy_file: str, dtype_file: str) -> Zcatalog:
    """Given a memory-mapped numpy array as a file, and the pickled dtype for it, read that in and return it

    :param numpy_file:
    :param dtype_file:
    :returns:

    """

    with open(dtype_file, "rb") as f:
        dtype = pickle.load(f)
    read = np.memmap(numpy_file, mode="r", dtype=dtype)
    return read



# TODO move this
@lru_cache(maxsize=1)
def preload_fits(release_names: Tuple[str]) -> Dict:
    """Find the Zcatalog fits files for each release, read them into numpy arrays, and reutrn a mapping of filenames to arrays. Intended to be called once on startup, and future calls use the cache instead of reading the files each time.

    :param release_names: A list of releases to read Zcat metadata for
    :returns: A dict mapping fits file names to ndarrays

    """

    preloads = dict()
    for r in release_names:
        log("reading fits for:", r)
        try:
            release = DataRelease(r)
            log(release.healpix_fits)
            log(release.tile_fits)
            preloads[release.healpix_fits] = fitsio.read(
                release.healpix_fits, "ZCATALOG"
            )
            preloads[release.tile_fits] = fitsio.read(release.tile_fits, "ZCATALOG")

        except Exception as e:
            log(e)
    return preloads


def main():
    for release in PRELOAD_RELEASES:
        try:
            create_memmap(release)
        except FileNotFoundError as e:
            log(e)


if __name__ == "__main__":
    main()
