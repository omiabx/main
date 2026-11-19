// Episode 7 props: circuit parts, transistor, foundry equipment.
import * as THREE from 'three';
import { VB, rgb, hash3, shade } from './vox.js';
import { C } from './models.js';

export const COPPER = rgb(214, 128, 70), COPPER_D = rgb(176, 98, 52);
const METAL = rgb(170, 176, 188), METAL_D = rgb(120, 126, 140);
export const SILICON = rgb(86, 98, 140), SILICON_L = rgb(120, 134, 182);

export function battery() {
  const v = new VB();
  v.box(-5, 0, -5, 5, 15, 5, (x, y, z) => (y > 11 ? rgb(214, 60, 52) : rgb(48, 50, 62)));
  v.box(-2, 16, -2, 1, 17, 1, METAL);
  v.box(-1, 13, 6, 0, 13, 6, rgb(255, 255, 255)); v.box(-1, 12, 6, -1, 14, 6, rgb(255, 255, 255)); // little +
  return v.mesh();
}

// knife switch; userData.set(closed 0..1). Lever hinges at its left post and swings up when open.
export function knifeSwitch() {
  const g = new THREE.Group(); const v = new VB();
  v.box(-10, 0, -4, 10, 1, 4, C.woodL); v.box(-8, 2, -1, -7, 5, 0, COPPER); v.box(7, 2, -1, 8, 5, 0, COPPER);
  g.add(v.mesh());
  const lever = new THREE.Group(); lever.position.set(-7.5, 5, -0.5); g.add(lever);
  const lv = new VB(); lv.box(0, 0, 0, 15, 0, 0, COPPER); lv.box(15, -1, 0, 17, 1, 0, rgb(200, 50, 44)); lever.add(lv.mesh({ offset: [0, 0.5, 0.5] }));
  g.userData = { set(c) { lever.rotation.z = (1 - c) * 1.15; } };
  g.userData.set(0); return g;
}

// light bulb; userData.set(on 0..1)
export function bulb() {
  const g = new THREE.Group(); const v = new VB();
  v.box(-3, 0, -3, 3, 4, 3, METAL_D); v.box(-2, 5, -2, 2, 6, 2, METAL);
  g.add(v.mesh());
  const glass = new THREE.Mesh(new THREE.SphereGeometry(7, 10, 8), new THREE.MeshLambertMaterial({ color: 0xdfe8f0, transparent: true, opacity: 0.55, emissive: 0x000000 }));
  glass.position.y = 12; g.add(glass);
  const fil = new THREE.Mesh(new THREE.BoxGeometry(4, 0.8, 0.8), new THREE.MeshBasicMaterial({ color: 0x5a4a30 })); fil.position.y = 12; g.add(fil);
  const halo = new THREE.Mesh(new THREE.SphereGeometry(11, 12, 10), new THREE.MeshBasicMaterial({ color: 0xffd860, transparent: true, opacity: 0, depthWrite: false })); halo.position.y = 12; g.add(halo);
  g.userData = { set(on) { glass.material.emissive.setRGB(1.0 * on, 0.82 * on, 0.35 * on); glass.material.opacity = 0.55 + 0.35 * on; fil.material.color.setRGB(0.35 + 0.65 * on, 0.29 + 0.6 * on, 0.19 + 0.3 * on); halo.material.opacity = 0.28 * on; } };
  g.userData.set(0); return g;
}

// a wire through 3D points (axis-aligned runs), plus a sampler along its length
export function wire(points, thick = 1.6, color = COPPER) {
  const g = new THREE.Group(); const mat = new THREE.MeshLambertMaterial({ color });
  const segs = []; let L = 0;
  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i], b = points[i + 1]; const d = b.clone().sub(a); const len = d.length();
    const m = new THREE.Mesh(new THREE.BoxGeometry(Math.abs(d.x) + thick, Math.abs(d.y) + thick, Math.abs(d.z) + thick), mat);
    m.position.copy(a).add(b).multiplyScalar(0.5); m.castShadow = true; m.receiveShadow = true; g.add(m);
    segs.push({ a, b, len, s: L }); L += len;
  }
  g.userData = { L, at(u) { const s = ((u % 1) + 1) % 1 * L; const sg = segs.find((q) => s <= q.s + q.len) || segs[segs.length - 1]; return sg.a.clone().lerp(sg.b, (s - sg.s) / sg.len); } };
  return g;
}

// glowing dots that run along a wire. update(t, flow 0..1, opts)
export function dots(w, n = 24, color = 0xffe066) {
  const inst = new THREE.InstancedMesh(new THREE.BoxGeometry(1.5, 1.5, 1.5), new THREE.MeshBasicMaterial({ color }), n);
  inst.frustumCulled = false; const o = new THREE.Object3D();
  inst.userData = {
    update(t, flow, opts = {}) {
      const speed = opts.speed ?? 0.12, stopAt = opts.stopAt ?? 2; // stopAt: fraction of path where dots pile up (open gap)
      for (let i = 0; i < n; i++) {
        let u = i / n + t * speed * flow;
        if (opts.frozen != null) u = i / n + opts.frozen;
        u = ((u % 1) + 1) % 1;
        if (u > stopAt) u = stopAt - 0.004 * ((i * 7) % 5);
        const p = w.userData.at(u); o.position.copy(p).add(new THREE.Vector3(0, 1.4, 0)); o.scale.setScalar(flow > 0.01 || opts.always ? 1 : 0.0001); o.updateMatrix(); inst.setMatrixAt(i, o.matrix);
      }
      inst.instanceMatrix.needsUpdate = true;
    },
  };
  inst.userData.update(0, 0); return inst;
}

// the transistor: silicon block between two metal pads, gate plate on top, three legs. userData.set(gateOn 0..1)
export function transistor(scale = 1) {
  const g = new THREE.Group(); const v = new VB();
  const si = (x, y, z) => (hash3(x, y, z) > 0.7 ? SILICON_L : SILICON);
  v.box(-8, 4, -6, 8, 10, 6, si);                       // silicon body
  v.box(-14, 4, -5, -9, 10, 5, METAL); v.box(9, 4, -5, 14, 10, 5, METAL); // in/out pads
  v.box(-7, 11, -5, 7, 11, 5, rgb(236, 240, 246));      // thin insulating layer
  v.box(-7, 12, -5, 7, 14, 5, METAL_D);                 // gate plate
  v.box(-12, 0, -1, -11, 3, 0, METAL); v.box(11, 0, -1, 12, 3, 0, METAL); // legs in/out
  v.box(-1, 15, -1, 0, 20, 0, METAL);                   // gate leg (up)
  g.add(v.mesh());
  const ch = new THREE.Mesh(new THREE.BoxGeometry(17, 2, 11.5), new THREE.MeshBasicMaterial({ color: 0xffe066, transparent: true, opacity: 0 }));
  ch.position.set(0, 10.2, 0); g.add(ch);
  const gp = new THREE.Mesh(new THREE.BoxGeometry(15.2, 3.2, 11.2), new THREE.MeshBasicMaterial({ color: 0x7ff6ff, transparent: true, opacity: 0, depthWrite: false }));
  gp.position.set(0, 13.5, 0); g.add(gp);
  g.scale.setScalar(scale);
  g.userData = { set(on) { ch.material.opacity = 0.75 * on; gp.material.opacity = 0.45 * on; }, inL: new THREE.Vector3(-11.5, 0, -0.5), outL: new THREE.Vector3(11.5, 0, -0.5), gateL: new THREE.Vector3(-0.5, 20, -0.5) };
  return g;
}

// ---------- foundry equipment ----------
export function furnace() {
  const v = new VB(); const st = (x, y, z) => (hash3(x, y, z) > 0.5 ? rgb(96, 84, 80) : rgb(80, 70, 68));
  v.box(-16, 0, -12, 16, 26, 12, st);
  for (let x = -7; x <= 7; x++) for (let y = 3; y <= 14; y++) v.set(x, y, 12, null), v.set(x, y, 11, rgb(255, 150, 40)), v.set(x, y, 10, rgb(255, 196, 80));
  v.box(4, 27, -4, 9, 52, 1, st); // chimney
  return v.mesh();
}
// crucible with molten silicon; userData.glow(k)
export function crucible() {
  const g = new THREE.Group(); const v = new VB();
  for (let x = -10; x <= 10; x++) for (let z = -10; z <= 10; z++) { const d = Math.hypot(x, z); if (d > 10.3) continue; for (let y = 0; y <= 9; y++) if (d > 8.4 || y === 0) v.set(x, y, z, hash3(x, y, z) > 0.5 ? rgb(70, 66, 74) : rgb(58, 54, 62)); }
  g.add(v.mesh());
  const melt = new THREE.Mesh(new THREE.CylinderGeometry(8.4, 8.4, 1, 20), new THREE.MeshBasicMaterial({ color: 0xff8a2a })); melt.position.y = 8; g.add(melt);
  const halo = new THREE.Mesh(new THREE.CylinderGeometry(12, 12, 0.4, 20), new THREE.MeshBasicMaterial({ color: 0xffa040, transparent: true, opacity: 0.25, depthWrite: false })); halo.position.y = 8.8; g.add(halo);
  g.userData = { melt, glow(k) { melt.material.color.setRGB(1, 0.42 + 0.2 * k, 0.12 + 0.1 * k); halo.material.opacity = 0.15 + 0.25 * k; } };
  return g;
}
// silicon crystal ingot (grows/rises); userData.grow(k)
export function ingot() {
  const g = new THREE.Group(); const v = new VB();
  for (let y = 0; y < 40; y++) { const r = y < 3 ? 2 + y * 2 : y > 36 ? 8 - (y - 36) * 1.5 : 7.5; for (let x = -9; x <= 9; x++) for (let z = -9; z <= 9; z++) if (Math.hypot(x, z) <= r) v.set(x, y, z, hash3(x, y, z) > 0.75 ? rgb(170, 180, 204) : rgb(132, 142, 168)); }
  const m = v.mesh(); g.add(m);
  const rod = new THREE.Mesh(new THREE.BoxGeometry(1.2, 40, 1.2), new THREE.MeshLambertMaterial({ color: 0x8a8f9a })); rod.position.y = 60; g.add(rod);
  g.userData = { grow(k) { m.scale.y = Math.max(0.001, k); } };
  return g;
}
// wafer: thin disc with a grid of chips (canvas texture). userData.chips(k) reveals the printed grid
export function wafer(r = 16) {
  const g = new THREE.Group();
  const cv = document.createElement('canvas'); cv.width = cv.height = 512; const x = cv.getContext('2d');
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const top = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.8, 48), [new THREE.MeshLambertMaterial({ color: 0x9aa2b4 }), new THREE.MeshLambertMaterial({ map: tex }), new THREE.MeshLambertMaterial({ color: 0x9aa2b4 })]);
  top.castShadow = true; top.receiveShadow = true; g.add(top);
  const draw = (k) => {
    const gr = x.createLinearGradient(0, 0, 512, 512); gr.addColorStop(0, '#c9d1e0'); gr.addColorStop(0.5, '#9ea8c0'); gr.addColorStop(1, '#d4dbe8'); x.fillStyle = gr; x.fillRect(0, 0, 512, 512);
    const cs = 34;
    for (let i = 0; i < 15; i++) for (let j = 0; j < 15; j++) {
      const cx = i * cs + 2, cy = j * cs + 2; if (Math.hypot(cx + cs / 2 - 256, cy + cs / 2 - 256) > 236) continue;
      const d = ((i * 7 + j * 13) % 15) / 15; if (d >= k) continue;
      const hue = (190 + (i * 17 + j * 29) % 120); x.fillStyle = `hsl(${hue},55%,${48 + (i + j) % 3 * 6}%)`; x.fillRect(cx, cy, cs - 4, cs - 4);
      x.fillStyle = 'rgba(255,255,255,0.25)'; x.fillRect(cx + 4, cy + 4, cs - 12, 3);
    }
    tex.needsUpdate = true;
  };
  draw(0);
  g.userData = { chips(k) { if (Math.abs((g.userData._k ?? -1) - k) > 0.01) { draw(k); g.userData._k = k; } } };
  return g;
}
