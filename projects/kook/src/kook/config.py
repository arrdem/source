"""Configuration for the Kook client."""

import os

import yaml


class KookConfig(object):
    """A config type used to control the keys Kook uses."""

    def __init__(
        self,
        hosts="zookeeper:2181",
        host_prefix="/kook/host",
        host_schema=None,
        host_ttl=None,
        group_prefix="/kook/group",
        lock_suffix="lock",
        meta_suffix="meta",
    ):

        if isinstance(hosts, list):
            hosts = ",".join(hosts)

        self.hosts = hosts
        self.host_prefix = host_prefix
        self.host_schema = host_schema
        self.host_ttl = host_ttl

        self.group_prefix = group_prefix

        assert not lock_suffix.startswith("/")
        self.lock_suffix = lock_suffix

        assert not meta_suffix.startswith("/")
        self.meta_suffix = meta_suffix

        self.meta_lock_suffix = meta_suffix + "/" + lock_suffix


def current_config(path="/etc/kook.yml") -> KookConfig:
    """Either the default config, or a config drawn from /etc/kook.yml"""

    path = os.getenv("KOOK_CONFIG", path)

    return KookConfig(**(yaml.safe_load(open(path)) if os.path.exists(path) else {}))
