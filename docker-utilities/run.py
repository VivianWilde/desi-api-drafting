#!/usr/bin/env py

# Here's wonderwall
import os
import subprocess
import sys
import tomllib
from typing import Iterable
import argparse

parser = argparse.ArgumentParser(prog="DESI API RUNNER")

parser.add_argument(
    "command",
    choices=["clean_cache", "emergency_clean_cache", "server"],
    default="server",
)

parser.add_argument("-c", "--config-file", default="./config.toml")

parser.add_argument("-m", "--mode", default="public", choices=["public","private"])

image_name = "desiapi:dev"


cache_volume = "desi-api-cache"
target_cache = "/cache"

build_cmd = f"docker build --tag {image_name} ."

cache_mount_opt = f"--mount type=volume,src={cache_volume},target={target_cache}"

# TODO host port should be more flexible
host_port="127.0.0.1:5000"
target_port=5000
port_forward_opt = f"-p {host_port}:{target_port}"

base_run_cmd = f"docker run --detach=false {cache_mount_opt} {port_forward_opt}"

# TODO: Other options: Config file, and whether to run


target_spectro_redux = "/desi/spectro/redux"
target_config = "/config/config.toml"


def execute(cmd):
    print("Executing: ", cmd)
    subprocess.Popen(cmd, shell=True)


def public(base, host_spectro_redux, args):
    def mount_option(release):
        return f"--mount type=bind,src={host_spectro_redux}/{release},target={target_spectro_redux}/{release},readonly"

    public_releases = ["fuji", "iron"]
    # execute(build_cmd)
    cmd = f"{base} {' '.join([mount_option(r) for r in public_releases])} {image_name} {args}"
    execute(cmd)


def private(base, host_spectro_redux, args):
    # execute(build_cmd)
    execute(
        f"{base} --mount type=bind,src={host_spectro_redux},target={target_spectro_redux},readonly {image_name} {args} "
    )


if __name__ == "__main__":
    args = parser.parse_intermixed_args()
    with open(args.config_file, "rb") as f:
        config = tomllib.load(f)

    # host_spectro_redux = config.get("spectro_redux") or
    host_spectro_redux = os.getenv("DESI_SPECTRO_REDUX")
    execute("docker volume create desi-api-cache")

    config_bind_opt = f"--mount type=bind,src={os.path.abspath(args.config_file)},target={target_config},readonly"

    new_base_cmd = f"{base_run_cmd} {config_bind_opt}"

    forwarded_args = f"-- {args.command} -c {target_config}  "



    if args.mode == "private":
        private(new_base_cmd, host_spectro_redux, forwarded_args)
    else:
        public(new_base_cmd, host_spectro_redux, forwarded_args)
