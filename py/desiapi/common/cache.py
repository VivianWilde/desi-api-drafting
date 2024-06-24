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
    print(cache_path)
    if os.path.isdir(cache_path):
        cached_responses = os.listdir(cache_path)
        most_recent = (
            max(cached_responses, key=basename) if len(cached_responses) else None
        )
        # Filenames are of the form <timestamp>.<ext>, the key filters out extension
        if most_recent:

            log("recent", basename(most_recent))
            age = request_time - dt.datetime.fromisoformat(basename(most_recent))
            log("age", age)
            log("max age:", max_age)
            # max_age==0 means never to consider the cache stale
            if max_age == 0 or age < dt.timedelta(minutes=max_age):
                log("using cache")
                return os.path.join(cache_path, most_recent)
    log("rebuilding")
    return None


def clean_cache(cache_path: str, max_age: int):
    """Run somewhat frequently (on the order of hours/days), delete files with sufficiently old access times (cutoff is determined by the value in CACHE_CONFIG)

    :returns:

    """
    log("cache path ", cache_path)
    log("max age ", max_age)
    for root, dirs, files in os.walk(cache_path):
        print(dirs)
        print(files)
        for entry in dirs:
            fullpath = f"{root}/{entry}"
            atime = dt.datetime.fromtimestamp(os.path.getatime(fullpath))
            time_since_access = dt.datetime.now() - atime
            print(time_since_access)
            if time_since_access > dt.timedelta(minutes=max_age):
                print(f"removing {fullpath}")
                shutil.rmtree(fullpath)


def emergency_clean_cache(cache_path: str, max_size: str):
    """Run approximately every hour. If the cache directory is beyond a certain size, defined in CACHE_CONFIG, nuke it."""
    cmd = f"du -s {cache_path}"
    out = subprocess.getoutput(cmd)
    size_bytes = int(out.split()[0])
    if size_bytes >= get_max_cache_size(max_size):
        shutil.rmtree(cache_path)


# We want this to run as cron/scheduler/whatever. How do we do that?
