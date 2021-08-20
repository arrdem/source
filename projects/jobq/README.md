# Jobq

Abusing sqlite3 as a job queue.

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
