# Jobq

Jobq is an event-oriented framework for recording _jobs_.
Each _job_ (a JSON request blob POSTed by the user) has an attached log of _events_, and a _state_.
Users may change the _state_ of a job, and doing so automatically produces a new _event_ recording the change.
Users may manually add _events_ to the log.

Note that, while we strongly suggest that _state_ should always be a tagged tuple and the default is `["CREATED"]`, no constraints are placed on its contents.

## HTTP API

### GET /api/v0/job
Return an enumeration of jobs active in the system.

**Response** -
```shell
$ curl -X POST $JOBQ/api/v0/job | jq .
{"jobs": [
  {"id": 1, "state": ["CREATED"]},
  {"id": 2, "state": ["ASSIGNED"]},
  {"id": 3, "state": ["SLEEPING"]},
  {"id": 3, "state": ["FINISHED"]}
]}
```

### POST /api/v0/job
Perform a point-in-time query for jobs.

The query is a list of `[OP, EXPR, EXPR]` triples, which are combined under `AND` to produce a server-side query.
Valid ops are `IS`, `LIKE` and binary comparisons (`<`, `=` and friends).
Valid ops any SQLite expression not containing sub-queries.

Here, we're looking for jobs tagged as in the `["CREATED"]` state.
``` shell
$ curl -X POST $JOBQ/api/v0/job --data '{"query": [["IS", "json_extract(state, '$[0]')", "CREATED"]]}' | jq .
{"jobs": [
  {"id": 1, "state": ["CREATED"]},
]}
```

### POST /api/v0/job/create
Given a JSON document as the POST body, create a new job.

```
$ curl -X POST $JOBQ/api/v0/job/create --data '{"msg": "Hello, world!"}' | jq .
{
  "id": 1
}
```

### POST /api/v0/job/poll
Poll for at most one job matching the given query, atomically advancing it to the given state.

Uses the same query format as the /job endpoint.

Here, we're polling for hosts which are in the null (initial) state, and assigning the first such job to this host.
Note that this assignment strategy is likely unsound as it lacks a time-to-live or other validity criteria.

``` shell
$ curl -X POST $JOBQ/api/v0/job/poll --data '{"query": [["IS", "j.state", null]], "state":["ASSIGNED", {"node": 1}]}' | jq .
{
  "id": 3,
  "state": [
    "ASSIGNED",
    {
      "node": 1
    }
  ]
}
```

### GET /api/v0/job/<job_id>
Return all available data about a given job, including the payload, event log and current state.

```shell
$ curl -X GET $JOBQ/api/v0/job/1 | jq .
{
  "id": 1,
  "payload": {
    "msg": "Hello, world"
  },
  "state": [
    "CREATED"
  ],
  "events": [
    [
      "job_created",
      {
        "timestamp": "1628909303"
      }
    ]
  ]
}
```

### POST /api/v0/job/<job_id>/state
Alter the state of a given job, appending a state change event to the log and returning the entire updated job.

``` shell
$ curl -X POST $JOBQ/api/v0/job/1/state --data '["ASSIGNED"]' | jq .
{
  "id": 1,
  "payload": {
    "msg": "Hello, world"
  },
  "state": [
    "ASSIGNED"
  ],
  "events": [
    [
      "job_created",
      {
        "timestamp": "1628911153"
      }
    ],
    [
      "job_state_advanced",
      {
        "new": [
          "ASSIGNED"
        ],
        "old": [
          "CREATED"
        ],
        "timestamp": "1628911184"
      }
    ]
  ]
}
```

### POST /api/v0/job/<job_id>/event
Append an arbitrary event to the log.
User-defined events will be coded in a `"user_event"` tag, and have `"timestamp"` metadata inserted.

``` shell
$ curl -X POST $JOBQ/api/v0/job/1/event --data '["my cool event"]' | jq .events[-1]
[
  "user_event",
  {
    "event": [
      "my cool event"
    ],
    "timestamp": "1628911503"
  }
]
```

### DELETE /api/v0/job/<job_id>
Expunge a given job from the system by ID.
