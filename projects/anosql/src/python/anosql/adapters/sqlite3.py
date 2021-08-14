"""
A driver object implementing support for SQLite3
"""

from contextlib import contextmanager
import logging
import sqlite3

log = logging.getLogger(__name__)


class SQLite3DriverAdapter(object):
    @staticmethod
    def process_sql(_query_name, _op_type, sql):
        """Pass through function because the ``sqlite3`` driver already handles the :var_name
        "named style" syntax used by anosql variables. Note, it will also accept "qmark style"
        variables.

        Args:
            _query_name (str): The name of the sql query. Unused.
            _op_type (anosql.SQLOperationType): The type of SQL operation performed by the sql.
            sql (str): The sql as written before processing.

        Returns:
            str: Original SQL text unchanged.
        """
        return sql

    @staticmethod
    def select(conn, _query_name, sql, parameters):
        cur = conn.cursor()
        log.debug({'sql': sql, 'parameters': parameters})
        cur.execute(sql, parameters)
        results = cur.fetchall()
        cur.close()
        return results

    @staticmethod
    @contextmanager
    def select_cursor(conn: sqlite3.Connection, _query_name, sql, parameters):
        cur = conn.cursor()
        log.debug({'sql': sql, 'parameters': parameters})
        cur.execute(sql, parameters)
        try:
            yield cur
        finally:
            cur.close()

    @staticmethod
    def insert_update_delete(conn: sqlite3.Connection, _query_name, sql, parameters):
        log.debug({'sql': sql, 'parameters': parameters})
        conn.execute(sql, parameters)

    @staticmethod
    def insert_update_delete_many(conn: sqlite3.Connection, _query_name, sql, parameters):
        log.debug({'sql': sql, 'parameters': parameters})
        conn.executemany(sql, parameters)

    @staticmethod
    def insert_returning(conn: sqlite3.Connection, _query_name, sql, parameters):
        cur = conn.cursor()
        log.debug({'sql': sql, 'parameters': parameters})
        cur.execute(sql, parameters)

        if "returning" not in sql.lower():
            # Original behavior - return the last row ID
            results = cur.lastrowid
        else:
            # New behavior - honor a `RETURNING` clause
            results = cur.fetchall()

        log.debug({"results": results})
        cur.close()
        return results

    @staticmethod
    def execute_script(conn: sqlite3.Connection, sql):
        log.debug({'sql': sql, 'parameters': None})
        conn.executescript(sql)
