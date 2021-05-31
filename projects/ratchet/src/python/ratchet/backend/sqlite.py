"""
An implementation of the ratchet model against SQLite.
"""

from contextlib import closing
import os
import socket
import sqlite3 as sql

from ratchet import Event, Message, Request


SCHEMA_SCRIPT = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ratchet_messages
( id               INTEGER
                     PRIMARY KEY
, header_timestamp INTEGER
                     DEFAULT CURRENT_TIMESTAMP
, header_author    TEXT
, header_space     TEXT
                     DEFAULT '_'
, header_ttl       INTEGER
, message          TEXT
);

CREATE TABLE IF NOT EXISTS ratchet_events
( id               INTEGER
                     PRIMARY KEY
, header_timestamp INTEGER
                     DEFAULT CURRENT_TIMESTAMP
, header_author    TEXT
, header_space     TEXT
                     DEFAULT '_'
, header_ttl       INTEGER
, timeout          INTEGER
, state            TEXT
                     DEFAULT 'pending'
                     CHECK(state IN ('pending', 'set', 'timeout'))
);

CREATE TABLE IF NOT EXISTS ratchet_event_messages
( id               INTEGER
                     PRIMARY KEY
, event_id         INTEGER
, message_id       INTEGER
, FOREIGN KEY(message_id) REFERENCES ratchet_messages(id)
, FOREIGN KEY(event_id) REFERENCES ratchet_events(id)
);

CREATE TABLE IF NOT EXISTS ratchet_requests
( id               INTEGER
                     PRIMARY KEY
, header_timestamp INTEGER
                     DEFAULT CURRENT_TIMESTAMP
, header_author    TEXT
, header_space     TEXT
                     DEFAULT '_'
, header_ttl       INTEGER
, timeout          INTEGER
, body             TEXT
, response         TEXT
                     DEFAULT NULL
, state            TEXT
                     DEFAULT 'pending'
                     CHECK(state IN ('pending', 'responded', 'revoked', 'timeout'))
);

CREATE TABLE IF NOT EXISTS ratchet_request_messages
( id               INTEGER
                     PRIMARY KEY
, request_id       INTEGER
, message_id       INTEGER
, FOREIGN KEY(request_id) REFERENCES ratchet_requests(id)
, FOREIGN KEY(message_id) REFERENCES ratchet_events(id)
);
"""

CREATE_MESSAGE_SCRIPT = """
INSERT INTO ratchet_messages (
  header_author
, header_space
, header_ttl
, message
)
VALUES (?, ?, ?, ?);
"""

CREATE_EVENT_SCRIPT = """
INSERT INTO ratchet_events (
  header_author
, header_space
, header_ttl
, timeout
)
VALUES (?, ?, ?, ?);
"""


class SQLiteDriver:
    def __init__(
        self,
        filename="~/.ratchet.sqlite3",
        sqlite_timeout=1000,
        message_ttl=60000,
        message_space="_",
        message_author=f"{os.getpid()}@{socket.gethostname()}",
    ):
        self._path = os.path.expanduser(filename)
        self._sqlite_timeout = sqlite_timeout
        self._message_ttl = message_ttl
        self._message_space = message_space
        self._message_author = message_author

        with closing(self._connection()) as conn:
            self.initialize_schema(conn)

    @staticmethod
    def initialize_schema(conn: sql.Connection):
        conn.executescript(SCHEMA_SCRIPT)

    def _connection(self):
        return sql.connect(self._filename, timeout=self._sqlite_timeout)

    def create_message(
        self, message: str, ttl: int = None, space: str = None, author: str = None
    ):
        """Create a single message."""

        ttl = ttl or self._message_ttl
        space = space or self._message_space
        author = author or self._message_author
        with closing(self._connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_MESSAGE_SCRIPT, author, space, ttl, message)
            return cursor.lastrowid

    def create_event(
        self, timeout: int, ttl: int = None, space: str = None, author: str = None
    ):
        """Create a (pending) event."""

        ttl = ttl or self._message_ttl
        space = space or self._message_space
        author = author or self._message_author
        with closing(self._connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_EVENT_SCRIPT, author, space, ttl, timeout)
            return cursor.lastrowid
