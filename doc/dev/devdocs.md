# Introduction

The quickest way to get started with running the server raw (i.e not through a docker container) is to run `python -m desi_api.web.cli server -c docker_utilities/config.toml`, which uses a prewritten config file and starts a webserver.

# Configuration
The file `default.toml` defines the basic configuration options along with default values for when running the program inside a Docker container, commented with annotations.
Simply copy that to a new file and pass the name to the `-c` parameter to run the server with the new configuration (such as if you want to use a different cache directory, or a smaller/larger cache)

# Autodoc Generation
To generate the Sphinx HTML documentation for this project
```
sphinx-apidoc py/desiapi -o doc/auto
cd doc/auto
make html
```
The resulting docs will be in `docs/auto/_build/html` (start browing from `index.html`)

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


# Rancher/Spin Setup
## Cache Volume
## Server (Deployment)
### Pod
- Add annotations as described in [DESI docs](https://desi.lbl.gov/trac/wiki/Computing/NerscSpin/Security#AddingaDESIread-onlypassword)
- Security Context: Specify the user ID to run as (any user with DESI permissions is fine)
- Add a bind-mount named *spectro-redux* pointing to `/global/cfs/cdirs/desi/spectro/redux` (or wherever `$DESI_SPECTRO_REDUX` points)
- Add a bind-mount named *public* pointing to `/global/cfs/cdirs/desi/public` (or wherever `$DESI_ROOT/public` points)
- TODO cache setup
### Container
- Image: `vivianwilde/desiapi` (or you can build the image from the repo yourself, and push it to whatever name you prefer, I'm not your boss)
- Networking: Add a networking service of type *Cluster IP*, named *Flask* running on port *5000* over *TCP*.
- Command: `python -m desiapi.web.cli`, with arguments just `server`
- Env Vars: `DESI_API_CONFIG_FILE` is the env var that defines where (within the container) to look for the config file. Point it to wherever you mounted the config file from CFS.
- Security Context: Input "Run As User ID" matching the pod Filsystem Group ID, and select "must run as non-root user"
- Mount *spectro-redux* at `/desi/spectro/redux`
- Mount *public* at `/desi/public`
- Mount *cache* at `/cache`
## Ingress

## Cache Clean (Cron Job)
# Core Libraries

- Flask :: Runs the web app
- FitsIO, Astropy.Table :: Handling the metadata stored in FITS format
- Desispec :: DESI utilities for dealing with spectra objects and the like
- DataTables :: HTML+JS library for plotting interactive tables from JSON data, used for the `zcat/plot` endpoint.

# Core Abstractions
TODO
## ZCatalogs
## Spectra
## ApiRequest
## Filters

# Module Structure

## Web
### `cli`

The top-level wrapper, that delegates to either running the server (as defined in `webapp`) or a particular cache clean routine (one of those defined in `cache`)
It reads the specified config file, and updates the app's internal config map with that data before running it.

### `server`
Treats `response_file` as a black box.

Responsible for the infrastructure around requests to `response_file`:

- Interpreting/parsing API requests
- Validating API requests
- Calling `response_file`, and sending the response back to the user over the network

### `response_file`
- Cache handling - saving responses to cache, and using cached responses if they exist.
- Given a request, either:
  - Find a response file in the cache and return it.
  - Call `build_spectra` to get response data (Zcatalog or Spectra data) and transform the data into the requested file.
- Then save the file to the cache and report the path.

## Python
This module provides python functions that map one-to-one to the API endpoints. When called, the function first looks in `$DESI_SPECTRO_REDUX` for the data it needs, if that fails it makes a query to the web server.
Either way, the functions return an internal python object, namely either a `desispec.Spectra` or an `astropy.table.Table` (for Zcatalog metadata).
### Implementation
Provides a class `DesiApiClient()` which essentially stores reusable configuration info like the base URL for the API server. The user-facing functions have the same pattern of constructing an `ApiRequest` based on the arguments passed to them, and then delegating to `get_data_with_fallback` to handle that request. 
`get_data_with_fallback` in turn tries to build the response object locally, and if that fails due to missing data it requests the file via the web API, caches it locally, and reads a python object from the file.

## Common
Stores the shared logic and data structures that both the web and python APIs rely on
### Models.py
TODO

Defines the basic structures, models, and types we use.

#### Types

#### DataRelease

#### ApiRequest

#### Parameters


### Build_Spectra.py

- Interacts with the DESI data, and reads data from the DESI filesystem into a internal format (`desispec.Spectra` objects for spectra, and just general `numpy.ndarray`s for Zcatalog/metadata)
- Top level functions have the form `handle_<thing>`. Currently we have `handle_spectra` and `handle_zcat`, which function as black boxes that take in `ApiRequest` objects and give out responses.
- Endpoint-specific functions have the form `get_<endpoint>_<response_type>`, for instance `get_tile_zcat` or `get_target_spectra`. These are where the main interaction with the DESI data model happens
- The rest are helper functions, or functions that help with [filtering](#filtering)

### Cache.py

Defines functions that take in some cache configuration (taken from the `[cache]` section of the config file) and interact with the cache director in some way.

- `check_cache` :: Check if a specified request has a sufficiently recent response in the cache and return it if it does
- `clean_cache` :: Remove files that haven't been accessed for a long time, as defined by the cache configuration
- `emergency_clean_cache` :: Run quite frequently, check if the cache exceeds a certain predefined size limit and remove all the contents if it does.

### Utils.py
A motley collection of general-purpose utilities like small parsers/translators.

## SQL
The logic for turning `zall-*.fits` files into sqlite files.

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
