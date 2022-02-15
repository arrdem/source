"""Cram's original (v0) configs.

An ill-considered pseudo-format.
"""

from pathlib import Path
import re
from typing import NamedTuple

from .common import Package, sh, stow

from vfs import Vfs


class PackageV0(Package):
    """The original package format from install.sh."""

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

        return requires

    def install(self, fs: Vfs, dest: Path):
        """Install this package."""
        buildf = self.root / "BUILD"
        if buildf.exists():
            fs.exec(self.root, sh([str(buildf)]))

        pref = self.root / "PRE_INSTALL"
        if pref.exists():
            fs.exec(self.root, sh([str(pref)]))

        installf = self.root / "INSTALL"
        if installf.exists():
            fs.exec(self.root, sh([str(installf)]))
        else:
            stow(fs, self.root, dest, self.SPECIAL_FILES)

        postf = self.root / "POST_INSTALL"
        if postf.exists():
            fs.exec(self.root, sh([str(postf)]))


class ProfileV0(PackageV0):
    def requires(self):
        requires = super().requires()
        for p in self.root.glob("*"):
            if p.is_dir():
                requires.append(self.name + "/" + p.name)
        return requires

    def install(self, fs: Vfs, dest: Path):
        """Profiles differ from Packages in that they don't support literal files."""

        buildf = self.root / "BUILD"
        if buildf.exists():
            fs.exec(self.root, sh([str(buildf)]))

        pref = self.root / "PRE_INSTALL"
        if pref.exists():
            fs.exec(self.root, sh([str(pref)]))

        installf = self.root / "INSTALL"
        if installf.exists():
            fs.exec(self.root, sh([str(installf)]))

        postf = self.root / "POST_INSTALL"
        if postf.exists():
            fs.exec(self.root, sh([str(postf)]))
