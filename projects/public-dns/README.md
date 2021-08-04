# Public DNS automation

A tool for wiring reading a public IPv4 address through to generating and publishing DNS records.
At present, this tool is wired up to leverage the Meraki API for read and the Gandi REST API as the write target.

## Example config

``` yaml
---
gandi:
  key: "[[ REDACTED ]]"

meraki:
  key:           "[[ REDACTED ]]"
  organization:  "[[ REDACTED ]]"
  network:       "[[ REDACTED ]]"
  router_serial: "[[ REDACTED ]]"

tasks:
  # My zones
  - template: arrdem.com.j2
    zones:
      - arrdem.com
      - arrdem.me
      - reidmckenzie.com

  - paren.party

  # Parked domains
  - template: park.j2
    zones:
      - yakshave.club

  - template: tirefireind.us.j2
    zones:
      - tirefireind.us
      - tirefire.industries

# Bindings consumed by jinja2
bindings:
  ttl: 300 # 5min TTL on records
  sroo:
    public_v4: 67.164.172.171

  # the local: key is automatically spliced in here
  # local: public_v4: < IPv4 addr. >
  # local: public_v6: < IPv6 addr. >

```

## LICENSE

Copyright Reid 'arrdem' McKenzie August 2021.

Published under the terms of the MIT license.
