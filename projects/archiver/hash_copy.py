"""
A tree deduplicator and archiver tool.
"""

import argparse
from pathlib import Path
from shutil import copy2 as copyfile

from .util import *


parser = argparse.ArgumentParser()
parser.add_argument("from_dir", type=Path)
parser.add_argument("to_dir", type=Path)


def main():
    opts, args = parser.parse_known_args()

    for abs_src_path in opts.from_dir.glob("**/*"):
        rel_src_path = abs_src_path.relative_to(opts.from_dir)
        abs_dest_path = opts.to_dir / rel_src_path

        if abs_src_path.is_dir():
            print("dir", abs_src_path, "->", abs_dest_path)
            abs_dest_path.mkdir(exist_ok=True)

        elif abs_src_path.is_file():
            print("file", abs_src_path, "->", abs_dest_path)

            if not abs_dest_path.exists():
                copyfile(abs_src_path, abs_dest_path)

            else:
                # If you trust mtime, this can go a lot faster
                trust_mtime = False

                if (
                    trust_mtime
                    and abs_dest_path.stat().st_mtime < abs_src_path.stat().st_mtime
                ):
                    pass

                elif (src_checksum := checksum_path(abs_src_path)) != (
                    dest_checksum := checksum_path(abs_dest_path)
                ):
                    print(
                        f"file conflict (src {src_checksum}, dest {dest_checksum}), correcting..."
                    )
                    copyfile(abs_src_path, abs_dest_path)

            abs_src_path.unlink()


if __name__ == "__main__":
    main()
