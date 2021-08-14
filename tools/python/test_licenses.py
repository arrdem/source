"""
Validate 3rdparty library licenses as approved.
"""

import re

import pytest
import requests
import requirements
from requirements.requirement import Requirement


# Licenses approved as representing non-copyleft and not precluding commercial usage.
# This is all easy, there's a good schema here.
APPROVED_LICENSES = [
    MIT    := "License :: OSI Approved :: MIT License",
    APACHE := "License :: OSI Approved :: Apache Software License",
    BSD    := "License :: OSI Approved :: BSD License",
    MPL10  := "License :: OSI Approved :: Mozilla Public License 1.0 (MPL)",
    MPL11  := "License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)",
    MPL20  := "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    PSFL   := "License :: OSI Approved :: Python Software Foundation License",
    LGPL   := "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    LGPL3  := "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
    ISCL   := "License :: OSI Approved :: ISC License (ISCL)",
]

UNAPPROVED_LICENSES = [
    GPL1 := "License :: OSI Approved :: GNU General Public License",
    GPL2 := "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    GPL3 := "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
]

# This data is GARBO.
LICENSES_BY_LOWERNAME = {
    "apache 2.0": APACHE,
    "apache": APACHE,
    "http://www.apache.org/licenses/license-2.0": APACHE,

    "bsd 3": BSD,
    "bsd": BSD,

    "gpl": GPL1,
    "gpl2": GPL2,
    "gpl3": GPL3,
    "lgpl": LGPL,
    "lgpl3": LGPL3,

    "isc": ISCL,

    "mit": MIT,

    "mpl": MPL10,
    "mpl 2.0": MPL20,

    "psf": PSFL,
}

# Mash in some cases.
LICENSES_BY_LOWERNAME.update(
    {l.split(" :: ")[-1].lower(): l for l in APPROVED_LICENSES}
)

# As a workaround for packages which don"t have correct meadata on PyPi, hand-verified packages
APPROVED_PACKAGES = [
    "yamllint",  # WARNING: YAMLLINT IS GLP3"d.
    "Flask_Log_Request_ID",  # MIT, currently depended on as a git dep.
    "anosql",  # BSD
]


with open("tools/python/requirements.txt") as fd:
    PACKAGES = list(requirements.parse(fd))


def bash_license(ln):
    while True:
        lnn = re.sub(r"[(),]|( version)|( license)|( ?v(?=\d))|([ -]clause)", "", ln.lower())
        if ln != lnn:
            ln = lnn
        else:
            break

    ln = LICENSES_BY_LOWERNAME.get(ln, ln)
    return ln


@pytest.mark.parametrize("a,b", [
    ("MIT", MIT),
    ("mit", MIT),
    ("BSD", BSD),
    ("BSD 3-clause", BSD),
    ("BSD 3 clause", BSD),
    ("GPL3", GPL3),
    ("GPL v3", GPL3),
    ("GPLv3", GPL3),
])
def test_bash_license(a, b):
    assert bash_license(a) == b


def licenses(package: Requirement):
    """Get package metadata (the licenses list) from PyPi.

    pip and other tools use the local package metadata to introspect licenses which requires that
    packages be installed. Going to PyPi isn't strictly reproducible both because the PyPi database
    could be updated and we could see network failures but there really isn't a good way to solve
    this problem.

    """
    l = []
    version = next((v for op, v in package.specs if op == "=="), None)
    print(package.name, version)

    # If we don't have a version (eg. forked git dep) assume we've got the same license constraints
    # as the latest upstream release. After all we can't re-license stuff.
    if not version:
        blob = requests.get(
            f"https://pypi.org/pypi/{package.name}/json",
            headers={"Accept": "application/json"}
        ).json()
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
            f"https://pypi.org/pypi/{package.name}/{version}/json",
            headers={"Accept": "application/json"}
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


@pytest.mark.parametrize("package", PACKAGES)
def test_approved_license(package):
    """Ensure that a given package is either allowed by name or uses an approved license."""

    _licenses = licenses(package)
    assert package.name in APPROVED_PACKAGES or any(
        l in APPROVED_LICENSES for l in _licenses
    ), f"{package} was not approved and its license(s) were unknown {_licenses!r}"
