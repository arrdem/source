# Kook

> I AM NOT A LOONY!
>
> ~ John Cleese

[Apache Zookeeper](https://zookeeper.apache.org/) is a mature distributed coordination system, providing locking, monitoring, leader election and other such capabilities comparable to [Google Chubby](https://ai.google/research/pubs/pub27897) in many ways.
Google has deployed Chubby to solve a number of interesting problems around service discovery (DNS), leadership management & coarse coordination, as well as cluster membership and configuration management.
While these problems prima face appear to be unrelated, they have deep similarities in the requirements they introduce for reliability, and the distributed consensus capabilities needed to offer them.

Kook is a Python library - backed by the Kazoo Zookeeper client - which sketches at a leveraging a Zookeeper cluster to build out host management and coordination capabilities.

Kook's data model consists of hosts and groups.

A host is a model of a physical device.
It has key/value storage in the form of `attributes` and may be a member of one or more `groups`.
Groups likewise have `attributes` and may themselves be members (children) of other groups.

```
>>> from kook.client import KookClient
>>> client = KookClient(hosts="zookeeper:2181")
>>> client.servers()
>>> client.hosts()
[<KookHost '/server/ethos'>,
 <KookHost '/server/pathos'>,
 <KookHost '/server/logos'>,
 ...]
>>> client.server("ethos").groups()
[<KookGroup '/group/hw_ryzen0'>,
 <KookGroup '/group/geo_apartment'>,
 <KookGroup '/group/apartment_git'>,
 <KookGroup '/group/apartment_www'>]
```

## With Ansible

The [`import_inventory.py`](https://git.arrdem.com/arrdem/kook/tree/import_inventory.py) script can be used to convert an existing Ansible inventory into host and group records in Kook.
The script contains shims for importing both host vars and group vars.
However kook is only intended for tracking slow-moving host level vars, and group membership.
I believe configuration data (group vars) should be on groups, and live in source control.
Only inventory and membership should be fast-enough moving to live in Zookeeper.

The [`kook_inventory.py`](https://git.arrdem.com/arrdem/kook/tree/kook_inventory.py) script uses the `KookClient` to provide an [Ansible dynamic inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_dynamic_inventory.html).
To use `kook_inventory.py` with Ansible, you'll need the following lines in your `ansible.cfg`:

```
[default]
inventory = kook_inventory.py
...

[inventory]
enable_plugins = script
...
```

This tells Ansible to use the `kook_inventory.py` script as its sole source of inventory.

## Status

Kook is currently prototype-grade.
The client works, the inventory script works.
The `kook` CLI script is woefully incomplete.

Both the client and client and inventory feature significant limitations.
Zookeeper really wasn't designed for a "full scan" workload like this.
It's a coordination system not a database - for all it may seem appropriate to overload its usage.
Really making this viable would require a meaningful effort to leverage client-side data caching.

The real concern is improving the locking story, using watches to update fetched nodes rather than re-fetching every time.
For coarse-grained actions on slow moving inventory the current naive strategies should be close enough to correct.

## License

Published under the MIT license.
