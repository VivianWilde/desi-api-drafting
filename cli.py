#!/usr/bin/env ipython3

import argparse
import webapp
import cache
import utils

parser = argparse.ArgumentParser(prog='DESI API')

parser.add_argument("command", choices=['clean_cache','emergency_clean_cache','server'], default='server')

parser.add_argument("-c","--config-file",default="/default_config/config.toml")


def main():
    args = parser.parse_intermixed_args()
    config = utils.get_config_map(args.config_file)
    if args.command == "server":
        webapp.main()
    elif args.command == "clean_cache":
        cache.clean_cache()
    elif args.command == "emergency_clean_cache":
        cache.emergency_clean_cache()
# TODO: refactor so that config file location is from here, not hardcoded.
# Basic idea: Do the config file reading and processing inside this main(). Pass the resulting dict to the functions.
