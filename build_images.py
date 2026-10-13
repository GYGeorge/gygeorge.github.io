"""Build three browser-friendly image sizes from the originals in this folder.

Run with: py -3.10 build_images.py
Requires Pillow and rawpy (available in the workspace's _photo_deps folder).
The NEF previews use the camera-embedded JPEG, so export final Capture One
edits separately when an exact match to the developed image is needed.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "_photo_deps"))

from PIL import Image, ImageDraw, ImageFont, ImageOps  # noqa: E402
import rawpy  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
OUT = ROOT / "assets" / "photos"
OUT.mkdir(parents=True, exist_ok=True)


def load_photo(path: Path) -> Image.Image:
    if path.suffix.lower() == ".nef":
        with rawpy.imread(str(path)) as raw:
            thumb = raw.extract_thumb()
        if thumb.format == rawpy.ThumbFormat.JPEG:
            im = Image.open(io.BytesIO(thumb.data))
        else:
            im = Image.fromarray(thumb.data)
    else:
        im = Image.open(path)
    return ImageOps.exif_transpose(im).convert("RGB")


sources = sorted(
    (p for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in {".nef", ".tif", ".tiff"}),
    key=lambda p: p.name.casefold(),
)
records: list[dict] = []
contact = Image.new("RGB", (1600, ((len(sources) + 3) // 4) * 300), "#17191d")
draw = ImageDraw.Draw(contact)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
except OSError:
    font = ImageFont.load_default()

for number, source in enumerate(sources, 1):
    im = load_photo(source)
    width, height = im.size
    stem = f"{number:02d}"
    full = im.copy()
    full.thumbnail((2200, 1600), Image.Resampling.LANCZOS)
    full.save(OUT / f"{stem}.webp", "WEBP", quality=85, method=6)
    detail = im.copy()
    detail.thumbnail((4800, 3600), Image.Resampling.LANCZOS)
    detail.save(OUT / f"{stem}-detail.webp", "WEBP", quality=86, method=5)
    thumb = im.copy()
    thumb.thumbnail((800, 600), Image.Resampling.LANCZOS)
    thumb.save(OUT / f"{stem}-thumb.webp", "WEBP", quality=82, method=6)
    preview = im.copy()
    preview.thumbnail((380, 250), Image.Resampling.LANCZOS)
    x = ((number - 1) % 4) * 400
    y = ((number - 1) // 4) * 300
    contact.paste(preview, (x + (400 - preview.width) // 2, y + (250 - preview.height) // 2))
    draw.text((x + 12, y + 258), f"{stem}  {source.name}", fill="#f3eee7", font=font)
    records.append(
        {
            "id": stem,
            "original": source.name,
            "src": f"assets/photos/{stem}.webp",
            "detail": f"assets/photos/{stem}-detail.webp",
            "thumb": f"assets/photos/{stem}-thumb.webp",
            "width": width,
            "height": height,
            "format": source.suffix[1:].upper(),
        }
    )
    print(f"{number}/{len(sources)} {source.name}", flush=True)

(ROOT / "photos.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
contact.save(ROOT / "_contact.jpg", quality=88)
print(f"Built {len(records)} photographs", flush=True)
