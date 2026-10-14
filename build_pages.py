"""Generate real collection pages and navigation from the public manifest."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

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
    cards = []
    for index, album in enumerate(albums, 1):
        info = config[album]
        rows = [photo for photo in photos if photo["album"] == album]
        cover = next((photo for photo in rows if photo["id"] == info.get("cover")), rows[0])
        cards.append(f'''<a class="album-card" data-album="{escape(album)}" href="collections/{info['route']}/">
          <img src="{escape(cover['src'])}" alt="{escape(info['title'])}" loading="lazy" />
          <span class="album-card-content"><small>{index:02d} / {escape(album)}</small><strong>{escape(info['title'])}</strong>
          <span>{escape(info['description'])}</span><em>{len(rows)} 张照片 ↗</em></span></a>''')
    homepage = re.sub(r'(<div class="album-grid" id="album-grid">).*?(</div>)',
                      lambda match: match[1] + "\n".join(cards) + match[2], homepage, flags=re.S)
    (ROOT / "index.html").write_text(homepage, encoding="utf-8")

    for album in [*albums, "all"]:
        info = config.get(album, {"title": "全部照片", "description": "从所有系列中慢慢看。", "route": "all"})
        rows = photos if album == "all" else [photo for photo in photos if photo["album"] == album]
        page_head = re.sub(r"<title>.*?</title>", f'<title>{escape(info["title"])} · 山与光</title>', head)
        page_head = re.sub(r'<meta name="description" content="[^"]*" />',
                           f'<meta name="description" content="{escape(info["description"], quote=True)}" />', page_head)
        page = f'''<!doctype html>
<html lang="zh-CN"><head>{page_head}</head>
<body class="collection-page" data-album="{escape(album)}">
  <a class="skip-link" href="#main">跳到内容</a>
  <header class="site-header" id="top">
    <a class="brand" href="../../"><span class="brand-mark" aria-hidden="true">△</span><span>山与光</span><small>FIELD NOTES</small></a>
    <nav class="main-nav" aria-label="主导航"><a href="../../">首页</a>
      <details class="collection-menu" id="collection-menu"><summary>作品集</summary><div class="collection-menu-list" id="album-menu-list">{menu('../../')}</div></details>
      <a href="../../#about">关于</a></nav>
    <a class="header-action" href="../../#archive">全部系列 ↗</a>
  </header>
  <main id="main"><section class="archive section-wrap" id="archive" aria-labelledby="archive-title">
    <div class="section-heading archive-heading"><div><p class="section-number">作品集 / {escape(album)}</p><h1 id="archive-title">{escape(info['title'])}。</h1></div><p id="archive-description">{escape(info['description'])}</p></div>
    <div id="album-gallery"><div class="album-gallery-top"><a class="album-back" href="../../#archive">← 全部系列</a><span class="gallery-count" id="gallery-count">{len(rows)} PHOTOGRAPHS</span></div>
      <div class="gallery-grid" id="gallery-grid">{''.join(photo_card(photo) for photo in rows)}</div>
    </div>
  </section></main>
  <footer class="site-footer"><a href="../../">山与光 · 个人摄影作品集</a><a href="#top">BACK TO TOP ↑</a></footer>
  {dialog}
</body></html>'''
        destination = ROOT / "collections" / info["route"]
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(page, encoding="utf-8")
    (ROOT / ".nojekyll").touch()
    print(f"Generated {len(albums) + 1} independent collection pages")


if __name__ == "__main__":
    generate_pages()
