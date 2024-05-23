#!/usr/bin/env ipython3

import os
import tomllib
import datetime as dt
from typing import Any, Callable, List


def mimetype(path: str) -> str:
    """Returns the extension of the file"""
    return os.path.splitext(path)[1].lower()


def filename(path: str) -> str:
    """Return the file name and extension (no path info)"""
    return os.path.split(path)[0]


def basename(path: str):
    """Return the file name without extension or path info"""
    return os.path.splitext(path)[0].split(".")[0]


def build_list_parser(func: Callable[[str], Any]) -> Callable[[str], List[Any]]:
    """Returns a func that takes in a string representing a comma-separated list of integers or floats (no spaces) and returns the list"""
    return lambda s: [func(i) for i in s.split(",")]


parse_list_int = build_list_parser(int)
parse_list_float = build_list_parser(float)


def log(*args):
    """Designed as a placeholder, will replace with more"""
    # logger = get_logger()
    # logger.info(*args)

    print("LOG INFO:", *args)


def get_config_map(CONFIG_FILE: str) -> dict:
    """Read in values from the toml CONFIG_FILE, and expand paths."""

    with open(CONFIG_FILE, "rb") as conf:
        CONFIG = tomllib.load(conf)

        # for k in CONFIG["paths"]:
        #     CONFIG["paths"][k]=os.path.expanduser(CONFIG["paths"][k])
        CONFIG["cache"]["path"] = os.path.expanduser(CONFIG["cache"]["path"])

        return CONFIG


def get_bytes(size: float, suffix: str) -> int:
    """Translate a human-readable measurement like '1gb' into an integer number of bytes"""
    size = int(float(size))
    suffix = suffix.lower()

    if suffix == "kb" or suffix == "kib":
        return size * (2**10)
    elif suffix == "mb" or suffix == "mib":
        return size * (2**20)
    elif suffix == "gb" or suffix == "gib":
        return size * (2**30)

    return False


def get_max_cache_size(cache_size: str) -> int:
    size = float(cache_size[:-2])
    suffix = cache_size[-2:]
    return get_bytes(size, suffix)
