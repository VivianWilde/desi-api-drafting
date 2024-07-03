#!/usr/bin/env ipython3
import os
import argparse
from ..common import cache, utils
from ..common.models import DEFAULT_CONF, USER_CONF
from .server import run_app

parser = argparse.ArgumentParser(prog="DESI API")

parser.add_argument(
    "command",
    choices=["clean_cache", "emergency_clean_cache", "server"],
    default="server",
)

# parser.add_argument("-c", "--config-file", default=DEFAULT_CONF)


def get_config_location():
    from_env = os.getenv("DESI_API_CONFIG_FILE")
    expanded = utils.expand_path(from_env) if from_env else ""
    if expanded and utils.is_nonempty(expanded):
        return expanded
    expected = USER_CONF if utils.is_nonempty(USER_CONF) else DEFAULT_CONF
    return expected


def main():
    args = parser.parse_intermixed_args()
    config_file = get_config_location()
    utils.log("config file", config_file)
    config = utils.get_config_map(config_file)
    utils.log("config", config)
    if args.command == "server":
        run_app(config)
    elif args.command == "clean_cache":
        cache.clean_cache(config["cache"]["path"], config["cache"]["max_age"])
    elif args.command == "emergency_clean_cache":
        cache.emergency_clean_cache(
            config["cache"]["path"], config["cache"]["max_size"]
        )


if __name__ == "__main__":
    main()
