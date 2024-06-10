from typing import Tuple
from astropy.table import Table
import fitsio
import pickle
from pandas import DataFrame
import pandas as pd
from collections import OrderedDict
from ..common.utils import basename, filename
import numpy as np
from numpy import ndarray
import sqlite3
import numpy.lib.recfunctions as rfn

SQL_DIR = "/home/vivien/d/urap/sql"
COEFF_COLUMN = "COEFF"


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
    array = fitsio.read(fits_file)
    df = numpy_to_dataframe(array)
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
    return df.to_sql(table_name, connection, if_exists="replace")


# Other way around
def sql_to_astropy(sqlite_file: str) -> Table:
    connection = sqlite3.connect(sqlite_file)
    df = sql_to_dataframe(connection)
    return dataframe_to_astropy(df)


def sql_to_numpy(sqlite_file: str) -> ndarray:
    connection = sqlite3.connect(sqlite_file)
    df = sql_to_dataframe(connection)
    return dataframe_to_numpy(df)


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
    num_coeffs = max(coeff_indices) + 1
    new_dtype =[(COEFF_COLUMN, (">f8", (num_coeffs,)))]
    naive = add_field(naive, new_dtype)

    for i in range(num_coeffs):
        naive[COEFF_COLUMN][:, i] = naive[f"{COEFF_COLUMN}_{i}"]

    return naive


def sql_to_dataframe(connection: sqlite3.Connection) -> DataFrame:
    unique_table = get_table_list(connection)[0]
    # print(unique_table)
    # This is injectable, probably. That's not great.
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
FITS_FILE = "/home/vivien/d/urap/data/fujilite/zcatalog/zall-pix-fujilite.fits"


def to_sql():
    return numpy_to_sql(FITS_FILE)



def from_sql():
    sql_file = get_sql_file_path(tablename_from_filename(FITS_FILE))
    return sql_to_numpy(sql_file)



if __name__ == "__main__":
    orig = fitsio.read(FITS_FILE)
    to_sql()
    reconstructed = from_sql()
    # Play around, check values
