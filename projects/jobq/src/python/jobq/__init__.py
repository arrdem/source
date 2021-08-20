"""
A job queue library teetering atop sqlite3.
"""

import logging
import os
import sys
import sqlite3
import json

import anosql
from anosql_migrations import run_migrations, with_migrations

_GET_JOB_FIELDS = """\
    `id`
,   `payload`
,   `events`
,   `state`
,   `modified`
"""

_SQL = f"""\
-- name: migration-0000-create-jobq
CREATE TABLE `job` (
   `id` INTEGER PRIMARY KEY AUTOINCREMENT       -- primary key
,  `payload` TEXT                               -- JSON payload
,  `events` TEXT DEFAULT '[]'                   -- append log of JSON events
,  `state` TEXT                                 -- JSON state of the job
,  `modified` INTEGER DEFAULT CURRENT_TIMESTAMP -- last modified
-- note the `rowid` field is defaulted
);
-- name: migration-0001-index-modified
-- Enable efficient queries ordered by job modification
CREATE INDEX IF NOT EXISTS `job_modified` ON `job` (
    `modified`
);
-- name: job-create<!
INSERT INTO `job` (
    `payload`
,   `state`
,   `events`
) VALUES (
    :payload
,   :state
,   json_array(json_array('job_created', json_object('timestamp', CURRENT_TIMESTAMP)))
)
RETURNING
    `id`
,   `state`
;
-- name: job-get?
SELECT
{_GET_JOB_FIELDS}
FROM `job`
WHERE
    `id` = :id
;
-- name: job-delete!
DELETE FROM `job`
WHERE
    `id` = :id
;
-- name: job-list
SELECT
    `id`
,   `state`
FROM `job`
ORDER BY
    `id` ASC
;
-- name: job-filter-state
SELECT
    `id`
,   `state`
FROM `job`
WHERE `state` = :state
;
-- name: job-append-event!
UPDATE
    `job`
SET
    `events` = json_insert(events, '$[#]', json_array('user_event', json_object('event', json(:event), 'timestamp', CURRENT_TIMESTAMP)))
,   `modified` = CURRENT_TIMESTAMP
WHERE
    `id` = :id
RETURNING
{_GET_JOB_FIELDS}
;
-- name: job-cas-state<!
UPDATE
   `job`
SET
    `events` = json_insert(events, '$[#]', json_array('job_state_advanced', json_object('old', json(:old_state), 'new', json(:new_state), 'timestamp', CURRENT_TIMESTAMP)))
,   `state` = json(:new_state)
,   `modified` = CURRENT_TIMESTAMP
WHERE
    `id` = :id
AND `state` = json(:old_state)
RETURNING
{_GET_JOB_FIELDS}
;
"""

# Anosql even as forked doesn't quite support inserting formatted sub-queries.
# It's not generally safe, etc. So we have to do it ourselves :/
# These two are broken out because they use computed `WHERE` clauses.

_QUERY_SQL = """\
SELECT
    `id`
,   `state`
FROM
    `job` AS `j`
WHERE
    ({})
;
"""

_POLL_SQL = f"""\
UPDATE `job`
SET
    `events` = json_insert(events, '$[#]', json_array('job_state_advanced', json_object('old', json(state), 'new', json(:state), 'timestamp', CURRENT_TIMESTAMP)))
,   `state` = json(:state)
,   `modified` = CURRENT_TIMESTAMP
WHERE
    `id` IN (
SELECT
    `id`
FROM
    `job` AS `j`
WHERE
    ({{}})
ORDER BY
    `modified` ASC
LIMIT 1
)
RETURNING
{_GET_JOB_FIELDS}
;
"""

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def compile_query(query):
    """Compile a query to a SELECT over jobs.

    The query is a sequence of ordered pairs [op, path, val].
    Supported ops are:
     - `<`, `>`, `<=`, `>=`, `=`
     - `LIKE`

    Query ops join under `AND`
    """

    def compile_term(term):
        if term is None:
            return "NULL"
        else:
            assert not any(keyword in term.lower() for keyword in ["select", "update", "delete", ";"])
            return term

    def compile_op(op):
        op, qexpr, val = op
        assert op in ["<", "<=", "=", "!=", ">=", ">", "LIKE", "IS"]
        return f"{compile_term(qexpr)} {op} {compile_term(val)}"

    ops = [compile_op(op) for op in query]
    return " AND ".join(ops)


class JobQueue(object):

    def __init__(self, path):
        self._db = sqlite3.connect(path)
        self._queries = anosql.from_str(_SQL, "sqlite3")

        with self._db as db:
            self._queries = with_migrations("sqlite3", self._queries, db)
            run_migrations(self._queries, db)

    def query(self, query, limit=None):
        with self._db as db:
            query = compile_query(query)

            def qf():
                cur = db.cursor()
                cur.execute(_QUERY_SQL.format(query))
                yield from cur.fetchall()
                cur.close()

            jobs = qf()

            if limit:
                limit = int(limit)
                def lf(iterable):
                    iterable = iter(iterable)
                    for i in range(limit):
                        try:
                            yield next(iterable)
                        except StopIteration:
                            break
                        jobs = lf(jobs)

            return list(jobs)

    def create(self, job, new_state=None):
        """Create a new job on the queue, optionally specifying its state."""

        with self._db as db:
            (id, state), = self._queries.job_create(
                db,
                payload=json.dumps(job),
                state=json.dumps(new_state),
            )
            return id

    def poll(self, query, new_state):
        """Query for the longest-untouched job matching, advancing it to new_state."""

        with self._db as db:
            cur = db.cursor()
            cur.execute(_POLL_SQL.format(compile_query(query)),
                       {"state": json.dumps(new_state)})
            results = cur.fetchall()
            if results:
                return results

    def get(self, job_id):
        """Fetch all available data about a given job by ID."""

        with self._db as db:
            return self._queries.job_get(db, id=job_id)

    def cas_state(self, job_id, old_state, new_state):
        """CAS update a job's state, returning the updated job or indicating a conflict."""

        with self._db as db:
            return self._queries.job_cas_state(
                db,
                id=job_id,
                old_state=json.dumps(old_state),
                new_state=json.dumps(new_state),
            )

    def append_event(self, job_id, event):
        """Append a user-defined event to the job's log."""

        with self._db as db:
            return self._queries.job_append_event(
                db,
                id=job_id,
                event=json.dumps(event)
            )

    def delete_job(self, job_id):
        """Delete a job by ID, regardless of state."""

        with self._db as db:
            return self._queries.job_delete(db, id=job_id)
