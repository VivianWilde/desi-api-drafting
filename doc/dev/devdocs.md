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
