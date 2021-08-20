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

The `naive_fsync` benchmark takes how long a simple `f.write(); f.flush(); os.fsync(f.fnum())` takes, and represents a lower bound for "transactional" I/O in a strictly appending system. That `insert` clocks in at about 10ms/op whereas `naive_fsync` clocks in at about 4.5ms suggests that the "overhead" imposed by SQLite is actually pretty reasonable, and only ~2x gains are possible without sacrificing durability.

``` shell
$ bazel run :benchmark

...

Target //projects/jobq:benchmark up-to-date:
  bazel-bin/projects/jobq/benchmark

...

Getting a baseline
Ran 'naive_serialize' 10000 times, total time 61.108668 ms
  mean: 4.4800743 us
  median: 3.876 us
  stddev: 2.9536885497940415 us
  test overhead: 1.6307925 us

Ran 'naive_fsync' 10000 times, total time 46.169303029 s
  mean: 4.5833899318 ms
  median: 4.3935955 ms
  stddev: 3.6405235897574997 ms
  test overhead: 33.540371099999994 us

Testing with /tmp/jobq-bench.sqlite3
Ran 'insert' 10000 times, total time 106.925228341 s
  mean: 10.660283108 ms
  median: 9.6410375 ms
  stddev: 7.318317035793426 ms
  test overhead: 32.2397261 us

Ran 'poll' 10000 times, total time 102.727780818 s
  mean: 10.2409366588 ms
  median: 9.7355345 ms
  stddev: 6.566850750848292 ms
  test overhead: 31.841423 us

Ran 'append_event' 10000 times, total time 105.075667417 s
  mean: 10.4747147621 ms
  median: 9.6445595 ms
  stddev: 8.221955029149633 ms
  test overhead: 32.8519796 us

Testing with :memory:
Ran 'insert' 10000 times, total time 527.735484 ms
  mean: 49.054487699999996 us
  median: 43.823 us
  stddev: 13.212556522688379 us
  test overhead: 3.7190607 us

Ran 'poll' 10000 times, total time 4.995857505 s
  mean: 495.27983409999996 us
  median: 161.8315 us
  stddev: 443.6358523771585 us
  test overhead: 4.3059164 us

Ran 'append_event' 10000 times, total time 579.750342 ms
  mean: 54.1721441 us
  median: 48.054 us
  stddev: 15.205861822465426 us
  test overhead: 3.8028901 us
```
