import datetime as dt
import json
import os

import desispec.io
import desispec.spectra
import fitsio
import numpy as np
from flask import render_template
from numpyencoder import NumpyEncoder
from prospect.viewer import plotspectra

from ..common.build_spectra import handle_spectra, handle_zcatalog
from ..common.cache import check_cache
from ..common.errors import MalformedRequestException, ServerFailedException
from ..common.models import *
from ..common.utils import *


def build_response(
    req: ApiRequest, request_time: dt.datetime, cache_root: str, cache_max_age: int
) -> str:
    """Build the file asked for by REQ, or reuse an existing one if it is sufficiently recent, and return the path to it

    :param req: An ApiRequest object
    :param request_time: The time the request was made, used for cache checks, etc.
    :returns: A complete path (including the file extension) to a created file that should be sent back as the response
    """
    cached = check_cache(req, request_time, cache_root, cache_max_age)
    if cached:
        return cached
    cache_path = f"{cache_root}/{req.get_cache_path()}"

    if req.requested_data == RequestedData.SPECTRA:
        spectra = handle_spectra(req)
        resp_file_path = create_spectra_file(
            req.response_type, spectra, cache_path, request_time.isoformat()
        )
        return resp_file_path
    else:
        zcatalog = handle_zcatalog(
            req
        )  # object returned by fitsio.read + slicing/dicing
        resp_file_path = create_zcat_file(
            req,
            zcatalog,
            cache_path,
            request_time.isoformat(),
            req.filters,
        )
        return resp_file_path


def create_zcat_file(
    req: ApiRequest,
    zcat: Zcatalog,
    save_dir: str,
    file_name: str,
    filters: Filter,
) -> str:
    """Write a collection of zcatalog metadata to either an Html or Fits file, cache that file, and return the path to it.

    :param response_type: One of download/plot
    :param zcat: Data to be written to a file
    :param save_dir: Path to the cache dir to save the file
    :param file_name:
    :param filters: A collection of key-value pairs. Mainly used to indicate the desired file format
    :returns: Path to a file containing the Zcat info
    """

    os.makedirs(save_dir, exist_ok=True)
    if req.response_type == ResponseType.PLOT:
        # We want an html table
        return zcat_to_html(req, zcat, save_dir, file_name)
    else:
        filetype = filters.get("filetype", DEFAULT_FILETYPE).lower()
        # NOTE: The .zcat.filetype is important internally.
        target_file = f"{save_dir}/{file_name}.zcat.{filetype}"
        try:
            write_zcat_to_file(target_file, zcat, filetype)
            return target_file
        except Exception as e:
            raise ServerFailedException(
                "unable to create spectra file - fitsio failed to write to "
                + target_file
            )


def write_zcat_to_file(target_file: str, zcat: Zcatalog, filetype: str):
    log("requested filetype: ", filetype)
    match filetype:
        case "fits":
            fitsio.write(target_file, zcat)
        case "json":
            with open(target_file, "w") as f:
                f.write(zcat_to_json_str(zcat))
        case "csv":
            np.savetxt(target_file, zcat)
            # TODO: test, and also should we have a header
        case _:
            raise MalformedRequestException("invalid filetype requested")


def zcat_to_json_str(zcat: Zcatalog) -> str:
    """Jsonify the data in the Zcatalog object ZCAT and return the raw Json data."""

    keys = zcat.dtype.names
    log("zcat", zcat["TARGETID"])
    return json.dumps([dict(zip(keys, record)) for record in zcat], cls=NumpyEncoder)


def create_spectra_file(
    response_type: ResponseType, spectra: Spectra, save_dir: str, file_name: str
) -> str:
    """Creates a file at SAVE_PATH.<ext> generated from data in SPECTRA. The type of file (FITS vs HTML currently) is determined by RESPONSE_TYPE.

    :param response_type: Response type from the request, one of DOWNLOAD or PLOT, defines whether the output is raw data or an HTML plot.
    :param spectra: The Spectra object to draw our data from
    :param save_path: The path (without an extension) to which we should save our file.
    :returns: The full path (including extension) to the file created
    """
    os.makedirs(save_dir, exist_ok=True)
    if response_type == ResponseType.DOWNLOAD:
        # NOTE: .spectra.fits is important internally
        target_file = f"{save_dir}/{file_name}.spectra.fits"
        try:
            desispec.io.write_spectra(target_file, spectra)
            return target_file
        except Exception as e:
            raise ServerFailedException("unable to create spectra file")
    elif response_type == ResponseType.PLOT:
        return spectra_to_html(spectra, save_dir, file_name)
    else:
        raise MalformedRequestException(
            "invalid response_type (must be PLOT or DOWNLOAD)"
        )


def zcat_to_html(req: ApiRequest, zcat: Zcatalog, save_dir: str, file_name: str) -> str:
    """Render ZCAT data to an interactive html table based on a template, and return the path to the filled-in html file
    :param req: The ApiRequest (generates the title/description for the table)
    :param zcat: The Zcatalog metadata to generate a table from
    :param save_dir:
    :param file_name:
    :returns:

    """

    html_file = f"{save_dir}/{file_name}.html"
    json_data = json.loads(zcat_to_json_str(zcat))
    for record in json_data:
        record["TARGETID"]=str(record["TARGETID"])
    json_str = json.dumps(json_data)
    with open(html_file, "w") as out:
        out.write(
            render_template(
                "table.html", columns=zcat.dtype.names, json_data=json_str, request=req
            )
        )
    return html_file


def spectra_to_html(spectra: Spectra, save_dir: str, file_name: str) -> str:
    """Render Spectra data to an interactive html plot using the DESI Prosect library, and return the path to the html file.

    :param spectra:
    :param save_dir:
    :param file_name:
    :returns:

    """

    try:
        print(spectra.extra_catalog)
        plotspectra(
            spectra,
            zcatalog=spectra.extra_catalog,
            html_dir=save_dir,
            title=file_name,
            with_vi_widgets=False,
            with_full_2ndfit=False,
            num_approx_fits=0,
        )
        return f"{save_dir}/{file_name}.html"
    except Exception as e:
        raise ServerFailedException("unable to produce plot", e)
