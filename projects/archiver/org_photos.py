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
from datetime import datetime
from hashlib import sha256, sha512
from pathlib import Path
import re
from shutil import copy2 as copyfile
import sys
import typing as t

# FIXME: use piexif, which supports writeback not exifread.
import exifread


parser = argparse.ArgumentParser()
parser.add_argument("src_dir", type=Path)
parser.add_argument("dest_dir", type=Path)


MODIFIED_ISO_DATE = "%Y:%m:%dT%H:%M:%SF%f"


def take(n, iter):
    """Take the first N items lazily off of an iterable."""

    for _ in range(0, n):
        try:
            yield next(iter)
        except StopIteration:
            break


def exif_tags(p: Path) -> object:
    """Return the EXIF tags on an image."""
    with open(p, "rb") as fp:
        return exifread.process_file(fp)


# EXIF tags dataset (exifread edition) -
#
# ---
# - 'EXIF ApertureValue'
# - 'EXIF BodySerialNumber'
# - 'EXIF BrightnessValue'
# - 'EXIF CVAPattern'
# - 'EXIF CameraOwnerName'
# - 'EXIF ColorSpace'
# - 'EXIF ComponentsConfiguration'
# - 'EXIF CompressedBitsPerPixel'
# - 'EXIF Contrast'
# - 'EXIF CustomRendered'
# - 'EXIF DateTimeDigitized'
# - 'EXIF DateTimeOriginal'
# - 'EXIF DeviceSettingDescription'
# - 'EXIF DigitalZoomRatio'
# - 'EXIF ExifImageLength'
# - 'EXIF ExifImageWidth'
# - 'EXIF ExifVersion'
# - 'EXIF ExposureBiasValue'
# - 'EXIF ExposureIndex'
# - 'EXIF ExposureMode'
# - 'EXIF ExposureProgram'
# - 'EXIF ExposureTime'
# - 'EXIF FNumber'
# - 'EXIF FileSource'
# - 'EXIF Flash'
# - 'EXIF FlashEnergy'
# - 'EXIF FlashPixVersion'
# - 'EXIF FocalLength'
# - 'EXIF FocalLengthIn35mmFilm'
# - 'EXIF FocalPlaneResolutionUnit'
# - 'EXIF FocalPlaneXResolution'
# - 'EXIF FocalPlaneYResolution'
# - 'EXIF GainControl'
# - 'EXIF ISOSpeedRatings'
# - 'EXIF ImageUniqueID'
# - 'EXIF InteroperabilityOffset'
# - 'EXIF JPEGInterchangeFormat'
# - 'EXIF JPEGInterchangeFormatLength'
# - 'EXIF LensMake'
# - 'EXIF LensModel'
# - 'EXIF LensSerialNumber'
# - 'EXIF LensSpecification'
# - 'EXIF LightSource'
# - 'EXIF MakerNote'
# - 'EXIF MaxApertureValue'
# - 'EXIF MeteringMode'
# - 'EXIF OffsetSchema'
# - 'EXIF OffsetTime'
# - 'EXIF OffsetTimeDigitized'
# - 'EXIF OffsetTimeOriginal'
# - 'EXIF Padding'
# - 'EXIF RecommendedExposureIndex'
# - 'EXIF Saturation'
# - 'EXIF SceneCaptureType'
# - 'EXIF SceneType'
# - 'EXIF SensingMethod'
# - 'EXIF SensitivityType'
# - 'EXIF Sharpness'
# - 'EXIF ShutterSpeedValue'
# - 'EXIF SubSecTime'
# - 'EXIF SubSecTimeDigitized'
# - 'EXIF SubSecTimeOriginal'
# - 'EXIF SubjectArea'
# - 'EXIF SubjectDistance'
# - 'EXIF SubjectDistanceRange'
# - 'EXIF UserComment'
# - 'EXIF WhiteBalance'
# - 'GPS GPSAltitude'
# - 'GPS GPSAltitudeRef'
# - 'GPS GPSDOP'
# - 'GPS GPSDate'
# - 'GPS GPSImgDirection'
# - 'GPS GPSImgDirectionRef'
# - 'GPS GPSLatitude'
# - 'GPS GPSLatitudeRef'
# - 'GPS GPSLongitude'
# - 'GPS GPSLongitudeRef'
# - 'GPS GPSMapDatum'
# - 'GPS GPSMeasureMode'
# - 'GPS GPSProcessingMethod'
# - 'GPS GPSTimeStamp'
# - 'GPS GPSVersionID'
# - 'GPS Tag 0xEA1C'
# - 'Image Artist'
# - 'Image BitsPerSample'
# - 'Image Copyright'
# - 'Image DateTime'
# - 'Image DateTimeDigitized'
# - 'Image ExifOffset'
# - 'Image ExposureMode'
# - 'Image ExposureProgram'
# - 'Image ExposureTime'
# - 'Image FNumber'
# - 'Image Flash'
# - 'Image FocalLength'
# - 'Image GPSInfo'
# - 'Image ISOSpeedRatings'
# - 'Image ImageDescription'
# - 'Image ImageLength'
# - 'Image ImageWidth'
# - 'Image JPEGInterchangeFormat'
# - 'Image JPEGInterchangeFormatLength'
# - 'Image LightSource'
# - 'Image Make'
# - 'Image MeteringMode'
# - 'Image Model'
# - 'Image Orientation'
# - 'Image Padding'
# - 'Image PhotometricInterpretation'
# - 'Image PrintIM'
# - 'Image ResolutionUnit'
# - 'Image SamplesPerPixel'
# - 'Image Software'
# - 'Image UserComment'
# - 'Image WhiteBalance'
# - 'Image XPComment'
# - 'Image XPKeywords'
# - 'Image XPTitle'
# - 'Image XResolution'
# - 'Image YCbCrPositioning'
# - 'Image YResolution'
# - 'Interoperability InteroperabilityIndex'
# - 'Interoperability InteroperabilityVersion'
# - 'JPEGThumbnail'
# - 'MakerNote AEBracketCompensationApplied'
# - 'MakerNote AESetting'
# - 'MakerNote AFAreaMode'
# - 'MakerNote AFInfo2'
# - 'MakerNote AFPointSelected'
# - 'MakerNote AFPointUsed'
# - 'MakerNote ActiveDLighting'
# - 'MakerNote AspectInfo'
# - 'MakerNote AutoBracketRelease'
# - 'MakerNote AutoFlashMode'
# - 'MakerNote BracketMode'
# - 'MakerNote BracketShotNumber'
# - 'MakerNote BracketValue'
# - 'MakerNote BracketingMode'
# - 'MakerNote CanonImageWidth'
# - 'MakerNote ColorBalance'
# - 'MakerNote ColorSpace'
# - 'MakerNote ContinuousDriveMode'
# - 'MakerNote Contrast'
# - 'MakerNote CropHiSpeed'
# - 'MakerNote CropInfo'
# - 'MakerNote DigitalVariProgram'
# - 'MakerNote DigitalZoom'
# - 'MakerNote DustRemovalData'
# - 'MakerNote EasyShootingMode'
# - 'MakerNote ExposureDifference'
# - 'MakerNote ExposureMode'
# - 'MakerNote ExposureTuning'
# - 'MakerNote ExternalFlashExposureComp'
# - 'MakerNote FileInfo'
# - 'MakerNote FileNumber'
# - 'MakerNote FilterEffect'
# - 'MakerNote FirmwareVersion'
# - 'MakerNote FlashActivity'
# - 'MakerNote FlashBias'
# - 'MakerNote FlashBracketCompensationApplied'
# - 'MakerNote FlashCompensation'
# - 'MakerNote FlashDetails'
# - 'MakerNote FlashExposureLock'
# - 'MakerNote FlashInfo'
# - 'MakerNote FlashMode'
# - 'MakerNote FlashSetting'
# - 'MakerNote FocalLength'
# - 'MakerNote FocalType'
# - 'MakerNote FocalUnitsPerMM'
# - 'MakerNote FocusMode'
# - 'MakerNote FocusType'
# - 'MakerNote HDRImageType'
# - 'MakerNote HighISONoiseReduction'
# - 'MakerNote ISO'
# - 'MakerNote ISOInfo'
# - 'MakerNote ISOSetting'
# - 'MakerNote ISOSpeedRequested'
# - 'MakerNote ImageDataSize'
# - 'MakerNote ImageSize'
# - 'MakerNote ImageStabilization'
# - 'MakerNote ImageType'
# - 'MakerNote InternalSerialNumber'
# - 'MakerNote LensData'
# - 'MakerNote LensFStops'
# - 'MakerNote LensMinMaxFocalMaxAperture'
# - 'MakerNote LensModel'
# - 'MakerNote LensType'
# - 'MakerNote LiveViewShooting'
# - 'MakerNote LongExposureNoiseReduction2'
# - 'MakerNote LongFocalLengthOfLensInFocalUnits'
# - 'MakerNote MacroMagnification'
# - 'MakerNote Macromode'
# - 'MakerNote MakernoteVersion'
# - 'MakerNote ManualFlashOutput'
# - 'MakerNote MeteringMode'
# - 'MakerNote ModelID'
# - 'MakerNote MultiExposure'
# - 'MakerNote NikonPreview'
# - 'MakerNote NoiseReduction'
# - 'MakerNote NumAFPoints'
# - 'MakerNote OwnerName'
# - 'MakerNote PhotoCornerCoordinates'
# - 'MakerNote PictureControl'
# - 'MakerNote PowerUpTime'
# - 'MakerNote ProgramShift'
# - 'MakerNote Quality'
# - 'MakerNote RawJpgQuality'
# - 'MakerNote RawJpgSize'
# - 'MakerNote RecordMode'
# - 'MakerNote RetouchHistory'
# - 'MakerNote Saturation'
# - 'MakerNote SelfTimer'
# - 'MakerNote SequenceNumber'
# - 'MakerNote SerialNumber'
# - 'MakerNote Sharpness'
# - 'MakerNote ShortFocalLengthOfLensInFocalUnits'
# - 'MakerNote ShotInfo'
# - 'MakerNote SlowShutter'
# - 'MakerNote SpotMeteringMode'
# - 'MakerNote SubjectDistance'
# - 'MakerNote Tag 0x0001'
# - 'MakerNote Tag 0x0002'
# - 'MakerNote Tag 0x0003'
# - 'MakerNote Tag 0x0004'
# - 'MakerNote Tag 0x0005'
# - 'MakerNote Tag 0x0006'
# - 'MakerNote Tag 0x0007'
# - 'MakerNote Tag 0x0008'
# - 'MakerNote Tag 0x0009'
# - 'MakerNote Tag 0x000E'
# - 'MakerNote Tag 0x0014'
# - 'MakerNote Tag 0x0015'
# - 'MakerNote Tag 0x0019'
# - 'MakerNote Tag 0x002B'
# - 'MakerNote Tag 0x002C'
# - 'MakerNote Tag 0x002D'
# - 'MakerNote Tag 0x0083'
# - 'MakerNote Tag 0x0099'
# - 'MakerNote Tag 0x009D'
# - 'MakerNote Tag 0x00A0'
# - 'MakerNote Tag 0x00A3'
# - 'MakerNote Tag 0x00AA'
# - 'MakerNote Tag 0x00BB'
# - 'MakerNote Tag 0x00D0'
# - 'MakerNote Tag 0x00E0'
# - 'MakerNote Tag 0x4001'
# - 'MakerNote Tag 0x4008'
# - 'MakerNote Tag 0x4009'
# - 'MakerNote Tag 0x4010'
# - 'MakerNote Tag 0x4011'
# - 'MakerNote Tag 0x4012'
# - 'MakerNote Tag 0x4015'
# - 'MakerNote Tag 0x4016'
# - 'MakerNote Tag 0x4017'
# - 'MakerNote Tag 0x4018'
# - 'MakerNote Tag 0x4019'
# - 'MakerNote Tag 0x4020'
# - 'MakerNote ThumbnailImageValidArea'
# - 'MakerNote ToningEffect'
# - 'MakerNote TotalShutterReleases'
# - 'MakerNote Unknown'
# - 'MakerNote VRInfo'
# - 'MakerNote ValidAFPoints'
# - 'MakerNote WBBracketMode'
# - 'MakerNote WBBracketValueAB'
# - 'MakerNote WBBracketValueGM'
# - 'MakerNote WhiteBalance'
# - 'MakerNote WhiteBalanceBias'
# - 'MakerNote WhiteBalanceRBCoeff'
# - 'MakerNote Whitebalance'
# - 'MakerNote WorldTime'
# - 'Thumbnail Compression'
# - 'Thumbnail DateTime'
# - 'Thumbnail ImageDescription'
# - 'Thumbnail ImageLength'
# - 'Thumbnail ImageWidth'
# - 'Thumbnail JPEGInterchangeFormat'
# - 'Thumbnail JPEGInterchangeFormatLength'
# - 'Thumbnail Make'
# - 'Thumbnail Model'
# - 'Thumbnail Orientation'
# - 'Thumbnail ResolutionUnit'
# - 'Thumbnail Software'
# - 'Thumbnail XResolution'
# - 'Thumbnail YCbCrPositioning'
# - 'Thumbnail YResolution'


def checksum(p: Path, sum=sha256) -> str:
    """Compute a chunked checksum of a file.

    Does not produce individual block checksums.
    """

    def iter_blocks(fp):
        yield from iter(lambda: fp.read(4096), b"")

    with open(p, "rb") as fp:
        digest = sum()
        for chunk in iter_blocks(fp):
            digest.update(chunk)
        return digest.hexdigest()


def checksum_list(iter, sum=sha256):
    """Compute the checksum of a bunch of stuff from an iterable."""

    sum = sum()
    for i in iter:
        sum.update(b";")  # Merkle tree salting.
        if isinstance(i, str):
            i = str.encode(i, "utf-8")
        try:
            sum.update(i)
        except Exception as e:
            print(i, type(i))
            raise e

    return sum.hexdigest()


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
        return None


def date_from_name(p: Path):
    """Try to munge a datestamp out of a path."""

    fname = ".".join(p.name.split(".")[:-1])

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
    for fmt in [
        # Our date format
        MODIFIED_ISO_DATE,
        # A bug
        # 2014:08:21T19:4640F1408672000
        # 2015:12:14T23:0933F1450159773
        "%Y:%m:%dT%H:%M%SF%f",
        # 2020-12-21 17.15.09.0
        "%Y-%m-%d %H.%M.%S.%f",
        # 2020-12-21 17.15.09
        "%Y-%m-%d %H.%M.%S",
        # 2019-02-09 12.45.32-6
        # 2019-01-13 13.43.45-16
        "%Y-%m-%d %H.%M.%S-%f",
        # Note the _1 or such may not be millis, but we assume it is.
        # 20171113_130826_1
        # 20171113 130826 1
        "%Y%m%d %H%M%S %f",
        # 20180404_114639
        # 20180404 114639
        "%Y%m%d %H%M%S",
        # 2017-11-05_15:15:55
        # 2017-11-05 15:15:55
        "%Y-%m-%d %H:%M:%S",
        # 20210417_220753284
        # 20210417 220753284
        # 20210304 204755545
        "%Y%m%d %h%m%s%f",
    ]:
        try:
            return datetime.strptime(fname, fmt)
        except ValueError:
            continue
    else:
        print(f"Warning: Unable to infer datetime from {fname!r}", file=sys.stderr)


def normalize_ext(p: Path):
    renaming = {
        ".jpg": ".jpeg",
        ".jpeg": ".jpeg",
        ".png": ".png",
        ".mov": ".mov",
        ".gif": ".gif",
        ".mp4": ".mp4",
        ".m4a": ".m4a",
        ".oga": ".oga",  # How the hell do I have ogg files kicking around
    }
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
        return checksum(self.file_path, sha256)

    def file_sha512sum(self):
        return checksum(self.file_path, sha512)


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
    elif date := date_from_name(p):
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

    print("---")
    for src in list(opts.src_dir.glob("**/*")):
        if src.is_dir():
            continue

        info = img_info(src)
        year_dir = Path(opts.dest_dir / str(info.date.year))
        year_dir.mkdir(exist_ok=True)  # Ignore existing and continue
        # Figure out a stable file name
        stable_name = f"v1_{info.date.strftime(MODIFIED_ISO_DATE)}_{sanitize(info.camera_make)}_{sanitize(info.camera_model)}_{info.device_fingerprint()}"
        try:
            ext = normalize_ext(src)
        except AssertionError:
            continue  # Just skip fucked up files
        target = Path(year_dir / f"{stable_name}{ext}")

        print(f"{src}:")
        print(f"  rename: {target}")
        if not target.exists():
            try:
                src.rename(target)  # Execute the rename
            except OSError:
                copyfile(src, target)
                target.chmod(0o644)
                src.unlink()
        elif src == target:
            pass  # Nothing to do
        else:
            target.chmod(0o644)
            src.unlink()  # Delete the source


if __name__ == "__main__":
    main()
