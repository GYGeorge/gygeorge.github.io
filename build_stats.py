"""Generate the photograph settings log and four stacked SVG bar charts."""

from __future__ import annotations

import html
import math
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path

METRICS = (("aperture", "光圈"), ("shutter", "快门"), ("focalLength", "焦距"), ("iso", "ISO 感光度"))


def numeric_value(value: object) -> float:
    text = str(value).replace("f/", "").replace(" 秒", "").replace(" mm", "")
    return float(Fraction(text))


def distribution(photos: list[dict], field: str) -> tuple[list[tuple[str, int]], int]:
    counts = Counter(str(photo.get("exposure", {}).get(field)) for photo in photos if photo.get("exposure", {}).get(field) is not None)
    values = sorted(counts.items(), key=lambda pair: numeric_value(pair[0]))
    return values, len(photos) - sum(counts.values())


def chart_svg(field: str, title: str, values: list[tuple[str, int]]) -> str:
    escape = html.escape
    width, height = 900, 330
    left, right, top, bottom = 48, 20, 30, 92
    plot_width, plot_height = width - left - right, height - top - bottom
    maximum = max((count for _, count in values), default=1)
    step = 1 if maximum <= 5 else 2 if maximum <= 10 else 5 if maximum <= 25 else 10
    ceiling = max(step, math.ceil(maximum / step) * step)
    elements = [f'<title id="{field}-chart-title">{escape(title)}使用分布</title>', '<text class="axis-unit" x="0" y="15">照片数</text>']
    for tick in range(0, ceiling + 1, step):
        y = top + plot_height * (1 - tick / ceiling)
        elements.append(f'<line class="chart-gridline" x1="{left}" y1="{y:.2f}" x2="{width-right}" y2="{y:.2f}" />')
        elements.append(f'<text class="chart-tick" x="{left-12}" y="{y+4:.2f}" text-anchor="end">{tick}</text>')
    slot = plot_width / max(1, len(values))
    bar_width = min(76, slot * .65)
    for index, (label, count) in enumerate(values):
        center = left + slot * (index + .5)
        bar_height = plot_height * count / ceiling
        y = top + plot_height - bar_height
        short = label.replace(" 秒", " s").replace(" mm", "")
        elements.append(f'<rect class="chart-bar" data-value="{escape(label)}" data-count="{count}" x="{center-bar_width/2:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}"><title>{escape(label)}：{count} 张</title></rect>')
        elements.append(f'<text class="chart-count" x="{center:.2f}" y="{y-8:.2f}" text-anchor="middle">{count}</text>')
        elements.append(f'<text class="chart-label" transform="translate({center:.2f},{top+plot_height+17}) rotate(-48)" text-anchor="end">{escape(short)}</text>')
    unit = "mm" if field == "focalLength" else "ISO" if field == "iso" else ""
    elements.append(f'<text class="axis-unit" x="{width-right}" y="{height-5}" text-anchor="end">{unit}</text>')
    return f'<svg class="parameter-chart" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{field}-chart-title">' + "".join(elements) + "</svg>"


def generate_statistics(root: Path, photos: list[dict], config: dict, head: str, menu: str, dialog: str) -> None:
    escape = html.escape
    head = re.sub(r"<title>.*?</title>", "<title>拍摄参数 · gao yuan</title>", head)
    head = re.sub(r'<meta name="description" content="[^"]*" />', '<meta name="description" content="照片拍摄参数与使用分布" />', head)
    complete = sum(all(photo.get("exposure", {}).get(field) is not None for field, _ in METRICS) for photo in photos)
    charts = []
    for field, title in METRICS:
        values, missing = distribution(photos, field)
        charts.append(f'''<section class="parameter-chart-section" data-metric="{field}">
          <div class="parameter-chart-heading"><h2>{title}</h2><span>{len(photos)-missing} 张有记录 · {missing} 张未保留</span></div>
          <div class="chart-scroll" tabindex="0" aria-label="{title}分布柱状图，可横向滚动">{chart_svg(field, title, values)}</div>
        </section>''')
    rows = []
    for photo in photos:
        exposure = photo.get("exposure", {})
        cells = "".join(f'<td>{escape(str(exposure[field])) if exposure.get(field) is not None else "—"}</td>' for field, _ in METRICS)
        rows.append(f'''<tr data-photo-id="{escape(photo['id'])}"><td><a class="parameter-photo" data-photo-id="{escape(photo['id'])}" href="../{escape(photo['detail'])}" aria-label="查看照片：{escape(photo['original'])}"><img src="../{escape(photo['thumb'])}" alt="" width="64" height="48" loading="lazy" /></a></td>
          <th scope="row">{escape(photo['original'])}</th><td>{escape(config.get(photo['album'], {}).get('title', photo['album']))}</td>{cells}</tr>''')
    page = f'''<!doctype html>
<html lang="zh-CN"><head>{head}</head>
<body class="collection-page parameter-page">
  <a class="skip-link" href="#main">跳到内容</a>
  <header class="site-header minimal-header"><a class="site-name" href="../">gao yuan</a>
    <nav class="main-nav" aria-label="主导航"><details class="collection-menu" id="collection-menu"><summary>作品集</summary><div class="collection-menu-list" id="album-menu-list">{menu}</div></details><a href="./" aria-current="page">拍摄参数</a></nav>
  </header>
  <main id="main" class="parameter-main"><h1>拍摄参数</h1>
    <div class="parameter-summary"><span>{len(photos)} 张照片</span><span>{complete} 张参数完整</span><span>{len(photos)-complete} 张参数未完整保留</span></div>
    <div class="parameter-charts">{''.join(charts)}</div>
    <section class="parameter-log" aria-labelledby="parameter-log-title"><h2 id="parameter-log-title">全部照片</h2>
      <div class="table-scroll" tabindex="0" aria-label="所有照片的拍摄参数，可横向滚动"><table class="parameter-table"><thead><tr><th aria-label="照片预览"></th><th scope="col">照片</th><th scope="col">作品集</th><th scope="col">光圈</th><th scope="col">快门</th><th scope="col">焦距</th><th scope="col">ISO</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
    </section>
  </main>
  {dialog}
</body></html>'''
    destination = root / "parameters"
    destination.mkdir(exist_ok=True)
    (destination / "index.html").write_text(page, encoding="utf-8")
