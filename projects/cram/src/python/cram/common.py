#!/usr/bin/env python3

from abc import abstractmethod
from pathlib import Path
from shlex import quote as sh_quote
from typing import List, Optional

from vfs import Vfs


SHELL = "/bin/sh"

def sh(cmd: List[str], /,
       env: Optional[dict] = None):

    prefix = []
    if env:
        prefix.append("/usr/bin/env")
        for k, v in env.items():
            v = sh_quote(str(v))
            prefix.append(f"{k}={v}")

    return tuple(prefix + [SHELL, *cmd])


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


class Package(object):
    def __init__(self, root: Path, name: str):
        self.root = root
        self.name = name

    def test(self):
        return True

    def requires(self):
        return []

    def install(self, fs: Vfs, dest: Path):
        self.do_build(fs, dest)
        self.pre_install(fs, dest)
        self.do_install(fs, dest)
        self.post_install(fs, dest)

    def do_build(self, fs: Vfs, dest: Path):
        pass

    def pre_install(self, fs: Vfs, dest: Path):
        pass

    def do_install(self, fs: Vfs, dest: Path):
        pass

    def post_install(self, fs: Vfs, dest: Path):
        pass
