#!/usr/bin/env ipython3
from desispec.io.util import subprocess
from models import *
from utils import *
import shutil


def check_cache(req: ApiRequest, request_time: dt.datetime, cache_config: dict):
    cache_path = f"{cache_config['path']}/{req.get_cache_path()}"
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
        if age < dt.timedelta(minutes=cache_config["max_age"]):
            log("using cache")
            return os.path.join(cache_path, most_recent)
        else:
            log("rebuilding")
            return None


def clean_cache(cache_config: dict):
    """Run somewhat frequently (on the order of hours/days), delete files with sufficiently old access times.

    :returns:

    """
    for root, dirs, files in os.walk(cache_config["path"]):
        for f in files:
            fullpath = f"{root}/{f}"
            atime = dt.datetime.fromtimestamp(os.path.getatime(fullpath))
            cutoff = dt.datetime.now() - atime
            if cutoff < cache_config["max_age"]:
                os.remove(fullpath)


def emergency_clean_cache(cache_config: dict):
    """Run approximately every hour. If the cache directory is beyond a certain size, nuke it."""
    cmd = f"du -s {cache_config['path']}"
    out = subprocess.getoutput(cmd)
    size_bytes = int(out.split()[0])
    if size_bytes >= cache_config["max_size"]:
        shutil.rmtree(cache_config["path"])


# We want this to run as cron/scheduler/whatever. How do we do that?
