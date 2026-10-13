const photoDetails = {
  "01": { title: "风过山脊 · I", category: "mountain", alt: "云雾掠过有小路的高山山脊" },
  "02": { title: "风过山脊 · II", category: "mountain", alt: "云雾中的尖峰与山脊小路" },
  "03": { title: "低云与湖", category: "water", alt: "低云覆盖山体，前方湖水映出山影" },
  "04": { title: "水城暮光", category: "journey", alt: "傍晚的运河与两岸建筑" },
  "05": { title: "湖边的群山", category: "water", alt: "高山、湖畔建筑与清晰的水中倒影" },
  "06": { title: "向谷底", category: "mountain", alt: "两侧岩壁之间延伸到远方的山谷" },
  "07": { title: "石塔", category: "mountain", alt: "近处灌木和远方的高耸岩峰" },
  "08": { title: "三峰", category: "mountain", alt: "蓝天下三座雄伟岩峰的轮廓" },
  "09": { title: "雾中山脊", category: "mountain", alt: "浓雾里通向远处的山脊步道" },
  "10": { title: "云后有山", category: "water", alt: "厚云下蓝灰色的远山和谷地" },
  "11": { title: "山与湖之间", category: "water", alt: "云影压在山间湖泊与草坡之上" },
  "12": { title: "蓝色层峦", category: "mountain", alt: "一层层蓝色山峦延伸向远方" },
  "13": { title: "远山层叠", category: "mountain", alt: "逆光下起伏的山坡与层叠远山" },
  "14": { title: "山脊上的路", category: "mountain", alt: "近处断崖与小路指向云中的远峰" },
  "15": { title: "秋树", category: "journey", alt: "一棵金黄的秋树在深色森林前发光" },
  "16": { title: "云影下的高原", category: "water", alt: "云影下的草坡、树林和远处山峰" },
  "17": { title: "山间小屋", category: "journey", alt: "阳光下山间草坡的小木屋" },
  "18": { title: "星河之下", category: "night", alt: "银河悬在山谷与草地上空" },
  "19": { title: "风过山脊 · III", category: "mountain", alt: "云雾绕过高山和山脊" },
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
    renderGallery();
  })
  .catch(() => {
    count.textContent = "照片暂时无法加载";
  });
