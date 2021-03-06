"""
A quick and dirty public DNS script, super tightly coupled to my infrastructure.
"""

import argparse
import os
from pprint import pprint
import re

from gandi.client import GandiAPI
import jinja2
import meraki
import yaml


RECORD_LINE_PATTERN = re.compile(
    r"^(?P<rrset_name>\S+)\s+"
    r"(?P<rrset_ttl>\S+)\s+"
    r"IN\s+"
    r"(?P<rrset_type>\S+)\s+"
    r"(?P<rrset_values>.+)$"
)


def update(m, k, f, *args, **kwargs):
    """clojure.core/update for Python's stateful maps."""

    if k in m:
        m[k] = f(m[k], *args, **kwargs)

    return m


def parse_zone_record(line):
    if match := RECORD_LINE_PATTERN.search(line):
        dat = match.groupdict()
        dat = update(dat, "rrset_ttl", int)
        dat = update(dat, "rrset_values", lambda x: [x])
        return dat


def same_record(lr, rr):
    """
    A test to see if two records name the same zone entry.
    """

    return lr["rrset_name"] == rr["rrset_name"] and lr["rrset_type"] == rr["rrset_type"]


def records_equate(lr, rr):
    """
    Equality, ignoring rrset_href which is generated by the API.
    """

    if not same_record(lr, rr):
        return False
    elif lr["rrset_ttl"] != rr["rrset_ttl"]:
        return False
    elif set(lr["rrset_values"]) != set(rr["rrset_values"]):
        return False
    else:
        return True


def template_and_parse_zone(template_file, template_bindings):
    assert template_file is not None
    assert template_bindings is not None

    with open(template_file) as fp:
        dat = jinja2.Template(fp.read()).render(**template_bindings)

    uncommitted_records = []
    for line in dat.splitlines():
        if line and not line[0] == "#":
            record = parse_zone_record(line)
            if record:
                uncommitted_records.append(record)

    records = []

    for uncommitted_r in uncommitted_records:
        flag = False
        for committed_r in records:
            if same_record(uncommitted_r, committed_r):
                # Join the two records
                committed_r["rrset_values"].extend(uncommitted_r["rrset_values"])
                flag = True

        if not flag:
            records.append(uncommitted_r)

    sorted(records, key=lambda x: (x["rrset_type"], x["rrset_name"]))

    return records


def diff_zones(left_zone, right_zone):
    """
    Equality between unordered lists of records constituting a zone.
    """

    in_left_not_right = []
    for lr in left_zone:
        flag = False
        for rr in right_zone:
            if same_record(lr, rr) and records_equate(lr, rr):
                flag = True
                break

        if not flag:
            in_left_not_right.append(lr)

    in_right_not_left = []
    for rr in right_zone:
        flag = False
        for lr in left_zone:
            if same_record(lr, rr) and records_equate(lr, rr):
                flag = True
                break

        if not flag:
            in_right_not_left.append(lr)

    return in_left_not_right or in_right_not_left


parser = argparse.ArgumentParser(
    description='"Dynamic" DNS updating for self-hosted services'
)
parser.add_argument("--config", dest="config_file", required=True)
parser.add_argument("--templates", dest="template_dir", required=True)
parser.add_argument("--dry-run", dest="dry", action="store_true", default=False)


def main():
    args = parser.parse_args()

    with open(args.config_file, "r") as fp:
        config = yaml.safe_load(fp)

    dashboard = meraki.DashboardAPI(config["meraki"]["key"], output_log=False)
    org = config["meraki"]["organization"]
    device = config["meraki"]["router_serial"]

    uplinks = dashboard.appliance.getOrganizationApplianceUplinkStatuses(
        organizationId=org, serials=[device]
    )[0]["uplinks"]

    template_bindings = {
        "local": {
            # One of the two
            "public_v4s": [
                link.get("publicIp") for link in uplinks if link.get("publicIp")
            ],
        },
        # Why isn't there a merge method
        **config["bindings"],
    }

    api = GandiAPI(config["gandi"]["key"])

    for task in config["tasks"]:
        if isinstance(task, str):
            task = {"template": task + ".j2", "zones": [task]}

        computed_zone = template_and_parse_zone(
            os.path.join(args.template_dir, task["template"]), template_bindings
        )

        for zone_name in task["zones"] or []:
            try:
                live_zone = api.domain_records(zone_name)

                if diff_zones(computed_zone, live_zone):
                    print("Zone {} differs, computed zone:".format(zone_name))
                    pprint(computed_zone)
                    if not args.dry:
                        print(api.replace_domain(zone_name, computed_zone))
                else:
                    print("Zone {} up to date".format(zone_name))

            except Exception as e:
                print("While processing zone {}".format(zone_name))
                raise e


if __name__ == "__main__" or 1:
    main()
