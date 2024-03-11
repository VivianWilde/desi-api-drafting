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
    return os.path.splitext(path)[0]


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


def clean_cache():
    # Look inside every dir
    # For each dir:
    # Delete everything older, if it's empty delete the top-level dir as well.
    pass


def get_config_map(CONFIG_FILE: str):
    with open(CONFIG_FILE, "rb") as conf:
        CONFIG = tomllib.load(conf)

        def get_dir(key: str):
            return os.path.expanduser(CONFIG["paths"][key])

        return dict(
            CACHE=get_dir("cache"),
            SPECTRO_REDUX=get_dir("spectro_redux") or os.getenv("DESI_SPECTRO_REDUX"),
            SQL_DIR=get_dir("sql"),
            MAX_CACHE_AGE=dt.timedelta(minutes=CONFIG["max_cache_age"]),
            MAX_CACHE_SIZE=get_max_cache_size(CONFIG["max_cache_size"]),
        )


def get_bytes(size, suffix):
    size = int(float(size))
    suffix = suffix.lower()

    if suffix == "kb" or suffix == "kib":
        return size * (2**10)
    elif suffix == "mb" or suffix == "mib":
        return size * (2**20)
    elif suffix == "gb" or suffix == "gib":
        return size * (2**30)

    return False


def get_max_cache_size(config_str):
    size = float(config_str[:-2])
    suffix = config_str[-2:]
    return get_bytes(size, suffix)
