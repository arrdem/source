# Flowmetal

> A shining mercurial metal laden with sensors and almost infinitely reconfigurable.
>
> The stuff of which robots and servitors are made.

Flowmetal is a substrate for automation.
It attempts to provide a programming environment wherein programs are durable, evented and asynchronous aimed at what would traditionally be described as scripting or coordination.

Let's unpack these terms.

**Durable** - programs and their state are not dynamic and RAM located as with traditional models of processes.
Instead programs and their state are always persisted to storage.
This allows programs to sleep for a long time or even move seamlessly between machines.

**Evented** - durability is implemented in an event sourced style.
Each program retails - or at least has the opportunity to retain - both a log of any external events and of its own execution.
This allows for programs to easily rebuild their state, simplifies the durable programming model, and greatly simplifies debugging as intermediary states are retained and inspectable.

This also allows for external systems such as REST callback APIs, databases and such to easily integrate with Flowmetal programs as event sources.
It also allows bidirectional communication between Flowmetal programs and other more traditional programming environments.
Anything that can communicate with Flowmetal can provide function implementations, or call Flowmetal programs!

**Asynchronous** - thanks to Flowmetal's evented execution model, waiting for slow external events either synchronously or asynchronously is second nature!
Flowmetal is especially good at waiting for very, very slow external operations.
Stuff like webhooks and batch processes.

**Scripting** - the tradeoff Flowmetal makes for the evented model is that it's slow.
While Flowmetal foreign functions could be fast, Flowmetal's interpreter isn't designed for speed.
It's designed for eventing and ensuring durability.
This makes Flowmetal suitable for interacting with and coordinating other systems, but it's not gonna win any benchmark games.

## An overview

In the systems world we have SH, Borne SH, BASH, ZSH and friends which provide a common interface for connecting processes together.
However in the distributed system world we don't have a good parallel for connecting microservices; especially where complex failure handling is required.

I previously [blogged a bit](https://www.arrdem.com/2019/04/01/the_silver_tower/) about some ideas for what this could look like.
I'm convinced that a programming environment based around [virtual resiliency](https://www.microsoft.com/en-us/research/publication/a-m-b-r-o-s-i-a-providing-performant-virtual-resiliency-for-distributed-applications/) is a worthwhile goal (having independently invented it) and worth trying to bring to a mainstream general purpose platform like Python.

Flowmetal is an interpreted language backed by a durable event store.
The execution history of a program is persisted to the durable store as execution precedes.
If an interpretation step fails to persist, it can't have external effects and can be retried or recovered.
The event store also provides Flowmetal's only interface for communicating with external systems.
Other systems can attach to Flowmetal's datastore and send events to and receive them from Flowmetal.
For instance Flowmetal contains a reference implementation of a HTTP callback connector and of a HTTP request connector.
This allows Flowmetal programs to request that HTTP requests be sent on their behalf, consume the result, and wait for callbacks.

A Flowmetal setup would look something like this -

```
                      +----------------------------+
                    +---------------------------+  |
                  +--------------------------+  |--+
                  | External HTTP service(s) |--+
                  +--------------------------+
                     ^                  ^
                     |                  |
                     v                  v
   +-----------------------+     +------------------------+
   | HTTP server connector |     | HTTP request connector |
   +-----------------------+     +------------------------+
                     ^                  ^
                     |                  |
                     v                  v
                    +--------------------+
                    | Shared event store |
                    +--------------------+
                             ^
                             |
                             v
                +--------------------------+
                | Flowmetal interpreter(s) |
                +--------------------------+
```

A Flowmetal program could look something like this -

``` python
#!/usr/bin/env flowmetal

from flow.http import callback
from flow.http import request
from flow.time import forever, sleep


# A common pattern is to make a HTTP request to some service which will do some
# processing and attempt to deliver a callback.
def simple_remote_job(make_request):
  # Make a HTTP callback.
  # HTTP callbacks have a URL to which a result may be delivered at most once,
  # and define an "event" which can be waited for.
  cb = callback.new()
  # Use user-defined logic to construct a job request.
  # When the job completes, it should make a request to the callback URL.
  request = make_request(cb.url)
  # We can now start the job
  resp = request.execute(request)
  # And now we can await a response which will populate the callback's event.
  return await cb.event


# But there are a couple things which can go wrong here. The initial request
# could fail, the remote process could fail and the callback delivery could fail
# to name a few. We can provide general support for handling this by using the
# same control inversion pattern we used for building the request.
def reliable_remote_job(make_request,
                        job_from_response,
                        get_job,
                        callback_timeout=None,
                        job_completed=None,
                        poll_sleep=None,
                        poll_timeout=None):
  # The structure here is much the same, except we need to handle some extra cases.
  # First, we're gonna do the same callback dance but potentially with a timeout.
  cb = callback.new()
  request = make_request(cb.url)
  resp = request.execute(request)
  resp.raise_for_status()
  job = job_from_response(resp)

# If the user gave us a circuit breaker, use that to bound our waiting.
  with callback_timeout or forever():
    try:
      await cb.event
      return get_job(job)
    except Timeout:
      pass

  # The user hasn't given us enough info to do busy waiting, so we timed out.
  if not (job_from_response and job_completed and get_job):
    raise Timeout

  # If we failed to wait for the callback, let's try polling the job.
  # We'll let the user put a total bound on this too.
  with poll_timeout or forever():
    # We use user-defined logic to wait for the job to complete.
    # Note that we don't conflate get_job and job_completed or assume they
    # compose so that users can consume status endpoints without fetches.
    while not job_completed(job):
      # The user can define how we back off too.
      # A stateful function could count successive calls and change behavior.
      # For instance implementing constant, fibonacci or exponential backoff.
      sleep(poll_sleep() if poll_sleep else 1)

    # When the job is "complete", we let the user control fetching its status
    return get_job(job)


# Let's do a quick example of consuming something like this.
# Say we have a system - let's call it wilson - that lets us request jobs
# for doing bare metal management. Drains, reboots, undrains and the like.
def create_job_request(host, stages, callbacks):
  """Forge but don't execute a job creation request."""
  return request.new("POST", f"http://wilson.local/api/v3/host/{host}",
                     json={"stages": stages, "callbacks": callbacks or []})


def job_from_response(create_resp):
  """Handle the job creation response, returning the ID of the created job."""
  return create_resp.json().get("job_id")


def get_job(job_id):
  """Fetch a job."""
  return request.new("GET" f"http://wilson.local/api/v3/job/{job_id}").json()


def job_completed(job_id):
  """Decide if a job has competed."""
  return (
    request.new("GET" f"http://wilson.local/api/v3/job/{job_id}/status")
    .json()
    .get("status", "PENDING")
  ) in ["SUCCESS", "FAILURE"]


# These tools in hand, we can quickly express a variety of reliable jobs.
def reboot(host):
  """Reboot a host, attempting callback waiting but falling back to retry."""
  return reliable_remote_job(
    lambda url: create_job_request(host, ["drain", "reboot", "undrain"], [url]),
    job_from_response,
    get_job,
    job_completed=job_completed,
  )
```

## License

Mirrored from https://git.arrdem.com/arrdem/flowmetal

Published under the MIT license. See [LICENSE.md](LICENSE.md)
