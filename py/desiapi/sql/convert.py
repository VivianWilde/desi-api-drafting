from typing import Tuple
from astropy.table import Table
from pandas import DataFrame
import pandas as pd
from collections import OrderedDict
from ..common.utils import basename, filename
import numpy as np
import sqlite3

SQL_DIR = "/home/vivien/d/urap/sql"


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


def astropy_to_dataframe(table: Table) -> DataFrame:
    names = [
        name for name in table.colnames if name != "COEFF"
    ]  # The problem column, a 10-element float array
    without_coeffs = table[names].to_pandas()
    return without_coeffs
    # return table.to_pandas()


def dataframe_to_sql(
    df: DataFrame, table_name: str, connection: sqlite3.Connection
) -> int | None:
    return df.to_sql(table_name, connection, if_exists="replace")


# Other way around
def sql_to_astropy(sqlite_file: str) -> Table:
    connection = sqlite3.connect(sqlite_file)
    return dataframe_to_astropy(sql_to_dataframe(connection))


def dataframe_to_astropy(df: DataFrame) -> Table:
    return Table.from_pandas(df)


def sql_to_dataframe(connection: sqlite3.Connection) -> DataFrame:
    unique_table = get_table_list(connection)[0]
    print(unique_table)
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


# Driver code
FITS_FILE = "/home/vivien/d/urap/data/fujilite/zcatalog/zall-pix-fujilite.fits"


def to_sql():
    return astropy_to_sql(FITS_FILE)


def from_sql():
    sql_file = get_sql_file_path(tablename_from_filename(FITS_FILE))
    return sql_to_astropy(sql_file)


if __name__ == "__main__":
    orig = Table.read(FITS_FILE)
    to_sql()
    reconstructed = from_sql()
    # Play around, check values
