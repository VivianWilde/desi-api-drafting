#!/usr/bin/env py

# Here's wonderwall
import os
import subprocess
import sys
from typing import Iterable
import argparse

parser = argparse.ArgumentParser(prog='DESI API RUNNER')

parser.add_argument("command", choices=['clean_cache','emergency_clean_cache','server'], default='server')

parser.add_argument("-c","--config-file",default="./config.toml")

image_name = "desi-api-vi"


cache_volume = "desi-api-cache"
target_cache = "/cache"

build_cmd = f"docker build --tag {image_name} ."

cache_mount_opt = f"--mount type=volume,src={cache_volume},target={target_cache}"

# TODO: Other options: Config file, and whether to run


host_spectro_redux = os.getenv("$DESI_SPECTRO_REDUX") # TODO read from config
target_spectro_redux = "/spectro_redux"



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
    elif "--public" in args:
        public(filter(lambda x: x != "--public", args))
    else:
        print("ERROR: Specify whether to run private or public API")
