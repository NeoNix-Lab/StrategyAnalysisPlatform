"""
Module for managing SQLite database operations and CSV integration using pandas.
"""

import os
import sqlite3
from typing import Any, Optional

import pandas as pd


class DataRetriever:
    """
    Provides methods to create tables from CSV, insert DataFrame data, and fetch data
    from an SQLite database file specified by a path.
    """

    def __init__(self, db_path: str="C:\\Users\\user\\OneDrive\\Desktop\\DB\\Test_Cloud_Lite.db"):
        """
        Initialize the DataRetriever with the path to the SQLite database file.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        directory = os.path.dirname(db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        """
        Create and return a new connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection object to the database.
        """
        return sqlite3.connect(self.db_path)

    def create_table_from_csv(self, table_name: str, csv_path: str) -> None:
        """
        Create or replace a table in the database from a CSV file.

        Args:
            table_name (str): Name of the table to create or replace.
            csv_path (str): Path to the CSV file to import.

        Raises:
            FileNotFoundError: If the CSV file does not exist.
            sqlite3.Error: If a database error occurs.
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        conn = self._connect()
        try:
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        finally:
            conn.close()

    def insert_data(self, table_name: str, data: pd.DataFrame) -> None:
        """
        Append records from a DataFrame to an existing table.

        Args:
            table_name (str): Name of the target table.
            data (pd.DataFrame): DataFrame containing the records to insert.

        Raises:
            ValueError: If the DataFrame is empty.
            sqlite3.Error: If a database error occurs.
        """
        if data.empty:
            raise ValueError("Cannot insert an empty DataFrame.")

        conn = self._connect()
        try:
            data.to_sql(table_name, conn, if_exists='append', index=False)
        finally:
            conn.close()

    def fetch_data(self, table_name: str) -> pd.DataFrame:
        """
        Retrieve all records from a specified table.

        Args:
            table_name (str): Name of the table to query.

        Returns:
            pd.DataFrame: DataFrame containing all table records.

        Raises:
            sqlite3.Error: If a database error occurs.
        """
        conn = self._connect()
        try:
            return pd.read_sql(f"SELECT * FROM {table_name};", conn)
        finally:
            conn.close()

    def fetch_data_from_prop(
            self,
            table_name: str,
            prop_name: str,
            prop_val: Any
    ) -> pd.DataFrame:
        """
        Retrieve records from a table filtered by a column value.

        Args:
            table_name (str): Name of the table to query.
            prop_name (str): Column name to filter on.
            prop_val (Any): Value to filter the column by.

        Returns:
            pd.DataFrame: DataFrame of filtered records.

        Raises:
            sqlite3.Error: If a database error occurs.
        """
        conn = self._connect()
        try:
            query = f"SELECT * FROM {table_name} WHERE {prop_name} = ?;"
            return pd.read_sql(query, conn, params=(prop_val,))
        finally:
            conn.close()

    def create_dedicated_table(self, table_name: str, data: pd.DataFrame) -> None:
        """
        Create or replace a dedicated table from a DataFrame.

        Args:
            table_name (str): Name of the new table.
            data (pd.DataFrame): DataFrame to populate the table.

        Raises:
            ValueError: If the DataFrame is empty.
            sqlite3.Error: If a database error occurs.
        """
        if data.empty:
            raise ValueError("Cannot create a table from an empty DataFrame.")

        conn = self._connect()
        try:
            data.to_sql(table_name, conn, if_exists='replace', index=False)
        finally:
            conn.close()
