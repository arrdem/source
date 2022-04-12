"""Cram's v1 configs.

Based on well* defined TOML manifests, rather than many files.

*Okay. Better.
"""

from hashlib import sha256
from pathlib import Path
from typing import List, Optional, Union

from .common import Package, sh, stow

from vfs import Vfs

import toml


def tempf(name):
    root = Path("/tmp/stow")
    root.mkdir(exist_ok=True, parents=True)
    return root / name


class PackageV1(Package):
    """The v1 package format."""

    SPECIAL_FILES = ["pkg.toml"]
    _config = None

    def config(self):
        if not self._config:
            with open(self.root / self.SPECIAL_FILES[0], "r") as fp:
                self._config = toml.load(fp)
        return self._config

    def test(self):
        return (self.root / self.SPECIAL_FILES[0]).exists() and self.config().get("cram", {}).get("version") == 1

    def requires(self):
        """Get the dependencies of this package."""

        return self.config().get("package", {}).get("requires") or [
            it["name"] for it in self.config().get("package", {}).get("require", [])
        ]

    def do_sh_or_script(self, content: Optional[Union[List[str], str]], fs: Vfs, dest: Path, cwd: Path = "/tmp"):
        if content is None:
            pass

        elif isinstance(content, list):
            return any(self.do_sh_or_script(c, fs, dest) for c in content)

        elif isinstance(content, dict):
            return self.do_sh_or_script(content["run"], fs, dest, {"cwd": self.root}.get(content.get("root"), "/tmp"))

        elif isinstance(content, str):
            sum = sha256()
            sum.update(content.encode("utf-8"))
            sum = sum.hexdigest()

            installf = self.root / content
            if installf.exists():
                with open(installf, "r") as fp:
                    return self.do_sh_or_script(fp.read(), fs, dest)

            elif content:
                f = tempf(f"{sum}.sh")
                with open(f, "w") as fp:
                    fp.write(content)
                    fs.exec(cwd, sh([f]))
                    return True

    def do_build(self, fs: Vfs, dest: Path):
        self.do_sh_or_script(self.config().get("package", {}).get("build"), fs, dest)

    def pre_install(self, fs: Vfs, dest: Path):
        self.do_sh_or_script(self.config().get("package", {}).get("pre_install"), fs, dest)

    def do_install(self, fs: Vfs, dest: Path):
        if not self.do_sh_or_script(self.config().get("package", {}).get("install"), fs, dest):
            stow(fs, self.root, dest, self.SPECIAL_FILES)

    def post_install(self, fs: Vfs, dest: Path):
        self.do_sh_or_script(self.config().get("package", {}).get("post_install"), fs, dest)


class ProfileV1(PackageV1):
    """Unline packages, profiles don't support recursive stow of contents."""

    def do_install(self, fs: Vfs, dest: Path):
        self.do_sh_or_script(self.config().get("package", {}).get("install"), fs, dest)

    def requires(self):
        requires = super().requires()

        # Implicitly depended subpackages
        for p in self.root.glob("*"):
            if p.is_dir():
                requires.append(self.name + "/" + p.name)

        return requires
