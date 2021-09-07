import os
import re
import sys


def main(opts, args):
    """Usage: python rollback.py date

    Parse /var/log/pacman.log, enumerating package transactions since the
    specified date and building a plan for restoring the state of your system to
    what it was at the specified date.

    Assumes:
    - /var/log/pacman.log has not been truncated

    - /var/cache/pacman/pkg has not been flushed and still contains all required
      packages

    - The above paths are Arch default and have not been customized

    - That it is not necessary to remove any "installed" packages

    Note: no attempt is made to inspect the dependency graph of packages to be
    downgraded to detect when a package is already transitively listed for
    downgrading. This can create some annoying errors where eg. systemd will be
    downgraded, meaning libsystemd will also be downgraded, but pacman considers
    explicitly listing the downgrade of libsystemd when it will already be
    transitively downgraded an error.

    """

    date, = args

    print("Attempting to roll back package state to that of {0}...\n"
          .format(date),
          file=sys.stderr)

    # These patterns can't be collapsed because we want to select different
    # version identifying strings depending on which case we're in. Not ideal,
    # but it works.

    # Ex. [2017-04-01 09:51] [ALPM] upgraded filesystem (2016.12-2 -> 2017.03-2)
    upgraded_pattern = re.compile(
        ".*? upgraded (?P<name>\w+) \((?P<from>[^ ]+) -> (?P<to>[^\)]+)\)")

    # Ex: [2018-02-23 21:18] [ALPM] downgraded emacs (25.3-3 -> 25.3-2)
    downgraded_pattern = re.compile(
        ".*? downgraded (?P<name>\w+) \((?P<to>[^ ]+) -> (?P<from>[^\)]+)\)")

    # Ex: [2017-03-31 07:05] [ALPM] removed gdm (3.22.3-1)
    removed_pattern = re.compile(
        ".*? removed (?P<name>\w+) \((?P<from>[^ ]+)\)")

    checkpoint = {}
    flag = False

    with open("/var/log/pacman.log") as logfile:
        for line in logfile:
            if date in line:
                flag = True
            elif not flag:
                continue

            match = re.match(upgraded_pattern, line)\
                or re.match(downgraded_pattern, line)\
                or re.match(removed_pattern, line)

            if match:
                package = match.group("name")
                from_rev = match.group("from")
                if package not in checkpoint:
                    checkpoint[package] = from_rev
                continue

    print("Checkpoint state:")
    for k in checkpoint.keys():
        print("{0} -> {1}".format(k, checkpoint[k]), file=sys.stderr)

    pkgcache = "/var/cache/pacman/pkg"
    pkgs = os.listdir(pkgcache)
    pkgnames = ["{0}-{1}".format(k, v) for k, v in checkpoint.items()]

    selected_pkgs = set([os.path.join(pkgcache, p)
                         for n in pkgnames
                         for p in pkgs
                         if n in p])

    print("Suggested incantation:\n", file=sys.stderr)
    print("sudo pacman --noconfirm -U {}"
          .format("\\\n  ".join(selected_pkgs)))


if __name__ == "__main__":
  main(None, sys.argv[1:])
