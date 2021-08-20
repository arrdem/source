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

from jobq import JobQueue

from flask import abort, current_app, Flask, jsonify, request


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8080)
parser.add_argument("--host", default="localhost")
parser.add_argument("--db", default="~/jobq.sqlite3")


@app.before_first_request
def setup_queries():
    current_app.q = JobQueue(current_app.config["db"])


@app.route("/api/v0/job", methods=["GET", "POST"])
def get_jobs():
    """Return jobs in the system."""

    if request.method == "POST":
        blob = request.get_json(force=True)
    else:
        blob = {}

    query = blob.get("query", [["true"]])

    return jsonify({
        "jobs": [
            {
                "id": id,
                "state": json.loads(state) if state is not None else state
            }
            for id, state in current_app.q.query(query)
        ]
    }), 200


@app.route("/api/v0/job/create", methods=["POST"])
def create_job():
    """Create a job."""

    blob = request.get_json(force=True)
    payload = blob["payload"]
    state = blob.get("state", None)
    id, state = current_app.q.create(
        payload, state
    )
    return jsonify({"id": id, "state": state}), 200


@app.route("/api/v0/job/poll", methods=["POST"])
def poll_job():
    """Using a query, attempt to poll for the next job matching criteria."""

    blob = request.get_json(force=True)
    query = blob["query"]
    state = blob["state"]
    results = current_app.q.poll(query, state)
    if results:
        (id, state), = results
        return jsonify({"id": id, "state": json.loads(state)}), 200
    else:
        abort(404)


@app.route("/api/v0/job/<job_id>", methods=["GET"])
def get_job(job_id):
    """Return a job by ID."""

    r = current_app.q.get(id=job_id)
    if not r:
        abort(404)

    # Unpack the response tuple
    id, payload, events, state, modified = r
    return jsonify({
        "id": id,
        "payload": json.loads(payload),
        "events": json.loads(events),
        "state": json.loads(state) if state is not None else state,
        "modified": modified,
    }), 200


@app.route("/api/v0/job/<job_id>/state", methods=["POST"])
def update_state(job_id):
    """CAS update a job's state, returning the updated job or indicating a conflict."""

    document = request.get_json(force=True)
    old = document["old"]
    new = document["new"]
    if current_app.q.cas_state(job_id, old, new):
        return get_job(job_id)
    else:
        abort(409)


@app.route("/api/v0/job/<job_id>/event", methods=["POST"])
def append_event(job_id):
    """Append a user-defined event to the job's log."""

    return current_app.q.append_event(job_id, event=request.get_json(force=True))


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
