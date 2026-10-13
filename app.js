const photoDetails = {
  "01": { title: "云遮山影", category: "water", alt: "云雾遮住岩峰，山影倒映在平静的湖面" },
  "02": { title: "城中暮色", category: "journey", alt: "暮色中的城市建筑与灯光" },
  "03": { title: "湖边的群山", category: "water", alt: "高山、湖畔建筑与湖水中的倒影" },
  "04": { title: "谷底的河", category: "water", alt: "黑白山谷中一条明亮的河流蜿蜒向远方" },
  "05": { title: "石塔", category: "mountain", alt: "黑白岩峰和山坡上的光影" },
  "06": { title: "群峰之间", category: "mountain", alt: "蓝天下的岩峰与近处草坡" },
  "07": { title: "云后有山", category: "mountain", alt: "高山在云与层层山坡之后" },
  "08": { title: "山脊上的路", category: "mountain", alt: "近处断崖与小路指向云中的远峰" },
  "09": { title: "云影下的高原", category: "mountain", alt: "积云下的远山与草坡" },
  "10": { title: "山谷晨光", category: "mountain", alt: "晨光从山谷一侧照向谷地" },
  "11": { title: "山间小屋", category: "journey", alt: "阳光下山间草坡的小木屋" },
  "12": { title: "窗外雪山", category: "journey", alt: "从室内窗口望向远处的雪山" },
  "13": { title: "粉色黄昏", category: "journey", alt: "黄昏的粉色云彩和山脚小屋" },
  "14": { title: "蓝调山路", category: "journey", alt: "蓝色暮光下通向山间建筑的道路" },
  "15": { title: "云层下的光", category: "mountain", alt: "云层透出光线，照亮远处山峰" },
  "16": { title: "雾中山峰", category: "mountain", alt: "蓝色云雾间露出的山峰" },
  "17": { title: "云海中的峰", category: "mountain", alt: "冷蓝色云海中露出的山峰" },
  "18": { title: "星河之下", category: "night", alt: "银河悬在山谷与草地上空" },
};

const categoryNames = {
  mountain: "山峦",
  water: "水与云",
  journey: "路上",
  night: "夜空",
};

const grid = document.getElementById("gallery-grid");
const count = document.getElementById("gallery-count");
const filters = [...document.querySelectorAll(".filter")];
const dialog = document.getElementById("lightbox");
const lightboxImage = document.getElementById("lightbox-image");
const lightboxStage = document.getElementById("lightbox-stage");
const zoomButton = document.getElementById("lightbox-zoom");
const minusButton = document.getElementById("lightbox-minus");
const plusButton = document.getElementById("lightbox-plus");
const zoomLevel = document.getElementById("lightbox-zoom-level");
const lightboxTitle = document.getElementById("lightbox-title");
const lightboxFile = document.getElementById("lightbox-file");
const lightboxExposure = document.getElementById("lightbox-exposure");
const lightboxGear = document.getElementById("lightbox-gear");
const lightboxPosition = document.getElementById("lightbox-position");
let photos = [];
let visiblePhotos = [];
let currentIndex = 0;
let returnFocus = null;
let zoomScale = 1;
let offsetX = 0;
let offsetY = 0;
let detailLoaded = false;
let detailRequest = 0;
let panStart = null;
let pinchStart = null;
const pointers = new Map();

function cameraSettings(photo) {
  const exif = photo.exposure || {};
  const parts = [exif.iso && `ISO ${exif.iso}`, exif.shutter, exif.aperture, exif.focalLength].filter(Boolean);
  return parts.length ? parts.join("  ·  ") : "拍摄参数未保留";
}

function cameraGear(photo) {
  const exif = photo.exposure || {};
  return [exif.camera, exif.lens].filter(Boolean).join("  ·  ");
}

function updateZoom() {
  const maxX = Math.max(0, (lightboxImage.offsetWidth * zoomScale - lightboxStage.clientWidth) / 2);
  const maxY = Math.max(0, (lightboxImage.offsetHeight * zoomScale - lightboxStage.clientHeight) / 2);
  offsetX = Math.max(-maxX, Math.min(maxX, offsetX));
  offsetY = Math.max(-maxY, Math.min(maxY, offsetY));
  lightboxImage.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${zoomScale})`;
  lightboxStage.classList.toggle("is-zoomed", zoomScale > 1);
  zoomLevel.textContent = zoomScale === 1 ? "适应屏幕" : `${zoomScale.toFixed(1)}×`;
  zoomButton.textContent = zoomScale === 1 ? "查看细节" : "返回全图";
  zoomButton.setAttribute("aria-pressed", String(zoomScale > 1));
  minusButton.disabled = !detailLoaded || zoomScale <= 1;
  plusButton.disabled = !detailLoaded || zoomScale >= 4;
}

function setZoom(scale) {
  zoomScale = Math.max(1, Math.min(4, scale));
  if (zoomScale === 1) offsetX = offsetY = 0;
  updateZoom();
}

function resetZoom() {
  zoomScale = 1;
  offsetX = offsetY = 0;
  detailLoaded = false;
  panStart = pinchStart = null;
  pointers.clear();
  lightboxStage.classList.remove("is-dragging");
  zoomButton.disabled = false;
  updateZoom();
}

function loadDetail() {
  if (detailLoaded) {
    setZoom(2);
    return;
  }
  const photo = visiblePhotos[currentIndex];
  const request = ++detailRequest;
  zoomButton.disabled = true;
  zoomButton.textContent = "加载高清…";
  const image = new Image();
  image.onload = () => {
    if (request !== detailRequest || !dialog.open) return;
    detailLoaded = true;
    lightboxImage.src = photo.detail;
    zoomButton.disabled = false;
    setZoom(2);
  };
  image.onerror = () => {
    if (request !== detailRequest) return;
    zoomButton.disabled = false;
    zoomButton.textContent = "重试高清";
  };
  image.src = photo.detail;
}

function cardFor(photo) {
  const button = document.createElement("button");
  button.className = "gallery-card";
  button.type = "button";
  button.dataset.photoId = photo.id;
  button.setAttribute("aria-label", `查看照片：${photo.title}`);

  const imageWrap = document.createElement("span");
  imageWrap.className = "image-wrap";
  const image = document.createElement("img");
  image.src = photo.thumb;
  image.alt = photo.alt;
  image.loading = "lazy";
  image.decoding = "async";
  image.width = photo.width;
  image.height = photo.height;
  imageWrap.append(image);
  const exposure = document.createElement("span");
  exposure.className = "gallery-exposure";
  exposure.textContent = cameraSettings(photo);
  imageWrap.append(exposure);

  const meta = document.createElement("span");
  meta.className = "gallery-card-meta";
  const title = document.createElement("strong");
  title.textContent = photo.title;
  const category = document.createElement("small");
  category.textContent = categoryNames[photo.category];
  meta.append(title, category);
  button.append(imageWrap, meta);
  button.addEventListener("click", () => openPhoto(photo.id, button));
  return button;
}

function renderGallery(filter = "all") {
  visiblePhotos = filter === "all" ? photos : photos.filter((photo) => photo.category === filter);
  grid.replaceChildren(...visiblePhotos.map(cardFor));
  count.textContent = `${String(visiblePhotos.length).padStart(2, "0")} PHOTOGRAPHS`;
  filters.forEach((button) => {
    const active = button.dataset.filter === filter;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function showPhoto(index) {
  detailRequest++;
  resetZoom();
  currentIndex = (index + visiblePhotos.length) % visiblePhotos.length;
  const photo = visiblePhotos[currentIndex];
  lightboxImage.src = photo.src;
  lightboxImage.alt = photo.alt;
  lightboxTitle.textContent = photo.title;
  lightboxFile.textContent = photo.original;
  lightboxExposure.textContent = cameraSettings(photo);
  lightboxGear.textContent = cameraGear(photo);
  lightboxPosition.textContent = `${String(currentIndex + 1).padStart(2, "0")} / ${String(visiblePhotos.length).padStart(2, "0")}`;
}

function openPhoto(id, trigger) {
  const inCurrentList = visiblePhotos.findIndex((photo) => photo.id === id);
  if (inCurrentList < 0) visiblePhotos = photos;
  returnFocus = trigger;
  showPhoto(visiblePhotos.findIndex((photo) => photo.id === id));
  dialog.showModal();
  document.body.style.overflow = "hidden";
  document.getElementById("lightbox-close").focus();
}

filters.forEach((button) => button.addEventListener("click", () => renderGallery(button.dataset.filter)));
document.querySelectorAll(".feature-card").forEach((button) => {
  button.addEventListener("click", () => openPhoto(button.dataset.photoId, button));
});
document.getElementById("lightbox-close").addEventListener("click", () => dialog.close());
document.getElementById("lightbox-prev").addEventListener("click", () => showPhoto(currentIndex - 1));
document.getElementById("lightbox-next").addEventListener("click", () => showPhoto(currentIndex + 1));
zoomButton.addEventListener("click", () => zoomScale > 1 ? setZoom(1) : loadDetail());
minusButton.addEventListener("click", () => setZoom(zoomScale - 0.5));
plusButton.addEventListener("click", () => setZoom(zoomScale + 0.5));
lightboxStage.addEventListener("wheel", (event) => {
  event.preventDefault();
  if (!detailLoaded) {
    if (event.deltaY < 0 && !zoomButton.disabled) loadDetail();
    return;
  }
  setZoom(zoomScale + (event.deltaY < 0 ? 0.25 : -0.25));
}, { passive: false });
lightboxStage.addEventListener("pointerdown", (event) => {
  if (zoomScale <= 1) return;
  lightboxStage.setPointerCapture(event.pointerId);
  pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (pointers.size === 1) {
    panStart = { id: event.pointerId, x: event.clientX, y: event.clientY, offsetX, offsetY };
    lightboxStage.classList.add("is-dragging");
  } else if (pointers.size === 2) {
    const [a, b] = [...pointers.values()];
    pinchStart = { distance: Math.hypot(a.x - b.x, a.y - b.y), scale: zoomScale };
    panStart = null;
  }
});
lightboxStage.addEventListener("pointermove", (event) => {
  if (!pointers.has(event.pointerId)) return;
  pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (pointers.size === 2 && pinchStart) {
    const [a, b] = [...pointers.values()];
    setZoom(pinchStart.scale * Math.hypot(a.x - b.x, a.y - b.y) / pinchStart.distance);
  } else if (pointers.size === 1 && panStart?.id === event.pointerId) {
    offsetX = panStart.offsetX + event.clientX - panStart.x;
    offsetY = panStart.offsetY + event.clientY - panStart.y;
    updateZoom();
  }
});
function endPointer(event) {
  pointers.delete(event.pointerId);
  pinchStart = null;
  panStart = null;
  if (pointers.size === 1) {
    const [id, point] = [...pointers.entries()][0];
    panStart = { id, x: point.x, y: point.y, offsetX, offsetY };
  } else {
    lightboxStage.classList.remove("is-dragging");
  }
}
lightboxStage.addEventListener("pointerup", endPointer);
lightboxStage.addEventListener("pointercancel", endPointer);
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
dialog.addEventListener("close", () => {
  detailRequest++;
  resetZoom();
  document.body.style.overflow = "";
  returnFocus?.focus();
});
document.addEventListener("keydown", (event) => {
  if (!dialog.open) return;
  if (event.key === "ArrowLeft") showPhoto(currentIndex - 1);
  if (event.key === "ArrowRight") showPhoto(currentIndex + 1);
  if (event.key === "+" || event.key === "=") detailLoaded ? setZoom(zoomScale + 0.5) : loadDetail();
  if (event.key === "-") setZoom(zoomScale - 0.5);
  if (event.key === "0") setZoom(1);
});

fetch("photos.json")
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((records) => {
    photos = records.map((record) => ({ ...record, ...photoDetails[record.id] }));
    const featured = document.querySelectorAll(".feature-card");
    featured.forEach((card) => {
      const photo = photos.find((item) => item.id === card.dataset.photoId);
      const label = card.querySelector(".feature-exposure");
      if (photo && label) label.textContent = cameraSettings(photo);
    });
    const hero = photos.find((item) => item.id === "08");
    if (hero) document.getElementById("hero-exposure").textContent = cameraSettings(hero);
    const closing = photos.find((item) => item.id === "11");
    if (closing) document.getElementById("closing-exposure").textContent = cameraSettings(closing);
    renderGallery();
  })
  .catch(() => {
    count.textContent = "照片暂时无法加载";
  });
