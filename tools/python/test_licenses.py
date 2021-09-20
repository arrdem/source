"""
Validate 3rdparty library licenses as approved.
"""

import re

from pkg_resources import (
    DistInfoDistribution,
    working_set,
)
import pytest


# Licenses approved as representing non-copyleft and not precluding commercial usage.
# This is all easy, there's a good schema here.
APPROVED_LICENSES = [
    MIT := "License :: OSI Approved :: MIT License",
    APACHE := "License :: OSI Approved :: Apache Software License",
    BSD := "License :: OSI Approved :: BSD License",
    MPL10 := "License :: OSI Approved :: Mozilla Public License 1.0 (MPL)",
    MPL11 := "License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)",
    MPL20 := "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    PSFL := "License :: OSI Approved :: Python Software Foundation License",
    LGPL := "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    LGPL3 := "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
    ISCL := "License :: OSI Approved :: ISC License (ISCL)",
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
    {lic.split(" :: ")[-1].lower(): lic for lic in APPROVED_LICENSES}
)

# As a workaround for packages which don"t have correct meadata on PyPi, hand-verified packages
APPROVED_PACKAGES = [
    "yamllint",  # WARNING: YAMLLINT IS GLP3"d.
    "Flask_Log_Request_ID",  # MIT, currently depended on as a git dep.
    "anosql",  # BSD
]


def bash_license(ln):
    while True:
        lnn = re.sub(
            r"[(),]|( version)|( license)|( ?v(?=\d))|([ -]clause)|(or later)", "", ln.lower()
        )
        if ln != lnn:
            ln = lnn
        else:
            break

    ln = LICENSES_BY_LOWERNAME.get(ln, ln)
    return ln


@pytest.mark.parametrize(
    "a,b",
    [
        ("MIT", MIT),
        ("mit", MIT),
        ("BSD", BSD),
        ("BSD 3-clause", BSD),
        ("BSD 3 clause", BSD),
        ("GPL3", GPL3),
        ("GPL v3", GPL3),
        ("GPLv3", GPL3),
    ],
)
def test_bash_license(a, b):
    assert bash_license(a) == b


def licenses(dist: DistInfoDistribution):
    """Get dist metadata (the licenses list) from PyPi.

    pip and other tools use the local dist metadata to introspect licenses which requires that
    packages be installed. Going to PyPi isn't strictly reproducible both because the PyPi database
    could be updated and we could see network failures but there really isn't a good way to solve
    this problem.

    """

    lics = []
    name = dist.project_name
    version = dist.version
    print(name, version, type(dist))

    meta = dist.get_metadata(dist.PKG_INFO).split("\n")
    classifiers = [l.replace("Classifier: ", "", 1) for l in meta if l.startswith("Classifier: ")]
    license = bash_license(next((l for l in meta if l.startswith("License:")), "License: UNKNOWN").replace("License: ", "", 1))
    lics.extend(l for l in classifiers if l.startswith("License ::"))

    if not lics:
        lics.append(license)

    return lics


@pytest.mark.parametrize("dist", (w for w in working_set if w.location.find("arrdem_source_pypi") != -1), ids=lambda dist: dist.project_name)
def test_approved_license(dist: DistInfoDistribution):
    """Ensure that a given package is either allowed by name or uses an approved license."""

    _licenses = licenses(dist)
    print(dist.location)
    assert dist.project_name in APPROVED_PACKAGES or any(
        lic in APPROVED_LICENSES for lic in _licenses
    ), f"{dist.project_name} ({dist.location}) was not approved and its license(s) were unknown {_licenses!r}"
