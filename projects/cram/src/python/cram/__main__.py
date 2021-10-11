#!/usr/bin/env python3

import argparse
from itertools import chain
import logging
import os
from pathlib import Path
import sys
from typing import NamedTuple

from toposort import toposort_flatten
from vfs import Vfs

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-x", "--execute", dest="execute", action="store_true", default=False)
parser.add_argument("-d", "--dry-run", dest="execute", action="store_false")
parser.add_argument("confdir", type=Path)
parser.add_argument("destdir", type=Path)


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

    SPECIAL_FILES = ["BUILD", "PRE_INSTALL", "INSTALL", "POST_INSTALL", "REQUIRES"]

    def requires(self):
        """Get the dependencies of this package."""
        requiresf = self.root / "REQUIRES"
        if requiresf.exists():
            with open(requiresf) as fp:
                return [l.strip() for l in fp]
        return []

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


def main():
    """The entry point of cram."""

    opts, args = parser.parse_known_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    root = opts.confdir

    packages = {str(p.relative_to(root)): PackageV0(p, str(p))
                for p in chain((root / "packages.d").glob("*"),
                               (root / "profiles.d").glob("*"),
                               (root / "hosts.d").glob("*"))}

    hostname = os.uname()[1]

    # Compute the closure of packages to install
    requirements = [f"hosts.d/{hostname}"]

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

    for r in toposort_flatten(requirements):
        r = packages[r]
        r.install(fs, opts.destdir)

    fs.execute(opts.execute)


if __name__ == "__main__" or 1:
    main()
