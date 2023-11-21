#!/usr/bin/env ipython3

from desispec.util import get_logger
import os
from typing import List, Callable, Any

def mimetype(path: str) -> str:
    """Returns the extension of the file"""
    return os.path.splitext(path)[1].lower()


def filename(path: str) -> str:
    """Return the file name and extension (no path info)"""
    return os.path.split(path)[0]


def basename(path: str):
    """Return the file name without extension or path info"""
    return os.path.splitext(path)[0]


def build_list_parser(func: Callable[[str], Any]) -> Callable[[str], List[Any]] :
    """Returns a func that takes in a string representing a comma-separated list of integers or floats (no spaces) and returns the list"""
    return lambda s: [func(i) for i in s.split(",")]

parse_list_int = build_list_parser(int)
parse_list_float = build_list_parser(float)


def log(*args):
    """Designed as a placeholder, will replace with more"""
    # logger = get_logger()
    # logger.info(*args)

    print("LOG INFO:", *args)
