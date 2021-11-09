"""
The implementation.
"""

import logging
from subprocess import run


_log = logging.getLogger(__name__)


class Vfs(object):
    """An abstract filesystem device which can accumulate changes, and apply them in a batch."""

    def __init__(self, log=None):
        self._log = log or []

    def execute(self, execute=False):
        for e in self._log:
            _log.debug(e)

            if not execute:
                continue

            match e:
                case ["exec", dir, cmd]:
                    run(cmd, cwd=str(dir))

                case ["link", src, dest]:
                    if dest.is_file() or dest.is_symlink():
                        if dest.is_symlink() and dest.readlink() == src:
                            continue
                        else:
                            dest.unlink()

                    assert not dest.exists()
                    dest.symlink_to(src)

                case ["copy", src, dest]:
                    raise NotImplementedError()

                case ["chmod", dest, mode]:
                    dest.chmod(mode)

                case ["mkdir", dest]:
                    dest.mkdir(exist_ok=True)

                case ["unlink", dest]:
                    dest.unlink()

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

    def unlink(self, dest):
        self._append(("unlink", dest))

    def copy(self):
        return Vfs(list(self._log))
