# Jobq

Abusing sqlite3 as a job queue.

## API

**Note** - this API currently does not support multiplexing queues within a single state store.
As files are ultimately the performance bottleneck, using multiple files PROBABLY serves you better anyway.
But investigation here is needed.

### jobq.JobQueue(path)
Construct and return a fully migrated and connected job queue.
The queue is closable, and usable as a context manager.

### jobq.JobQueue.create(payload, new_state=None)
Create a job with the given payload and optional state.

### jobq.JobQueue.get(job_id)
Read a job back by ID from the queue.

### jobq.JobQueue.poll(query, new_state)
Poll the queue for a single job matching the given query, atomically advancing it to the new state and returning it as if from `get()`.
Note that poll selects the OLDEST MATCHING JOB FIRST, thus providing a global round-robin scheduler on jobs, optimizing for progress not throughput.

### jobq.JobQueue.cas_state(job_id, old_state, new_state)
Atomically update the state of a single job from an old state to a new state.
Note that this operation NEED NOT SUCCEED, as the job MAY be concurrently modified.
Job queue algorithms should either be lock-free or use state to implement markers/locks with timeout based recovery.

### jobq.JobQueue.append_event(job_id, event)
Append a user-defined event to the given job's event log.

### jobq.JobQueue.delete(job_id)
Purge a given job by ID from the system.

## Benchmarks

Benchmarks are extremely steady.
Flushing a sqlite file to disk seems to be the limiting factor of I/O, and pipelining multiple message writes is undoubtably the way to go.
However the purpose of the API is to use the sqlite file as the shared checkpoint between potentially many processes, so 'large' transactions are an antipattern.

Tests suggest that this library is rock steady at 100 writes per sec. and 100 polls per sec. and completely bounded by sqlite controlled I/O as evidenced by using `":memory:"` which doesn't have to `fsync()`.

``` shell
$ bazel run :benchmark

...

Target //projects/jobq:benchmark up-to-date:
  bazel-bin/projects/jobq/benchmark

...

Ran 'insert' 10000 times, total time 101.810816516 (s)
  mean: 0.010148992843 (s)
  median: 0.009474293 (s)
  stddev: 0.006727934042954838 (s)
  test overhead: 3.20888086e-05 (s)

Ran 'poll' 10000 times, total time 100.482262487 (s)
  mean: 0.0100152467857 (s)
  median: 0.0095528585 (s)
  stddev: 0.00821730176268304 (s)
  test overhead: 3.2979463000000004e-05 (s)

Ran 'append_event' 10000 times, total time 105.015296419 (s)
  mean: 0.0104681294652 (s)
  median: 0.009592544 (s)
  stddev: 0.007321370576225584 (s)
  test overhead: 3.34001767e-05 (s)

Testing with :memory:
Ran 'insert' 10000 times, total time 0.37031511 (s)
  mean: 3.3595880100000005e-05 (s)
  median: 2.96015e-05 (s)
  stddev: 1.045088890675899e-05 (s)
  test overhead: 3.4356309e-06 (s)

Ran 'poll' 10000 times, total time 1.17148314 (s)
  mean: 0.0001128911222 (s)
  median: 9.7398e-05 (s)
  stddev: 3.213524197973896e-05 (s)
  test overhead: 4.2571917999999996e-06 (s)

Ran 'append_event' 10000 times, total time 0.415490332 (s)
  mean: 3.78861989e-05 (s)
  median: 3.3019e-05 (s)
  stddev: 1.1752889674795285e-05 (s)
  test overhead: 3.6628343e-06 (s)
```
