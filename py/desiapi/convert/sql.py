from typing import Tuple, List
from astropy.table import Table
import fitsio
from pandas import DataFrame
import pandas as pd
import numpy as np
from numpy import ndarray
import sqlite3
import os
import datetime as dt
import math

#SQL_DIR = "/home/vivien/d/urap/sql"
SQL_DIR = os.path.expandvars("$SCRATCH/sql")
COEFF_COLUMN = "COEFF"

COLS = ["TARGETID", "TILEID", "FIBER", "SURVEY", "PROGRAM", "ZCAT_PRIMARY", "TARGET_RA", "TARGET_DEC"]


def filename(path: str) -> str:
    """Return the file name and extension (no path info)"""
    return os.path.split(path)[1]


def basename(path: str):
    """Return the file name without extension or path info"""
    return os.path.splitext(path)[0].split(".")[0]



def astropy_to_sql(fits_file: str) -> int | None:
    table_name = tablename_from_filename(fits_file)
    sql_file = get_sql_file_path(table_name)
    engine = setup_db(sql_file)
    table = Table.read(fits_file)
    df = astropy_to_dataframe(table)
    return dataframe_to_sql(df, table_name, engine)

    # data, metadata = astropy_to_dataframe(table)
    # data.to_sql(table_name, engine)
    # metadata.to_sql(table_name + "_meta", engine)


def numpy_to_sql(fits_file: str):
    table_name = tablename_from_filename(fits_file)
    sql_file = get_sql_file_path(table_name)
    engine = setup_db(sql_file)
    array = fitsio.read(fits_file, columns=COLS)
    print("read", dt.datetime.now())
    df = numpy_to_dataframe(array)
    print("dataframed!", dt.datetime.now())
    del array
    return dataframe_to_sql(df, table_name, engine)


def numpy_to_dataframe(arr: ndarray) -> DataFrame:
    copy = arr[[name for name in arr.dtype.names if name != COEFF_COLUMN]]
    naive = DataFrame(copy)
    num_coeffs = len(arr[COEFF_COLUMN][0])
    print(num_coeffs)
    for i in range(num_coeffs):
        naive[f"{COEFF_COLUMN}_{i}"] = arr[COEFF_COLUMN][:, i]
    return naive


def astropy_to_dataframe(table: Table) -> DataFrame:
    names = [
        name for name in table.colnames if name != COEFF_COLUMN
    ]  # The problem column, a 10-element float array
    naive = table[names].to_pandas()
    num_coeffs = len(table[COEFF_COLUMN])
    for i in range(num_coeffs):
        naive[f"{COEFF_COLUMN}_{i}"] = table[COEFF_COLUMN][:, i]
    return naive
    # return table.to_pandas()


def dataframe_to_sql(
    df: DataFrame, table_name: str, connection: sqlite3.Connection
) -> int | None:
    # return df.to_sql(table_name, connection, if_exists="replace", chunksize=10000)
    stepsize=2*(10**6)
    print("Expected Iters: ", len(df)//stepsize)
    for i in range(0, len(df), stepsize):
        print(i)
        try:
            df.iloc[i:min(i+stepsize,len(df))].to_sql(table_name, connection, index=False, if_exists="append")
        except Exception as e:
            print(f"FAILED! At Index {i}")
            print(e)




# Other way around
def sql_to_astropy(sqlite_file: str, columns=[]) -> Table:
    connection = sqlite3.connect(sqlite_file)
    df = sql_to_dataframe(connection, columns)
    return dataframe_to_astropy(df)


def sql_to_numpy(sqlite_file: str, columns=[]) -> ndarray:
    connection = sqlite3.connect(sqlite_file)
    df = sql_to_dataframe(connection, columns)
    return df
    # return dataframe_to_numpy(df)


def dataframe_to_astropy(df: DataFrame) -> Table:
    # TODO
    return Table.from_pandas(df)


def dataframe_to_numpy(df: DataFrame) -> ndarray:
    # Assumes the dataframe has a DType column as we created earlier
    naive = df.to_records(index=False)
    # print(naive.dtype)
    colnames = naive.dtype.names
    coeff_indices = [
        int(name.replace(f"{COEFF_COLUMN}_", ""))
        for name in colnames
        if name.startswith(f"{COEFF_COLUMN}_")
    ]
    if coeff_indices:
        num_coeffs = max(coeff_indices) + 1
        new_dtype = [(COEFF_COLUMN, (">f8", (num_coeffs,)))]
        naive = add_field(naive, new_dtype)
        for i in range(num_coeffs):
            naive[COEFF_COLUMN][:, i] = naive[f"COEFF_{i}"]

    return naive


def sql_to_dataframe(connection: sqlite3.Connection, columns: List[str]) -> DataFrame:
    unique_table = get_table_list(connection)[0]
    # print(unique_table)
    # This is injectable, probably. That's not great.
    # TODO Switch to sqlalchemy so I don't fuck myself over and disgrace myself.
    print(connection)
    print(columns)
    if columns:
        return pd.read_sql_query(
            f"SELECT {','.join(columns)} FROM {unique_table}", connection
        )
    return pd.read_sql_query(f"SELECT * FROM {unique_table}", connection)
    # return pd.read_sql_table(unique_table, connection)


# Helpers
def get_table_list(connection: sqlite3.Connection) -> Tuple[str]:
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return cursor.fetchall()[0]


def tablename_from_filename(path: str) -> str:
    return basename(filename(path)).replace("-", "_")


def setup_db(sql_file: str) -> sqlite3.Connection:
    print(sql_file)
    return sqlite3.connect(sql_file)


def get_sql_file_path(tablename: str) -> str:
    return f"{SQL_DIR}/{tablename}.sqlite"


# From https://stackoverflow.com/questions/1201817/adding-a-field-to-a-structured-numpy-array
def add_field(a, descr):
    """Return a new array that is like "a", but has additional fields.

    Arguments:
      a     -- a structured numpy array
      descr -- a numpy type description of the new fields

    The contents of "a" are copied over to the appropriate fields in
    the new array, whereas the new fields are uninitialized.  The
    arguments are not modified.

    >>> sa = numpy.array([(1, 'Foo'), (2, 'Bar')], \
                         dtype=[('id', int), ('name', 'S3')])
    >>> sa.dtype.descr == numpy.dtype([('id', int), ('name', 'S3')])
    True
    >>> sb = add_field(sa, [('score', float)])
    >>> sb.dtype.descr == numpy.dtype([('id', int), ('name', 'S3'), \
                                       ('score', float)])
    True
    >>> numpy.all(sa['id'] == sb['id'])
    True
    >>> numpy.all(sa['name'] == sb['name'])
    True
    """
    if a.dtype.fields is None:
        raise ValueError("`A' must be a structured numpy array")
    b = np.empty(a.shape, dtype=a.dtype.descr + descr)
    for name in a.dtype.names:
        b[name] = a[name]
    return b


# Driver code
FITS_FILE = os.path.expandvars("/dvs_ro/cfs/cdirs/desi/spectro/redux/jura/zcatalog/v1/zall-tilecumulative-jura.fits")
# FITS_FILE = os.path.expandvars(
# j  ("~/d/urap/data/fujilite/zcatalog/zall-tilecumulative-fujilite.fits")
#)


def to_sql():
    return numpy_to_sql(FITS_FILE)


def from_sql():
    sql_file = get_sql_file_path(tablename_from_filename(FITS_FILE))
    return sql_to_numpy(sql_file, columns=COLS)


if __name__ == "__main__":
    print(dt.datetime.now())
    orig = fitsio.read(FITS_FILE, columns=COLS)
    #print("read orig", dt.datetime.now())
    new=from_sql()
    print("read sql", dt.datetime.now())
    # to_sql()
    # reconstructed = from_sql()
    # Play around, check values
