#!/usr/bin/env python3

"""ReqMan; the Requirements Manager.

Reqman is a quick and dirty tool that knows about Bazel, rules_python and requirements.txt files. It
exists to extend the upstream (and very good) pip-tools / pip-compile task with some helpers
providing better ergonomics for manipulating a monorepo.

Usage:
  reqman deps
    Print out a summary of all available dependencies.

  reqman install <requirement>
    Install a new (pinned) dependency (and any transitives) into the locked requirements.txt

  reqman install --upgrade <requirement>
    Upgrade a given (pinned) dependency (and any transitives)

  reqman lint
    Check for now-unused dependencies

  reqman clean
    Rewrite the requirements to emove unused dependencies

"""

import re
import subprocess

import click


REQ_PATTERN = re.compile(
    r"(?P<pkgname>[a-zA-Z0-9_-]+)(?P<features>\[.*?\])?(?P<specifiers>((==|>=?|<=?|~=|!=)(?P<version>[^\s;#]+),)+)?|(.*?#egg=(?P<eggname>[a-zA-Z0-9_-]+))"
)


SHITLIST = [
    "pip",
    "pkg-resources",
    "setuptools",
]

def req_name(requirement: str) -> str:
    requirement = requirement.lower()
    match = re.match(REQ_PATTERN, requirement)
    return match.group("pkgname") or match.group("eggname")


def sort_key(requirement: str) -> str:
    return (
        req_name(requirement)  # Get the match group
        .lower()           # We ignore case
        .replace("-", "")  # We ignore -
        .replace("_", "")  # And _
    )


def _bq(query):
    """Enumerate the PyPi package names from a Bazel query."""

    unused = subprocess.check_output(["bazel", "query", query, "--output=package"]).decode("utf-8")
    for l in unused.split("\n"):
        if l:
            yield l.replace("@arrdem_source_pypi//pypi__", "")


def _unused():
    """Find unused requirements."""

    return set(_bq("@arrdem_source_pypi//...")) - set(_bq("filter('//pypi__', deps(//...))"))


def _load(fname):
    """Slurp requirements from a file."""

    with open(fname, "r") as reqfile:
        # FIXME (arrdem 2021-08-03):
        #   Return a parse, not just lines.
        return list(l.strip() for l in reqfile)


def _write(fname, reqs):
    """Dump requirements back to a file in sorted format."""

    reqs = sorted(reqs, key=sort_key)
    with open(fname, "w") as f:
        for r in reqs:
            f.write(f"{r}\n")


@click.group()
def cli():
    pass


@cli.command()
@click.argument("requirements")
def deps(requirements):
    """Enumerate the installed dependencies."""

    for r in _load(requirements):
        print(f"- {r}")


@cli.command()
@click.option("--no-upgrade/--upgrade", "", "upgrade", default=False)
@click.argument("requirements")
def install(requirements, upgrade):
    """Install (or upgrade) a dependency.

    This is somewhat tricky because we need to come up with, format and persist a new dependency
    solution. We aren't just doing formatting here.

    """




@cli.command()
@click.option("--shout/--quiet", "-q/-S", default=True)
@click.argument("requirements")
def lint(shout, requirements):
    """Check for unused dependencies."""

    unused = list(_unused())
    if shout:
        if unused:
            print("Unused deps:")
        for d in unused:
            print(f" - {d}")

    if unused:
        exit(1)

    reqs = _load(requirements)
    if reqs != sorted(reqs, key=sort_key):
        exit(1)


@cli.command()
@click.argument("requirements")
def clean(requirements):
    """Expunge unused dependencies."""

    unused = set(_unused())
    reqs = _load(requirements)
    usedreqs = [r for r in reqs if sort_key(r) not in unused]
    _write(requirements, usedreqs)
    if usedreqs != reqs:
        exit(1)


@cli.command()
@click.argument("requirements")
def sort(requirements):
    """Just format the requirements file."""

    reqs = _load(requirements)
    sortedreqs = sorted(reqs, key=sort_key)
    _write(requirements, sortedreqs)
    if reqs != sortedreqs:
        exit(1)


if __name__ == "__main__":
    cli()
