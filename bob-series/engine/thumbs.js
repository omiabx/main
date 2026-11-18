// Thumbnail scenes (rendered as stills, then downscaled to 1280x720).
import * as THREE from 'three';
import { VB, rgb, hash3 } from './vox.js';
import { character, pose, cactus, rock, phone, pedestal } from './models.js';
import { TS, island } from './terrain.js';
import { SKY, lights, makeCam, aim, v3, project, text, tag, g2, W, H, Y, G, R, B, WH } from './core.js';
import { face16, photoCanvas } from './pics.js';

function desertBase() {
  const scene = new THREE.Scene(); scene.background = SKY.day; const L = lights(scene, 'day'); const cam = makeCam(30);
  const vb = new VB(); island(vb, 0, -6, 34, 11, 6); scene.add(vb.mesh({ scale: TS }));
  [[cactus(3, 16), -70, -60], [cactus(4, 12), 60, -90], [rock(2, 5), -40, -30]].forEach(([m, x, z]) => { m.position.set(x, 4, z); scene.add(m); });
  L.fitShadow(0, 0, 0, 160); return { scene, L, cam, O: {} };
}
const hex = (c) => '#' + c.toString(16).padStart(6, '0');

// A: Bob's face, right half dissolves into numbered pixels
export function thumbA() {
  const S = desertBase();
  const bob = character('bob', { mouth: 'open', brows: true }); bob.position.set(-8, 4, 40); bob.rotation.y = 0.32; S.scene.add(bob); pose(bob, 0.5, { blink: 0, tilt: -0.06 });
  aim(S.cam, v3(-12, 27, 84), v3(9, 22, 40));
  S.update = () => {};
  S.post = () => {
    const f = face16(); const cs = 54, x0 = 1010, y0 = 150;
    g2.fillStyle = '#0d0b1e'; g2.fillRect(x0 - 16, y0 - 16, cs * 16 + 28, cs * 16 + 28); g2.strokeStyle = '#f2c14e'; g2.lineWidth = 8; g2.strokeRect(x0 - 16, y0 - 16, cs * 16 + 28, cs * 16 + 28);
    for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) {
      const x = x0 + i * cs - (j % 2 ? 0 : 0); if (x > W - 20) continue; const c = f[j * 16 + i];
      g2.fillStyle = hex(c); g2.fillRect(x, y0 + j * cs, cs - 4, cs - 4);
    }
    // numbers in a few cells
    const r = (c) => (c >> 16) & 255;
    for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) { const x = x0 + i * cs; if (x > W - 40 || (i + j) % 2) continue; const c = f[j * 16 + i]; const v = (c >> 16) & 255; const l = 0.3 * r(c) + 0.59 * ((c >> 8) & 255) + 0.11 * (c & 255);
      g2.font = '17px "PS2P"'; g2.textAlign = 'center'; g2.textBaseline = 'middle'; g2.fillStyle = l > 140 ? 'rgba(20,16,42,0.85)' : 'rgba(255,255,255,0.9)'; g2.fillText(String(v), x + cs / 2 - 2, y0 + j * cs + cs / 2); }
    // jagged seam
    text('NOT A', 450, 110, { size: 80 });
    text('PICTURE?', 450, 220, { size: 96, color: Y });
    g2.fillStyle = '#14102a'; g2.beginPath(); g2.moveTo(990, 540); g2.lineTo(926, 494); g2.lineTo(926, 586); g2.fill(); g2.fillStyle = Y; g2.beginPath(); g2.moveTo(978, 540); g2.lineTo(934, 509); g2.lineTo(934, 571); g2.fill();
  };
  return S;
}

// B: phone with Bob's photo + magnifier showing numbers
export function thumbB() {
  const scene = new THREE.Scene(); scene.background = SKY.stage; const L = lights(scene, 'stage'); const cam = makeCam(30);
  const vb = new VB(); for (let x = -40; x <= 40; x++) for (let z = -40; z <= 20; z++) vb.set(x, -1, z, ((Math.floor(x / 3) + Math.floor(z / 3)) & 1) ? rgb(74, 42, 138) : rgb(88, 52, 158));
  scene.add(vb.mesh({ scale: 6 })); scene.fog = new THREE.Fog(0x2b1652, 260, 560);
  const ped = pedestal(26); scene.add(ped); const ph = phone(); ph.position.set(0, 6, 0); ph.rotation.y = -0.25; scene.add(ph);
  const tex = new THREE.CanvasTexture(photoCanvas()); tex.colorSpace = THREE.SRGBColorSpace; ph.userData.screen.material = new THREE.MeshBasicMaterial({ map: tex });
  const bob = character('bob', { mouth: 'open', brows: true }); bob.position.set(-40, 0, 52); bob.rotation.y = 0.75; scene.add(bob); pose(bob, 0.3, { point: 0.9, blink: 0 });
  L.fitShadow(0, 0, 0, 140); aim(cam, v3(-10, 40, 150), v3(-6, 28, 0));
  const S = { scene, L, cam, O: {}, update() {} };
  S.post = () => {
    const [px, py] = project(cam, v3(2, 38, 3)); const cx = 1380, cy = 470, rr = 300;
    g2.save(); g2.strokeStyle = '#14102a'; g2.lineWidth = 30; g2.beginPath(); g2.moveTo(cx - rr * 0.7, cy + rr * 0.7); g2.lineTo(cx - rr * 1.15, cy + rr * 1.15); g2.stroke(); g2.strokeStyle = '#8a5a30'; g2.lineWidth = 20; g2.stroke();
    g2.beginPath(); g2.arc(cx, cy, rr, 0, 7); g2.fillStyle = '#0d0b1e'; g2.fill(); g2.clip();
    const f = face16(); const cs = 92;
    for (let j = 0; j < 8; j++) for (let i = 0; i < 8; i++) { const c = f[(j + 5) * 16 + i + 3]; const x = cx - 4 * cs + i * cs, y = cy - 4 * cs + j * cs; g2.fillStyle = hex(c); g2.fillRect(x, y, cs - 6, cs - 6); const l = 0.3 * ((c >> 16) & 255) + 0.59 * ((c >> 8) & 255) + 0.11 * (c & 255); g2.font = '22px "PS2P"'; g2.textAlign = 'center'; g2.textBaseline = 'middle'; g2.fillStyle = l > 140 ? '#14102a' : '#ffffff'; g2.fillText(String((c >> 16) & 255), x + cs / 2 - 3, y + cs / 2); }
    g2.restore(); g2.strokeStyle = '#f2c14e'; g2.lineWidth = 16; g2.beginPath(); g2.arc(cx, cy, rr, 0, 7); g2.stroke(); g2.strokeStyle = '#14102a'; g2.lineWidth = 5; g2.beginPath(); g2.arc(cx, cy, rr + 9, 0, 7); g2.stroke();
    text('PHOTOS', 520, 130, { size: 100 }); text([['= ', WH], ['NUMBERS?', G]], 540, 260, { size: 90 });
  };
  return S;
}

// C: one giant pixel = 3 lights
export function thumbC() {
  const scene = new THREE.Scene(); scene.background = SKY.stage; const L = lights(scene, 'stage'); const cam = makeCam(30);
  const vb = new VB(); for (let x = -40; x <= 40; x++) for (let z = -40; z <= 20; z++) vb.set(x, -1, z, ((Math.floor(x / 3) + Math.floor(z / 3)) & 1) ? rgb(74, 42, 138) : rgb(88, 52, 158));
  scene.add(vb.mesh({ scale: 6 })); scene.fog = new THREE.Fog(0x2b1652, 260, 560); scene.add(pedestal(26));
  const g = new THREE.Group(); g.position.set(26, 6, 0); scene.add(g);
  const fv = new VB(); fv.box(-15, 0, -4, 14, 1, 3, rgb(40, 40, 52)); fv.box(-15, 44, -4, 14, 45, 3, rgb(40, 40, 52)); fv.box(-15, 0, -4, -14, 45, 3, rgb(40, 40, 52)); fv.box(13, 0, -4, 14, 45, 3, rgb(40, 40, 52)); fv.box(-14, 1, -4, 13, 44, -3, rgb(18, 18, 26)); g.add(fv.mesh());
  [0xff2a2a, 0x2aff4a, 0x2a6aff].forEach((c, k) => { const m = new THREE.Mesh(new THREE.BoxGeometry(8, 40, 4), new THREE.MeshBasicMaterial({ color: c })); m.position.set((k - 1) * 9, 22.5, 0); g.add(m); });
  const bob = character('bob', { mouth: 'open', brows: true }); bob.position.set(-8, 6, 30); bob.rotation.y = 0.55; scene.add(bob); pose(bob, 0.3, { point: 0.9, blink: 0 });
  L.fitShadow(0, 0, 0, 140); aim(cam, v3(-30, 34, 116), v3(-4, 26, 0));
  const S = { scene, L, cam, O: {}, update() {} };
  S.post = () => { text('1 PIXEL', 470, 140, { size: 96 }); text('= 3 LIGHTS', 520, 270, { size: 90, color: Y }); };
  return S;
}

// D: framed portrait split in half: binary on the left, real face on the right. "BINARY -> PHOTO"
import { renderToCanvas } from './pics.js';
export function thumbD() {
  const S = desertBase();
  aim(S.cam, v3(0, 60, 200), v3(0, 20, -40));
  // portrait render of Bob (front, slight surprise)
  const ps = new THREE.Scene(); ps.background = new THREE.Color(0x9ed2f2);
  ps.add(new THREE.HemisphereLight(0xffffff, 0xb08a6a, 1.5));
  const dl = new THREE.DirectionalLight(0xfff2e0, 2.0); dl.position.set(-30, 50, 90); ps.add(dl);
  const bob = character('bob', { mouth: 'open', brows: true }); pose(bob, 0, { blink: 0 }); ps.add(bob);
  const pc = new THREE.PerspectiveCamera(26, 1, 1, 500); pc.position.set(0, 22.6, 51); pc.lookAt(0, 21.8, 0);
  let portrait = null;
  S.update = () => {};
  S.post = () => {
    if (!portrait) portrait = renderToCanvas(ps, pc, 816, 816);
    const FS = 816, fx = W / 2 - FS / 2, fy = 222, N = 12, cs = FS / N;
    // dim the background a little so the frame pops
    g2.fillStyle = 'rgba(10,8,30,0.28)'; g2.fillRect(0, 0, W, H);
    // wooden frame
    const bw = 34; g2.fillStyle = '#14102a'; g2.fillRect(fx - bw - 8, fy - bw - 8, FS + 2 * bw + 16, FS + 2 * bw + 16);
    g2.fillStyle = '#7a4e2c'; g2.fillRect(fx - bw, fy - bw, FS + 2 * bw, FS + 2 * bw);
    g2.fillStyle = '#9a6a3e'; g2.fillRect(fx - bw, fy - bw, FS + 2 * bw, 10); g2.fillRect(fx - bw, fy - bw, 10, FS + 2 * bw);
    g2.fillStyle = '#5c3820'; g2.fillRect(fx - bw, fy + FS + bw - 10, FS + 2 * bw, 10); g2.fillRect(fx + FS + bw - 10, fy - bw, 10, FS + 2 * bw);
    // right half: real face
    g2.drawImage(portrait, 0, 0, FS, FS, fx, fy, FS, FS);
    // left half: binary, stepped seam
    const px = portrait.getContext('2d').getImageData(0, 0, FS, FS).data;
    const seam = [6, 6, 5, 6, 7, 6, 6, 5, 6, 7, 6, 6];
    for (let j = 0; j < N; j++) for (let i = 0; i < seam[j]; i++) {
      const sx = Math.floor((i + 0.5) * cs), sy = Math.floor((j + 0.5) * cs), k = (sy * FS + sx) * 4;
      let r = px[k], gg = px[k + 1], b = px[k + 2]; const l = 0.3 * r + 0.59 * gg + 0.11 * b;
      const x = fx + i * cs, y = fy + j * cs;
      g2.fillStyle = `rgb(${Math.round(10 + r * 0.32)},${Math.round(12 + gg * 0.32)},${Math.round(26 + b * 0.3)})`; g2.fillRect(x, y, cs, cs);
      const boost = (v) => Math.min(255, Math.round(v * 1.25 + 30));
      g2.fillStyle = `rgb(${boost(r)},${boost(gg)},${boost(b)})`;
      g2.font = `${Math.round(cs * 0.62)}px "PS2P"`; g2.textAlign = 'center'; g2.textBaseline = 'middle';
      g2.fillText(l > 120 ? '1' : '0', x + cs / 2 + 2, y + cs / 2 + 3);
    }
    // seam glow
    g2.save(); g2.strokeStyle = '#ffd23f'; g2.lineWidth = 6; g2.shadowColor = '#ffd23f'; g2.shadowBlur = 18; g2.beginPath();
    for (let j = 0; j < N; j++) { const x = fx + seam[j] * cs, y = fy + j * cs; if (j === 0) g2.moveTo(x, y); else g2.lineTo(x, y); g2.lineTo(x, y + cs); }
    g2.stroke(); g2.restore();
    // title with drawn arrow
    const ty = 108, size = 104;
    text('BINARY', W / 2 - 430, ty, { size, color: G });
    text('PHOTO', W / 2 + 460, ty, { size, color: Y });
    g2.save(); g2.translate(W / 2 + 22, ty - 8); g2.scale(0.88, 0.88);
    const arrow = (c, o) => { g2.fillStyle = c; g2.beginPath(); g2.moveTo(-90 - o, -18 - o); g2.lineTo(20, -18 - o); g2.lineTo(20, -52 - o * 1.6); g2.lineTo(96 + o * 1.8, 0); g2.lineTo(20, 52 + o * 1.6); g2.lineTo(20, 18 + o); g2.lineTo(-90 - o, 18 + o); g2.closePath(); g2.fill(); };
    arrow('rgba(10,8,24,0.55)', 12); g2.translate(-4, -6); arrow('#14102a', 12); arrow('#ffffff', 0); g2.restore();
  };
  return S;
}

// E: whole thumbnail split down the middle. Left = BINARY (face as tinted 0/1 grid), right = PHOTO (real render).
import { renderer } from './core.js';
export function thumbE() {
  const S = desertBase();
  const bob = character('bob', { mouth: 'open', brows: true }); bob.position.set(0, 4, 20); pose(bob, 0, { blink: 0 }); S.scene.add(bob);
  aim(S.cam, v3(0, 26.6, 70), v3(0, 24.0, 20));
  const tmp = document.createElement('canvas'); tmp.width = W; tmp.height = H; const tx = tmp.getContext('2d', { willReadFrequently: true });
  S.update = () => {};
  S.post = () => {
    tx.drawImage(renderer.domElement, 0, 0); const d = tx.getImageData(0, 0, W, H).data;
    const cs = 40, cols = W / cs, rows = Math.ceil(H / cs);
    const seamCol = (j) => 24 + [0, 0, -1, -1, 0, 1, 1, 0, 0, -1, 0, 1][j % 12];
    for (let j = 0; j < rows; j++) for (let i = 0; i < seamCol(j); i++) {
      const sx = Math.min(W - 1, Math.floor((i + 0.5) * cs)), sy = Math.min(H - 1, Math.floor((j + 0.5) * cs)), k = (sy * W + sx) * 4;
      const r = d[k], gg = d[k + 1], b = d[k + 2]; const l = 0.3 * r + 0.59 * gg + 0.11 * b;
      const x = i * cs, y = j * cs;
      g2.fillStyle = `rgb(${Math.round(6 + r * 0.42)},${Math.round(8 + gg * 0.42)},${Math.round(20 + b * 0.4)})`; g2.fillRect(x, y, cs, cs);
      const boost = (v) => Math.min(255, Math.round(v * 1.2 + 34));
      g2.fillStyle = `rgb(${boost(r)},${boost(gg)},${boost(b)})`;
      g2.font = `${Math.round(cs * 0.6)}px "PS2P"`; g2.textAlign = 'center'; g2.textBaseline = 'middle';
      g2.fillText(l > 120 ? '1' : '0', x + cs / 2 + 2, y + cs / 2 + 3);
    }
    g2.save(); g2.strokeStyle = '#ffd23f'; g2.lineWidth = 8; g2.shadowColor = '#ffd23f'; g2.shadowBlur = 22; g2.beginPath();
    for (let j = 0; j < rows; j++) { const x = seamCol(j) * cs, y = j * cs; if (j === 0) g2.moveTo(x, y); else g2.lineTo(x, y); g2.lineTo(x, y + cs); }
    g2.stroke(); g2.restore();
    const plate = (cx, w, col) => { const y0 = 34, h = 136; g2.fillStyle = '#0d0b1e'; g2.fillRect(cx - w / 2 - 8, y0 - 8, w + 16, h + 16); g2.fillStyle = '#1d1640'; g2.fillRect(cx - w / 2, y0, w, h); g2.strokeStyle = col; g2.lineWidth = 6; g2.strokeRect(cx - w / 2 + 6, y0 + 6, w - 12, h - 12); };
    plate(W / 4, 720, G); plate(W * 3 / 4, 600, Y);
    text('BINARY', W / 4, 106, { size: 100, color: G });
    text('PHOTO', W * 3 / 4, 106, { size: 100, color: Y });
  };
  return S;
}

// F (episode 6): BINARY | SOUND. Left: the voice wave as columns of 0/1. Right: Bob shouting, a glowing wave leaving his mouth.
export function thumbF() {
  const S = desertBase();
  const bob = character('bob', { mouth: 'open', brows: true }); bob.position.set(26, 4, 30); bob.rotation.y = -1.15; pose(bob, 0, { blink: 0, cheer: 0.35, nod: -0.15 }); S.scene.add(bob);
  aim(S.cam, v3(4, 26, 92), v3(4, 22, 20));
  const TAU = Math.PI * 2;
  const env = (u) => 0.3 + 0.7 * Math.abs(Math.sin(Math.PI * 2.6 * u + 0.4));
  const voice = (u) => env(u) * (0.62 * Math.sin(TAU * 6 * u) + 0.26 * Math.sin(TAU * 15 * u + 1) + 0.12 * Math.sin(TAU * 29 * u + 2));
  S.update = () => {};
  S.post = () => {
    const [mx, my] = project(S.cam, bob.getWorldPosition(v3(0, 0, 0)).add(v3(-6.5, 15.5, 2)));
    const seam = W / 2, mid = 610, A = 380;
    // left panel
    g2.fillStyle = '#120e26'; g2.fillRect(0, 0, seam, H);
    g2.strokeStyle = 'rgba(140,120,220,0.16)'; g2.lineWidth = 2; for (let x = 0; x < seam; x += 60) { g2.beginPath(); g2.moveTo(x, 0); g2.lineTo(x, H); g2.stroke(); } for (let y = 0; y < H; y += 60) { g2.beginPath(); g2.moveTo(0, y); g2.lineTo(seam, y); g2.stroke(); }
    const cs = 36, cols = Math.floor(seam / cs);
    g2.font = '30px "PS2P"'; g2.shadowColor = '#4ff07a'; g2.shadowBlur = 10; g2.textAlign = 'center'; g2.textBaseline = 'middle';
    for (let i = 0; i < cols; i++) {
      const u = 0.08 + i / cols * 0.84; const v = voice(u); const n = Math.round(Math.abs(v) * A / cs); const dir = v >= 0 ? -1 : 1;
      for (let k = 0; k <= n; k++) { const y = mid + dir * k * cs; const hot = k === n; g2.fillStyle = hot ? '#ffd23f' : `rgba(79,240,122,${0.55 + 0.45 * k / Math.max(1, n)})`; g2.fillText(((i * 7 + k * 3) % 5) > 1 ? '1' : '0', i * cs + cs / 2, y); }
    }
    g2.shadowBlur = 0;
    // glowing wave from Bob's mouth to the seam
    g2.save(); g2.strokeStyle = '#ffd23f'; g2.lineWidth = 12; g2.shadowColor = '#ffd23f'; g2.shadowBlur = 26; g2.lineJoin = 'round'; g2.beginPath();
    const x0 = mx - 20, x1 = seam;
    for (let i = 0; i <= 300; i++) { const f = i / 300; const x = x0 + (x1 - x0) * f; const amp = 40 + 260 * f; const y = lerpN(my, mid, f) + Math.sin(f * TAU * 4.2) * amp * (0.6 + 0.4 * Math.sin(f * 9)); if (!i) g2.moveTo(x, y); else g2.lineTo(x, y); }
    g2.stroke(); g2.restore();
    // seam line
    g2.save(); g2.strokeStyle = '#ffd23f'; g2.lineWidth = 8; g2.shadowColor = '#ffd23f'; g2.shadowBlur = 22; g2.beginPath(); g2.moveTo(seam, 0); g2.lineTo(seam, H); g2.stroke(); g2.restore();
    const plate = (cx, w, col) => { const y0 = 34, h = 136; g2.fillStyle = '#0d0b1e'; g2.fillRect(cx - w / 2 - 8, y0 - 8, w + 16, h + 16); g2.fillStyle = '#1d1640'; g2.fillRect(cx - w / 2, y0, w, h); g2.strokeStyle = col; g2.lineWidth = 6; g2.strokeRect(cx - w / 2 + 6, y0 + 6, w - 12, h - 12); };
    if (!S.noText) {
      plate(W / 4, 720, G); plate(W * 3 / 4, 600, Y);
      text('BINARY', W / 4, 106, { size: 100, color: G });
      text('SOUND', W * 3 / 4, 106, { size: 100, color: Y });
    }
  };
  return S;
}
function lerpN(a, b, t) { return a + (b - a) * t; }
// F without labels
export function thumbFnt() { const S = thumbF(); S.noText = true; return S; }

// G (episode 6, no text): sound turns into binary across the frame, no hard split.
// right: Bob + smooth glowing wave. middle: the scene breaks into pixel blocks and the wave becomes a staircase.
// left: fully binary, the wave rebuilt from columns of 0/1.
export function thumbG() {
  const S = desertBase();
  const bob = character('bob', { mouth: 'open', brows: true }); bob.position.set(26, 4, 30); bob.rotation.y = -1.15; pose(bob, 0, { blink: 0, cheer: 0.35, nod: -0.15 }); S.scene.add(bob);
  aim(S.cam, v3(4, 26, 92), v3(4, 22, 20));
  const TAU = Math.PI * 2;
  const tmp = document.createElement('canvas'); tmp.width = W; tmp.height = H; const tx = tmp.getContext('2d', { willReadFrequently: true });
  S.update = () => {};
  S.post = () => {
    tx.drawImage(renderer.domElement, 0, 0); const d = tx.getImageData(0, 0, W, H).data;
    const [mx, my] = project(S.cam, bob.getWorldPosition(v3(0, 0, 0)).add(v3(-6.5, 15.5, 2)));
    const cs = 36, cols = Math.ceil(W / cs), rows = Math.ceil(H / cs), mid = 600;
    const hash = (i, j) => { let h = (i * 374761393 + j * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177 | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
    const sm = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
    // how "binary" each column is: 1 on the left, 0 near Bob
    const bin = (x) => 1 - sm(W * 0.2, W * 0.66, x);
    // the wave (screen space): amplitude grows away from the mouth
    const x0 = mx - 20;
    const waveY = (x) => { const f = Math.min(1, Math.max(0, (x0 - x) / (x0 - 0))); const amp = 40 + 300 * Math.min(1, f * 1.6); return my + (mid - my) * Math.min(1, f * 2.2) + Math.sin(f * TAU * 6.2) * amp * (0.62 + 0.38 * Math.sin(f * 11 + 1)); };
    // 1) pixel-block dissolve of the scene
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
      const cx = i * cs + cs / 2; const b = bin(cx); if (hash(i, j) >= b) continue;
      const sx = Math.min(W - 1, Math.floor(cx)), sy = Math.min(H - 1, Math.floor(j * cs + cs / 2)), k = (sy * W + sx) * 4;
      const t = 0.18 + 0.2 * (1 - b);
      g2.fillStyle = `rgb(${Math.round(10 + d[k] * t)},${Math.round(10 + d[k + 1] * t)},${Math.round(28 + d[k + 2] * t)})`;
      g2.fillRect(i * cs, j * cs, cs, cs);
      if (b > 0.7 && hash(j, i) < 0.3) { g2.font = '18px "PS2P"'; g2.textAlign = 'center'; g2.textBaseline = 'middle'; g2.fillStyle = `rgba(120,110,190,${0.2 * b})`; g2.fillText(hash(i + 7, j) > 0.5 ? '1' : '0', cx, j * cs + cs / 2 + 2); }
    }
    // 2) digit columns on the left (fade in where the scene is mostly binary)
    g2.font = '32px "PS2P"'; g2.textAlign = 'center'; g2.textBaseline = 'middle'; g2.shadowColor = '#4ff07a'; g2.shadowBlur = 14;
    for (let i = 0; i < cols; i++) {
      const cx = i * cs + cs / 2; const a = sm(W * 0.36, W * 0.24, cx); if (a <= 0) continue;
      const v = waveY(cx) - mid; const n = Math.round(Math.abs(v) / cs); const dir = v < 0 ? -1 : 1;
      for (let k = 0; k <= n; k++) { const hot = k === n; g2.globalAlpha = a; g2.fillStyle = hot ? '#ffd23f' : `rgba(79,240,122,${0.55 + 0.45 * k / Math.max(1, n)})`; g2.fillText(hash(i, k) > 0.4 ? '1' : '0', cx, mid + dir * k * cs); }
    }
    g2.globalAlpha = 1; g2.shadowBlur = 0;
    // 3) the wave: smooth near Bob, staircase in the middle (fades out where the digits take over)
    g2.save(); g2.lineJoin = 'miter'; g2.lineCap = 'butt'; g2.shadowColor = '#ffd23f'; g2.shadowBlur = 26;
    const step = (x) => { const c = Math.floor(x / cs); return waveY(c * cs + cs / 2); };
    for (let x = x0; x > W * 0.2; x -= 3) {
      const b = bin(x); const fade = sm(W * 0.24, W * 0.36, x);
      const yS = waveY(x), yQ = step(x), y = yS + (yQ - yS) * sm(0.15, 0.6, b);
      const xn = x - 3, ySn = waveY(xn), yQn = step(xn), yn = ySn + (yQn - ySn) * sm(0.15, 0.6, bin(xn));
      g2.strokeStyle = `rgba(255,210,63,${fade})`; g2.lineWidth = 12; g2.beginPath(); g2.moveTo(x, y); g2.lineTo(xn, yn); g2.stroke();
    }
    g2.restore();
  };
  return S;
}
