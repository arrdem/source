"""
Quick and shitty Gandi REST API driver
"""

from datetime import datetime
import json

import requests


class GandiAPI(object):
    """An extremely incomplete Gandi REST API driver class.

    Exists to close over your API key, and make talking to the API slightly more idiomatic.

    Note: In an effort to be nice, this API maintains a cache of the zones visible with your API
    key. The cache is maintained when using this driver, but concurrent modifications of your zone(s)
    via the web UI or other processes will obviously undermine it. This cache can be disabled by
    setting the `use_cache` kwarg to `False`.

    """

    def __init__(self, key=None, use_cache=True):
        self._base = "https://dns.api.gandi.net/api/v5"
        self._key = key
        self._use_cache = use_cache
        self._zones = None

    # Helpers for making requests with the API key as required by the API.

    def _do_request(self, method, path, headers=None, **kwargs):
        headers = headers or {}
        headers["X-Api-Key"] = self._key
        resp = method(self._base + path, headers=headers, **kwargs)
        if resp.status_code > 299:
            print(resp.text)
            resp.raise_for_status()

        return resp

    def _get(self, path, **kwargs):
        return self._do_request(requests.get, path, **kwargs)

    def _post(self, path, **kwargs):
        return self._do_request(requests.post, path, **kwargs)

    def _put(self, path, **kwargs):
        return self._do_request(requests.put, path, **kwargs)

    # Intentional public API

    def domain_records(self, domain):
        return self._get("/domains/{0}/records".format(domain)).json()

    def get_zones(self):
        if self._use_cache:
            if not self._zones:
                self._zones = self._get("/zones").json()
            return self._zones
        else:
            return self._get("/zones").json()

    def get_zone(self, zone_id):
        return self._get("/zones/{}".format(zone_id)).json()

    def get_zone_by_name(self, zone_name):
        for zone in self.get_zones():
            if zone["name"] == zone_name:
                return zone

    def create_zone(self, zone_name):
        new_zone_id = (
            self._post(
                "/zones",
                headers={"content-type": "application/json"},
                data=json.dumps({"name": zone_name}),
            )
            .headers["Location"]
            .split("/")[-1]
        )
        new_zone = self.get_zone(new_zone_id)

        # Note: If the cache is active, update the cache.
        if self._use_cache and self._zones is not None:
            self._zones.append(new_zone)

        return new_zone

    def replace_domain(self, domain, records):
        date = datetime.now()
        date = "{:%A, %d. %B %Y %I:%M%p}".format(date)
        zone_name = f"updater generated domain - {domain} - {date}"

        zone = self.get_zone_by_name(zone_name)
        if not zone:
            zone = self.create_zone(zone_name)

        print("Using zone", zone["uuid"])

        for r in records:
            self._post(
                "/zones/{0}/records".format(zone["uuid"]),
                headers={"content-type": "application/json"},
                data=json.dumps(r),
            )

        return self._post(
            "/zones/{0}/domains/{1}".format(zone["uuid"], domain),
            headers={"content-type": "application/json"},
        )
