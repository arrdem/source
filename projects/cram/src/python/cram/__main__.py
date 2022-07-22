"""Cram's entry point."""

from itertools import chain
import logging
import os
from pathlib import Path
import pickle
import sys
from typing import List

from . import (
    __author__,
    __copyright__,
    __license__,
    __version__,
)
from .v0 import PackageV0, ProfileV0
from .v1 import PackageV1, ProfileV1

import click
from toposort import toposort_flatten
from vfs import Vfs


log = logging.getLogger(__name__)


def load(root: Path, name: str, clss):
    for c in clss:
        i = c(root, name)
        if i.test():
            return i


def load_package(root, name):
    return load(root, name, [PackageV1, PackageV0])


def load_profile(root, name):
    return load(root, name, [ProfileV1, ProfileV0])

    
def load_packages(root: Path) -> dict:
    """Load the configured packages."""

    packages = {}
    for p in (root / "packages.d").glob("*"):
        name = str(p.relative_to(root))
        packages[name] = load_package(p, name)

    # Add profiles, hosts which contain subpackages.
    for mp_root in chain((root / "profiles.d").glob("*"), (root / "hosts.d").glob("*")):

        # First find all subpackages
        for p in mp_root.glob("*"):
            if p.is_dir():
                name = str(p.relative_to(root))
                packages[name] = load_package(p, name)

        # Register the metapackages themselves using the profile type
        mp_name = str(mp_root.relative_to(root))
        packages[mp_name] = load_profile(mp_root, mp_name)

    return packages


def build_fs(root: Path, dest: Path, prelude: List[str]) -> Vfs:
    """Build a VFS by configuring dest from the given config root."""

    packages = load_packages(root)
    requirements = []
    requirements.extend(prelude)

    for r in requirements:
        try:
            for d in packages[r].requires():
                if d not in requirements:
                    requirements.append(d)
        except KeyError:
            print(f"Error: Unable to load package {r}", file=sys.stderr)
            exit(1)

    # Compute the topsort graph
    requirements = {r: packages[r].requires() for r in requirements}
    fs = Vfs()

    # Abstractly execute the current packages
    for r in toposort_flatten(requirements):
        r = packages[r]
        r.install(fs, dest)

    return fs


def load_state(statefile: Path) -> Vfs:
    """Load a persisted VFS state from disk. Sort of."""

    oldfs = Vfs()

    if statefile.exists():
        log.debug("Loading statefile %s", statefile)
        with open(statefile, "rb") as fp:
            oldfs._log = pickle.load(fp)
    else:
        log.warning("No previous statefile %s", statefile)

    return oldfs


def simplify(old_fs: Vfs, new_fs: Vfs, /, exec_idempotent=True) -> Vfs:
    """Try to reduce a new VFS using diff from the original VFS."""

    old_fs = old_fs.copy()
    new_fs = new_fs.copy()

    # Scrub anything in the new log that's in the old log
    for txn in list(old_fs._log):
        # Except for execs which are stateful
        if txn[0] == "exec" and not exec_idempotent:
            continue

        try:
            new_fs._log.remove(txn)
        except ValueError:
            pass

    # Dedupe the new log while preserving order
    distinct = set()
    for txn, idx in zip(new_fs._log, range(len(new_fs._log))):
        if txn in distinct:
            new_fs._log.pop(idx)
        else:
            distinct.add(txn)

    return new_fs


def scrub(old_fs: Vfs, new_fs: Vfs) -> Vfs:
    """Try to eliminate files which were previously installed but are no longer used."""

    old_fs = old_fs.copy()
    new_fs = new_fs.copy()

    # Look for files in the old log which are no longer present in the new log
    for txn in old_fs._log:
        if txn[0] == "link" and txn not in new_fs._log:
            new_fs.unlink(txn[2])

        elif txn[0] == "mkdir" and txn not in new_fs._log:
            new_fs.unlink(txn[1])

    return new_fs


@click.group()
@click.version_option(version=1, message=f"""Cram {__version__}

Documentation
  https://github.com/arrdem/source/tree/trunk/projects/cram/

Features
 - 0.0.0 legacy config format
 - 0.1.0 TOML config format
 - 0.1.0 log based optimizer
 - 0.1.0 idempotent default for scripts

About
  {__copyright__}, {__author__}.
  Published under the terms of the {__license__} license.
""")
def cli():
    pass


@cli.command("apply")
@click.option("--execute/--dry-run", default=False)
@click.option("--state-file", default=".cram.log", type=Path)
@click.option("--optimize/--no-optimize", default=True)
@click.option("--require", type=str, multiple=True, default=[f"hosts.d/{os.uname()[1].split('.')[0]}", "profiles.d/default"])
@click.option("--exec-idempotent/--exec-always", "exec_idempotent", default=True)
@click.argument("confdir", type=Path)
@click.argument("destdir", type=Path)
def do_apply(confdir, destdir, state_file, execute, optimize, require, exec_idempotent):
    """The entry point of cram."""

    # Resolve the two input paths to absolutes
    root = confdir.resolve()
    dest = destdir.resolve()
    if not state_file.is_absolute():
        state_file = root / state_file

    new_fs = build_fs(root, dest, require)
    old_fs = load_state(state_file)

    # Middleware processing of the resulting filesystem(s)
    executable_fs = scrub(old_fs, new_fs)
    if optimize:
        executable_fs = simplify(old_fs, executable_fs,
                                 exec_idempotent=exec_idempotent)

    # Dump the new state.
    # Note that we dump the UNOPTIMIZED state, because we want to simplify relative complete states.
    def cb(e):
        print("-", *e)

    if execute:
        executable_fs.execute(callback=cb)

        with open(state_file, "wb") as fp:
            pickle.dump(new_fs._log, fp)

    else:
        for e in executable_fs._log:
            cb(e)


@cli.command("list")
@click.argument("confdir", type=Path)
@click.argument("list_packages", nargs=-1)
def do_list(confdir, list_packages):
    """List out packages, profiles, hosts and subpackages in the <confdir>."""
    packages = load_packages(confdir)

    if list_packages:
        dest = Path("~/")
        for pname in list_packages:
            fs = Vfs()
            p = packages[pname]
            p.install(fs, dest)
            print(f"{pname}: ({type(p).__name__})")
            print("requires:")
            for e in p.requires():
                print("  -", e)
            print("log:")
            for e in fs._log:
                print("  -", *e)

    else:
        for pname in sorted(packages.keys()):
            p = packages[pname]
            print(f"{pname}: ({type(p).__name__})")
            for d in p.requires():
                print(f"- {d}")


@cli.command("state")
@click.option("--state-file", default=".cram.log", type=Path)
@click.argument("confdir", type=Path)
def do_state(confdir, state_file):
    """List out the last `apply` state in the <confdir>/.cram.log or --state-file."""
    root = confdir.resolve()
    if not state_file.is_absolute():
        state_file = root / state_file
    fs = load_state(state_file)
    for e in fs._log:
        print(*e)


@cli.command("migrate-to-toml")
@click.argument("confdir", type=Path)
@click.argument("requirement", type=str)
def do_migrate(confdig, requirement):
    """Convert from the 0.0.0 config format to the 0.1.0 TOML format"""


if __name__ == "__main__" or 1:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    cli()
