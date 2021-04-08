"""
Validate 3rdparty library licenses as approved.
"""

import re

import pytest
import requests

# Licenses approved as representing non-copyleft and not precluding commercial usage.
# This is all easy, there's a good schema here.
APPROVED_LICENSES = [
    "License :: OSI Approved :: MIT License",
    "License :: OSI Approved :: Apache Software License",
    "License :: OSI Approved :: BSD License",
    "License :: OSI Approved :: Mozilla Public License 1.0 (MPL)",
    "License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    "License :: OSI Approved :: Python Software Foundation License",
    "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    "License :: OSI Approved :: ISC License (ISCL)",
]

# This data is GARBO.
LICENSES_BY_LOWERNAME = {
    "apache 2.0": "License :: OSI Approved :: Apache Software License",
    "apache": "License :: OSI Approved :: Apache Software License",
    "bsd 3 clause": "License :: OSI Approved :: BSD License",
    "bsd": "License :: OSI Approved :: BSD License",
    "gplv3": "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "http://www.apache.org/licenses/license-2.0": "License :: OSI Approved :: Apache Software License",
    "isc": "License :: OSI Approved :: ISC License (ISCL)",
    "mit": "License :: OSI Approved :: MIT License",
    "mpl 2.0": "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    "mpl": "License :: OSI Approved :: Mozilla Public License 1.0 (MPL)",
    "psf": "License :: OSI Approved :: Python Software Foundation License",
}

# Mash in some cases.
LICENSES_BY_LOWERNAME.update(
    {l.split(" :: ")[-1].lower(): l for l in APPROVED_LICENSES}
)

# As a workaround for packages which don"t have correct meadata on PyPi, hand-verified packages
APPROVED_PACKAGES = [
    "yamllint",  # WARNING: YAMLLINT IS GLP3"d.
    "Flask_Log_Request_ID",  # MIT, currently depended on as a git dep.
]

REQ_PATTERN = re.compile(
    r"(?P<pkgname>[a-zA-Z0-9_-]+)(?P<features>\[.*?\])?==(?P<version>[^\s;#]+)|(.*?#egg=(?P<eggname>[a-zA-Z0-9_-]+))"
)


def parse_requirement(line):
    """Given a requirement return the requirement name and version as a tuple.

    Only the strict `==` version pinning subset is supported.
    Features are supported.
    """

    if m := re.match(REQ_PATTERN, line):
        return (m.group("pkgname") or m.group("eggname")), m.group("version")


@pytest.mark.parametrize(
    "line,t",
    [
        ("foo==1.2.3", ("foo", "1.2.3")),
        ("foo[bar]==1.2.3", ("foo", "1.2.3")),
        ("foo[bar, baz, qux]==1.2.3", ("foo", "1.2.3")),
        # Various stuff we should ignore
        ("# comment line", None),
        ("    # garbage whitespace", None),
        ("     \t", None),
    ],
)
def test_parse_requirement(line, t):
    """The irony of testing one"s tests is not lost."""

    assert parse_requirement(line) == t


with open("tools/python/requirements.txt") as f:
    PACKAGES = [parse_requirement(l) for l in f.readlines()]


def bash_license(ln):
    if ln:
        ln = re.sub("[(),]|( version)|( license)", "", ln.lower())
        ln = LICENSES_BY_LOWERNAME.get(ln, ln)
    return ln


def licenses(package, version):
    """Get package metadata (the licenses list) from PyPi.

    pip and other tools use the local package metadata to introspect licenses which requires that
    packages be installed. Going to PyPi isn't strictly reproducible both because the PyPi database
    could be updated and we could see network failures but there really isn't a good way to solve
    this problem.

    """
    l = []

    # If we don't have a version (eg. forked git dep) assume we've got the same license constraints
    # as the latest upstream release. After all we can't re-license stuff.
    if not version:
        blob = requests.get(f"https://pypi.python.org/pypi/{package}/json").json()
        if ln := bash_license(blob.get("license")):
            l.append(ln)
        else:
            try:
                version = list(blob.get("releases", {}).keys())[-1]
            except IndexError:
                pass

    # If we have a version, try to pull that release's metadata since it may have more/better.
    if version:
        blob = requests.get(
            f"https://pypi.python.org/pypi/{package}/{version}/json"
        ).json()
        l = [
            c
            for c in blob.get("info", {}).get("classifiers", [])
            if c.startswith("License")
        ]
        ln = blob.get("info", {}).get("license")
        if ln and not l:
            l.append(bash_license(ln))

    return l


@pytest.mark.parametrize("package,version", PACKAGES)
def test_approved_license(package, version):
    """Ensure that a given package is either allowed by name or uses an approved license."""

    _licenses = licenses(package, version)
    assert package in APPROVED_PACKAGES or any(
        l in APPROVED_LICENSES for l in _licenses
    ), f"{package} was not approved and its license(s) were unknown {_licenses!r}"
