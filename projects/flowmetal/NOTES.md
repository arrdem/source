# Notes

https://github.com/Pyrlang/Pyrlang
https://en.wikipedia.org/wiki/Single_system_image

## Example - Await

A common pattern working in distributed environments is to want to request another system perform a job and wait for its results.
There are lots of parallels here to making a function or RPC call, except that it's a distributed system with complex failure modes.

In a perfect world we'd want to just write something like this -

```python
#!/usr/bin/env python3.10

from service.client import Client

CLIENT = Client("http://service.local", api_key="...")
job = client.create_job(...)
result = await job
# Do something with the result
```

There's some room for variance here around API design taste, but this snippet is probably familiar to many Python readers.
Let's think about its failure modes.

First, that `await` is doing a lot of heavy lifting.
Presumably it's wrapping up a polling loop of some sort.
That may be acceptable in some circumstances, but it really leaves to the client library implementer the question of what an acceptable retry policy is.

Second, this snippet assumes that `create_job` will succeed.
There won't be an authorization error, or a network transit error, or a remote server error or anything like that.

Third, there's no other record of whatever `job` is.
If the Python interpreter running this program dies, or the user gets bored and `C-c`'s it or the computer encounters a problem, the job will be lost.
Maybe that's OK, maybe it isn't.
But it's a risk.

Now, let's think about taking on some of the complexity needed to solve these problems ourselves.

### Retrying challenges

We can manually write the retry loop polling a remote API.

``` python
#!/usr/bin/env python3.10

from datetime import datetime, timedelta

from service.client import Client


CLIENT = Client("http://service.local", api_key="...")
AWAIT_TIMEOUT = timedelta(minutes=30)
POLL_TIME = timedelta(seconds=10)


def sleep(duration=POLL_TIME):
    """A slightly more useful sleep. Has our default and does coercion."""
    from time import sleep
    if isinstance(duration, timedelta):
        duration = duration.total_seconds()
    sleep(duration)


# Create a job, assuming idempotence
while True:
    try:
        job = client.create_job(...)
        start_time = datetime.now()
        break
    except:
        sleep()

# Waiting for the job
while True:
    # Time-based timeout
    if datetime.now() - start_time > AWAIT_TIMEOUT:
        raise TimeoutError

    # Checking the job status, no backoff linear polling
    try:
        if not job.complete():
            continue
    except:
        sleep()
        continue

    # Trying to read the job result, re-using the retry loop & total timeout machinery
    try:
        result = job.get()
        break
    except:
        sleep()
        continue

# Do something with the result
```

We could pull [retrying](https://pypi.org/project/retrying/) off the shelf and get some real mileage here.
`retrying` is a super handy little library that provides the `@retry` decorator, which implements a variety of common retrying concerns such as retrying N times with linear or exponential back-off, and such.
It's really just the `while/try/except` state machine we just wrote a couple times as a decorator.

``` python
#!/usr/bin/env python3.10

from datetime import datetime, timedelta

from retrying import retry

from service.client import Client


CLIENT = Client("http://service.local", api_key="...")
AWAIT_TIMEOUT = timedelta(minutes=30)
POLL_TIME = timedelta(seconds=10)


class StillWaitingException(Exception):
    """Something we can throw to signal we're still waiting on an external event."""


@retry(wait_fixed=POLL_TIME.total_milliseconds())
def r_create_job(client):
    """R[eliable] create job. Retries over exceptions forever with a delay. No jitter."""
    return client.create_job()


@retry(stop_max_delay=AWAIT_TIMEOUT.total_milliseconds(),
       wait_fixed=POLL_TIME.total_milliseconds())
def r_get_job(job):
    """R[eliable] get job. Retries over exceptions up to a total time with a delay. No jitter."""
    if not job.complete():
        raise StillWaitingException

    return job.get()


job = r_create_job(client)
result = r_get_job(job)
# Do something with the result
```

That's pretty good!
We've preserved most of our direct control over the mechanical retrying behavior, we can tweak it or choose a different provider.
And we've managed to get the syntactic density of the original `await` example back ... almost.

This is where Python's lack of an anonymous function block syntax and other lexical structures becomes a sharp limiter.
In another language like Javascript or LUA, you could probably get this down to something like -

``` lua
-- retry is a function of retrying options to a function of a callable to retry
-- which returns a zero-argument callable which will execute the callable with
-- the retrying behavior as specified.

client = Client("http://service.local", api_key="...")
retry_config = {} -- Fake, obviously
with_retry = retry(retry_config)

job = with_retry(
   funtion ()
     return client.start_plan(...)
   end)()

result = with_retry(
   function()
     if job.complete() then
       return job.get()
     end
   end)()
```

The insight here is that the "callback" function we're defining in the Python example as `r_get_job` and so forth has no intrinsic need to be named.
In fact choosing the arbitrary names `r_get_job` and `r_create_job` puts more load on the programmer and the reader.
Python's lack of block anonymous procedures precludes us from cramming the `if complete then get` operation or anything more complex into a `lambda` without some serious syntax crimes.

Using [PEP-0342](https://www.python.org/dev/peps/pep-0342/#new-generator-method-send-value), it's possible to implement arbitrary coroutines in Python by `.send()`ing values to generators which may treat `yield` statements as rvalues for receiving remotely sent inputs.
This makes it possible to explicitly yield control to a remote interpreter, which will return or resume the couroutine with a result value.

Microsoft's [Durable Functions](https://docs.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview?tabs=python) use exactly this behavior to implement durable functions.
The "functions" provided by the API return sentinels which can be yielded to an external interpreter, which triggers processing and returns control when there are results.
This is [interpreter effect conversion pattern (Extensible Effects)](http://okmij.org/ftp/Haskell/extensible/exteff.pdf) as seen in Haskell and other tools; applied.


``` python
import azure.functions as func
import azure.durable_functions as df

def orchestrator_function(context: df.DurableOrchestrationContext):
    x = yield context.call_activity("F1", None)
    y = yield context.call_activity("F2", x)
    z = yield context.call_activity("F3", y)
    result = yield context.call_activity("F4", z)
    return result

main = df.Orchestrator.create(orchestrator_function)
```

Now it would seem that you could "just" automate doing rewriting that to something like this -

``` python
@df.Durable
def main(ctx):
    x = context.call_activity("F1", None)
    y = context.call_activity("F2", x)
    z = context.call_activity("F3", y)
    return context.call_activity("F4", z)
```

There's some prior art for doing this (https://eigenfoo.xyz/manipulating-python-asts/, https://greentreesnakes.readthedocs.io/en/latest/manipulating.html#modifying-the-tree) but it's a lot of legwork for not much.
There are also some pretty gaping correctness holes in taking the decorator based rewriting approach;
how do you deal with rewriting imported code, or code that's in classes/behind `@property` and other such tricks?

Just not worth it.

Now, what we _can_ do is try to hijack the entire Python interpreter to implement the properties/tracing/history recording we want there.
The default cpython lacks hooks for doing this, but we can write a python-in-python interpreter and "lift" the user's program into an interpreter we control, which ultimately gets most of its behavior "for free" from the underlying cpython interpreter.
There's [an example](https://github.com/pfalcon/pyastinterp) of doing this as part of the pycopy project; although there it's more of a Scheme-style proof of metacircular self-hosting.

There's a modified copy of the astinterp in `scratch/` which is capable of running a considerable subset of py2/3.9 to the point of being able to source-import many libraries including `requests` and run PyPi sourced library code along with user code under hoisted interpretation.

It doesn't support coroutines/generators yet, and there's some machinery required to make it "safe" (meaningfully single-stepable; "fix"/support eval, enable user-defined import/`__import__` through the lifted python VM) but as a proof of concept of a lifted VM I'm genuinely shocked how well this works.

Next questions here revolve around how to "snapshot" the state of the interpreter meaningfully, and how to build a replayable interpreter log.
There are some specific challenges around how Python code interacts with native C code that could limit the viability of this approach, but at the absolute least this fully sandboxed Python interpreter could be used to implement whatever underlying magic could be desired and restricted to some language subset as desired.

The goal is to make something like this work -

``` python
from df import Activity

f1 = Activity("F1")
f2 = Activity("F2")
f3 = Activity("F3")
f4 = Activity("F4")

def main():
    return f4(f3(f2(f1(None))))
```

Which may offer a possible solution to the interpreter checkpointing problem - only checkpoint "supported" operations.
Here the `Activity().__call__` operation would have special support, as with `datetime.datetime.now()` and controlling `time.sleep()`, threading and possibly `random.Random` seeding which cannot trivially be made repeatable.

### Durability challenges

FIXME - manually implementing snapshotting and recovery is hard


### Leverage with language support

FIXME - What does a DSL that helps with all this look like?
