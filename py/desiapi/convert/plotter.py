#!/usr/bin/env ipython3
from memory_profiler import memory_usage
import datetime as dt
from experiment import *
from pprint import pprint


def plot_values():
    pass


def time_read(reader_func, dataset, columns):
    def fn():
        data =reader_func(dataset, columns)
        return data[data["ZCAT_PRIMARY"]==True]
    start = dt.now()
    mem = memory_usage(fn)
    end = dt.now()
    elapsed = (end - start).total_seconds()
    return {"gigabytes": max(mem)/1000, "seconds": elapsed}


def main():
    results = {}
    for reader in [memmap_read, hdf5_read, fits_read]:
        for cols in [TEN_COLS, TWENTY_COLS, FIFTY_COLS, ALL_FIELDS]:
            results[reader.__name__, len(cols)] = time_read(reader, DATASET, cols)
    pprint(results)


main()
