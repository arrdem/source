"""A quick and dirty Python driver for the jobqd API."""

from datetime import datetime
import typing as t

import requests


class Job(t.NamedTuple):
    id: int
    payload: object
    events: object
    state: object
    modified: datetime

    @classmethod
    def from_json(cls, obj):
        return cls(
            id=int(obj["id"]),
            payload=obj["payload"],
            events=obj["events"],
            state=obj["state"],
            modified=datetime.fromtimestamp(obj["modified"])
        )


class JobqClient(object):
    def __init__(self, url, session=None):
        self._url = url
        self._session = session or requests.Session()

    def jobs(self, query=None, limit=10) -> t.Iterable[Job]:
        """Enumerate jobs on the queue."""

        for job in self._session.post(self._url + "/api/v0/job",
                                      json={"query": query or [],
                                            "limit": limit})\
                                .json()\
                                .get("jobs"):
            yield Job.from_json(job)

    def poll(self, query, state) -> Job:
        """Poll the job queue for the first job matching the given query, atomically advancing it to the given state and returning the advanced Job."""

        return Job.from_json(
            self._session
                .post(self._url + "/api/v0/job/poll",
                      json={"query": query,
                            "state": state})
                .json())

    def create(self, payload: object, state=None) -> Job:
        """Create a new job in the system."""

        return Job.from_json(
            self._session
                .post(self._url + "/api/v0/job/create",
                      json={"payload": payload,
                            "state": state})
                .json())

    def fetch(self, job: Job) -> Job:
        """Fetch the current state of a job."""

        return Job.from_json(
            self._session
                .get(self._url + "/api/v0/job/" + job.id)
                .json())

    def advance(self, job: Job, state: object) -> Job:
        """Attempt to advance a job to a subsequent state."""

        return Job.from_json(
            self._session
                .post(job.url + "/state",
                      json={"old": job.state,
                            "new": state})
                .json())

    def event(self, job: Job, event: object) -> Job:
        """Attempt to record an event against a job."""

        return Job.from_json(
            self._session
                .post(self._url + f"/api/v0/job/{job.id}/event",
                      json=event)
                .json())

    def delete(self, job: Job) -> None:
        """Delete a remote job."""

        return (self._session
                    .delete(self._url + f"/api/v0/job/{job.id}")
                    .raise_for_status())
