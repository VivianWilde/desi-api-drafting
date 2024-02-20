#!/usr/bin/env py

# Here's wonderwall
import os,sys
import subprocess

image_name = "desi-api-vi"

host_spectro_redux = os.getenv("$DESI_SPECTRO_REDUX")
target_spectro_redux = "/spectro_redux"

host_cache = "" # TODO
target_cache = "/cache"

build_cmd =f"docker build --tag {image_name} ."

cache_mount_opt = f"--mount type=bind,src={host_cache},target={target_cache}"


def mount_option(release):
    return f"--mount type=bind,src={host_spectro_redux}/{release},target={target_spectro_redux}/{release},readonly"


def execute(cmd):
    subprocess.Popen(cmd, shell=True)


def public():
    public_releases = ["fuji","iron"]
    execute(build_cmd)
    cmd = f"docker run {' '.join([mount_option(r) for r in public_releases])} {image_name}"
    execute(cmd)

def private():
    execute(build_cmd)
    execute(f"docker run --mount type=bind,src={host_spectro_redux},target={target_spectro_redux},readonly {image_name}")


if __name__ == "__main__":
    cmd = sys.argv[1].lower()
    if cmd == "public":
        public()
    elif cmd == "private":
        private()
    else:
        raise Exception("Must be public or private")
