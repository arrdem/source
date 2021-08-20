# Jobq

Jobq is an event-oriented framework for recording _jobs_.
Each _job_ (a JSON request blob POSTed by the user) has an attached log of _events_, and a _state_.
Users may change the _state_ of a job, and doing so automatically produces a new _event_ recording the change.
Users may manually add _events_ to the log.

Note that, while we strongly suggest that _state_ should always be a tagged tuple, no constraints are placed on its contents.

## HTTP API

### GET /api/v0/queue
Enumerate all the queues in the system.

### POST /api/v0/queue
Create a new queue of jobs.

### DELETE /api/v0/queue/<q_id>
Expunge a queue, deleting all jobs in it regardless of state.

### GET /api/v0/queue/<q_id>/job
Return an enumeration of jobs active in the system.

### POST /api/v0/queue/<q_id>/query_jobs
Perform a point-in-time query for jobs.

The query is a list of `[OP, EXPR, EXPR]` triples, which are combined under `AND` to produce a server-side query.
Valid ops are `IS`, `LIKE` and binary comparisons (`<`, `=` and friends).
Valid exprs are any SQLite expression not containing sub-queries.

Here, we're looking for jobs tagged as in the `["CREATED"]` state.

### POST /api/v0/queue/<q_id>/poll_job
Poll for at most one job matching the given query, atomically advancing it to the given state.

Uses the same query format as the /job endpoint.

Here, we're polling for hosts which are in the null (initial) state, and assigning the first such job to this host.
Note that this assignment strategy is likely unsound as it lacks a time-to-live or other validity criteria.

### POST /api/v0/queue/<q_id>/job
Given a JSON document as the POST body, create a new job with a payload in the given state.
If state is not provided, the state `null` is used.

### GET /api/v0/queue/<q_id>/job/<job_id>
Return all available data about a given job, including the payload, event log and current state.

### DELETE /api/v0/queue/<q_id>/job/<job_id>
Expunge a given job from the system by ID.

### POST /api/v0/queue/<q_id>/job/<job_id>/state
POST the 'current' state, and a proposed new state, attempting to update the state of the job using CAS.
If the state of the job updates successfully, a new event will be appended to the job's log and the resulting job will be returned.
Otherwise a conflict will be signaled.

### POST /api/v0/queue/<q_id>/job/<job_id>/event
Append an arbitrary event to the log.
User-defined events will be coded in a `"user_event"` tag, and have `"timestamp"` metadata inserted.
