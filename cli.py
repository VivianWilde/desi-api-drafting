#!/usr/bin/env ipython3

import argparse

import cache
import utils
import webapp
from models import DEFAULT_CONF

parser = argparse.ArgumentParser(prog="DESI API")

parser.add_argument(
    "command",
    choices=["clean_cache", "emergency_clean_cache", "server"],
    default="server",
)

parser.add_argument("-c", "--config-file", default=DEFAULT_CONF)


def main():
    args = parser.parse_intermixed_args()
    config = utils.get_config_map(args.config_file)
    if args.command == "server":
        webapp.run_app(config)
    elif args.command == "clean_cache":
        cache.clean_cache(config["cache"])
    elif args.command == "emergency_clean_cache":
        cache.emergency_clean_cache(config["cache"])


if __name__ == "__main__":
    main()
