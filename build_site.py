"""Package only the public website files into dist/ for GitHub Pages."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

for name in ("index.html", "styles.css", "app.js", "photos.json"):
    shutil.copy2(ROOT / name, DIST / name)

source_assets = ROOT / "assets"
destination_assets = DIST / "assets"
if destination_assets.exists():
    shutil.rmtree(destination_assets)
shutil.copytree(source_assets, destination_assets)
(DIST / ".nojekyll").touch()

print(f"Ready: {DIST}")
