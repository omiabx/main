// Pictures used inside the episode: Bob's portrait rendered from the real model, the 8x8 1-bit face,
// phone screen canvases (gallery, lunch, digits).
import * as THREE from 'three';
import { renderer } from './core.js';
import { character, pose } from './models.js';

// 8x8 one-bit Bob (hat + face + smile). 1 = light, 0 = dark.
export const FACE8 = [
  '00111100',
  '11111111',
  '01111110',
  '01011010',
  '01111110',
  '01011010',
  '01100110',
  '00111100',
];
export const LIGHT = 0xf4e6c4, DARK = 0x2a2840;

export function renderToCanvas(scene, cam, w, h) {
  const rt = new THREE.WebGLRenderTarget(w, h, { samples: 4 }); rt.texture.colorSpace = THREE.SRGBColorSpace;
  renderer.setRenderTarget(rt); renderer.render(scene, cam);
  const px = new Uint8Array(w * h * 4); renderer.readRenderTargetPixels(rt, 0, 0, w, h, px);
  renderer.setRenderTarget(null); rt.dispose();
  const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d');
  const id = x.createImageData(w, h);
  for (let y = 0; y < h; y++) id.data.set(px.subarray((h - 1 - y) * w * 4, (h - y) * w * 4), y * w * 4);
  x.putImageData(id, 0, 0); return c;
}
function portraitScene(bg) {
  const sc = new THREE.Scene(); sc.background = new THREE.Color(bg);
  sc.add(new THREE.HemisphereLight(0xffffff, 0xb08a6a, 1.6));
  const d = new THREE.DirectionalLight(0xfff2e0, 1.9); d.position.set(-30, 40, 80); sc.add(d);
  const bob = character('bob'); pose(bob, 0, { blink: 0 }); sc.add(bob);
  return { sc, bob };
}

// 16x16 face: ortho, one voxel per cell, sampled at cell centres
let _face16 = null;
export function face16() {
  if (_face16) return _face16;
  const { sc } = portraitScene(0x8cc8f0);
  const cam = new THREE.OrthographicCamera(-8, 8, 30, 14, 0.1, 200); cam.position.set(0, 0, 60); cam.lookAt(0, 0, 0);
  // ortho with explicit top/bottom: shift so view spans y 14..30
  cam.top = 8; cam.bottom = -8; cam.position.set(0, 22, 60); cam.lookAt(0, 22, 0); cam.updateProjectionMatrix();
  const N = 16, S = 10; const c = renderToCanvas(sc, cam, N * S, N * S); const x = c.getContext('2d');
  const out = [];
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { const p = x.getImageData(i * S + S / 2, j * S + S / 2, 1, 1).data; out.push((p[0] << 16) | (p[1] << 8) | p[2]); }
  _face16 = out; return out;
}

// phone "photo" of Bob: perspective, slight angle, 240x460
let _photo = null;
export function photoCanvas() {
  if (_photo) return _photo;
  const { sc, bob } = portraitScene(0x9ed2f2);
  bob.rotation.y = -0.28;
  const g = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshLambertMaterial({ color: 0xe8c890 })); g.rotation.x = -Math.PI / 2; sc.add(g);
  const cam = new THREE.PerspectiveCamera(30, 240 / 460, 1, 500); cam.position.set(4, 20, 62); cam.lookAt(0, 17, 0);
  _photo = renderToCanvas(sc, cam, 240, 460); return _photo;
}

// sample any canvas into cols x rows colors (nearest, cell centres)
export function sample(cv, cols, rows) {
  const x = cv.getContext('2d'); const d = x.getImageData(0, 0, cv.width, cv.height).data; const out = [];
  for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
    const px = Math.floor((i + 0.5) / cols * cv.width), py = Math.floor((j + 0.5) / rows * cv.height); const k = (py * cv.width + px) * 4;
    out.push((d[k] << 16) | (d[k + 1] << 8) | d[k + 2]);
  }
  return out;
}

function px(x, X, Y, s, rows, pal) { rows.forEach((r, j) => [...r].forEach((ch, i) => { if (ch !== '.' && pal[ch]) { x.fillStyle = pal[ch]; x.fillRect(X + i * s, Y + j * s, s, s); } })); }

export function galleryCanvas() {
  const c = document.createElement('canvas'); c.width = 240; c.height = 460; const x = c.getContext('2d');
  x.fillStyle = '#f4f4f8'; x.fillRect(0, 0, 240, 460);
  x.fillStyle = '#1c1c28'; x.font = '16px "PS2P"'; x.fillText('Photos', 14, 34);
  const ph = photoCanvas();
  const thumbs = [
    (X, Y, s) => { const g = x.createLinearGradient(0, Y, 0, Y + s); g.addColorStop(0, '#ff8a5c'); g.addColorStop(1, '#ffd36b'); x.fillStyle = g; x.fillRect(X, Y, s, s); x.fillStyle = '#fff3c4'; x.fillRect(X + s * 0.4, Y + s * 0.5, s * 0.22, s * 0.22); x.fillStyle = '#4a3a6a'; x.fillRect(X, Y + s * 0.72, s, s * 0.28); },
    (X, Y, s) => { x.fillStyle = '#ffffff'; x.fillRect(X, Y, s, s); x.fillStyle = '#cfd3e0'; for (let k = 0; k < 6; k++) x.fillRect(X + 6, Y + 8 + k * 11, s - 12 - (k % 3) * 12, 5); x.fillStyle = '#4a8cff'; x.fillRect(X + 6, Y + s - 16, 30, 8); },
    (X, Y, s) => { x.drawImage(ph, 30, 60, 180, 180, X, Y, s, s); },
    (X, Y, s) => { x.fillStyle = '#9ed2f2'; x.fillRect(X, Y, s, s); x.fillStyle = '#eac98e'; x.fillRect(X, Y + s * 0.7, s, s * 0.3); x.fillStyle = '#4ca046'; x.fillRect(X + s * 0.45, Y + s * 0.25, s * 0.12, s * 0.5); x.fillRect(X + s * 0.3, Y + s * 0.4, s * 0.15, s * 0.08); x.fillRect(X + s * 0.3, Y + s * 0.3, s * 0.07, s * 0.15); },
    (X, Y, s) => { x.fillStyle = '#ffffff'; x.fillRect(X, Y, s, s); x.fillStyle = '#d8dbe6'; for (let k = 0; k < 5; k++) x.fillRect(X + 6, Y + 10 + k * 13, s - 20, 6); x.fillStyle = '#ff5a5a'; x.fillRect(X + s - 22, Y + 6, 14, 14); },
    (X, Y, s) => { x.fillStyle = '#2b2b40'; x.fillRect(X, Y, s, s); x.fillStyle = '#ffd23f'; for (let k = 0; k < 9; k++) x.fillRect(X + 8 + (k * 23) % (s - 16), Y + 8 + (k * 37) % (s - 16), 3, 3); x.fillStyle = '#f2f2f2'; x.fillRect(X + s * 0.6, Y + s * 0.2, s * 0.2, s * 0.2); },
    (X, Y, s) => { lunchDraw(x, X, Y, s); },
    (X, Y, s) => { x.fillStyle = '#ffffff'; x.fillRect(X, Y, s, s); x.fillStyle = '#e1e4ee'; for (let k = 0; k < 7; k++) x.fillRect(X + 6, Y + 6 + k * 10, s - 12 - (k % 2) * 20, 4); },
    (X, Y, s) => { x.fillStyle = '#7ab7ff'; x.fillRect(X, Y, s, s); x.fillStyle = '#5cb85c'; x.fillRect(X, Y + s * 0.6, s, s * 0.4); x.fillStyle = '#ffffff'; x.fillRect(X + 10, Y + 12, s * 0.35, 10); },
    (X, Y, s) => { x.fillStyle = '#ffffff'; x.fillRect(X, Y, s, s); x.fillStyle = '#cfd3e0'; for (let k = 0; k < 6; k++) x.fillRect(X + 6, Y + 8 + k * 11, s - 30, 5); },
    (X, Y, s) => { x.fillStyle = '#c86a4a'; x.fillRect(X, Y, s, s); x.fillStyle = '#e8b878'; x.fillRect(X, Y + s * 0.5, s, s * 0.5); },
    (X, Y, s) => { x.fillStyle = '#ffffff'; x.fillRect(X, Y, s, s); x.fillStyle = '#d0d4e2'; for (let k = 0; k < 4; k++) x.fillRect(X + 6, Y + 10 + k * 16, s - 12, 8); },
    (X, Y, s) => { x.drawImage(ph, 0, 100, 240, 240, X, Y, s, s); },
    (X, Y, s) => { x.fillStyle = '#ffffff'; x.fillRect(X, Y, s, s); x.fillStyle = '#d8dbe6'; for (let k = 0; k < 6; k++) x.fillRect(X + 6, Y + 8 + k * 11, s - 16, 5); },
    (X, Y, s) => { x.fillStyle = '#3a5a8a'; x.fillRect(X, Y, s, s); x.fillStyle = '#ffd36b'; x.fillRect(X + s * 0.3, Y + s * 0.3, s * 0.4, s * 0.4); },
  ];
  const s = 72, gap = 6, X0 = 6, Y0 = 52; c.userData = { screenshots: [] };
  thumbs.forEach((f, i) => { const X = X0 + (i % 3) * (s + gap), Yy = Y0 + Math.floor(i / 3) * (s + gap); f(X, Yy, s); });
  c.userData.screenshots = [1, 4, 7, 9, 11, 13].map((i) => [X0 + (i % 3) * (s + gap), Y0 + Math.floor(i / 3) * (s + gap), s]);
  return c;
}

export function lunchDraw(x, X, Y, s) {
  x.fillStyle = '#e8eef2'; x.fillRect(X, Y, s, s);
  x.fillStyle = '#ffffff'; x.fillRect(X + s * 0.08, Y + s * 0.5, s * 0.84, s * 0.38);
  const l = (c, y0, h, w = 0.72) => { x.fillStyle = c; x.fillRect(X + s * (0.5 - w / 2), Y + s * y0, s * w, s * h); };
  l('#d89a52', 0.62, 0.1); l('#e85a4a', 0.55, 0.07, 0.68); l('#5cc05a', 0.5, 0.06, 0.78); l('#f6d260', 0.45, 0.06, 0.7); l('#d89a52', 0.33, 0.12, 0.72); l('#f0c070', 0.3, 0.04, 0.6);
}
export function lunchCanvas() { const c = document.createElement('canvas'); c.width = 240; c.height = 460; const x = c.getContext('2d'); x.fillStyle = '#e8eef2'; x.fillRect(0, 0, 240, 460); lunchDraw(x, 0, 110, 240); return c; }

export function digitsCanvas(t) {
  const c = digitsCanvas.c || (digitsCanvas.c = document.createElement('canvas')); c.width = 240; c.height = 460; const x = c.getContext('2d');
  x.fillStyle = '#0d1020'; x.fillRect(0, 0, 240, 460); x.font = '14px "PS2P"';
  const off = Math.floor(t * 30);
  for (let r = 0; r < 26; r++) { let s = ''; for (let k = 0; k < 4; k++) s += String((Math.imul(r + off, 2654435761) ^ Math.imul(k + 7, 40503)) >>> 0 % 1).slice(-3).padStart(3, '0') + ' '; x.fillStyle = r % 3 ? '#4ff07a' : '#ffd23f'; x.fillText(s, 10, 22 + r * 17); }
  return c;
}
