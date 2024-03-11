#!/usr/bin/env ipython3
from desispec.io.util import subprocess
from models import *
from utils import *
import shutil

def check_cache(req: ApiRequest, request_time: dt.datetime):
    cache_path = f"{CACHE}/{req.get_cache_path()}"
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
        if age < MAX_CACHE_AGE:
            log("using cache")
            return os.path.join(cache_path, most_recent)
        else:
            log("rebuilding")
            return None

def clean_cache():
    """ Run somewhat frequently (on the order of hours/days), delete files with sufficiently old access times.

    :returns:

    """
    for root,dirs,files in os.walk(CACHE):
        for f in files:
            fullpath = f"{root}/{f}"
            atime = dt.datetime.fromtimestamp(os.path.getatime(fullpath))
            cutoff = dt.datetime.now()-atime
            if cutoff < MAX_CACHE_AGE:
                os.remove(fullpath)


def emergency_clean_cache():
    """ Run approximately every hour. If the cache directory is beyond a certain size, nuke it."""
    cmd = f"du -s {CACHE}"
    out = subprocess.getoutput(cmd)
    size_bytes=int(out.split()[0])
    if size_bytes >= MAX_CACHE_SIZE:
        shutil.rmtree(CACHE)


# We want this to run as cron/scheduler/whatever. How do we do that?
