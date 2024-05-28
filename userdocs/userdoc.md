---
author: Vivien Goyal
title: User Documentation
---

# Introduction

The API allows you to programatically query data from the DESI project (<https://www.desi.lbl.gov>). Conceptually the data is spectrographic information on various objects and regions of space, and the API returns it in the form of either FITS files or interactive plots.

# Endpoints

## Tile

Explanation : Given a tile ID and a list of fiber IDs for fibers on that tile, retrieve spectra for each of the specified fibers.

Arguments: `tile: int, fibers: List[int]`

Syntax : `/api/v1/<response_type>/<release>/tile/<tile>/<fiber_1,fiber_2...>`

Example : `/api/v1/plot/fuji/tile/80605/10,234,2761,3951` would read the spectra from fibers `10, 234, 2761` and `3951` on tile `80605` and return a corresponding HTML plot.

Restrictions : You can request at most `500` fiber IDs in a single `plot` request, and `5000` for a `download` request.

## Targets

Explanation : Given a list of target IDs retrieve spectra for each of those targets, where target IDs are positive integers.

Arguments: `target_ids: List[int] `

Syntax : `/api/v1/<response_type>/<release>/targets/<targetid_1,targetid_2...>`

Example : `/api/v1/plot/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784`

Restrictions : You can request at most `500` target IDs in a single `plot` request, and `5000` for a `download` request.

## Ra-Dec

Explanation : Given a point on the sky in `(right ascension, declination)` coordinates and a `radius` in arcsceconds, retrieve the spectra for all objects within `radius` of the point.

Arguments: `ra: float, dec: float, radius: float`

Syntax : `/api/v1/<response_type>/<release>/radec/<ra>,<dec>,<radius>`

Example : `/api/v1/plot/fuji/radec/23.7649,29.8324,15`

Restrictions : The radius can be at most `60` arcsceconds.

# ZCatalog vs Spectra
There are two kinds of data that the API can return.
## Zcatalog (Metadata)
The underlying python object is `astropy.table.Table`.
Metadata on the targets that match the request, such as:
* Target ID
* Target location (in the form of `ra` and `dec`)
* Survey and Program the target belongs to.
## Spectra (Spectrographic Data)
The underlying python object is `desispec.spectra.Spectra`. Just records of the observed spectrographic data for targets that match the request.


# Filtering

Currently the primary use for optional query parameters. For filtering, you pass in a column name as the query keys, like "PROGRAM" or "SURVEY", and a string like ">{num}" or "={string}" as the values. For instance you might append `?PROGRAM==dark&SURVEY==main` (the double-equals is intentional - the first is part of the HTML query syntax and the second distinguishes an equality query from a greater than query) to a URL to only select records which satisfy those properties.

If you want to include a non-default column in the response data, but don't necessarily want to do any filtering on it, add the filter param with `*` as the value, such as `?PROGRAM=*`.

## Filetypes
For the `zcat/download` endpoints in the web app, the file that is returned defaults to a FITS file. However, you can add a `?filetype=<type>` query parameter to the request to get the data in a fomat you specify.
At the moment only FITS and JSON are supported, we plan to add support for CSV and other files soon.

# Web API
The web app exposes an API to request either the raw data or visualisations of it.
By default, the web app returns a FITS file when asked for raw data and an HTML page when asked for a plot/visualisation.

## URL Syntax

The basic format for a URL to send the request to is `<host>/api/v1/<requested_data>/<response_type>/<release>/<endpoint>/<endpoint_params>`

### Requested Data

`zcat` : The server will respond with a table of targets (with their metadata) that meet the specified criteria.

`spectra` : The server will respond with the spectra data for the targets that meet the criteria

### Response Type

`download` : The server will give you back a file containing the spectra you requested - for Spectra endpoints this will always be a FITS file, for Zcat endpoints you can specify the filetype (the options are listed under the _Filtering_ section).

`plot` : The server will render an HTML page with a visualisation of the data you requested - either a table of target data, or an interactive plot of the spectra you requested.

### Release

The data release/production run within which to search. Valid (public) releases are `fuji` or `iron`. `fuji` can also be referred to as `edr`, and `iron` as `dr1`.

### Endpoint

The possible endpoints, and the structure of the parameters for each of
them, is explained in [Endpoints](#Endpoints)

### Optional Query Parameters

Currently ignored, but will be documented as they are built out.

## Post Requests
Post requests can be made to the `/api/v1/post` endpoint ,with the payload/data in the format
```python
{
requested_data: <zcat/spectra>
response_type: <plot/download>
release: <name of desi data release to query>
endpoint: <tile/target/radec>
params: {}
}
```
`params` is a dictionary of parameter names to values, with keys determined by the endpoint.
For instance, `params = {"ra": 210.9, "dec": 24.8, "radius":180}` when hitting the `radec` endpoint.

# Python API
Instead of returning files, functions in the API return python objects. Spectra are represented by `desispec.spectra.Spectra` objects, and Zcatalog metadata by `astropy.table.Table`s.
The functions search for data locally if `$DESI_SPECTRO_REDUX` is set.
If a function fails to find data locally, it retrieves and caches a file from the server via the web API, and then reads a python object from that file.
## How to Import
`from desi_api.python.api import get_zcat_radec` (or whatever function you may want).

## Usage
In most cases, simply running the function with the required arguments will get you what you need. Filters are specified as a dictionary. For instance `{"program":"dark","fiber":">100"}` would be a valid filter.

The only non-obvious argument is the `release` parameter. Meaning and possible values are explained in [Release](#Release)
### `DesiApiClient` Class
For more fine-grained control over the inner workings of the library, such as cache configuration, you can create an instance of the `DesiApiClient` class. The class essentially holds configuration variables which are used by its class methods. For instance,
```python
client = DesiApiClient(<configuration variables>)
client.get_zcat_radec(210.9, 24.8, 180)
```
Would ensure that `get_zcat_radec` used the provided configuration rather than the default.

#### Config Options
- Release: The DESI data release to request from
- Server URL: Base URL for the server to ping.
- Cache Root: The directory to use for caching files retrieved from the server
- Cache Max Age: The amount of time before a cached response is considered stale, in minutes. Any cache entries older than this will be ignored and re-fetched.
