# 山与光 · 个人摄影作品集

这是一个静态摄影网站，可部署到 GitHub Pages。首页、精选照片、主题筛选和大图浏览都在 `index.html`、`styles.css`、`app.js` 中。`photos.json` 是照片清单。

照片分三级：相册缩略图（最长边约 800px）、单张浏览图（最长边约 2200px）、细节图（最长边约 4800px）。点开照片先加载浏览图；点击「查看细节」后才下载细节图，可用按钮或滚轮缩放，拖动查看局部，手机上可双指缩放。上传到 GitHub 的只有压缩后的 WebP，不包含 NEF/TIFF 原片。

## 本地查看

在本文件夹运行 `py -3.10 -m http.server 8765`，然后打开 `http://127.0.0.1:8765/`。

## 更新照片

把新的 NEF/TIFF 原片放在此文件夹，运行 `py -3.10 build_images.py` 生成 `assets/photos/` 和 `photos.json`。随后在 `app.js` 的 `photoDetails` 中添加对应编号的标题、分类与替代文字。NEF 的 WebP 使用相机内嵌预览；若想让网站照片与 Capture One 调色完全一致，请从 Capture One 导出成品，再生成或替换对应的 `编号-thumb.webp`、`编号.webp` 和 `编号-detail.webp`。建议保留宽约 4800px 的成品供细节浏览。

## GitHub Pages

原始 NEF/TIFF 文件不应上传到 GitHub；`.gitignore` 已排除它们。此站点使用 `gygeorge/gygeorge.github.io` 仓库，推送到 `main` 后，在仓库 Settings → Pages 中选择 **GitHub Actions**。工作流会运行 `build_site.py`，只发布网页文件和压缩后的 WebP 图片。发布地址为 `https://gygeorge.github.io/`。

参考网站只借鉴了作品系列与完整照片索引的浏览结构；本页的文案、版式和照片均独立制作。
