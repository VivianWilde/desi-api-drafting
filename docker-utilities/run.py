#!/usr/bin/env py

# Here's wonderwall
import os
import subprocess
import sys
from typing import Iterable

image_name = "desi-api-vi"

host_spectro_redux = os.getenv("$DESI_SPECTRO_REDUX")
target_spectro_redux = "/spectro_redux"

host_cache = ""  # TODO
target_cache = "/cache"
# NOTE: Do we need a host cache, or can we just use internal filesystem or something
# https://docs.docker.com/storage/volumes/ Use a volume for the cache

build_cmd = f"docker build --tag {image_name} ."

cache_mount_opt = f"--mount type=bind,src={host_cache},target={target_cache}"

# TODO: Other options: Config file, and whether to run

def mount_option(release):
    return f"--mount type=bind,src={host_spectro_redux}/{release},target={target_spectro_redux}/{release},readonly"


def execute(cmd):
    subprocess.Popen(cmd, shell=True)


def public(args: Iterable[str]):
    public_releases = ["fuji", "iron"]
    execute(build_cmd)
    cmd = f"docker run {' '.join([mount_option(r) for r in public_releases])} {image_name} {' '.join(args)}"
    execute(cmd)


def private(args: Iterable[str]):
    execute(build_cmd)
    execute(
        f"docker run --mount type=bind,src={host_spectro_redux},target={target_spectro_redux},readonly {image_name} {' '.join(args)} "
    )


if __name__ == "__main__":
    args = sys.argv
    if "--private" in args:
        private(filter(lambda x: x != "--private", args))
    else:
        public(filter(lambda x: x != "--public", args))
