# 山与光 · 个人摄影作品集

这是部署在 [gygeorge.github.io](https://gygeorge.github.io/) 的静态摄影网站。首页与各作品集有独立的 HTML 页面；`app.js` 为照片增加大图、高清缩放和参数展示。`photos.json` 包含照片清单及从成片 EXIF 读取的拍摄参数。

## 更新照片

把最终导出的 JPG 或 AVIF 放在 `photos/` 下的作品集文件夹，例如 `photos/Italy/`、`photos/budapest/`。每个文件夹会成为网站中的独立作品集；原有 18 张照片保留在 `photos/original/`。运行 `py -3.10 build_images.py` 后，脚本按文件夹和文件名排序，为每张图在 `photos/previews/<文件夹名>/` 生成三种 WebP：缩略图（最长约 800px）、普通查看图（约 2200px）和按需加载的细节图（约 4800px）。它同时重建带作品集归属的 `photos.json`。原始 JPG/AVIF 只留在本机，不会进入 Git 或 GitHub Pages。

作品集的中文名称、简介、封面和页面地址在 `collection_config.json` 中维护。`build_pages.py` 生成首页的实际链接以及 `collections/<地址>/index.html`；菜单、封面和照片缩略图在脚本加载前就可以显示。照片标题在 `app.js` 的 `photoDetails` 和 `albumPhotoTitles` 中维护。首页精选图片使用固定编号，调整顺序或替换照片时也要同步检查 `index.html` 中的精选与首页图片编号。

独立页面：布达佩斯 `/collections/budapest/`、德国 `/collections/germany/`、意大利 `/collections/italy/`、山水风光 `/collections/landscapes/`、舷窗之外 `/collections/from-plane/`，以及全部照片 `/collections/all/`。

网站从 JPG 的 EXIF 读取 ISO、快门、光圈、焦距、机身和镜头信息。若导出时这些信息已被清除，网页会显示“拍摄参数未保留”，不会推测数值。公开的 `photos.json` 不包含 GPS、相机序列号等 EXIF 字段。

## 本地查看与发布

更新照片后运行 `py -3.10 build_site.py`，它会先更新独立页面，再生成待发布的 `dist/`；其中只有网页文件和 `photos/previews/`，不含任何原始照片文件夹。在本文件夹运行 `py -3.10 -m http.server 8765`，然后打开 `http://127.0.0.1:8765/`。

站点使用 [GYGeorge/gygeorge.github.io](https://github.com/GYGeorge/gygeorge.github.io) 仓库。推送到 `main` 后，GitHub Actions 会运行 `build_site.py` 并发布到 GitHub Pages。
