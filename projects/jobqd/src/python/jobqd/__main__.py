"""
A job queue over HTTP.
"""

import argparse
import logging
import os

from flask import (
    abort,
    current_app,
    Flask,
    jsonify,
    request,
)
from jobq import Job, JobQueue


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8080)
parser.add_argument("--host", default="localhost")
parser.add_argument("--db", default="~/jobq.sqlite3")


@app.before_request
def setup_q():
    request.q = JobQueue(current_app.config["db"])


@app.after_request
def teardown_q():
    request.q.close()


def job_as_json(job: Job) -> dict:
    return {
        "id": job.id,
        "payload": job.payload,
        "events": job.events,
        "state": job.state,
        "modified": int(job.modified),
    }


@app.route("/api/v0/job", methods=["GET", "POST"])
def get_jobs():
    """Return jobs in the system."""

    if request.method == "POST":
        blob = request.get_json(force=True)
    else:
        blob = {}

    query = blob.get("query", "true")

    return jsonify({"jobs": [job_as_json(j) for j in request.q.query(query)]}), 200


@app.route("/api/v0/job/create", methods=["POST"])
def create_job():
    """Create a job."""

    blob = request.get_json(force=True)
    payload = blob["payload"]
    state = blob.get("state", None)
    job = request.q.create(payload, state)
    return jsonify(job_as_json(job)), 200


@app.route("/api/v0/job/poll", methods=["POST"])
def poll_job():
    """Using a query, attempt to poll for the next job matching criteria."""

    blob = request.get_json(force=True)
    query = blob["query"]
    state = blob["state"]
    r = request.q.poll(query, state)
    if r:
        return jsonify(job_as_json(r)), 200
    else:
        abort(404)


@app.route("/api/v0/job/<job_id>", methods=["GET"])
def get_job(job_id):
    """Return a job by ID."""

    r = request.q.get(id=job_id)
    if r:
        return jsonify(job_as_json(r)), 200
    else:
        abort(404)


@app.route("/api/v0/job/<job_id>/state", methods=["POST"])
def update_state(job_id):
    """CAS update a job's state, returning the updated job or indicating a conflict."""

    document = request.get_json(force=True)
    old = document["old"]
    new = document["new"]
    r = request.q.cas_state(job_id, old, new)
    if r:
        return jsonify(job_as_json(r)), 200
    else:
        abort(409)


@app.route("/api/v0/job/<job_id>/event", methods=["POST"])
def append_event(job_id):
    """Append a user-defined event to the job's log."""

    r = request.q.append_event(job_id, event=request.get_json(force=True))
    if r:
        return jsonify(job_as_json(r)), 200
    else:
        abort(404)


@app.route("/api/v0/job/<job_id>", methods=["DELETE"])
def delete_job(job_id):
    """Delete a given job."""

    request.q.job_delete(request.db, id=job_id)

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
