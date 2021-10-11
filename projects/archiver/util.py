from hashlib import sha256
from pathlib import Path
import typing as t


def iter_chunks(fp):
    yield from iter(lambda: fp.read(4096), b"")


def take(n, iter):
    """Take the first N items lazily off of an iterable."""

    for _ in range(0, n):
        try:
            yield next(iter)
        except StopIteration:
            break


def checksum_list(iter, sum=sha256, salt=b";"):
    """Compute the checksum of a bunch of stuff from an iterable."""

    sum = sum()
    for i in iter:
        if salt:
            sum.update(salt)  # Merkle tree salting.
        if isinstance(i, str):
            i = str.encode(i, "utf-8")
        try:
            sum.update(i)
        except Exception as e:
            print(i, type(i))
            raise e

    return sum.hexdigest()


def checksum_path_blocks(p: Path, sum=sha256) -> t.Iterable[str]:
    """Compute block-wise checksums of a file.

    Inspired by the Dropbox content-hashing interface -

    https://www.dropbox.com/developers/reference/content-hash

    """

    def _helper():
        with open(p, "rb") as fp:
            for chunk in iter_chunks(fp):
                digest = sum()
                digest.update(chunk)
                yield digest.hexdigest()

    return list(_helper())


def checksum_path(p: Path, sum=sha256) -> str:
    """Compute 'the' checksum of an entire file.

    Note that this does semi-streaming I/O.

    """

    sum = sum()
    with open(p, "rb") as fp:
        for chunk in iter_chunks(fp):
            sum.update(chunk)
    return sum.hexdigest()
