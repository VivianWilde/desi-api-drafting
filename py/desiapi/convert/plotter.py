#!/usr/bin/env ipython3
from memory_profiler import memory_usage
import datetime as dt
from experiment import *
from pprint import pprint
import matplotlib.pyplot as plt


def time_read(reader_func, dataset, columns):
    def fn():
        data = reader_func(dataset, columns)
        return data[data["ZCAT_PRIMARY"] == True]

    start = dt.now()
    mem = memory_usage(fn)
    end = dt.now()
    elapsed = (end - start).total_seconds()
    return {"gigabytes": max(mem) / 1000, "seconds": elapsed}


def gather_data():
    results = {}
    for reader in [memmap_read, hdf5_read, fits_read]:
        for cols in [TEN_COLS, TWENTY_COLS, FIFTY_COLS, ALL_FIELDS]:
            results[reader.__name__, len(cols)] = time_read(reader, DATASET, cols)
    pprint(results)


fits = {
    ("fits_read", 13): {"gigabytes": 23.80631640625, "seconds": 1616.247802},
    ("fits_read", 23): {"gigabytes": 65.76861328125, "seconds": 2295.547334},
    ("fits_read", 53): {"gigabytes": 86.21563671875, "seconds": 2083.876817},
    ("fits_read", 135): {"gigabytes": 136.1495390625, "seconds": 1889.922526},
}

hdf5 = {
    ("hdf5_read", 13): {"gigabytes": 42.6348359375, "seconds": 28.145192},
    ("hdf5_read", 23): {"gigabytes": 197.51148046875, "seconds": 162.427674},
    ("hdf5_read", 53): {"gigabytes": 239.65559375, "seconds": 215.691149},
    ("hdf5_read", 135): {"gigabytes": 293.85751953125, "seconds": 230.461556},
}

memmap = {
    ("memmap_read", 13): {"gigabytes": 138.05971875, "seconds": 49.179302},
    ("memmap_read", 23): {"gigabytes": 138.06298828125, "seconds": 54.505638},
    ("memmap_read", 53): {"gigabytes": 138.0291875, "seconds": 62.866711},
    ("memmap_read", 135): {"gigabytes": 138.10680078125, "seconds": 79.69729},
}


def plot_values(data, fig, ax):
    simplified = {}
    name = list(data.keys())[0][0].split("_")[0]
    for k, v in data.items():
        simplified[k[1]] = v["seconds"]

    x,y = simplified.keys(), simplified.values()
    ax.plot(x,y, label=name, marker="o")
    for (xi, yi) in (zip(x,y)):
        plt.annotate(f'({round(xi)}, {round(yi)})', (xi, yi), textcoords="offset points", xytext=(0, 10), ha='center')


    plt.annotate(name, (xi, yi), ha='left')

def main():
    fig = plt.figure()
    ax = plt.axes()
    ax.set_xlabel("# Columns")
    ax.set_ylabel("Time (Seconds)")
    for data in (fits, hdf5, memmap):
        plot_values(data, fig, ax)
    plt.show()


main()
