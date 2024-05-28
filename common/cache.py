#!/usr/bin/env ipython3
from .models import *
from .utils import *
import shutil
import subprocess


def check_cache(
    req: ApiRequest, request_time: dt.datetime, cache_path: str, max_age: int
) -> str | None:
    """Check whether a suitably recent response to the current request exists in the cache, if it does then return that file, else return None

    :param req:
    :param request_time:
    :param cache_config:
    :returns:

    """

    cache_path = f"{cache_path}/{req.get_cache_path()}"
    if os.path.isdir(cache_path):
        cached_responses = os.listdir(cache_path)
        most_recent = (
            max(cached_responses, key=basename)
            if len(cached_responses)
            else dt.datetime.fromtimestamp(0).isoformat()
        )
        # Filenames are of the form <timestamp>.<ext>, the key filters out extension
        # If there are no cached responses, use 1970 as the time so it doesn't get selected.
        log("recent", basename(most_recent))
        age = request_time - dt.datetime.fromisoformat(basename(most_recent))
        log("age", age)
        log("max age:", max_age)
        # max_age==0 means never to consider the cache stale
        if max_age == 0 or age < dt.timedelta(minutes=max_age):
            log("using cache")
            return os.path.join(cache_path, most_recent)
        else:
            log("rebuilding")
            return None


def clean_cache(cache_path: str, max_age: int):
    """Run somewhat frequently (on the order of hours/days), delete files with sufficiently old access times (cutoff is determined by the value in CACHE_CONFIG)

    :returns:

    """
    for root, dirs, files in os.walk(cache_path):
        for f in files:
            fullpath = f"{root}/{f}"
            atime = dt.datetime.fromtimestamp(os.path.getatime(fullpath))
            cutoff = dt.datetime.now() - atime
            if cutoff < dt.timedelta(minutes=max_age):
                os.remove(fullpath)


def emergency_clean_cache(cache_path: str, max_size: str):
    """Run approximately every hour. If the cache directory is beyond a certain size, defined in CACHE_CONFIG, nuke it."""
    cmd = f"du -s {cache_path}"
    out = subprocess.getoutput(cmd)
    size_bytes = int(out.split()[0])
    if size_bytes >= get_max_cache_size(max_size):
        shutil.rmtree(cache_path)


# We want this to run as cron/scheduler/whatever. How do we do that?
