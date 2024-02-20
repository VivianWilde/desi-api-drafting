---
author: Vivien Goyal
title: User Documentation
---

# Introduction

The API allows you to programatically query data from the DESI project
(<https://www.desi.lbl.gov>). Conceptually the data is spectrographic
information on various objects and regions of space, and the API returns
it in the form of either FITS files or interactive plots.

# URL Syntax

The basic format for a URL to send the request to is
`<host>/api/v1/<command>/<release>/<endpoint>/<endpoint_params>`{.verbatim}

## Command

`download`{.verbatim}
:   The server will give you back a FITS file containing the spectra you
    requested

`plot`{.verbatim}
:   The server will render an HTML page with an interactive plot of the
    spectra you requested

## Release

The data release/production run within which to search. Valid (public)
releases are `fuji`{.verbatim} or `iron`{.verbatim}. `fuji`{.verbatim}
can also be referred to as `edr`{.verbatim}, and `iron`{.verbatim} as
`dr1`{.verbatim}.

## Endpoint

The possible endpoints, and the structure of the parameters for each of
them, is explained in [3](#*Endpoints)

## Optional Query Parameters

Currently ignored, but will be documented as they are built out.

# Endpoints

## Tile

Explanation
:   Given a tile ID and a list of fiber IDs for fibers on that tile,
    retrieve spectra for each of the specified fibers.

Data Type
:   All parameters should be positive integers.

Syntax
:   `/api/v1/<command>/<release>/tile/<tile_id>/<fiber_1,fiber_2...>`{.verbatim}

Example
:   `/api/v1/plot/fuji/tile/80605/10,234,2761,3951`{.verbatim} would
    read the spectra from fibers `10, 234, 2761`{.verbatim} and
    `3951`{.verbatim} on tile `80605`{.verbatim} and return a
    corresponding HTML plot.

Restrictions
:   You can request at most `500`{.verbatim} fiber IDs in a single
    `plot`{.verbatim} request, and `5000`{.verbatim} for a
    `download`{.verbatim} request.

## Targets

Explanation
:   Given a list of target IDs retrieve spectra for each of those
    targets, where target IDs are positive integers.

Data Type
:   All parameters should be positive integers.

Syntax
:   `/api/v1/<command>/<release>/targets/<target_1,target_2...>`{.verbatim}

Example
:   `/api/v1/plot/fuji/targets/39628473198710603,39632946386177593,39632956452508085,39632971434560784`{.verbatim}

Restrictions
:   You can request at most `500`{.verbatim} target IDs in a single
    `plot`{.verbatim} request, and `5000`{.verbatim} for a
    `download`{.verbatim} request.

## Ra-Dec

Explanation
:   Given a point on the sky in
    `(right ascension, declination)`{.verbatim} coordinates and a
    `radius`{.verbatim} in arcsceconds, retrieve the spectra for all
    objects within `radius`{.verbatim} of the point.

Data Type
:   All parameters can be floating-point numbers.

Syntax
:   `/api/v1/<command>/<release>/radec/<ra>,<dec>,<radius>`{.verbatim}

Example
:   `/api/v1/plot/fuji/radec/23.7649,29.8324,15`{.verbatim}

Restrictions
:   The radius can be at most `60`{.verbatim} arcsceconds.

# Roadmap

## Post Requests

## Optional Query Params
