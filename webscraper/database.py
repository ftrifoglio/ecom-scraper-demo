""""Databse functions."""

import sqlite3

import pandas as pd

from ._constants import (
    ARTICLES_DATA_TABLE,
    ARTICLES_URLS_TABLE,
    CATEGORIES_TABLE,
    DATABASE_NAME,
    PAGES_URLS_TABLE,
)

DB_SCHEMA = {
    "categories": CATEGORIES_TABLE,
    "pages_urls": PAGES_URLS_TABLE,
    "articles_urls": ARTICLES_URLS_TABLE,
    "articles_data": ARTICLES_DATA_TABLE,
}


class TableHandler:
    """
    A handler for SQLite table operations.

    Examples
    --------
    >>> categories_table = TableHandler("categories")
    >>> data = [
    ...   {"id": 1, "name": "Category1"},
    ...   {"id": 2, "name": "Category2"}
    ... ]
    >>> categories_table.insert_into(data)
    >>> categories_table.read()
    >>> df = categories_table.to_pandas()
    >>> print(df)
    """

    def __init__(self, table_name: str, db_name: str | None = None):
        """
        Initialize a new instance of TableHandler.

        A handler for SQLite table operations.

        Parameters
        ----------
        table_name : str
            Name of the table to handle.
        db_name : str, optional.
            Name of the table to handle. Default is None.
        """
        if db_name:
            self._db_name = db_name
        else:
            self._db_name = DATABASE_NAME
        self._table_name = table_name
        self.create_table()

    def _connect(self) -> sqlite3.Connection:
        """Establish and returns a connection to the database."""
        return sqlite3.connect(self._db_name)

    def create_table(self) -> None:
        """
        Create a table based on the provided table_name.

        The table schema is fetched from the DB_SCHEMA dictionary.
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS {self._table_name}
                ({DB_SCHEMA[self._table_name]})"""
            )
            conn.commit()

    def insert_into(self, data: list[dict]) -> None:
        """
        Insert data into the table.

        Parameters
        ----------
        data : list[dict]
            List of dictionaries, where each dictionary represents a record to insert.

        Examples
        --------
        >>> data = [{"id": 1, "name": "Category1"}, {"id": 2, "name": "Category2"}]
        >>> handler.insert_into(data)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{self._table_name}')")
            columns = [c[1] for c in cursor.fetchall()]
            string_columns = ",".join(columns)
            values = ",".join(["?"] * len(columns))
            cursor.executemany(
                f"""INSERT OR REPLACE INTO {self._table_name} ({string_columns})
                VALUES ({values})""",
                [tuple(c.values()) for c in data],
            )
            conn.commit()

    def read(self) -> None:
        """
        Read and prints the first 5 records from the table.

        Examples
        --------
        >>> handler.read()
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self._table_name} LIMIT 5")
            print(cursor.fetchall())

    def to_pandas(self) -> pd.DataFrame:
        """
        Fetch data from the table and returns it as a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame containing all records from the table.

        Examples
        --------
        >>> df = handler.to_pandas()
        >>> print(df)
        """
        with self._connect() as conn:
            return pd.read_sql_query(f"SELECT * FROM {self._table_name}", conn)
