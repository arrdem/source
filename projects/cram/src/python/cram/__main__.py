#!/usr/bin/env python3

import argparse
from itertools import chain
import os
from pathlib import Path
from subprocess import run
import sys
from typing import NamedTuple

from toposort import toposort_flatten


parser = argparse.ArgumentParser()
parser.add_argument("-x", "--execute", dest="execute", action="store_true", default=False)
parser.add_argument("-d", "--dry-run", dest="execute", action="store_false")
parser.add_argument("confdir", default="~/conf", type=Path)
parser.add_argument("destdir", default="~/", type=Path)


class Fs(object):
    """An abstract filesystem device which can accumulate changes, and apply them in a batch."""

    def __init__(self):
        self._log = []

    def execute(self, execute=False):
        for e in self._log:
            print(e)

            if not execute:
                continue

            elif e[0] == "exec":
                _, dir, cmd = e
                run(cmd, cwd=str(dir))

            elif e[0] == "link":
                _, src, dest = e
                if dest.exists() and dest.is_symlink() and dest.readlink() == dest:
                    continue
                else:
                    if dest.exists():
                        dest.unlink()
                    dest.symlink_to(src)

            elif e[0] == "copy":
                raise NotImplementedError()

            elif e[0] == "chmod":
                _, dest, mode = e
                dest.chmod(mode)

            elif e[0] == "mkdir":
                _, dest = e
                dest.mkdir(exist_ok=True)


    def _append(self, msg):
        self._log.append(msg)

    def link(self, src, dest):
        self._append(("link", src, dest))

    def copy(self, src, dest):
        self._append(("copy", src, dest))

    def chmod(self, dest, mode):
        self._append(("chmod", dest, mode))

    def mkdir(self, dest):
        self._append(("mkdir", dest))

    def exec(self, dest, cmd):
        self._append(("exec", dest, cmd))


def stow(fs: Fs, src_dir: Path, dest_dir: Path, skip=[]):
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

    SPECIAL_FILES = ["BUILD", "INSTALL", "POST_INSTALL", "requires"]

    def requires(self):
        """Get the dependencies of this package."""
        requiresf = self.root / "requires"
        if requiresf.exists():
            with open(requiresf) as fp:
                return [l.strip() for l in fp]
        return []

    def install(self, fs, dest):
        """Install this package."""
        buildf = self.root / "BUILD"
        if buildf.exists():
            fs.exec(self.root, ["bash", str(buildf)])

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
    fs = Fs()

    for r in toposort_flatten(requirements):
        r = packages[r]
        r.install(fs, opts.destdir)

    fs.execute(opts.execute)


if __name__ == "__main__" or 1:
    main()
