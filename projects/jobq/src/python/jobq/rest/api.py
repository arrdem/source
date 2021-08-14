"""A quick and dirty Python driver for the jobq API."""

import typing as t

import requests


class DehydratedJob(t.NamedTuple):
    """The 'important' bits of a given job."""

    id: int
    url: str
    state: object


class HydratedJob(t.NamedTuple):
    """The full state of a given job."""

    id: int
    url: str
    state: object
    payload: object
    events: object


Job = t.Union[DehydratedJob, HydratedJob]


class JobqClient(object):
    def __init__(self, url, session=None):
        self._url = url
        self._session = session or requests.Session()

    def _job(self, json):
        return DehydratedJob(id=json["id"],
                             url=f"{self._url}/api/v0/job/{json.get('id')}",
                             state=json["state"])

    def jobs(self, query=None, limit=10) -> t.Iterable[DehydratedJob]:
        """Enumerate jobs on the queue."""

        for job_frag in self._session.post(self._url + "/api/v0/job",
                                           json={"query": query or [],
                                                 "limit": limit})\
                                     .json()\
                                     .get("jobs"):
            yield self._job(job_frag)

    def poll(self, query, state) -> DehydratedJob:
        """Poll the job queue for the first job matching the given query, atomically advancing it to the given state and returning the advanced Job."""

        return self._job(self._session.post(self._url + "/api/v0/job/poll",
                                            json={"query": query,
                                                  "state": state}).json())

    def create(self, payload: object) -> DehydratedJob:
        """Create a new job in the system."""

        job_frag = self._session.post(self._url + "/api/v0/job/create",
                                      json=payload)\
                                .json()
        return self._job(job_frag)

    def fetch(self, job: Job) -> HydratedJob:
        """Fetch the current state of a job."""

        return HydratedJob(url=job.url, **self._session.get(job.url).json())

    def advance(self, job: Job, state: object) -> Job:
        """Attempt to advance a job to a subsequent state."""

        return HydratedJob(url=job.url,
                           **self._session.post(job.url + "/state",
                                                json={"old": job.state,
                                                      "new": state}).json())

    def event(self, job: Job, event: object) -> HydratedJob:
        """Attempt to record an event against a job."""

        return HydratedJob(url=job.url,
                           **self._session.post(job.url + "/event",
                                                json=event).json())

    def delete(self, job: Job) -> None:
        """Delete a remote job."""

        return self._session.delete(job.url)\
                            .raise_for_status()
