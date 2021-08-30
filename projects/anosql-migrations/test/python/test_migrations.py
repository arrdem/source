"""Tests covering the migrations framework."""

import sqlite3

import anosql
from anosql.core import Queries
import anosql_migrations
import pytest


_SQL = """\
-- name: migration_0000_create_kv
CREATE TABLE kv (`id` INT, `key` TEXT, `value` TEXT);
"""


def table_exists(conn, table_name):
    return list(conn.execute(f"""\
    SELECT (
        `name`
    )
    FROM `sqlite_master`
    WHERE
        `type` = 'table'
    AND `name` = '{table_name}'
    ;"""))


@pytest.fixture
def conn() -> sqlite3.Connection:
    """Return an (empty) SQLite instance."""

    return sqlite3.connect(":memory:")


def test_connect(conn: sqlite3.Connection):
    """Assert that the connection works and we can execute against it."""

    assert list(conn.execute("SELECT 1;")) == [(1, ), ]


@pytest.fixture
def queries(conn) -> Queries:
    """A fixture for building a (migrations capable) anosql queries object."""

    q = anosql.from_str(_SQL, "sqlite3")
    return anosql_migrations.with_migrations("sqlite3", q, conn)


def test_queries(queries):
    """Assert that we can construct a queries instance with migrations features."""

    assert isinstance(queries, Queries)
    assert hasattr(queries, "anosql_migrations_create_table")
    assert hasattr(queries, "anosql_migrations_list")
    assert hasattr(queries, "anosql_migrations_create")


def test_migrations_create_table(conn, queries):
    """Assert that the migrations system will (automagically) create the table."""

    assert table_exists(conn, "anosql_migration"), "Migrations table did not create"


def test_migrations_list(conn, queries):
    """Test that we can list out available migrations."""

    ms = list(anosql_migrations.available_migrations(queries, conn))
    assert any(m.name == "migration_0000_create_kv" for m in ms), f"Didn't find in {ms!r}"


def test_committed_migrations(conn, queries):
    """Assert that only the bootstrap migration is committed to the empty connection."""

    ms = list(anosql_migrations.committed_migrations(queries, conn))
    assert len(ms) == 1
    assert ms[0].name == "anosql_migrations_create_table"


def test_apply_migrations(conn, queries):
    """Assert that if we apply migrations, the requisite table is created."""

    anosql_migrations.run_migrations(queries, conn)
    assert table_exists(conn, "kv")


@pytest.fixture
def migrated_conn(conn, queries):
    """Generate a connection whithin which the `kv` migration has already been run."""

    anosql_migrations.run_migrations(queries, conn)
    return conn


def test_post_committed_migrations(migrated_conn, queries):
    """Assert that the create_kv migration has been committed."""

    ms = list(anosql_migrations.committed_migrations(queries, migrated_conn))
    assert any(m.name == "migration_0000_create_kv" for m in ms), "\n".join(migrated_conn.iterdump())
