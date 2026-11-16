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
