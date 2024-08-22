import fitsio
import datetime as dt
import numpy as np
import pickle
from typing import Tuple, Dict


from ..common.models import (
    DESIRED_COLUMNS_TARGET,
    DESIRED_COLUMNS_TILE,
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


def main():
    for release in PRELOAD_RELEASES:
        try:
            create_memmap(release)
        except FileNotFoundError as e:
            log(e)


if __name__ == "__main__":
    main()
