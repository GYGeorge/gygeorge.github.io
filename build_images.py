"""Create web previews and a safe EXIF manifest from album folders.

Run with: py -3.10 build_images.py
Requires Pillow in ../_photo_deps. Original exports remain local and are not
included in the GitHub Pages build.
"""

from __future__ import annotations

import json
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "_photo_deps"))

from PIL import ExifTags, Image, ImageOps  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
PHOTOS = ROOT / "photos"
PREVIEWS = PHOTOS / "previews"
PREVIEWS.mkdir(parents=True, exist_ok=True)
SUPPORTED = {".jpg", ".jpeg", ".avif"}
PREFERRED_ALBUMS = ("original", "Italy", "budapest", "from_plane", "germany")


def number(value: object) -> float | None:
    try:
        result = float(value)
        return result if result > 0 else None
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def shutter_label(value: object) -> str | None:
    seconds = number(value)
    if seconds is None:
        return None
    if seconds < 0.5:
        denominator = round(1 / seconds)
        if denominator > 0:
            return f"1/{denominator} 秒"
    fraction = Fraction(seconds).limit_denominator(100)
    display = (f"{seconds:.1f}".rstrip("0").rstrip(".") if fraction.denominator != 1
               else str(fraction.numerator))
    return f"{display} 秒"


def exposure_data(exif: Image.Exif) -> dict[str, object]:
    top = {ExifTags.TAGS.get(tag, tag): value for tag, value in exif.items()}
    detail = {ExifTags.TAGS.get(tag, tag): value for tag, value in exif.get_ifd(ExifTags.IFD.Exif).items()}
    aperture = number(detail.get("FNumber"))
    focal = number(detail.get("FocalLength"))
    iso = number(detail.get("ISOSpeedRatings") or detail.get("PhotographicSensitivity"))
    return {
        "shutter": shutter_label(detail.get("ExposureTime")),
        "aperture": f"f/{aperture:g}" if aperture else None,
        "iso": round(iso) if iso else None,
        "focalLength": f"{focal:g} mm" if focal else None,
        "camera": str(top.get("Model", "")).strip() or None,
        "lens": str(detail.get("LensModel", "")).strip() or None,
    }


album_folders = sorted(
    (p for p in PHOTOS.iterdir() if p.is_dir() and p != PREVIEWS),
    key=lambda p: (PREFERRED_ALBUMS.index(p.name) if p.name in PREFERRED_ALBUMS else len(PREFERRED_ALBUMS), p.name.casefold()),
)
sources = [
    (album, source)
    for album in album_folders
    for source in sorted(album.iterdir(), key=lambda p: p.name.casefold())
    if source.is_file() and source.suffix.lower() in SUPPORTED
]
if not sources:
    raise SystemExit(f"No JPG or AVIF exports in album folders below {PHOTOS}")

records: list[dict[str, object]] = []
expected: set[str] = set()
album_counts: dict[str, int] = {}
for number_in_set, (album, source) in enumerate(sources, 1):
    album_counts[album.name] = album_counts.get(album.name, 0) + 1
    stem = f"{album_counts[album.name]:02d}"
    photo_id = stem if album.name == "original" else f"{album.name}-{stem}"
    album_previews = PREVIEWS / album.name
    album_previews.mkdir(exist_ok=True)
    with Image.open(source) as raw:
        exposure = exposure_data(raw.getexif())
        image = ImageOps.exif_transpose(raw).convert("RGB")
    width, height = image.size

    detail = image.copy()
    detail.thumbnail((4800, 3600), Image.Resampling.LANCZOS)
    detail_name = f"{stem}-detail.webp"
    detail.save(album_previews / detail_name, "WEBP", quality=86, method=5)

    view = detail.copy()
    view.thumbnail((2200, 1600), Image.Resampling.LANCZOS)
    view_name = f"{stem}-view.webp"
    view.save(album_previews / view_name, "WEBP", quality=85, method=6)

    thumb = view.copy()
    thumb.thumbnail((800, 600), Image.Resampling.LANCZOS)
    thumb_name = f"{stem}-thumb.webp"
    thumb.save(album_previews / thumb_name, "WEBP", quality=82, method=6)
    expected.update(f"{album.name}/{name}" for name in (detail_name, view_name, thumb_name))

    records.append({
        "id": photo_id,
        "album": album.name,
        "original": source.name,
        "src": f"photos/previews/{album.name}/{view_name}",
        "detail": f"photos/previews/{album.name}/{detail_name}",
        "thumb": f"photos/previews/{album.name}/{thumb_name}",
        "width": width,
        "height": height,
        "exposure": exposure,
    })
    print(f"{number_in_set}/{len(sources)} {album.name}/{source.name}", flush=True)

for old in PREVIEWS.rglob("*.webp"):
    relative = old.relative_to(PREVIEWS).as_posix()
    if re.fullmatch(r"\d+-(?:detail|view|thumb)\.webp", old.name) and relative not in expected:
        old.unlink()

(ROOT / "photos.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Built {len(records)} photographs in {PREVIEWS}", flush=True)
