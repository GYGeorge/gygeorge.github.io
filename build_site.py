"""Package only the public website files into dist/ for GitHub Pages."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()

for name in ("index.html", "styles.css", "app.js", "photos.json"):
    shutil.copy2(ROOT / name, DIST / name)

source_previews = ROOT / "photos" / "previews"
destination_photos = DIST / "photos"
if destination_photos.exists():
    shutil.rmtree(destination_photos)
shutil.copytree(source_previews, destination_photos / "previews")
(DIST / ".nojekyll").touch()

print(f"Ready: {DIST} (original JPGs excluded)")
