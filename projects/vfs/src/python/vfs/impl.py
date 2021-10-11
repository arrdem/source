"""
The implementation.
"""

import logging
from subprocess import run


_log = logging.getLogger(__name__)


class Vfs(object):
    """An abstract filesystem device which can accumulate changes, and apply them in a batch."""

    def __init__(self):
        self._log = []

    def execute(self, execute=False):
        for e in self._log:
            _log.debug(e)

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
