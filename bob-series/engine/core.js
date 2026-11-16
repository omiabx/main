// Renderer, lighting presets, overlay drawing, easing helpers.
import * as THREE from 'three';

export const W = 1920, H = 1080;
export const canvas = document.getElementById('gl');
export const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;

export const out = document.createElement('canvas'); out.width = W; out.height = H;
export const octx = out.getContext('2d');
export const ov = document.createElement('canvas'); ov.width = W; ov.height = H;
export const g2 = ov.getContext('2d');
export const buf = document.createElement('canvas'); buf.width = W; buf.height = H;
export const bctx = buf.getContext('2d');

// ---------- easing ----------
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
export const ease = (t) => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const easeOut = (t) => { t = clamp(t); return 1 - Math.pow(1 - t, 3); };
export const backOut = (t) => { t = clamp(t); const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
export const ramp = (t, a, b) => clamp((t - a) / (b - a));
export const pop = (t, t0, d = 0.35) => backOut((t - t0) / d);
export const v3 = (x, y, z) => new THREE.Vector3(x, y, z);

// ---------- sky ----------
function gradTex(stops) {
  const c = document.createElement('canvas'); c.width = 4; c.height = 512; const x = c.getContext('2d');
  const gr = x.createLinearGradient(0, 0, 0, 512); stops.forEach(([p, col]) => gr.addColorStop(p, col));
  x.fillStyle = gr; x.fillRect(0, 0, 4, 512);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
export const SKY = {
  day: gradTex([[0, '#4f9be0'], [0.45, '#8cc2ee'], [0.78, '#cfe5f2'], [1, '#f3d9b8']]),
  dusk: gradTex([[0, '#3d4f9a'], [0.4, '#a06aa8'], [0.75, '#f0956a'], [1, '#ffcf8a']]),
  stage: gradTex([[0, '#1a0f33'], [0.6, '#2b1652'], [1, '#3a1d6b']]),
  map: gradTex([[0, '#1e2a44'], [1, '#2c3e5c']]),
};

export function lights(scene, preset = 'day') {
  const L = {};
  if (preset === 'stage') {
    L.hemi = new THREE.HemisphereLight(0xd8c8ff, 0x3a2266, 1.25);
    L.sun = new THREE.DirectionalLight(0xfff2e0, 2.4);
    L.sun.position.set(-60, 140, 110);
    L.rim = new THREE.DirectionalLight(0xb08cff, 0.9); L.rim.position.set(80, 60, -120); scene.add(L.rim);
  } else {
    L.hemi = new THREE.HemisphereLight(0xcfe6ff, 0xc89a6a, 1.35);
    L.sun = new THREE.DirectionalLight(0xfff0d8, 2.5);
    L.sun.position.set(-90, 180, 120);
  }
  L.sun.castShadow = true; L.sun.shadow.mapSize.set(2048, 2048); L.sun.shadow.bias = -0.0004; L.sun.shadow.normalBias = 0.4;
  L.sun.shadow.radius = 3;
  scene.add(L.hemi, L.sun, L.sun.target);
  L.fitShadow = (cx, cy, cz, r) => {
    const s = L.sun.shadow.camera; s.left = -r; s.right = r; s.top = r; s.bottom = -r; s.near = 1; s.far = 1200; s.updateProjectionMatrix();
    L.sun.target.position.set(cx, cy, cz); const d = L.sun.userData.dir || L.sun.position.clone().normalize();
    L.sun.userData.dir = d; L.sun.position.set(cx + d.x * 500, cy + d.y * 500, cz + d.z * 500);
  };
  L.sun.userData.dir = L.sun.position.clone().normalize();
  return L;
}

// ---------- camera helper ----------
export function makeCam(fov = 32) { const c = new THREE.PerspectiveCamera(fov, W / H, 1, 5000); return c; }
export function aim(cam, pos, look, roll = 0) { cam.position.copy(pos); cam.up.set(Math.sin(roll), Math.cos(roll), 0); cam.lookAt(look); }
export function project(cam, p) { const v = p.clone().project(cam); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H, v.z]; }

// ---------- 2D overlay ----------
export const FONT = '"PS2P"';
export function text(str, x, y, o = {}) {
  const size = o.size ?? 64, sc = o.scale ?? 1; if (sc <= 0.001) return;
  g2.save(); g2.translate(x, y); g2.scale(sc, sc); if (o.rot) g2.rotate(o.rot);
  g2.globalAlpha = o.alpha ?? 1;
  g2.font = `${size}px ${FONT}`; g2.textAlign = o.align ?? 'center'; g2.textBaseline = 'middle';
  const lw = o.stroke ?? Math.max(6, size * 0.24);
  const parts = Array.isArray(str) ? str : [[str, o.color ?? '#ffffff']];
  // measure
  let total = 0; const ws = parts.map(([s]) => { const w = g2.measureText(s).width; total += w; return w; });
  let cx = g2.textAlign === 'center' ? -total / 2 : g2.textAlign === 'right' ? -total : 0;
  g2.textAlign = 'left';
  const sh = o.shadow ?? size * 0.12;
  // shadow
  g2.fillStyle = 'rgba(10,8,24,0.55)'; let xx = cx;
  parts.forEach(([s], i) => { g2.lineJoin = 'round'; g2.lineWidth = lw; g2.strokeStyle = 'rgba(10,8,24,0.55)'; g2.strokeText(s, xx + sh * 0.3, sh); xx += ws[i]; });
  xx = cx;
  parts.forEach(([s], i) => { g2.lineJoin = 'round'; g2.lineWidth = lw; g2.strokeStyle = o.outline ?? '#14102a'; g2.strokeText(s, xx, 0); xx += ws[i]; });
  xx = cx;
  parts.forEach(([s, col], i) => { g2.fillStyle = col; if (o.glow) { g2.shadowColor = col; g2.shadowBlur = o.glow; } g2.fillText(s, xx, 0); g2.shadowBlur = 0; xx += ws[i]; });
  g2.restore();
}
export const Y = '#ffd23f', G = '#4ff07a', R = '#ff4a4a', B = '#4aa8ff', WH = '#ffffff', CY = '#5ff2ff';

// pixel speech bubble
export function bubble(str, x, y, o = {}) {
  const sc = o.scale ?? 1; if (sc <= 0.001) return;
  const size = o.size ?? 44;
  g2.save(); g2.translate(x, y); g2.scale(sc, sc);
  g2.font = `${size}px ${FONT}`;
  const lines = Array.isArray(str) ? str : [str];
  const w = Math.max(...lines.map((l) => g2.measureText(l).width)) + size * 1.2, h = lines.length * size * 1.35 + size * 0.8;
  const tail = o.tail ?? 0; // horizontal offset of tail
  const bx = -w / 2, by = -h - size * 0.9;
  g2.fillStyle = '#14102a';
  g2.fillRect(bx - 6, by - 6, w + 12, h + 12);
  g2.beginPath(); g2.moveTo(tail - 18, by + h); g2.lineTo(tail + 4, by + h + size * 0.95 + 6); g2.lineTo(tail + 22, by + h); g2.fill();
  g2.fillStyle = '#ffffff'; g2.fillRect(bx, by, w, h);
  g2.beginPath(); g2.moveTo(tail - 10, by + h - 2); g2.lineTo(tail + 4, by + h + size * 0.85 - 2); g2.lineTo(tail + 14, by + h - 2); g2.fill();
  g2.fillStyle = o.color ?? '#14102a'; g2.textAlign = 'center'; g2.textBaseline = 'middle';
  lines.forEach((l, i) => g2.fillText(l, 0, by + size * 0.4 + size * 0.68 + i * size * 1.35));
  g2.restore();
}

// small navy tag with gold text (like the 4 2 1 tags in earlier episodes)
export function tag(str, x, y, o = {}) {
  const sc = o.scale ?? 1; if (sc <= 0.001) return;
  const size = o.size ?? 30;
  g2.save(); g2.translate(x, y); g2.scale(sc, sc); g2.globalAlpha = o.alpha ?? 1;
  g2.font = `${size}px ${FONT}`; const w = g2.measureText(str).width + size * 0.9, h = size * 1.6;
  g2.fillStyle = '#0d0b1e'; g2.fillRect(-w / 2 - 4, -h / 2 - 4, w + 8, h + 8);
  g2.fillStyle = o.bg ?? '#1d2347'; g2.fillRect(-w / 2, -h / 2, w, h);
  g2.fillStyle = o.color ?? Y; g2.textAlign = 'center'; g2.textBaseline = 'middle'; g2.fillText(str, 0, 2);
  g2.restore();
}

export function vignette(a = 0.35) {
  const gr = g2.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, `rgba(8,4,20,${a})`);
  g2.fillStyle = gr; g2.fillRect(0, 0, W, H);
}

// dynamic sky: k=0 day .. 1 dusk
const _dc = document.createElement('canvas'); _dc.width = 4; _dc.height = 512; const _dx = _dc.getContext('2d');
SKY.dyn = new THREE.CanvasTexture(_dc); SKY.dyn.colorSpace = THREE.SRGBColorSpace;
const _day = ['#4f9be0', '#8cc2ee', '#cfe5f2', '#f3d9b8'], _dusk = ['#3d4f9a', '#a06aa8', '#f0956a', '#ffcf8a'];
function _lc(a, b, t) { const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)); const A = p(a), B = p(b); return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`; }
let _lastK = -1;
export function setSky(k) {
  if (Math.abs(k - _lastK) < 0.002) return SKY.dyn; _lastK = k;
  const gr = _dx.createLinearGradient(0, 0, 0, 512); [0, 0.45, 0.78, 1].forEach((p, i) => gr.addColorStop(p, _lc(_day[i], _dusk[i], k)));
  _dx.fillStyle = gr; _dx.fillRect(0, 0, 4, 512); SKY.dyn.needsUpdate = true; return SKY.dyn;
}
