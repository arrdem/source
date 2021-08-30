"""Quick and dirty migrations for AnoSQL."""

from datetime import datetime
from hashlib import sha256
import logging
import re
import typing as t

from anosql.core import from_str, Queries


log = logging.getLogger(__name__)


class MigrationDescriptor(t.NamedTuple):
    name: str
    sha256sum: str
    committed_at: t.Optional[datetime] = None

    def __repr__(self):
        return f"MigrationDescriptor(name={self.name!r}, sha256sum='{self.sha256sum[:7]}...')"

    def __hash__(self):
        return hash((self.name, self.sha256sum))

    def __eq__(self, other):
        return (self.name, self.sha256sum) == (other.name, other.sha256sum)


_SQL = """
-- name: anosql_migrations_create_table#
-- Create the migrations table for the anosql_migrations plugin.
CREATE TABLE IF NOT EXISTS `anosql_migration` (
    `name` TEXT PRIMARY KEY NOT NULL
,   `committed_at` INT
,   `sha256sum` TEXT NOT NULL
,   CONSTRAINT `am_sha256sum_unique` UNIQUE (`sha256sum`)
);

-- name: anosql_migrations_list
-- List committed migrations
SELECT
    `name`
,   `committed_at`
,   `sha256sum`
FROM `anosql_migration`
WHERE
    `committed_at` > 0
ORDER BY
    `name` ASC
;

-- name: anosql_migrations_get
-- Get a given migration by name
SELECT
    `name`
,   `committed_at`,
,   `sha256sum`
FROM `anosql_migration`
WHERE
    `name` = :name
ORDER BY
    `rowid` ASC
;

-- name: anosql_migrations_create<!
-- Insert a migration, marking it as committed
INSERT OR REPLACE INTO `anosql_migration` (
    `name`
,   `committed_at`
,   `sha256sum`
) VALUES (
    :name
,   :date
,   :sha256sum
);
"""


def with_migrations(driver_adapter, queries: Queries, conn) -> Queries:
    """Initialize the migrations plugin."""

    # Compile SQL as needed from the _SQL constant
    _q = from_str(_SQL, driver_adapter)

    # Merge. Sigh.
    for _qname in _q.available_queries:
        queries.add_query(_qname, getattr(_q, _qname))

    # Create the migrations table
    create_tables(queries, conn)

    return queries


def create_tables(queries: Queries, conn) -> None:
    """Create the migrations table (if it doesn't exist)."""

    if queries.anosql_migrations_create_table(conn):
        log.info("Created migrations table")

    # Insert the bootstrap 'fixup' record
    execute_migration(queries, conn,
                      MigrationDescriptor(
                          name="anosql_migrations_create_table",
                          sha256sum=sha256(queries.anosql_migrations_create_table.sql.encode("utf-8")).hexdigest()))


def committed_migrations(queries: Queries, conn) -> t.Iterable[MigrationDescriptor]:
    """Enumerate migrations committed to the database."""

    for name, committed_at, sha256sum in queries.anosql_migrations_list(conn):
        yield MigrationDescriptor(
            name=name,
            committed_at=datetime.fromtimestamp(committed_at),
            sha256sum=sha256sum,
        )


def available_migrations(queries: Queries, conn) -> t.Iterable[MigrationDescriptor]:
    """Enumerate all available migrations, executed or no."""

    for query_name in sorted(queries.available_queries):
        if not re.match("^migration", query_name):
            continue

        if query_name.endswith("_cursor"):
            continue

        # query_name: str
        # query_fn: t.Callable + {.__name__, .__doc__, .sql}
        query_fn = getattr(queries, query_name)
        yield MigrationDescriptor(
            name = query_name,
            committed_at = None,
            sha256sum = sha256(query_fn.sql.encode("utf-8")).hexdigest())


def execute_migration(queries: Queries, conn, migration: MigrationDescriptor):
    """Execute a given migration singularly."""

    with conn:
    # Mark the migration as in flight
        queries.anosql_migrations_create(
            conn,
            # Args
            name=migration.name,
            date=-1,
            sha256sum=migration.sha256sum,
        )

        # Run the migration function
        getattr(queries, migration.name)(conn)

        # Mark the migration as committed
        queries.anosql_migrations_create(
            conn,
            # Args
            name=migration.name,
            date=int(datetime.utcnow().timestamp()),
            sha256sum=migration.sha256sum,
        )


def run_migrations(queries, conn):
    """Run all remaining migrations."""

    avail = set(available_migrations(queries, conn))
    committed = set(committed_migrations(queries, conn))

    for migration in sorted(avail, key=lambda m: m.name):
        if migration in committed:
            log.info(f"Skipping committed migration {migration.name}")

        else:
            log.info(f"Beginning migration {migration.name}")

            try:
                execute_migration(queries, conn, migration)
            except Exception as e:
                log.exception(f"Migration {migration.name} failed!", e)
                raise e
