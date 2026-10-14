# 山与光 · 个人摄影作品集

这是部署在 [gygeorge.github.io](https://gygeorge.github.io/) 的静态摄影网站。首页、精选照片、主题筛选和大图浏览分别由 `index.html`、`styles.css`、`app.js` 实现。`photos.json` 包含照片清单及从成片 EXIF 读取的拍摄参数。

## 更新照片

把最终导出的 JPG 或 AVIF 放在 `photos/` 下的作品集文件夹，例如 `photos/Italy/`、`photos/budapest/`。每个文件夹会成为网站中的独立作品集；原有 18 张照片保留在 `photos/original/`。运行 `py -3.10 build_images.py` 后，脚本按文件夹和文件名排序，为每张图在 `photos/previews/<文件夹名>/` 生成三种 WebP：缩略图（最长约 800px）、普通查看图（约 2200px）和按需加载的细节图（约 4800px）。它同时重建带作品集归属的 `photos.json`。原始 JPG/AVIF 只留在本机，不会进入 Git 或 GitHub Pages。

作品集的中文名称、简介、封面在 `app.js` 的 `albumDetails` 中维护；新文件夹若没有配置，会先按文件夹名显示。照片标题在 `photoDetails` 和 `albumPhotoTitles` 中维护。首页精选图片使用固定编号，调整顺序或替换照片时也要同步检查 `index.html` 中的精选与首页图片编号。

网站从 JPG 的 EXIF 读取 ISO、快门、光圈、焦距、机身和镜头信息。若导出时这些信息已被清除，网页会显示“拍摄参数未保留”，不会推测数值。公开的 `photos.json` 不包含 GPS、相机序列号等 EXIF 字段。

## 本地查看与发布

在本文件夹运行 `py -3.10 -m http.server 8765`，然后打开 `http://127.0.0.1:8765/`。运行 `py -3.10 build_site.py` 可生成待发布的 `dist/`；其中只有网页文件和 `photos/previews/`，不含任何原始照片文件夹。

站点使用 [GYGeorge/gygeorge.github.io](https://github.com/GYGeorge/gygeorge.github.io) 仓库。推送到 `main` 后，GitHub Actions 会运行 `build_site.py` 并发布到 GitHub Pages。
