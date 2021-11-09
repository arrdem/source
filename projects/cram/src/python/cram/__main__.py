#!/usr/bin/env python3

from itertools import chain
import logging
import os
from pathlib import Path
import pickle
import re
import sys
from typing import NamedTuple

import click
from toposort import toposort_flatten
from vfs import Vfs


log = logging.getLogger(__name__)


def stow(fs: Vfs, src_dir: Path, dest_dir: Path, skip=[]):
    """Recursively 'stow' (link) the contents of the source into the destination."""

    dest_root = Path(dest_dir)
    src_root = Path(src_dir)
    skip = [src_root / n for n in skip]

    for src in src_root.glob("**/*"):
        if src in skip:
            continue

        dest = dest_root / src.relative_to(src_root)
        if src.is_dir():
            fs.mkdir(dest)
            fs.chmod(dest, src.stat().st_mode)

        elif src.is_file():
            fs.link(src, dest)


class PackageV0(NamedTuple):
    """The original package format from install.sh."""

    root: Path
    name: str
    subpackages: bool = False

    SPECIAL_FILES = ["BUILD", "PRE_INSTALL", "INSTALL", "POST_INSTALL", "REQUIRES"]

    def requires(self):
        """Get the dependencies of this package."""
        requiresf = self.root / "REQUIRES"
        requires = []

        # Listed dependencies
        if requiresf.exists():
            with open(requiresf) as fp:
                for l in fp:
                    l = l.strip()
                    l = re.sub(r"\s*#.*\n", "", l)
                    if l:
                        requires.append(l)

        # Implicitly depended subpackages
        if self.subpackages:
            for p in self.root.glob("*"):
                if p.is_dir():
                    requires.append(self.name + "/" + p.name)

        return requires

    def install(self, fs: Vfs, dest):
        """Install this package."""
        buildf = self.root / "BUILD"
        if buildf.exists():
            fs.exec(self.root, ["bash", str(buildf)])

        pref = self.root / "PRE_INSTALL"
        if pref.exists():
            fs.exec(self.root, ["bash", str(pref)])

        installf = self.root / "INSTALL"
        if installf.exists():
            fs.exec(self.root, ["bash", str(installf)])
        else:
            stow(fs, self.root, dest, self.SPECIAL_FILES)

        postf = self.root / "POST_INSTALL"
        if postf.exists():
            fs.exec(self.root, ["bash", str(postf)])


def load_config(root: Path) -> dict:
    """Load the configured packages."""

    packages = {
        str(p.relative_to(root)): PackageV0(p, str(p.relative_to(root)))
        for p in (root / "packages.d").glob("*")
    }

    # Add profiles, hosts which contain subpackages.
    for mp_root in chain((root / "profiles.d").glob("*"), (root / "hosts.d").glob("*")):

        # First find all subpackages
        for p in mp_root.glob(
            "*",
        ):
            if p.is_dir():
                packages[str(p.relative_to(root))] = PackageV0(
                    p, str(p.relative_to(root))
                )

        # Register the metapackages themselves
        packages[str(mp_root.relative_to(root))] = PackageV0(
            mp_root, str(mp_root.relative_to(root)), True
        )

    return packages


def build_fs(root: Path, dest: Path) -> Vfs:
    """Build a VFS by configuring dest from the given config root."""

    packages = load_config(root)

    hostname = os.uname()[1]

    # Compute the closure of packages to install
    requirements = [
        f"hosts.d/{hostname}",
        "profiles.d/default",
    ]

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


def load_fs(statefile: Path) -> Vfs:
    """Load a persisted VFS state from disk. Sort of."""

    oldfs = Vfs()

    if statefile.exists():
        log.debug("Loading statefile %s", statefile)
        with open(statefile, "rb") as fp:
            oldfs._log = pickle.load(fp)
    else:
        log.warning("No previous statefile %s", statefile)

    return oldfs


def simplify(old_fs: Vfs, new_fs: Vfs) -> Vfs:
    """Try to reduce a new VFS using diff from the original VFS."""

    old_fs = old_fs.copy()
    new_fs = new_fs.copy()

    # Scrub anything in the new log that's in the old log
    for txn in list(old_fs._log):
        # Except for execs which are stateful
        if txn[0] == "exec":
            continue

        new_fs._log.remove(txn)
        old_fs._log.remove(txn)

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
def cli():
    pass


@cli.command("apply")
@click.option("--execute/--dry-run", default=False)
@click.option("--optimize/--no-optimize", default=True)
@click.option("--state-file", default=".cram.log", type=Path)
@click.argument("confdir", type=Path)
@click.argument("destdir", type=Path)
def cmd_apply(confdir, destdir, state_file, execute, optimize):
    """The entry point of cram."""

    # Resolve the two input paths to absolutes
    root = confdir.resolve()
    dest = destdir.resolve()
    if not state_file.is_absolute():
        state_file = root / state_file

    new_fs = build_fs(root, dest)
    old_fs = load_fs(state_file)

    # Middleware processing of the resulting filesystem(s)
    executable_fs = scrub(old_fs, new_fs)
    if optimize:
        executable_fs = simplify(old_fs, new_fs)

    # Dump the new state.
    # Note that we dump the UNOPTIMIZED state, because we want to simplify relative complete states.
    if execute:
        executable_fs.execute()

        with open(state_file, "wb") as fp:
            pickle.dump(new_fs._log, fp)

    else:
        for e in executable_fs._log:
            print("-", *e)


@cli.command("show")
@click.option("--state-file", default=".cram.log", type=Path)
@click.argument("confdir", type=Path)
def cmd_show(confdir, state_file):
    """List out the last `apply` state in the <confdir>/.cram.log or --state-file."""
    root = confdir.resolve()

    if not state_file.is_absolute():
        state_file = root / state_file

    fs = load_fs(state_file)

    for e in fs._log:
        print(*e)


@cli.command("list")
@click.argument("confdir", type=Path)
def cmd_list(confdir):
    """List out packages, profiles, hosts and subpackages in the <confdir>."""
    packages = load_config(confdir)
    for pname in sorted(packages.keys()):
        p = packages[pname]
        print(f"{pname}:")
        for d in p.requires():
            print(f"- {d}")


if __name__ == "__main__" or 1:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    cli()
