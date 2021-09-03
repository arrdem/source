"""
A job queue library teetering atop sqlite3.
"""

from datetime import datetime
import json
import logging
import sqlite3
from typing import NamedTuple, Optional as Maybe

import anosql
from anosql_migrations import run_migrations, with_migrations


_GET_JOB_FIELDS = """\
    `id`
,   `payload`
,   `events`
,   `state`
,   `modified`
"""

_GET_JOB_ORDER = """\
    `modified` ASC
,   `rowid` ASC
"""

_SQL = f"""\
-- name: migration-0000-create-jobq
CREATE TABLE `job` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT  -- primary key
,   `payload` TEXT                          -- JSON payload
,   `events` TEXT DEFAULT '[]'              -- append log of JSON events
,   `state` TEXT                            -- JSON state of the job
,   `modified` INTEGER                      -- last modified
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
,   `modified`
) VALUES (
    :payload
,   json(:state)
,   json_array(json_array('job_created', json_object('timestamp', strftime('%s', 'now'))))
,   strftime('%s','now')
)
RETURNING
{_GET_JOB_FIELDS}
;
-- name: job-get
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
{_GET_JOB_ORDER}
;
-- name: job-append-event<!
UPDATE
    `job`
SET
    `events` = json_insert(events, '$[#]', json_array('user_event', json_object('event', json(:event), 'timestamp', strftime('%s', 'now'))))
,   `modified` = strftime('%s', 'now')
WHERE
    `id` = :id
RETURNING
{_GET_JOB_FIELDS}
;
-- name: job-cas-state<!
UPDATE
   `job`
SET
    `events` = json_insert(events, '$[#]', json_array('job_state_advanced', json_object('old', json(:old_state), 'new', json(:new_state), 'timestamp', strftime('%s', 'now'))))
,   `state` = json(:new_state)
,   `modified` = strftime('%s', 'now')
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

_QUERY_SQL = f"""\
SELECT
{_GET_JOB_FIELDS}
FROM
    `job` AS `j`
WHERE
    {{}}
ORDER BY
{_GET_JOB_ORDER}
;
"""

_POLL_SQL = f"""\
UPDATE `job`
SET
    `events` = json_insert(events, '$[#]', json_array('job_state_advanced', json_object('old', json(state), 'new', json(:state), 'timestamp', strftime('%s', 'now'))))
,   `state` = json(:state)
,   `modified` = strftime('%s', 'now')
WHERE
    `id` IN (
SELECT
    `id`
FROM
    `job` AS `j`
WHERE
    {{}}
ORDER BY
{_GET_JOB_ORDER}
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

    if isinstance(query, list):
        terms = query
    elif isinstance(query, str):
        terms = [query]

    assert not any(
        keyword in query.lower() for keyword in ["select", "update", "delete", ";"]
    )
    return " AND ".join(terms)


class Job(NamedTuple):
    id: int
    payload: object
    events: object
    state: object
    modified: datetime


class JobQueue(object):
    def __init__(self, path):
        self._db = sqlite3.connect(path)
        self._queries = anosql.from_str(_SQL, "sqlite3")

        with self._db as db:
            self._queries = with_migrations("sqlite3", self._queries, db)
            run_migrations(self._queries, db)

    def __enter__(self, *args, **kwargs):
        pass

    def __exit__(self, *args, **kwargs):
        self.close()

    def _from_tuple(self, result) -> Job:
        assert isinstance(result, tuple)
        id, payload, events, state, modified = result
        return Job(
            int(id),
            json.loads(payload),
            json.loads(events),
            json.loads(state),
            datetime.fromtimestamp(int(modified)),
        )

    def _from_result(self, result) -> Job:
        assert isinstance(result, list)
        assert len(result) == 1
        return self._from_tuple(result[0])

    def _from_results(self, results):
        return [self._from_tuple(t) for t in results]

    def close(self):
        if self._db:
            self._db.commit()
            self._db.close()
            self._db = None

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

            return self._from_results(jobs)

    def create(self, job, new_state=None) -> Job:
        """Create a new job on the queue, optionally specifying its state."""

        with self._db as db:
            return self._from_result(
                self._queries.job_create(
                    db,
                    payload=json.dumps(job),
                    state=json.dumps(new_state),
                )
            )

    def poll(self, query, new_state) -> Maybe[Job]:
        """Query for the longest-untouched job matching, advancing it to new_state."""

        with self._db as db:
            cur = db.cursor()
            statement = _POLL_SQL.format(compile_query(query))
            cur.execute(statement, {"state": json.dumps(new_state)})
            results = cur.fetchall()
            if results:
                return self._from_result(results)

    def get(self, job_id):
        """Fetch all available data about a given job by ID."""

        with self._db as db:
            return self._from_result(self._queries.job_get(db, id=job_id))

    def cas_state(self, job_id, old_state, new_state):
        """CAS update a job's state, returning the updated job or indicating a conflict."""

        with self._db as db:
            result = self._queries.job_cas_state(
                db,
                id=job_id,
                old_state=json.dumps(old_state),
                new_state=json.dumps(new_state),
            )
            if result:
                return self._from_result(result)

    def append_event(self, job_id, event):
        """Append a user-defined event to the job's log."""

        with self._db as db:
            return self._from_result(
                self._queries.job_append_event(db, id=job_id, event=json.dumps(event))
            )

    def delete_job(self, job_id):
        """Delete a job by ID, regardless of state."""

        with self._db as db:
            return self._queries.job_delete(db, id=job_id)
