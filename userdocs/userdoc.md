---
author: Vivien Goyal
title: User Documentation
---

# Introduction

The API allows you to programatically query data from the DESI project (<https://www.desi.lbl.gov>). Conceptually the data is spectrographic information on various objects and regions of space, and the API returns it in the form of either FITS files or interactive plots.
# URL Syntax

The basic format for a URL to send the request to is `<host>/api/v1/<requested_data>/<response_type>/<release>/<endpoint>/<endpoint_params>`

## Requested Data

`zcat`
: The server will respond with a table of targets (with their metadata) that meet the specified criteria

`spectra`
: The server will respond with the spectra data for the targets that meet the criteria

## Response Type

`download`
: The server will give you back a FITS file containing the spectra you
requested

`plot`
: The server will render an HTML page with a visualisation of the data you requested - either a table of target data, or an interactive plot of the spectra you requested

## Release

The data release/production run within which to search. Valid (public) releases are `fuji` or `iron`. `fuji` can also be referred to as `edr`, and `iron` as `dr1`.

## Endpoint

The possible endpoints, and the structure of the parameters for each of
them, is explained in [3](#*Endpoints)

## Optional Query Parameters

Currently ignored, but will be documented as they are built out.

# Endpoints

## Tile

Explanation
: Given a tile ID and a list of fiber IDs for fibers on that tile,
retrieve spectra for each of the specified fibers.

Data Type
: All parameters should be positive integers.

Syntax
: `/api/v1/<response_type>/<release>/tile/<tile_id>/<fiber_1,fiber_2...>`

Example
: `/api/v1/plot/fuji/tile/80605/10,234,2761,3951` would
read the spectra from fibers `10, 234, 2761` and
`3951` on tile `80605` and return a
corresponding HTML plot.

Restrictions
: You can request at most `500` fiber IDs in a single
`plot` request, and `5000` for a
`download` request.

## Targets

Explanation
: Given a list of target IDs retrieve spectra for each of those
targets, where target IDs are positive integers.

Data Type
: All parameters should be positive integers.

Syntax
: `/api/v1/<response_type>/<release>/targets/<target_1,target_2...>`

Example
: `/api/v1/plot/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784`

Restrictions
: You can request at most `500` target IDs in a single
`plot` request, and `5000` for a
`download` request.

## Ra-Dec

Explanation
: Given a point on the sky in `(right ascension, declination)` coordinates and a `radius` in arcsceconds, retrieve the spectra for all objects within `radius` of the point.

Data Type
: All parameters can be floating-point numbers.

Syntax
: `/api/v1/<response_type>/<release>/radec/<ra>,<dec>,<radius>`

Example
: `/api/v1/plot/fuji/radec/23.7649,29.8324,15`

Restrictions
: The radius can be at most `60` arcsceconds.

# Filtering

Currently the primary use for optional query parameters. For filtering, you pass in a column name as the query keys, like "PROGRAM" or "SURVEY", and a string like ">{num}" or "={string}" as the values. For instance you might append `?PROGRAM==dark&SURVEY==main` (the double-equals is intentional - the first is part of the HTML query syntax and the second distinguishes an equality query from a greater than query) to a URL to only select records which satisfy those properties.

If you want to include a non-default column in the response data, but don't necessarily want to do any filtering on it, add the filter param with `*` as the value, such as `?PROGRAM=*`.

## Filetypes
For the `zcat/plot` endpoints, the file that is returned defaults to a FITS file. However, you can add a `?filetype=<type>` query parameter to the request to get the data in a fomat you specify.
At the moment only FITS and JSON are supported.

# Roadmap

## Post Requests
Post requests to the /api/v1/post endpoint work as expected, with data in the format
```python
{
requested_data: <zcat/spectra>
response_type: <plot/download>
release: <name of desi data release to query>
endpoint: <tile/target/radec>
params: {}
}
```
The next step is to make the params object be its own dictionary rather than a string, for more readable and sensible-looking post requestions

## Optional Query Params
One thing in the pipeline is allowing you to specify the file type of downloads for `zcat/download` endpoints, to get the metadata in a variety of formats, such as JSON, CSV, etc. Currently only FITS is supported
