"""The core Kook client library."""

from contextlib import contextmanager
from itertools import chain
import json
import sys
import time
from typing import (
    Any,
    Iterable,
    Optional,
    Tuple,
    Union,
)

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError
from kazoo.protocol.states import ZnodeStat
from kazoo.recipe.lock import (
    Lock,
    ReadLock,
    WriteLock,
)
from kook.config import current_config, KookConfig
from toolz.dicttoolz import (
    assoc as _assoc,
    dissoc as _dissoc,
    merge as _merge,
    update_in,
)


def assoc(m, k, v):
    return _assoc(m or {}, k, v)


def dissoc(m, k):
    if m:
        return _dissoc(m, k)
    else:
        return {}


def merge(a, b):
    return _merge(a or {}, b or {})


class Timer(object):
    """A context manager for counting elapsed time."""

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

    def elapsed(self):
        return self.interval


@contextmanager
def lock(l: Lock, other: Optional[Lock] = None, **kwargs):
    """A context manager for acquiring a non-reentrant lock if it isn't held."""

    if l and other:
        flag = not l.is_acquired and not other.is_acquired
    if l and not other:
        flag = not l.is_acquired
    if l is None:
        raise ValueError("A Lock instance is required!")

    if flag:
        l.acquire(**kwargs)
    yield
    if flag:
        l.release()


def cl(f, *args):
    """Curry-Last.

    Lets me stop writing lambda x: f(x, ....)
    """

    def _helper(*inner_args):
        return f(*[*inner_args, *args])

    return _helper


def conj(l: Optional[list], v: Any) -> list:
    """conj(oin) a value onto a list, returning a new list with the value appended."""

    l = l or []
    if v not in l:
        return [v, *l]
    return l


def disj(l: Optional[list], v: Any) -> list:
    """disj(oin) a value from a list, returning a list with the value removed."""

    l = l or []
    return [e for e in l if e != v]


def as_str(v: Union[bytes, str]) -> str:
    """Force to a str."""

    if isinstance(v, bytes):
        return v.decode("utf-8")
    elif isinstance(v, str):
        return v
    else:
        raise TypeError("Unable to str-coerce " + str(type(v)))


class KookBase(object):
    """Base class for Kook types."""

    def __init__(
        self, config: KookConfig, client: "KookClient", key: str, exists=False
    ):
        self.config = config
        self.key = key
        self.meta_lkey = key + "/" + config.meta_lock_suffix
        self.client = client
        self._cache = None
        self._valid = True

        if not exists:
            if not self.client.exists(self.meta_lkey):
                self.client.create(self.meta_lkey, makepath=True)

        # self.rl = self.client.create_rlock(self.meta_lkey)
        self.wl = self.client.create_lock(self.meta_lkey)

    def __enter__(self):
        self.wl.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self.wl.release()

    def fetch(self, watch=None) -> Tuple[Any, ZnodeStat]:
        """Read the current value, using only the read lock."""

        assert self._valid

        def hook(*args, **kwargs):
            self._cache = None
            if watch is not None:
                watch(*args, **kwargs)

        if not self._cache:
            # with lock(self.rl, other=self.wl):
            data, stat = self.client.get(self.key, watch=hook)
            data = json.loads(as_str(data) or "{}")
            self._cache = data, stat

        return self._cache

    def update(self, xform) -> ZnodeStat:
        """With the appropriate lock, update the underlying key with the transformer."""

        # We take the write lock so we go after all live reads.
        with lock(self.wl):
            data, stat = self.fetch()
            newval = xform(data)
            newdata = json.dumps(newval).encode("utf-8")
            self.client.set(self.key, newdata)
            return self.fetch()

    def vars(self, watch=None) -> dict:
        """Read the entity's vars, optionally setting a watch.

        Note that the watch will be called the first time ANYTHING
        changes, not just if the vars change. Clients wanting to watch for
        something in specific must re-enter the watch after it is invoked,
        as it will not be called twice.

        """

        attrs, stat = self.fetch(watch=watch)
        return attrs.get("vars", {})

    def set_var(self, k, v) -> ZnodeStat:
        """Set a k/v pair on the entity."""

        return self.update(cl(update_in, ["vars"], cl(assoc, k, v)))

    def del_var(self, k) -> ZnodeStat:
        """Clear a k/v pair on the entity."""

        return self.update(cl(update_in, ["vars"], cl(dissoc, k)))

    def groups(self, watch=None):
        """Read the entity's groups, optionally setting a watch.

        Note that the watch will be called the first time ANYTHING changes, not
        just if the groups change. Clients wanting to watch for something in
        specific must re-enter the watch after it is invoked, as it will not be
        called twice.

        """

        data, stat = self.fetch(watch=watch)
        p = self.config.group_prefix + "/"
        return [self.client.group(g.replace(p, "")) for g in data.get("groups", [])]

    def group_closure(self):
        """Compute the transitive closure of group membership."""

        groups = list(self.groups())
        for g in groups:
            if not g:
                print(f"Error - got nil group! {self}", file=sys.stderr)
                continue

            for _g in g.groups():
                if _g not in groups:
                    groups.append(_g)
        groups.reverse()
        return groups

    def inherited_vars(self):
        """Merge all vars from all parent groups.

        Record keys' sources in _meta, but do not throw on conflicts.

        """

        groups = self.group_closure()
        keys = {}
        _groups = []
        attrs = {"_meta": keys, "_groups": _groups}
        for group in groups:
            _groups.append(group.name)
            for k, v in group.vars().items():
                attrs[k] = v
                s = keys[k] = keys.get(k, [])
                if group.name not in s:
                    s.append(group.name)

        return attrs

    def canonicalized_vars(self, meta=True):
        """Merge host vars with inherited vars.

        Inherited vars are merged in no order whatsoever. Conflicts will produce
        thrown exceptions. However host vars win over inherited vars.

        """

        attrs = self.inherited_vars()
        vars = self.vars()
        _meta = {}
        for k, v in vars.items():
            attrs[k] = v
            l = _meta[k] = _meta.get(k, [])
            if "host" not in l:
                l.append("host")

        if meta:
            vars["_meta"] = _meta

        return attrs

    def add_group(self, group: Union["KookGroup", str]):
        """Add the entity to a group."""

        assert self._valid
        group = self.client.group(group)

        with lock(self.wl):
            with lock(group.wl):
                self.update(cl(update_in, ["groups"], cl(conj, group.key)))
                group.update(cl(update_in, ["members"], cl(conj, self.key)))

    def remove_group(self, group: Union["KookGroup", str]):
        """Remove the entity from a group."""

        assert self._valid
        group = self.client.group(group)

        with lock(self.wl):
            with lock(group.wl):
                self.update(cl(update_in, ["groups"], cl(disj, group.key)))
                group.update(cl(update_in, ["members"], cl(disj, self.key)))


class KookGroup(KookBase):
    """Representation of a group."""

    def __init__(
        self, config: KookConfig, client: "KookClient", group_name: str, exists=False
    ):
        assert "/" not in group_name or group_name.startswith(config.group_prefix)

        if not group_name.startswith(config.group_prefix):
            key = "/".join([config.group_prefix, group_name])
        else:
            key = group_name
            group_name = group_name.replace(config.group_prefix + "/", "")

        super().__init__(config, client, key, exists=exists)
        self.name = group_name

    def _hosts(self, watch=None):
        """Return a list of hosts who are directly members of this group."""

        data, stat = self.fetch(watch=watch)
        p = self.config.host_prefix + "/"
        res = []
        for m in data.get("members", []):
            if m.startswith(p):
                if host := self.client.host(m.replace(p, "")):
                    res.append(host)
                else:
                    raise RuntimeError(f"Unable to locate host {m} on group {self}")

        return res

    def hosts(self, watch=None):
        """Return a list of hosts who are directly members of this group."""

        # Compute the group closure
        groups = list(self.children())
        for g in groups:
            for _g in g.children():
                if _g not in groups:
                    groups.append(_g)

        # Compute the host list
        hosts = list(self._hosts())
        for g in groups:
            for h in g._hosts():
                if h not in hosts:
                    hosts.append(h)

        return hosts

    def host_vars(self, watch=None):
        """Get the per-host vars assigned by this group."""

        attrs, stat = self.fetch(watch=watch)
        return attrs.get("host_vars") or {}

    def set_host_var(self, host: Union["KookHost", str], key, value):
        host = self.client.host(host)
        self.update(cl(update_in, ["host_vars", host.name], cl(assoc, key, value)))

    def del_host_var(self, host: Union["KookHost", str], key):
        host = self.client.host(host)
        self.update(cl(update_in, ["host_vars", host.name], cl(dissoc, key)))

    def del_host_vars(self, host: Union["KookHost", str]):
        host = self.client.host(host)
        self.update(cl(update_in, ["host_vars"], cl(dissoc, host.name)))

    def children(self, watch=None):
        """Return a list of groups which are children of this group."""

        data, stat = self.fetch(watch=watch)
        p = self.config.group_prefix + "/"
        return [
            self.client.group(m.replace(p, ""))
            for m in data.get("members", [])
            if m.startswith(p)
        ]

    def delete(self):
        """ "Remove parent relations

        Note - prevents group deletion while processing group updates
        Interleaved writes on non-locked groups still OK.

        """

        # with lock(self.client.grl, other=self.client.gwl):
        for group in self.groups():
            self.remove_group(group)

            # Remove member relations
            for member in chain(self.hosts(), self.children()):
                member.remove_group(self)

        # With the write lock on the server list
        # FIXME (arrdem 2019-06-25):
        #   Do we actually need this?
        with lock(self.client.swl):
            self.client.delete(self.key, recursive=True)
        self._valid = False

    def __repr__(self):
        return "<{} {}>".format(__class__.__name__, self.key)


class KookHost(KookBase):
    """
    Representation of a physical device.
    """

    def __init__(self, config, client: "KookClient", host_name: str, exists=False):
        assert "/" not in host_name or host_name.startswith(config.host_prefix)

        if not host_name.startswith(config.host_prefix):
            key = "{}/{}".format(config.host_prefix, host_name)
        else:
            key = host_name
            host_name = host_name.replace(config.host_prefix + "/", "")

        super().__init__(config, client, key, exists=exists)
        self.name = host_name
        host_lock = self.key + "/" + config.lock_suffix
        if not exists and not self.client.exists(host_lock):
            self.client.create(host_lock, makepath=True)
        self.lock = client.create_lock(host_lock)

    def canonicalized_vars(self, meta=True):
        """Factors in group host_vars atop inheriting group vars."""

        _meta = {}
        groups = []
        vars = {"_groups": groups}

        for group in self.group_closure():
            groups.append(group.name)
            for k, v in group.vars().items():
                vars[k] = v
                l = _meta[k] = _meta.get(k, [])
                if group.name not in l:
                    l.append(group.name)

            for k, v in group.host_vars().get(self.name, {}).items():
                vars[k] = v
                l = _meta[k] = _meta.get(k, [])
                if group.name not in l:
                    l.append("host[{0}]".format(group.name))

        for k, v in self.vars().items():
            vars[k] = v
            l = _meta[k] = _meta.get(k, [])
            if "host" not in l:
                l.append("host")

        if meta:
            vars["_meta"] = _meta

        return vars

    @property
    def lock_path(self):
        return self.lock.create_path.rsplit("/", 1)[0]

    def is_locked(self):
        """Return True if the host is locked by any client."""

        # A Kazoo lock is a ZK "directory" of files, the lowest sequence
        # number of which currently holds the lock and the rest of which
        # are waiting/contending. Consequently there being children at the
        # lock's create path is enough to say the lock is held.
        return bool(self.client.get_children(self.lock_path))

    def delete(self):
        for group in self.groups():
            group.update(cl(update_in, ["host_vars"], cl(dissoc, self.name)))
            self.remove_group(group)

        self.client.delete(self.key, recursive=True)
        self._valid = False

    def remove_group(self, group: Union[KookGroup, str]):
        group = self.client.group(group)
        group.del_host_vars(self)
        super().remove_group(group)

    def __repr__(self):
        return "<{} {}>".format(__class__.__name__, self.key)


class LockProxy(object):
    """Shim which behaves enough like a Kazoo lock to let me toggle locking."""

    def __init__(self, lock, use_synchronization=True):
        self.__lock = lock
        self.__elapsed = 0
        self.__use_synchronization = use_synchronization

    def acquire(self, **kwargs):
        if self.__use_synchronization:
            try:
                with Timer() as t:
                    return self.__lock.acquire(**kwargs)
            finally:
                self.__elapsed += t.elapsed()

    def release(self, **kwargs):
        if self.__use_synchronization:
            try:
                with Timer() as t:
                    return self.__lock.release(**kwargs)
            finally:
                self.__elapsed += t.elapsed()
                self.__elapsed = 0

    @property
    def create_path(self):
        return self.__lock.create_path

    @property
    def is_acquired(self):
        if hasattr(self.__lock, "is_acquired"):
            return self.__lock.is_acquired
        elif isinstance(self.__lock, ReadLock):
            return super(ReadLock, self.__lock).is_acquired
        elif isinstance(self.__lock, WriteLock):
            return super(WriteLock, self.__lock).is_acquired


class KookClient(object):
    """Client to the Kook metadata store.

    Connects to a Zookeeper deployment - by default using the uri
    `zookeeper:2181` - and uses a `KookConfig` instance (or the default instance
    if none is provided) to begin fetching data out of the Kook data store.

    As a convenience to the implementation of Kook, the `KookClient` proxies a
    number of methods on the `KazooClient`. Consumers of the `KookClient` are
    encouraged not to rely on these methods.

    """

    def __init__(self, hosts=None, client=None, config=None, use_synchronization=True):
        self.config = config or current_config()
        self.client = client or KazooClient(hosts=hosts or self.config.hosts)
        self.client.start()
        self.use_synchronization = use_synchronization

        # The various read locks
        _slk = self.config.host_prefix + "/" + self.config.meta_lock_suffix
        if not self.client.exists(_slk):
            self.client.create(_slk, makepath=True)
        # self.srl = self.create_rlock(self.slk)
        self.swl = self.create_lock(_slk)

        _glk = self.config.group_prefix + "/" + self.config.meta_lock_suffix
        if not self.client.exists(_glk):
            self.client.create(_glk, makepath=True)
        # self.grl = self.create_rlock(self.glk)
        self.gwl = self.create_lock(_glk)

        self._groups = {}
        self._hosts = {}

    # Proxies to the Kazoo client
    ####################################################################
    def start(self):
        """Proxy to `KazooClient.start`."""

        return self.client.start()

    def stop(self):
        """Proxy to `KazooClient.stop`."""

        return self.client.stop()

    def restart(self):
        """Proxy to `KazooClient.restart`."""

        return self.client.restart()

    def get(self, k, *args, **kwargs):
        """Proxy to `KazooClient.get`."""

        return self.client.get(k, *args, **kwargs)

    def get_children(self, *args, **kwargs):
        """Proxy to `KazooClient.get_children`."""

        return self.client.get_children(*args, **kwargs)

    def set(self, *args, **kwargs):
        """Proxy to `KazooClient.set`."""

        return self.client.set(*args, **kwargs)

    def exists(self, *args, **kwargs):
        """Proxy to `KazooClient.exists`."""

        return self.client.exists(*args, **kwargs)

    def create(self, *args, **kwargs):
        """Proxy to `KazooClient.create`."""

        try:
            return self.client.create(*args, **kwargs)
        except NodeExistsError:
            pass

    def delete(self, *args, **kwargs):
        """Proxy to `KazooClient.delete`."""

        return self.client.delete(*args, **kwargs)

    def create_lock(self, *args, **kwargs):
        """Wrapper around the Lock recipe."""

        return LockProxy(
            Lock(self.client, *args, **kwargs),
            use_synchronization=self.use_synchronization,
        )

    def create_rlock(self, *args, **kwargs):
        """Wrapper around the ReadLock recipe."""

        return LockProxy(
            ReadLock(self.client, *args, **kwargs),
            use_synchronization=self.use_synchronization,
        )

    def create_wlock(self, *args, **kwargs):
        """Wrapper around the WriteLock recipe."""

        return LockProxy(
            WriteLock(self.client, *args, **kwargs),
            use_synchronization=self.use_synchronization,
        )

    # The intentional API
    ####################################################################
    def group(self, group, value=None) -> Optional[KookGroup]:
        """Attempt to fetch a single group record."""

        if isinstance(group, KookGroup):
            return group

        if value is not None:
            group = "{group}_{value}".format(**locals())

        g = self._groups.get(group)
        if g is None:
            _key = "{}/{}".format(self.config.group_prefix, group)
            if self.exists(_key):
                g = KookGroup(self.config, self, group, exists=True)

        if g and not g._valid:
            g = None

        if g:
            self._groups[group] = g

        if not g:
            print(f"Warning: unable to resolve group {g}", file=sys.stderr)

        return g

    def create_group(self, group, value=None, vars=None) -> KookGroup:
        """Fetch a group if it exists, otherwise cause one to be created."""

        vars = vars or {}

        if value is not None:
            vars = merge(vars, {group: value})
            group = "{group}_{value}".format(**locals())

        g = self._groups.get(group)
        if g is None:
            with lock(self.gwl):
                g = self._groups[group] = KookGroup(self.config, self, group)

            # Apply the definitional k/v, and any extras.
            g.update(cl(update_in, ["vars"], cl(merge, vars)))
        return g

    def groups(self, watch=None) -> Iterable[KookGroup]:
        """In no order, produce a list (eagerly!) of all the group records."""

        mpath = self.config.meta_suffix.split("/", 1)[0]
        return [
            self.group(groupname)
            for groupname in self.client.get_children(
                self.config.group_prefix, watch=watch
            )
            if groupname != mpath
        ]

    def delete_group(self, group: Union[KookGroup, str]):
        """Given a group instance or string naming one, delete the group."""

        self.group(group).delete()

    def host(self, host) -> Optional[KookHost]:
        """Attempt to fetch a single host by name."""

        if isinstance(host, KookHost):
            return host

        h = self._hosts.get(host)
        if h is None:
            _key = "{}/{}".format(self.config.host_prefix, host)
            if self.exists(_key):
                h = KookHost(self.config, self, host, exists=True)
            else:
                return None

            self._hosts[host] = h

        if h._valid is False:
            return None

        return h

    def create_host(self, host_name, vars=None) -> KookHost:
        """Fetch a host if it exists, otherwise cause one to be created."""

        vars = merge(vars or {}, {"host_name": host_name})
        h = self._hosts.get(host_name)
        if h is None:
            with lock(self.swl):
                h = self._hosts[host_name] = KookHost(self.config, self, host_name)

            # Apply any host vars
            h.update(cl(update_in, ["vars"], cl(merge, vars)))
        return h

    def delete_host(self, host: Union[KookHost, str]):
        """Given a host instance or a string naming one, delete the host."""

        self.host(host).delete()

    def hosts(self, watch=None) -> Iterable[KookHost]:
        """In no order, produce a list (eagerly!) of all the host records."""

        mpath = self.config.meta_suffix.split("/", 1)[0]
        return [
            self.host(host_name)
            for host_name in self.client.get_children(
                self.config.host_prefix, watch=watch
            )
            if host_name != mpath
        ]
