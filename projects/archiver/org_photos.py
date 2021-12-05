"""Organize (and annotate) photos predictably.

This script is designed to eat a Dropbox style "camera uploads" directory containing many years of photos with various
metadata (or data only in the file name) and stomp that all down to something consistent by doing EXIF parsing and
falling back to filename parsing if need be.

Note that this script does NOT do EXIF rewriting, although it probably should.

Generates an output tree of the format -
  {year}/v1_{iso_date}_{camera_make}_{camera_model}_{device_fingerprint}.{ext}

The idea being that chronological-ish order is the default way users will want to view (or process) photos.
Note that this means if you do interleaved shooting between devices, it should Just Work (TM).

Inspired by https://github.com/herval/org_photos/blob/main/org_photos.rb

"""

import argparse
from datetime import datetime, timedelta
from hashlib import sha256, sha512
from pathlib import Path
import re
from shutil import copy2 as copyfile
import sys
import typing as t

from .util import *

# FIXME: use piexif, which supports writeback not exifread.
import exifread
from yaspin import Spinner, yaspin


_print = print


def print(*strs, **kwargs):
    _print("\r", *strs, **kwargs)


parser = argparse.ArgumentParser()
parser.add_argument("src_dir", type=Path)
parser.add_argument("dest_dir", type=Path)
parser.add_argument("destructive", action="store_true", default=False)


MODIFIED_ISO_DATE = "%Y:%m:%dT%H:%M:%SF%f"
SPINNER = Spinner(["|", "/", "-", "\\"], 200)
KNOWN_IMG_TYPES = {
    ".jpg": ".jpeg",
    ".jpeg": ".jpeg",
    ".png": ".png",
    ".mov": ".mov",
    ".gif": ".gif",
    ".mp4": ".mp4",
    ".m4a": ".m4a",
    ".oga": ".oga",  # How the hell do I have ogg files kicking around
}


def exif_tags(p: Path) -> object:
    """Return the EXIF tags on an image."""
    with open(p, "rb") as fp:
        return exifread.process_file(fp)


def sanitize(s: str) -> str:
    """Something like b64encode; sanitize a string to a path-friendly version."""

    to_del = [" ", ";", ":", "_", "-", "/", "\\", "."]
    s = s.lower()
    for c in to_del:
        s = s.replace(c, "")
    return s


def safe_strptime(date, format):
    try:
        return datetime.strptime(date, format)
    except ValueError:
        pass


def safe_ymdhmms(date):
    fmt = (
        r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"
        r" "
        r"(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})(?P<millisecond>\d{3})"
    )
    m = re.match(fmt, date)
    if m:
        return datetime(
            year=int(m.group("year")),
            month=int(m.group("month")),
            day=int(m.group("day")),
            hour=int(m.group("hour")),
            minute=int(m.group("minute")),
            second=int(m.group("second")),
            microsecond=int(m.group("millisecond")) * 1000,
        )


def date_from_name(fname: str):
    # Discard common prefixes
    fname = fname.replace("IMG_", "")
    fname = fname.replace("PXL_", "")
    fname = fname.replace("VID_", "")

    if fname.startswith("v1_"):
        # The date segment of the v1 file name
        fname = fname.split("_")[1]

    # Guess if we have a v0 file name, which neglected the prefix
    elif fname.count("_") == 3:
        # A bug
        fname = fname.split("_")[-1].replace("rc", "")[:25]

    # We have some other garbage, make our date parsing life easier.
    else:
        # A couple of date formats use _ as field separators, consistently choice " " instead so that we can write fewer
        # date patterns and be more correct.
        fname = fname.replace("_", " ")
        fname = re.sub(
            r"(-\d+)(-\d+)*$", r"\1", fname
        )  # deal with -1-2 etc. crap from Dropbox

    # Try to guess the date
    # File date formats:
    for unfmt in [
        # Our date format
        lambda d: safe_strptime(d, MODIFIED_ISO_DATE),
        # A bug
        # 2014:08:21T19:4640F1408672000
        # 2015:12:14T23:0933F1450159773
        lambda d: safe_strptime(d, "%Y:%m:%dT%H:%M%SF%f"),
        # 2020-12-21 17.15.09.0
        lambda d: safe_strptime(d, "%Y-%m-%d %H.%M.%S.%f"),
        # 2020-12-21 17.15.09
        lambda d: safe_strptime(d, "%Y-%m-%d %H.%M.%S"),
        # 2019-02-09 12.45.32-6
        # 2019-01-13 13.43.45-16
        lambda d: safe_strptime(d, "%Y-%m-%d %H.%M.%S-%f"),
        # Note the _1 or such may not be millis, but we assume it is.
        # 20171113_130826_1
        # 20171113 130826 1
        lambda d: safe_strptime(d, "%Y%m%d %H%M%S %f"),
        # 20180404_114639
        # 20180404 114639
        lambda d: safe_strptime(d, "%Y%m%d %H%M%S"),
        # 2017-11-05_15:15:55
        # 2017-11-05 15:15:55
        lambda d: safe_strptime(d, "%Y-%m-%d %H:%M:%S"),
        lambda d: safe_strptime(d, "%Y%m%d %h%m%s%f"),
        # HACK:
        #   Python doesn't support %s as milliseconds; these don't quite work.
        #   So use a custom matcher.
        # 20210526 002327780
        # 20210417_220753284
        # 20210417 220753284
        # 20210304 204755545
        # 20211111 224304117
        safe_ymdhmms,
    ]:
        val = unfmt(fname)
        if val is not None:
            return val


def date_from_path(p: Path):
    """Try to munge a datestamp out of a path."""

    fname = ".".join(p.name.split(".")[:-1])

    date = date_from_name(fname)
    if not date:
        print(f"Warning: Unable to infer datetime from {fname!r}", file=sys.stderr)
    return date


def normalize_ext(p: Path):
    renaming = KNOWN_IMG_TYPES
    exts = [e.lower() for e in p.suffixes]
    # Guess an ext out of potentially many, allowing only for folding of effective dupes
    exts = set(renaming[e] for e in exts if e in renaming)
    assert len(exts) == 1
    return list(exts)[0]


class ImgInfo(t.NamedTuple):
    file_path: Path
    tags: dict

    camera_make: str
    camera_model: str
    camera_sn: str

    lens_make: str
    lens_model: str
    lens_sn: str

    software: str

    date: datetime

    # A dirty bit, indicating whether the info needs to be written back
    dirty: bool = False

    shasum_prefix: int = 9

    def device_fingerprint(self):
        """Compute a stable 'fingerprint' for the device that took the shot."""

        return checksum_list(
            [
                self.camera_make,
                self.camera_model,
                self.camera_sn,
                self.lens_make,
                self.lens_model,
                self.lens_sn,
                self.software,
            ]
        )[: self.shasum_prefix]

    def file_fingerprint(self):
        """Compute a 'fingerprint' for the file itself.

        Note that this hash DOES include EXIF data, and is not stable.

        """
        return self.file_sha256sum()[: self.shasum_prefix]

    def file_sha256sum(self):
        return checksum_path(self.file_path, sha256)

    def file_sha512sum(self):
        return checksum_path(self.file_path, sha512)

    def incr(self, offset: int) -> "ImgInfo":
        return ImgInfo(
            self.file_path,
            self.tags,
            self.camera_make,
            self.camera_model,
            self.camera_sn,
            self.lens_make,
            self.lens_model,
            self.lens_sn,
            self.software,
            self.date + timedelta(microseconds=offset),
            True,
        )

def img_info(p: Path) -> ImgInfo:
    """Figure out everything we know from the image info."""

    tags = exif_tags(p)

    def get_tag(tag, default=None):
        if v := tags.get(tag):
            if isinstance(v.values, list):
                return v.values[0]
            elif isinstance(v.values, str):
                return v.values
            else:
                raise ValueError(f"Don't know how to simplify {v!r}")
        else:
            return default

    ## Camera data
    camera_make = get_tag("Image Make", "Unknown")
    camera_model = get_tag("Image Model", "Unknown")
    camera_sn = get_tag("MakerNote SerialNumber", "Unknown")
    lens_make = get_tag("EXIF LensMake", "Unknown")
    lens_model = get_tag("EXIF LensModel", "Unknown")
    lens_sn = get_tag("EXIF LensSerialNumber", "Unknown")
    software = get_tag("Image Software", "Unknown")
    dirty = False

    # Fixup magic for "correcting" metadata where possible
    # FIXME: This could be a postprocessing pass
    if camera_make == "Unknown" and p.name.lower().startswith("dji"):
        # Magic constants from found examples
        camera_make = "DJI"
        camera_model = "FC220"
        software = "v02.09.514"
        dirty |= True

    elif camera_make == "Unknown" and p.name.startswith("PXL_"):
        camera_make = "Google"
        camera_model = "Pixel"
        dirty |= True

    ## Timestamp data
    stat = p.stat()

    # 2019:03:31 15:59:26
    date = (
        get_tag("Image DateTime")
        or get_tag("EXIF DateTimeOriginal")
        or get_tag("EXIF DateTimeDigitized")
    )
    if date and (date := safe_strptime(date, "%Y:%m:%d %H:%M:%S")):
        pass
    elif date := date_from_path(p):
        dirty |= True
    else:
        # The oldest of the mtime and the ctime
        date = datetime.fromtimestamp(min([stat.st_mtime, stat.st_ctime]))
        dirty |= True

    # 944404
    subsec = int(
        get_tag("EXIF SubSecTime")
        or get_tag("EXIF SubSecTimeOriginal")
        or get_tag("EXIF SubSecTimeDigitized")
        or "0"
    )

    # GoPro burst format is G%f.JPG or something close to it
    if subsec == 0 and (m := re.match(r"g.*(\d{6}).jpe?g", p.name.lower())):
        subsec = int(m.group(1))

    date = date.replace(microsecond=subsec)

    if not (2015 <= date.year <= datetime.now().year):
        raise ValueError(f"{p}'s inferred date ({date!r}) is beyond the sanity-check range!")

    return ImgInfo(
        p,
        tags,
        camera_make,
        camera_model,
        camera_sn,
        lens_make,
        lens_model,
        lens_sn,
        software,
        date,
        dirty,
    )


def main():
    opts, args = parser.parse_known_args()

    def _copy(src, target):
        print(f"  rename: {target}")
        try:
            if not opts.destructive:
                raise OSError()

            src.rename(target)  # Execute the rename

        except OSError:  # cross-device move
            with yaspin(SPINNER):
                copyfile(src, target)

                if opts.destructive:
                    src.unlink()
                    print("  unlink: ok")

    print("---")

    sequence_name = None
    sequence = 0

    for src in opts.src_dir.glob("**/*"):
        print(f"{src}:")
        ext = "." + src.name.lower().split(".")[-1]
        print(f"  msg: ext inferred as {ext}")

        if src.is_dir():
            continue

        elif ext in ["thm", "lrv", "ico", "sav"] or src.name.startswith("._"):
            if opts.destructive:
                src.unlink()
            continue

        elif ext in KNOWN_IMG_TYPES:
            info = img_info(src)
            year_dir = Path(opts.dest_dir / str(info.date.year))
            year_dir.mkdir(exist_ok=True)  # Ignore existing and continue
            # Figure out a stable file name
            stable_name = f"v1_{info.date.strftime(MODIFIED_ISO_DATE)}_{sanitize(info.camera_make)}_{sanitize(info.camera_model)}_{info.device_fingerprint()}"

            # De-conflict using a sequence number added to the sub-seconds field
            if sequence_name == stable_name:
                sequence += 1
                info = info.incr(sequence)
                print(f"  warning: de-conflicting filenames with sequence {sequence}")
                stable_name = f"v1_{info.date.strftime(MODIFIED_ISO_DATE)}_{sanitize(info.camera_make)}_{sanitize(info.camera_model)}_{info.device_fingerprint()}"

            else:
                sequence = 0
                sequence_name = stable_name

            try:
                ext = normalize_ext(src)
            except AssertionError:
                continue  # Just skip fucked up files
            target = Path(year_dir / f"{stable_name}{ext}")

            if not target.exists():
                # src & !target => copy
                _copy(src, target)

            elif src == target:
                # src == target; skip DO NOT DELETE SRC
                pass

            elif checksum_path_blocks(src) == checksum_path_blocks(target):
                print(f"  ok: {target}")
                # src != target && id(src) == id(target); delete src
                if opts.destructive:
                    src.unlink()

            else:
                # src != target && id(src) != id(target); replace target with src?
                print(f"  warning: {target} is a content-id collision with a different checksum; skipping")

        else:
            print(f"  msg: unknown filetype {ext}")


if __name__ == "__main__":
    main()
