---
author: Vivien Goyal
---

# Introduction

The quickest way to get started with running the server raw (i.e not through a docker container) is to run `python cli.py server -c docker-utilities/config.toml`, which uses a prewritten config file and starts a webserver.

# Configuration
The file `default.toml` defines the basic configuration options along with default values for when running the program inside a Docker container, commented with annotations.
Simply copy that to a new file and pass the name to the `-c` parameter to run the server with the new configuration (such as if you want to use a different cache directory, or a smaller/larger cache)

# Docker Setup
Running the docker container correctly is a little tricky, since generating the right options to mount the DESI data we need is finnicky. Because I like you and do not want you to suffer, I've constructed a `run.py` file. Once you've locally built/downloaded the container, simply run `python run.py` and specify:
1. A command
2. A path to a configuration file
3. A mode to run in, one of Private or Public
This will generate and run the appropriate docker command, including the appropriate port forwarding and file-mounting witchcraft for the server to just work (TM).
For instance `python run.py server -c ./config.toml -m public` to run a server that only exposes public DESI releases, and uses config values from `config.toml`

## Container Structure
- We have a base container `desipod`, essentially builds python and all of the basic libraries/dependencies, including the ones from DESI.
- `desipod` does a few hacks to handle multiple versions of some repositories (like the redrock templates repository).
- After that, the `desiapi` container copies the code and other files (such as HTML templates and config files) from the repo into the container, declares a `cache` volume and some useful environment variables, and then simply forwards arguments to `docker run` to  `cli.py`.

## Little Trip-Ups
- For reasons that have been eaten by a wildebeest, if you run a server in a docker container, even if you enable port forwarding, the server won't be accessible from localhost.
- To get around this we specify `app.run(host="0.0.0", debug=True)` in the `webapp.py` file, so that the app responds to requests from outside the Docker container as well
- TODO: Document the redrock template shenanigans here.


# Core Libraries

- Flask :: Runs the web app
- FitsIO, Astropy.Table :: Handling the metadata stored in FITS format
- Desispec :: DESI utilities for dealing with spectra objects and the like
- DataTables :: HTML+JS library for plotting interactive tables from JSON data, used for the `zcat/plot` endpoint.

# Core Abstractions
## ZCatalogs
## Spectra
## ApiRequest
## Filters

# Module Structure

## Models.py
Defines the basic structures, models, and types we use.

### Types
### DataRelease
### ApiRequest
### Parameters



## Build_Spectra.py
- Interacts with the DESI data, and reads data from the DESI filesystem into a internal format (`desispec.Spectra` objects for spectra, and just general `numpy.ndarray`s for Zcatalog/metadata)
- Top level functions have the form `handle_<thing>`. Currently we have `handle_spectra` and `handle_zcat`, which function as black boxes that take in `ApiRequest` objects and give out responses.
- Endpoint-specific functions have the form `get_<endpoint>_<response_type>`, for instance `get_tile_zcat` or `get_target_spectra`. These are where the main interaction with the DESI data model happens
- The rest are helper functions, or functions that help with [filtering](#filtering)

### Useful Functions
Some functions in `build_spectra` are generic enough to be reusable outside the context of this program.
TODO: List them, and include their docstrings here.


## Cache.py
Defines functions that take in some cache configuration (taken from the `[cache]` section of the config file) and interact with the cache director in some way.

- `check_cache` :: Check if a specified request has a sufficiently recent response in the cache and return it if it does
- `clean_cache` :: Remove files that haven't been accessed for a long time, as defined by the cache configuration
- `emergency_clean_cache` :: Run quite frequently, check if the cache exceeds a certain predefined size limit and remove all the contents if it does.

## Webapp.py
Treats `build_spectra` and `cache` as black boxes.

Responsible for the infrastructure around requests to `build_spectra`:

- Interpreting/parsing API requests
- Validating API requests
- Cache handling - saving responses to cache, and using cached responses if they exist.
- Turning response data into files, either data files or HTML displays.

## Cli.py
The top-level wrapper, that delegates to either running the server (as defined in `webapp`) or a particular cache clean routine (one of those defined in `cache`)
It reads the specified config file, and updates the app's internal config map with that data before running it.



# Feature Implementation Details

## Filtering
Filtering occurs via optional query parameters bolted on to the endpoint URL.
The basic structure for filtering is that the keys of the parameters correspond to columns in the target metadata, and the actual content of the parameter is a combination of a test (one of `=`, `>`, `<`) and a value which may be a string or a float.

Columns which are filtered on are included in the response, regardless of whether they are one of the default included columns
(NOTE: Currently only strings are supported)

If you want to include a non-default column in the response but don't want to filter on it, the workaround is to pass in a filter with the content `*`, for instance `?program=*` as a query param will ensure data from the `program` column is included in the metadata, but will not exclude/filter any records.

## Request Parsing

### Parsing Params


# Extending