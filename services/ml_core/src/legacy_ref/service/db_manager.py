# -*- coding: utf-8 -*-
"""
Modulo per la gestione di database SQLite tramite la classe DBManager.
"""

import sqlite3
import os
from typing import Any, List, Tuple, Optional, Union


class DBManager:
    """
    Gestisce le operazioni di connessione e manipolazione di un database SQLite.
    """

    def __init__(self, db_path: str = "C:\\Users\\user\\OneDrive\\Desktop\\DB\\RNN_Tuning_V01.db"):
        """
        Inizializza il DBManager.

        Args:
            db_path (str): Percorso del file del database SQLite.
        """
        self.db_path = db_path
        directory = os.path.dirname(db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        """
        Crea e restituisce una nuova connessione al database.

        Returns:
            sqlite3.Connection: Connessione al database.
        """
        return sqlite3.connect(self.db_path)



    def create_table(self, table_schema: str) -> None:
        """
        Esegue la creazione di una tabella usando lo schema SQL fornito.

        Args:
            table_schema (str): Comando SQL per creare la tabella (CREATE TABLE...).

        Raises:
            sqlite3.Error: Se si verifica un errore durante la creazione.
        """
        conn = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(table_schema)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Errore in create_table: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def retrieve_item(self, table: str, column: str, value: Any) -> Optional[Tuple[Any, ...]]:
        """
        Recupera un singolo record dalla tabella in base al valore specificato.

        Args:
            table (str): Nome della tabella.
            column (str): Nome della colonna per il filtro.
            value (Any): Valore da ricercare.

        Returns:
            Optional[Tuple[Any, ...]]: Il record trovato o None se non esiste o in caso di errore.
        """
        conn = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            query = f"SELECT * FROM {table} WHERE {column}=? LIMIT 1;"
            cursor.execute(query, (value,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Errore in retrieve_item: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_values(self, table: str, desired_colum: str, column: str, value: Any) -> Optional[Tuple[Any, ...]]:
        """
        Recupera un singolo record dalla tabella in base al valore specificato.

        Args:
            table (str): Nome della tabella.
            column (str): Nome della colonna per il filtro.
            value (Any): Valore da ricercare.

        Returns:
            Optional[Tuple[Any, ...]]: Il record trovato o None se non esiste o in caso di errore.
        """
        conn = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            query = f"SELECT {desired_colum} FROM {table} WHERE {column}=?;"
            cursor.execute(query, (value,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Errore in retrieve_item: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def retrieve_all(self, table: str) -> List[Tuple[Any, ...]]:
        """
        Recupera tutti i record di una tabella.

        Args:
            table (str): Nome della tabella.

        Returns:
            List[Tuple[Any, ...]]: Lista di tuple, ciascuna rappresenta un record.
        """
        conn = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            query = f"SELECT * FROM {table};"
            cursor.execute(query)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Errore in retrieve_all: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def exists_retrieve(
            self,
            prop_name: str,
            val_name: str,
            table: str,
            obj_values: Union[Any, List[Any]]
    ) -> List[Tuple[Any, bool, Any]]:
        """
        Verifica l'esistenza di uno o più valori in una colonna e ne restituisce lo stato.

        Args:
            prop_name (str): Colonna da restituire se il record esiste.
            val_name (str): Colonna su cui effettuare il filtro.
            table (str): Nome della tabella.
            obj_values (Any | List[Any]): Valore o lista di valori da verificare.

        Returns:
            List[Tuple[Any, bool, Any]]: Lista di tuple (valore, esiste, parametro) per ciascun valore.
        """
        conn = None
        values = obj_values if isinstance(obj_values, list) else [obj_values]
        results: List[Tuple[Any, bool, Any]] = []
        try:
            conn = self._connect()
            cursor = conn.cursor()
            for val in values:
                query = f"SELECT {prop_name} FROM {table} WHERE {val_name}=? LIMIT 1;"
                cursor.execute(query, (val,))
                row = cursor.fetchone()
                if row:
                    results.append((val, True, row[0]))
                else:
                    results.append((val, False, None))
            return results
        except sqlite3.Error as e:
            print(f"Errore in exists_retrieve: {e}")
            return [(val, False, None) for val in values]
        finally:
            if conn:
                conn.close()

    def retrieve_list_of_records(
            self,
            val_name: str,
            table: str,
            obj_values: Union[Any, List[Any]]
    ) -> List[Tuple[Any, ...]]:
        """
        Recupera tutti i record corrispondenti ai valori specificati.

        Args:
            val_name (str): Colonna su cui effettuare il filtro.
            table (str): Nome della tabella.
            obj_values (Any | List[Any]): Valore o lista di valori da cercare.

        Returns:
            List[Tuple[Any, ...]]: Lista di record trovati.
        """
        conn = None
        values = obj_values if isinstance(obj_values, list) else [obj_values]
        records: List[Tuple[Any, ...]] = []
        try:
            conn = self._connect()
            cursor = conn.cursor()
            for val in values:
                query = f"SELECT * FROM {table} WHERE {val_name}=?;"
                cursor.execute(query, (val,))
                records.extend(cursor.fetchall())
            return records
        except sqlite3.Error as e:
            print(f"Errore in retrieve_list_of_records: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def push(
            self,
            obj_list: List[Tuple[Any, ...]],
            table_schema: str,
            query: str,
            unique_column: Optional[str] = None,
            unique_value_index: Optional[int] = None,
            table_name: Optional[str] = None
    ) -> List[Any]:
        """
        Inserisce una lista di oggetti nel database, evitando duplicati se richiesto.

        Args:
            obj_list (List[Tuple[Any, ...]]): Lista di tuple di valori da inserire.
            table_schema (str): SQL per la creazione della tabella (CREATE TABLE...).
            query (str): SQL di inserimento (INSERT INTO...).
            unique_column (Optional[str]): Colonna per il controllo di unicità.
            unique_value_index (Optional[int]): Indice del valore univoco nella tupla.
            table_name (Optional[str]): Nome della tabella in cui inserire.

        Returns:
            List[Any]: Oggetti restituiti dopo l'inserimento o quelli già esistenti.
        """
        conn = None
        returned: List[Any] = []
        try:
            conn = self._connect()
            cursor = conn.cursor()
            # Creazione tabella
            cursor.execute(table_schema)

            for obj in obj_list:
                if unique_column and unique_value_index is not None and table_name:
                    # Controllo unicità
                    check_q = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {unique_column}=?);"
                    cursor.execute(check_q, (obj[unique_value_index],))
                    exists = cursor.fetchone()[0]
                    if not exists:
                        cursor.execute(query, obj)
                    # Recupere l'oggetto esistente o inserito
                    sel = f"SELECT * FROM {table_name} WHERE {unique_column}=?;"
                    cursor.execute(sel, (obj[unique_value_index],))
                    returned.append(cursor.fetchone())
                else:
                    cursor.execute(query, obj)
                    returned.append(cursor.lastrowid)

            conn.commit()
            return returned
        except sqlite3.Error as e:
            print(f"Errore in push: {e}")
            if conn:
                conn.rollback()
            return []
        finally:
            if conn:
                conn.close()

    def retrieve_last(
            self,
            table: str,
            prop_name: str = 'id'
    ) -> Optional[Any]:
        """
        Recupera il valore dell'ultima riga basato su una colonna ordinata decrescente.

        Args:
            table (str): Nome della tabella.
            prop_name (str): Colonna usata per l'ordinamento (default 'id').

        Returns:
            Any | None: Valore dell'ultima proprietà o None.
        """
        conn = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            query = f"SELECT * FROM {table} ORDER BY {prop_name} DESC LIMIT 1;"
            cursor.execute(query)
            row = cursor.fetchone()
            return row if row else None
        except sqlite3.Error as e:
            print(f"Errore in retrieve_last: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def new_update_record(
            self,
            table: str,
            updates: dict,
            conditions: dict
    ) -> None:
        """
        Aggiorna i record nella tabella secondo gli argomenti forniti.

        Args:
            table (str): Nome della tabella.
            updates (dict): Colonne e nuovi valori da aggiornare.
            conditions (dict): Condizioni per il WHERE clause.
        """
        conn = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            update_clause = ', '.join([f"{k} = ?" for k in updates])
            cond_clause = ' AND '.join([f"{k} = ?" for k in conditions])
            query = f"UPDATE {table} SET {update_clause} WHERE {cond_clause};"
            values = list(updates.values()) + list(conditions.values())
            cursor.execute(query, values)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Errore in new_update_record: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
