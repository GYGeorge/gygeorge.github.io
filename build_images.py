"""Create web previews and a safe EXIF manifest from photos/original/*.jpg.

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
ORIGINALS = ROOT / "photos" / "original"
PREVIEWS = ROOT / "photos" / "previews"
PREVIEWS.mkdir(parents=True, exist_ok=True)


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


sources = sorted(
    (p for p in ORIGINALS.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"}),
    key=lambda p: p.name.casefold(),
)
if not sources:
    raise SystemExit(f"No JPG exports in {ORIGINALS}")

records: list[dict[str, object]] = []
expected: set[str] = set()
for number_in_set, source in enumerate(sources, 1):
    stem = f"{number_in_set:02d}"
    with Image.open(source) as raw:
        exposure = exposure_data(raw.getexif())
        image = ImageOps.exif_transpose(raw).convert("RGB")
    width, height = image.size

    detail = image.copy()
    detail.thumbnail((4800, 3600), Image.Resampling.LANCZOS)
    detail_name = f"{stem}-detail.webp"
    detail.save(PREVIEWS / detail_name, "WEBP", quality=86, method=5)

    view = detail.copy()
    view.thumbnail((2200, 1600), Image.Resampling.LANCZOS)
    view_name = f"{stem}-view.webp"
    view.save(PREVIEWS / view_name, "WEBP", quality=85, method=6)

    thumb = view.copy()
    thumb.thumbnail((800, 600), Image.Resampling.LANCZOS)
    thumb_name = f"{stem}-thumb.webp"
    thumb.save(PREVIEWS / thumb_name, "WEBP", quality=82, method=6)
    expected.update((detail_name, view_name, thumb_name))

    records.append({
        "id": stem,
        "original": source.name,
        "src": f"photos/previews/{view_name}",
        "detail": f"photos/previews/{detail_name}",
        "thumb": f"photos/previews/{thumb_name}",
        "width": width,
        "height": height,
        "exposure": exposure,
    })
    print(f"{number_in_set}/{len(sources)} {source.name}", flush=True)

for old in PREVIEWS.glob("*.webp"):
    if re.fullmatch(r"\d+-(?:detail|view|thumb)\.webp", old.name) and old.name not in expected:
        old.unlink()

(ROOT / "photos.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Built {len(records)} photographs in {PREVIEWS}", flush=True)
