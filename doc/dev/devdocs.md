## Introduction
Read the user docs (`userdoc.md`) before reading this, if you haven't already.

The quickest way to get started with running the server raw (i.e not through a docker container) is to run `python -m desi_api.web.cli server -c /etc/docker/config.toml`, which uses a prewritten config file and starts a webserver. If it fails, make sure that the `cache_path` in the config file is one that exists on your device and try again

## Configuration

The file `etc/docker/config.toml` defines the basic configuration options along with default values for when running the program inside a Docker container, commented with annotations.
Simply copy that to a new file and pass the name to the `-c` parameter to run the server with the new configuration (such as if you want to use a different cache directory, or a smaller/larger cache)

## Testing

Tests are defined in `/test` and are currently slightly ad-hoc. Running `python -m desiapi.test.test_web` or `python -m desiapi.test.test_python` will run the test suite for either the web server or python API respectively. The tests essentially make a few different requests and ensure they all returned non-empty, non-error responses.

## Autodoc Generation

To generate the Sphinx HTML documentation for this project

```
sphinx-apidoc py/desiapi -o doc/auto
cd doc/auto
make html
```

The resulting docs will be in `docs/auto/_build/html` (start browing from `index.html`)

## Core Libraries

- Flask :: Runs the web app
- FitsIO, Astropy.Table :: Handling the metadata stored in FITS format
- Desispec :: DESI utilities for dealing with spectra objects and the like
- DataTables :: HTML+JS library for plotting interactive tables from JSON data, used for the `zcat/plot` endpoint.

## Core Abstractions

### ZCatalogs

### Spectra

### ApiRequest

### Filters

## Module Structure

### Web

#### `cli`

The top-level wrapper, that delegates to either running the server (as defined in `webapp`) or a particular cache clean routine (one of those defined in `cache`)
It reads the specified config file, and updates the app's internal config map with that data before running it.

#### `server`

Treats `response_file` as a black box.

Responsible for the infrastructure around requests to `response_file`:

- Interpreting/parsing API requests
- Validating API requests
- Calling `response_file`, and sending the response back to the user over the network

#### `response_file`

- Cache handling - saving responses to cache, and using cached responses if they exist.
- Given a request, either:
  - Find a response file in the cache and return it.
  - Call `build_spectra` to get response data (Zcatalog or Spectra data) and transform the data into the requested file.
- Then save the file to the cache and report the path.

### Python

This module provides python functions that map one-to-one to the API endpoints. When called, the function first looks in `$DESI_SPECTRO_REDUX` for the data it needs, if that fails it makes a query to the web server.
Either way, the functions return an internal python object, namely either a `desispec.Spectra` or an `astropy.table.Table` (for Zcatalog metadata).

#### Implementation

Provides a class `DesiApiClient()` which essentially stores reusable configuration info like the base URL for the API server. The user-facing functions have the same pattern of constructing an `ApiRequest` based on the arguments passed to them, and then delegating to `get_data_with_fallback` to handle that request.
`get_data_with_fallback` in turn tries to build the response object locally, and if that fails due to missing data it requests the file via the web API, caches it locally, and reads a python object from the file.

### Common

Stores the shared logic and data structures that both the web and python APIs rely on

#### `models`

Defines the basic structures, models, and types we use, as well as a ton of constants

##### Types

Various type aliases, which map on to the core abstractions discussed earlier

##### DataRelease

A release is basically a "version" of DESI's dataset. A release has a bunch of files and folders associated with it, the `DataRelease` class is a helper for mapping between a release name and the set of files we care about from that release.

##### ApiRequest

A dataclass for containing all the data from a parsed API request

#### `build_spectra`

- Interacts with the DESI data, and reads data from the DESI filesystem into a internal format (`desispec.Spectra` objects for spectra, and just general `numpy.ndarray`s for Zcatalog/metadata)
- Top level functions have the form `handle_<thing>`. Currently we have `handle_spectra` and `handle_zcat`, which function as black boxes that take in `ApiRequest` objects and give out responses.
- Endpoint-specific functions have the form `get_<endpoint>_<response_type>`, for instance `get_tile_zcat` or `get_target_spectra`. These are where the main interaction with the DESI data model happens
- The rest are helper functions, or functions that help with [filtering](#filtering)

#### `cache`

Defines functions that take in some cache configuration (taken from the `[cache]` section of the config file) and interact with the cache director in some way.

- `check_cache` :: Check if a specified request has a sufficiently recent response in the cache and return it if it does
- `clean_cache` :: Remove files that haven't been accessed for a long time, as defined by the cache configuration
- `emergency_clean_cache` :: Run quite frequently, check if the cache exceeds a certain predefined size limit and remove all the contents if it does.

#### `utils`

A motley collection of general-purpose utilities like small parsers/translators.

### Convert

Initially we naively read the Zcatalog metadata for targets from a FITS file.
Unfortunately the performance of this was atrocious, so we instead maintain an intermediate layer for the Zcatalog information (specifically for the files `zall-pix-*` and `zall-tilecumulative-*`)
The `convert` module handles maintaining and reading from these.

The order of fallbacks (i.e which format the program tries to read from first) is defined by the `unfiltered_zcatalog` function in `build_spectra`

Files in this module all provide a `to_*` that serialises numpy recarrays (as returned by `fitsio.read`) to a file, and `from_*` function, that reads specified columns from a file and creates either a recarray or an astropy Table.
They also provide a `create_*` function that takes a release name and creates all the needed intermediate file

##### HDF5

We also maintain HDF5 format versions of the FITS files.
Running `python -m desiapi.convert.hdf5` should create the hdf5 files for the releases in `PRELOAD_RELEASES` and save them to `$DESI_API_INTERMEDIATE/hdf5`.

##### Memmap
https://numpy.org/doc/stable/reference/generated/numpy.memmap.html describes the basic idea. Informally, it serialises the in-memory representation of an array to a file, so that "reading" an array from this file just involves blindly "loading" the file into virtual memory and then accessing it as if it was RAM (i.e very quickly).
Run `python -m desiapi.convert.memmap` to create the files.
We also store the datatypes of the serialised arrays in `$DESI_API_INTERMEDIATE/dtype` to help us read them back in, but this is handled invisibly by the program so you don't have to worry about it.

## Feature Implementation Details

### Filtering

Filtering occurs via optional query parameters bolted on to the endpoint URL.
The basic structure for filtering is that the keys of the parameters correspond to columns in the target metadata, and the actual content of the parameter is a combination of a test (one of `=`, `>`, `<`) and a value which may be a string or a float.

Columns which are filtered on are included in the response, regardless of whether they are one of the default included columns
(NOTE: Currently only strings are supported)

If you want to include a non-default column in the response but don't want to filter on it, the workaround is to pass in a filter with the content `*`, for instance `?program=*` as a query param will ensure data from the `program` column is included in the metadata, but will not exclude/filter any records.

### Maintaining Target Order

Ensuring that targets are returned in the order specified by the order of input `target_ids`.

The `sort_zcat` function accomplishes this. It takes a `Zcatalog` (ndarray) of target objects, and a list of target IDs, and reshuffles the zcatalog to respect the order of the target IDs.
First, it computes the `argsort` of the Zcatalog, which is abstractly "how do we permute the Zcatalog to sort it by target ID (in normal ascending order)"
Then it computes the `argsort` of the target IDs, and inverts that, creating a permutation which reshuffles a sorted list of objects into a list that reflects the order of target IDs.
Then it sorts the Zcatalog by normal ascending order, and then "unsorts" it according to this inverse permutation we computed, with the end result of a Zcatalog sorted according to the input order of target IDs.

### Preloading

We load a subset of the FITS file on server start, and essentially cache it in memory. The columns loaded are the `DESIRED_COLUMNS_TILE` and `DESIRED_COLUMNS_TARGET` variables
The logic for this is defined in `preload_fits` in `server.py`. We use the `lru_cache` decorator to ensure that python caches a result from a single call to it (the first one) and uses that instead of recomputing whenever the function is called again with the same arguments.

## Roadmap

### Ra/Dec Performance

The `zcat/radec` endpoint is impractically slow. There are various slow sections, but the bottleneck is the computation step of `get_radec_zcatalog`:

```python
ctargets = SkyCoord(
    targets["TARGET_RA"] * u.degree, targets["TARGET_DEC"] * u.degree
)

log("computing filter index")
center = SkyCoord(ra * u.degree, dec * u.degree)

ii = center.separation(ctargets) <= radius * u.degree
```

There's probably a way to make that faster, since some parts of the SkyCoord construction might be possible to preload/cache.

### Memory Efficiency

#### HDF5

Currently, the program preloads the default columns from the FITS, but if a non-default column is requested it reads the _entire_ HDF5 file, including both default and non-default columns, so we have two copies of the default columns in memory which wastes space.
Fix: Look at the preloaded column names, and only read columns not in that set from the HDF5 file.

### Refactor: Dynamic Global Storage

The way we acess non-constant values (such as config file entries) is fairly ad-hoc: Only the main `server.py` module has access to the config file, and so passing those values to other modules/functions can only be done by explicitly including them as parameters (see `cache.py` for an example).
Fix: Some kind of `config` module, so that scripts can do `import config` and then call `config.get(KEY)` to read values from config without having to worry about the details of finding/parsing config files themselves.

#### PRELOAD_RELEASES in Config

Relatedly, the `PRELOAD_RELEASES` variable is currently hardcoded, ideally it would be configurable via the config file.
