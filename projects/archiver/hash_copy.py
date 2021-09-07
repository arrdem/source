"""
A tree deduplicator and archiver tool.
"""

import argparse
from pathlib import Path
from hashlib import sha256
from shutil import copyfile


parser = argparse.ArgumentParser()
parser.add_argument("from_dir", type=Path)
parser.add_argument("to_dir", type=Path)


def checksum(p: Path, sum=sha256) -> str:
    """Compute block-wise checksums of a file.

    Inspired by the Dropbox content-hashing interface -

    https://www.dropbox.com/developers/reference/content-hash

    """

    def iter_chunks(fp):
        yield from iter(lambda: fp.read(4096), b"")

    def _helper():
        with open(p, "rb") as fp:
            for chunk in iter_chunks(fp):
                digest = sum()
                digest.update(chunk)
                yield digest.hexdigest()

    return list(_helper())


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

                if trust_mtime and abs_dest_path.stat().st_mtime < abs_src_path.stat().st_mtime:
                     pass

                elif (src_checksum := checksum(abs_src_path)) != (dest_checksum := checksum(abs_dest_path)):
                    print(f"file conflict (src {src_checksum}, dest {dest_checksum}), correcting...")
                    copyfile(abs_src_path, abs_dest_path)

            abs_src_path.unlink()


if __name__ == "__main__":
    main()
