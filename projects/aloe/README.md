# Aloe

> - A [cactus](https://www.cacti.net/)-like plant
> - Traditionally used for a variety of skin conditions

Aloe is a quick and dirty network weathermapping tool, much like MTR or Cacti.
Aloe uses multiple threads to first establish a rough network topology via ICMP traceroutes, and then monitor it with ICMP pings.

## Usage

``` sh
$ bazel build //projects/aloe
$ sudo ./bazel-bin/projects/aloe/aloe twitter.com google.com
```

If hosts in topology stop responding for 10s or more (the polling interval is ~1s), they are declared to be warning.
If hosts in topology stop responding for 5s, they are declared down.
If a host in topology resume responding after 5s or more, they are declared to have recovered.
If hosts in topology stop responding for 30 min, they are declared dead and monitoring is stopped.
The topology is reconfigured every 5 min to account to DHCP and upstream changes.

A log of all these events is built in a plain-text format to `incidents.txt`.
The format of this file is -

```
UP        <ip>  <date>
WARN      <ip>  <date>
DOWN      <ip>  <date>
RECOVERED <ip>  <date>   <duration>
DEAD      <ip>  <date>   <duration>
```

## Future work

- [ ] Log topology
- [ ] Attempt to identify "root cause" incidents in the route graph which explain downstream failures
- [ ] Use sqlite3 for aggregation not a plain text file
- [ ] Use a more sophisticated counters and debounce model of host state in the main thread
- [ ] Find some way to incorporate rolling counters (mean, median, stddev, deciles, max) into the UI
- [ ] FFS find some way NOT to depend on that nonsense box-diagram service

## License

Copyright Reid 'arrdem' McKenzie, 11/20/2021.

Published under the terms of the MIT license.
