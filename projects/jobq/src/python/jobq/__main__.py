"""
A mock job queue.
"""

import argparse
from functools import wraps
import json
import logging
import os
import sys
import sqlite3

import anosql
from anosql_migrations import run_migrations, with_migrations
from flask import abort, current_app, Flask, jsonify, request


_SQL = """\
-- name: migration-0000-create-jobq
CREATE TABLE `job` (
   `id` INTEGER PRIMARY KEY AUTOINCREMENT  -- primary key
,  `payload` TEXT                          -- JSON payload
,  `events` TEXT DEFAULT '[]'              -- append log of JSON events
,  `state` TEXT                            -- JSON state of the job
);
-- name: job-create<!
INSERT INTO `job` (
    `payload`
,   `state`
,   `events`
) VALUES (
    :payload
,   :state
,   json_array(json_array('job_created',
                          json_object('timestamp', strftime('%s', 'now'))))
)
RETURNING
    `id`
,   `state`
;
-- name: job-get?
SELECT
    `id`
,   `payload`
,   `events`
,   `state`
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
    `events` = json_insert(events, '$[#]',
                           json_array('user_event',
                                      json_object('event', json(:event),
                                                  'timestamp', strftime('%s', 'now'))))
WHERE
    `id` = :id
;
-- name: job-advance-state!
UPDATE
    `job`
SET
    `events` = json_insert(events, '$[#]',
                           json_array('job_state_advanced',
                                      json_object('old', json(state),
                                                  'new', json(:state),
                                                  'timestamp', strftime('%s', 'now'))))
,   `state` = json(:state)
WHERE
    `id` = :id
;
-- name: job-cas-state<!
UPDATE
   `job`
SET
    `events` = json_insert(events, '$[#]',
                           json_array('job_state_advanced',
                                      json_object('old', json(:old_state),
                                                  'new', json(:new_state),
                                                  'timestamp', strftime('%s', 'now'))))
,   `state` = json(:new_state)
WHERE
    `id` = :id
AND `state` = json(:old_state)
RETURNING
    `id`
;
"""

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8080)
parser.add_argument("--host", default="localhost")
parser.add_argument("--db", default="~/jobq.sqlite3")


@app.before_first_request
def setup_queries():
    # Load the queries
    queries = anosql.from_str(_SQL, "sqlite3")

    # Do migrations
    with sqlite3.connect(current_app.config["db"]) as db:
        queries = with_migrations("sqlite3", queries, db)
        run_migrations(queries, db)

    current_app.queries = queries


@app.before_request
def before_request():
    request.db = sqlite3.connect(current_app.config["db"])
    request.db.set_trace_callback(logging.getLogger("sqlite3").debug)


@app.teardown_request
def teardown_request(exception):
    request.db.commit()
    request.db.close()


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


@app.route("/api/v0/job", methods=["GET", "POST"])
def get_jobs():
    """Return jobs in the system."""

    if request.method == "POST":
        blob = request.get_json(force=True)
    else:
        blob = {}

    if query := blob.get("query"):
        query = compile_query(query)
        print(query)
        def qf():
            cur = request.db.cursor()
            cur.execute(f"SELECT `id`, `state` FROM `job` AS `j` WHERE {query};")
            yield from cur.fetchall()
            cur.close()
        jobs = qf()

    else:
        jobs = current_app.queries.job_list(request.db)

    if limit := blob.get("limit", 100):
        limit = int(limit)
        def lf(iterable):
            iterable = iter(iterable)
            for i in range(limit):
                try:
                    yield next(iterable)
                except StopIteration:
                    break
        jobs = lf(jobs)

    return jsonify({
        "jobs": [
            {
                "id": id,
                "state": json.loads(state) if state is not None else state
            }
            for id, state in jobs
        ]
    }), 200


@app.route("/api/v0/job/create", methods=["POST"])
def create_job():
    """Create a job."""

    blob = request.get_json(force=True)
    payload = blob["payload"]
    state = blob.get("state", None)
    id, state = current_app.queries.job_create(
        request.db,
        payload=json.dumps(payload),
        state=json.dumps(state),
    )
    return jsonify({"id": id, "state": state}), 200


@app.route("/api/v0/job/poll", methods=["POST"])
def poll_job():
    """Using a query, attempt to poll for the next job matching criteria."""

    blob = request.get_json(force=True)
    query = compile_query(blob["query"])
    cur = request.db.cursor()
    cur.execute(f"""\
    UPDATE `job`
    SET
        `events` = json_insert(events, '$[#]',
                               json_array('job_state_advanced',
                                          json_object('old', json(state),
                                                      'new', json(:state),
                                                      'timestamp', strftime('%s', 'now'))))
    ,   `state` = json(:state)
    WHERE
        `id` IN (
            SELECT
                `id`
            FROM
                `job` AS `j`
            WHERE
                {query}
            LIMIT 1
        )
    RETURNING
        `id`
    ,   `state`
    ;""", {"state": json.dumps(blob["state"])})
    results = cur.fetchall()
    cur.close()
    if results:
        (id, state), = results
        return jsonify({"id": id, "state": json.loads(state)}), 200
    else:
        abort(404)


@app.route("/api/v0/job/<job_id>", methods=["GET"])
def get_job(job_id):
    """Return a job by ID."""

    r = current_app.queries.job_get(request.db, id=job_id)
    if not r:
        abort(404)

    # Unpack the response tuple
    id, payload, events, state = r
    return jsonify({
        "id": id,
        "payload": json.loads(payload),
        "events": json.loads(events),
        "state": json.loads(state) if state is not None else state,
    }), 200


@app.route("/api/v0/job/<job_id>/state", methods=["POST"])
def update_state(job_id):
    """CAS update a job's state, returning the updated job or indicating a conflict."""

    document = request.get_json(force=True)
    old = document["old"]
    new = document["new"]
    if current_app.queries.job_cas_state(
        request.db,
        id=job_id,
        old_state=json.dumps(old),
        new_state=json.dumps(new),
    ):
        return get_job(job_id)
    else:
        abort(409)


@app.route("/api/v0/job/<job_id>/event", methods=["POST"])
def append_event(job_id):
    """Append a user-defined event to the job's log."""

    current_app.queries.job_append_event(
        request.db,
        id=job_id,
        event=json.dumps(request.get_json(force=True))
    )

    return get_job(job_id)


@app.route("/api/v0/job/<job_id>", methods=["DELETE"])
def delete_job(job_id):
    """Delete a given job."""

    current_app.queries.job_delete(request.db, id=job_id)

    return jsonify({}), 200

def main():
    """Run the mock server."""

    opts, args = parser.parse_known_args()

    app.config["db"] = os.path.expanduser(os.path.expandvars(opts.db))
    app.config["host"] = opts.host
    app.config["port"] = opts.port

    app.run(
        threaded=True,
    )


if __name__ == "__main__":
    main()
