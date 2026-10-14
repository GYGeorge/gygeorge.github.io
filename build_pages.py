"""Generate real collection pages and navigation from the public manifest."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote
from build_stats import generate_statistics

ROOT = Path(__file__).resolve().parent


def generate_pages() -> None:
    photos = json.loads((ROOT / "photos.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "collection_config.json").read_text(encoding="utf-8"))
    present = list(dict.fromkeys(photo["album"] for photo in photos))
    for album in present:
        config.setdefault(album, {"title": album, "description": "旅途中的摄影作品。", "route": quote(album, safe="")})
    albums = [album for album in config if album in present]
    homepage = (ROOT / "index.html").read_text(encoding="utf-8")
    dialog = re.search(r"<dialog\b.*?</dialog>", homepage, re.S).group(0)
    head = re.search(r"<head>(.*?)</head>", homepage, re.S).group(1)
    head = head.replace('href="styles.css', 'href="../../styles.css').replace('src="app.js', 'src="../../app.js')
    escape = html.escape

    def menu(base: str) -> str:
        links = []
        for album in albums:
            total = sum(photo["album"] == album for photo in photos)
            links.append(f'<a href="{base}collections/{config[album]["route"]}/"><span>{escape(config[album]["title"])}</span><small>{total} 张</small></a>')
        links.append(f'<a href="{base}collections/all/"><span>全部照片</span><small>{len(photos)} 张</small></a>')
        return "\n".join(links)

    def settings(photo: dict) -> str:
        exif = photo.get("exposure", {})
        parts = [f'ISO {exif["iso"]}' if exif.get("iso") else None,
                 exif.get("shutter"), exif.get("aperture"), exif.get("focalLength")]
        return " · ".join(filter(None, parts)) or "拍摄参数未保留"

    def photo_card(photo: dict) -> str:
        name = escape(Path(photo["original"]).stem)
        return f'''<a class="gallery-card" href="../../{escape(photo['detail'])}">
          <span class="image-wrap"><img src="../../{escape(photo['thumb'])}" alt="{name}" loading="lazy" width="{photo['width']}" height="{photo['height']}" />
          <span class="gallery-exposure">{escape(settings(photo))}</span></span>
          <span class="gallery-card-meta"><strong>{name}</strong></span></a>'''

    # These links work immediately, before the shared gallery script loads.
    homepage = re.sub(r'(<div class="collection-menu-list" id="album-menu-list">).*?(</div>)',
                      lambda match: match[1] + menu("") + match[2], homepage, flags=re.S)
    # Alternate locations and orientations instead of showing whole folders in sequence.
    lead_ids = ("germany-03", "08", "from_plane-04", "01", "Italy-08", "germany-13",
                "budapest-01", "germany-10", "03", "04", "05", "Italy-01", "18",
                "budapest-10", "16", "11", "12", "Italy-10", "09")
    by_id = {photo["id"]: photo for photo in photos}
    ordered = [by_id[photo_id] for photo_id in lead_ids if photo_id in by_id]
    used = {photo["id"] for photo in ordered}
    queues = [[photo for photo in photos if photo["album"] == album and photo["id"] not in used] for album in albums]
    while any(queues):
        for queue in queues:
            if queue:
                ordered.append(queue.pop(0))
    wall_rows = []
    position = 0
    while position < len(ordered):
        row = []
        ratio = 0.0
        while position < len(ordered):
            photo = ordered[position]
            next_ratio = photo["width"] / photo["height"]
            if row and abs(1 / ratio - 1 / 3.1) <= abs(1 / (ratio + next_ratio) - 1 / 3.1):
                break
            loading = "eager" if position < 3 else "lazy"
            row.append(f'''<a class="home-photo" href="{escape(photo['detail'])}" style="flex-grow:{next_ratio:.6f}"><img src="{escape(photo['src'])}" alt="{escape(Path(photo['original']).stem)}" width="{photo['width']}" height="{photo['height']}" loading="{loading}" decoding="async" /></a>''')
            ratio += next_ratio
            position += 1
        wall_rows.append('<div class="photo-row">' + "".join(row) + '</div>')
    wall = '<div class="home-gallery" id="home-gallery" aria-label="摄影作品" data-photo-order="' + ' '.join(photo["id"] for photo in ordered) + '">' + '\n'.join(wall_rows) + '</div>'
    homepage = re.sub(r'<!-- HOME-GALLERY-START -->.*?<!-- HOME-GALLERY-END -->',
                      lambda match: '<!-- HOME-GALLERY-START -->' + wall + '<!-- HOME-GALLERY-END -->', homepage, flags=re.S)
    (ROOT / "index.html").write_text(homepage, encoding="utf-8")

    for album in [*albums, "all"]:
        info = config.get(album, {"title": "全部照片", "description": "从所有系列中慢慢看。", "route": "all"})
        rows = photos if album == "all" else [photo for photo in photos if photo["album"] == album]
        page_head = re.sub(r"<title>.*?</title>", f'<title>{escape(info["title"])} · gao yuan</title>', head)
        page_head = re.sub(r'<meta name="description" content="[^"]*" />',
                           f'<meta name="description" content="{escape(info["description"], quote=True)}" />', page_head)
        page = f'''<!doctype html>
<html lang="zh-CN"><head>{page_head}</head>
<body class="collection-page" data-album="{escape(album)}">
  <a class="skip-link" href="#main">跳到内容</a>
  <header class="site-header minimal-header">
    <a class="site-name" href="../../">gao yuan</a>
    <nav class="main-nav" aria-label="主导航">
      <details class="collection-menu" id="collection-menu"><summary>作品集</summary><div class="collection-menu-list" id="album-menu-list">{menu('../../')}</div></details>
      <a href="../../parameters/">拍摄参数</a>
      </nav>
  </header>
  <main id="main"><section class="archive section-wrap" id="archive" aria-labelledby="archive-title">
    <div class="section-heading archive-heading"><div><p class="section-number">作品集 / {escape(album)}</p><h1 id="archive-title">{escape(info['title'])}。</h1></div><p id="archive-description">{escape(info['description'])}</p></div>
    <div id="album-gallery"><div class="album-gallery-top"><a class="album-back" href="../../">← 首页</a><span class="gallery-count" id="gallery-count">{len(rows)} PHOTOGRAPHS</span></div>
      <div class="gallery-grid" id="gallery-grid">{''.join(photo_card(photo) for photo in rows)}</div>
    </div>
  </section></main>
  {dialog}
</body></html>'''
        destination = ROOT / "collections" / info["route"]
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(page, encoding="utf-8")
    (ROOT / ".nojekyll").touch()
    generate_statistics(ROOT, photos, config, head.replace('../../', '../'), menu('../'), dialog)
    print(f"Generated {len(albums) + 1} independent collection pages")


if __name__ == "__main__":
    generate_pages()
