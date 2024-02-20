---
author: Vivien Goyal
---

# Introduction

# Core Libraries

- Flask :: Runs the web app
- FitsIO, Astropy.Table :: Handling the metadata stored in FITS format
- Desispec :: DESI utilities for dealing with spectra objects and the like

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

## Webapp.py
Treats `build_spectra` as a black box for the most part.

Responsible for the infrastructure around requests to `build_spectra`:

- Interpreting/parsing API requests
- Validating API requests
- Cache handling - saving responses to cache, and using cached responses if they exist.
- Turning response data into files, either data files or HTML displays.



# Feature Implementation Details

## Filtering

## Request Parsing

### Parsing Params

# Extending
