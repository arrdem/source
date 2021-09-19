"""A shim to black which knows how to tee output for --output-file."""

import argparse
import sys

from black import nullcontext, patched_main


parser = argparse.ArgumentParser()
parser.add_argument("--output-file", default=None)


class Tee(object):
    """Something that looks like a File/Writeable but does teed writes."""

    def __init__(self, name, mode):
        self._file = open(name, mode)
        self._stdout = sys.stdout

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, *args, **kwargs):
        sys.stdout = self._stdout
        self.close()

    def write(self, data):
        self._file.write(data)
        self._stdout.write(data)

    def flush(self):
        self._file.flush()
        self._stdout.flush()

    def close(self):
        self._file.close()


if __name__ == "__main__":
    opts, args = parser.parse_known_args()

    if opts.output_file:
        print("Teeig output....")
        ctx = Tee(opts.output_file, "w")
    else:
        ctx = nullcontext()

    with ctx:
        sys.argv = [sys.argv[0]] + args
        patched_main()
