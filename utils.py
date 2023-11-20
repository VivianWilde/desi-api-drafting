#!/usr/bin/env ipython3

from desispec.util import get_logger
import os
from typing import List

def mimetype(path: str) -> str:
    """Returns the extension of the file"""
    return os.path.splitext(path)[1].lower()


def filename(path: str) -> str:
    """Return the file name and extension (no path info)"""
    return os.path.split(path)[0]


def basename(path: str):
    """Return the file name without extension or path info"""
    return os.path.splitext(path)[0]


def parse_list(lst: str) -> List[int]:
    """Takes in a string representing a comma-separated list of integers (no spaces) and returns the list"""
    return [int(i) for i in lst.split(",")]


def log(*args):
    """Designed as a placeholder, will replace with more"""
    logger = get_logger()
    logger.info(*args)
