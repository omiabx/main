// Character + prop models. 1 unit = 1 small voxel. Characters face +z.
import * as THREE from 'three';
import { VB, rgb, shade, hash3, MAT } from './vox.js';

export const C = {
  skin: rgb(232, 172, 124), skinD: rgb(214, 150, 104), cheek: rgb(240, 136, 128),
  hair: rgb(104, 62, 36), hairD: rgb(86, 50, 30),
  eye: rgb(30, 34, 52), eyeHi: rgb(84, 96, 128), mouth: rgb(120, 52, 46),
  shirt: rgb(40, 100, 200), vest: rgb(112, 70, 40), vestD: rgb(96, 58, 32),
  scarf: rgb(206, 44, 40), belt: rgb(236, 190, 64), buckle: rgb(196, 44, 40),
  pants: rgb(92, 60, 40), shoe: rgb(60, 40, 30),
  straw: rgb(218, 174, 104), strawD: rgb(198, 152, 86), band: rgb(204, 52, 44),
  // friend
  fskin: rgb(176, 114, 76), fskinD: rgb(156, 98, 64), fhair: rgb(38, 30, 32), fshirt: rgb(72, 156, 82), fscarf: rgb(236, 196, 70),
  // props
  wood: rgb(120, 78, 44), woodD: rgb(92, 58, 32), woodL: rgb(146, 98, 58),
  lampOn: rgb(255, 214, 72), lampOff: rgb(58, 60, 82),
  sand: rgb(234, 202, 142), sand2: rgb(226, 192, 130), sandD: rgb(212, 176, 116),
  rock1: rgb(214, 132, 82), rock2: rgb(190, 104, 66), rock3: rgb(226, 156, 98),
  cactus: rgb(76, 160, 70), cactusD: rgb(58, 132, 56), flower: rgb(240, 120, 160),
  stone: rgb(150, 140, 132), stoneD: rgb(124, 116, 110),
  wall: rgb(240, 226, 196), roof: rgb(204, 64, 50), roofD: rgb(170, 48, 40),
};

function part(vb, pivot, opts = {}) {
  const m = vb.mesh({ offset: pivot, ...opts });
  const g = new THREE.Group(); g.add(m); g.position.set(...pivot); return g;
}

// generic humanoid. kind: 'bob' | 'friend'
export function character(kind = 'bob', opt = {}) {
  const B = kind === 'bob';
  const skin = B ? C.skin : C.fskin, skinD = B ? C.skinD : C.fskinD;
  const root = new THREE.Group(); const P = {};
  // legs
  for (const [side, x0] of [['legL', -4], ['legR', 0]]) {
    const v = new VB();
    v.box(x0, 0, -2, x0 + 3, 5, 1, C.pants);
    v.box(x0, 0, -2, x0 + 3, 1, 2, C.shoe);
    P[side] = part(v, [x0 + 2, 6, 0]); root.add(P[side]);
  }
  // body
  const b = new VB();
  if (B) {
    b.box(-4, 6, -2, 3, 13, 2, C.shirt);
    b.box(-4, 7, -2, 3, 12, 2, (x, y, z) => (x <= -2 || x >= 1 || z < 2) ? (z === 2 ? C.vest : C.vestD) : C.shirt);
    b.box(-4, 6, -2, 3, 6, 2, C.belt); b.box(-1, 6, 2, 0, 6, 2, C.buckle);
    b.box(-3, 13, 2, 2, 13, 2, C.scarf); b.box(-4, 13, -2, 3, 13, 2, (x, y, z) => (z >= 1 || Math.abs(x + 0.5) > 3) ? C.scarf : C.shirt);
    b.box(-1, 11, 3, 0, 12, 3, C.scarf);
  } else {
    b.box(-4, 6, -2, 3, 13, 2, C.fshirt);
    b.box(-4, 6, -2, 3, 6, 2, C.pants);
    b.box(-4, 13, -2, 3, 13, 2, C.fscarf); b.box(-1, 8, 2, 0, 12, 2, C.fscarf); b.box(-1, 7, 3, 0, 9, 3, C.fscarf);
  }
  P.body = part(b, [0, 6, 0]); root.add(P.body);
  // arms
  for (const [side, x0] of [['armL', -7], ['armR', 4]]) {
    const v = new VB();
    v.box(x0, 7, -1, x0 + 2, 13, 1, B ? C.shirt : C.fshirt);
    v.box(x0, 7, -1, x0 + 2, 8, 1, skin);
    P[side] = part(v, [x0 + 1, 13, 0]); root.add(P[side]);
  }
  // head (neck at y=14)
  const h = new VB(); const Y = 14;
  h.box(-6, Y, -6, 5, Y + 10, 5, skin);
  const hair = B ? C.hair : C.fhair;
  // hair: top, back, sides upper
  h.box(-6, Y + 9, -6, 5, Y + 10, 5, hair);
  h.box(-6, Y + 3, -6, 5, Y + 10, -5, hair);
  h.box(-6, Y + 6, -6, -6, Y + 10, 4, hair); h.box(5, Y + 6, -6, 5, Y + 10, 4, hair);
  h.box(-6, Y + 4, -6, -6, Y + 5, -1, hair); h.box(5, Y + 4, -6, 5, Y + 5, -1, hair);
  // fringe
  for (let x = -6; x <= 5; x++) { const d = B ? [1, 2, 2, 1, 1, 2, 1, 1, 2, 2, 1, 2][x + 6] : [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2][x + 6]; h.box(x, Y + 10 - d, 5, x, Y + 10, 5, hair); }
  // face
  h.box(-5, Y + 2, 5, -4, Y + 3, 5, C.cheek); h.box(3, Y + 2, 5, 4, Y + 3, 5, C.cheek);
  h.box(-1, Y + 3, 6, 0, Y + 4, 7, skinD); // nose
  h.box(-1, Y + 1, 5, 0, Y + 1, 5, C.mouth);
  if (opt.mouth === 'open') { h.box(-1, Y, 5, 0, Y + 1, 5, C.mouth); h.box(-1, Y, 4, 0, Y + 1, 4, rgb(70, 30, 30)); }
  if (opt.brows) { h.box(-4, Y + 8, 6, -3, Y + 8, 6, B ? C.hairD : C.fhair); h.box(1, Y + 8, 6, 2, Y + 8, 6, B ? C.hairD : C.fhair); }
  h.box(-7, Y + 4, -1, -7, Y + 5, 0, skin); h.box(6, Y + 4, -1, 6, Y + 5, 0, skin); // ears
  if (B) {
    // straw hat
    const straw = (x, y, z) => ((x + z + y) & 1) ? C.straw : C.strawD;
    h.box(-9, Y + 10, -9, 8, Y + 10, 8, straw);
    h.box(-5, Y + 11, -5, 4, Y + 14, 4, straw);
    h.box(-5, Y + 11, -5, 4, Y + 11, 4, C.band);
    h.box(-4, Y + 15, -4, 3, Y + 15, 3, straw);
  } else {
    h.box(-2, Y + 11, -3, 1, Y + 13, 0, C.fhair); h.box(-1, Y + 14, -2, 0, Y + 14, -1, C.fhair);
  }
  P.head = part(h, [0, Y, 0]); root.add(P.head);
  // eyes (separate for blinking)
  for (const [side, x0] of [['eyeL', -4], ['eyeR', 1]]) {
    const v = new VB();
    v.box(x0, Y + 4, 6, x0 + 1, Y + 6, 6, C.eye); v.set(x0 + (side === 'eyeL' ? 1 : 0), Y + 6, 6, C.eyeHi);
    const g = part(v, [x0 + 1, Y + 5, 6], { cast: false }); P[side] = g; P.head.add(g); g.position.sub(new THREE.Vector3(0, Y, 0));
  }
  root.userData.P = P; root.userData.kind = kind;
  return root;
}

// pose: {walk: phase, wave: 0..1, point: 0..1, think: 0..1, blink: 0..1, look: yaw, nod, jump}
export function pose(ch, t, o = {}) {
  const P = ch.userData.P;
  const breathe = Math.sin(t * 2.2) * 0.25;
  P.body.position.y = 6 + breathe * 0.4; P.head.position.y = 14 + breathe * 0.6;
  for (const k of ['armL', 'armR', 'legL', 'legR']) P[k].rotation.set(0, 0, 0);
  P.head.rotation.set(0, 0, 0);
  P.armL.position.y = P.armR.position.y = 13 + breathe * 0.4;
  P.armL.rotation.z = -0.06; P.armR.rotation.z = 0.06;
  if (o.walk != null) {
    const s = Math.sin(o.walk);
    P.legL.rotation.x = s * 0.6; P.legR.rotation.x = -s * 0.6; P.armL.rotation.x = -s * 0.6; P.armR.rotation.x = s * 0.6;
    const bounce = Math.abs(Math.cos(o.walk)) * 0.8; P.body.position.y += bounce; P.head.position.y += bounce; P.armL.position.y += bounce; P.armR.position.y += bounce;
  }
  if (o.wave) { const w = o.wave; P.armR.rotation.z = 0.06 + 2.6 * w; P.armR.rotation.x = 0; P.armR.rotation.y = Math.sin(t * 9) * 0.35 * w; }
  if (o.point) { const w = o.point; P.armR.rotation.x = -1.45 * w; }
  if (o.pointL) { const w = o.pointL; P.armL.rotation.x = -1.45 * w; }
  if (o.think) { const w = o.think; P.armR.rotation.x = -2.2 * w; P.armR.rotation.z = 0.06 - 0.5 * w; P.head.rotation.z = 0.12 * w; }
  if (o.cheer) { const w = o.cheer; P.armL.rotation.z = -0.06 - 2.7 * w; P.armR.rotation.z = 0.06 + 2.7 * w; }
  if (o.lookY) P.head.rotation.y = o.lookY;
  if (o.tilt) P.head.rotation.z += o.tilt;
  if (o.nod) P.head.rotation.x = o.nod;
  const bl = o.blink ?? blinkAt(t);
  P.eyeL.scale.y = P.eyeR.scale.y = 1 - 0.85 * bl;
}
export function blinkAt(t) { const p = (t + 0.37) % 3.7; return p < 0.14 ? Math.sin(p / 0.14 * Math.PI) : 0; }

// ---------- props ----------
export function lampBoard(n = 8) {
  const g = new THREE.Group(); const v = new VB();
  const cell = 9, W = n * cell + 2, H0 = 22;
  v.box(-2, 0, -1, 0, H0 + cell + 3, 1, C.woodD); v.box(W, 0, -1, W + 2, H0 + cell + 3, 1, C.woodD);
  v.box(-3, H0 + cell + 2, -2, W + 3, H0 + cell + 4, 2, C.wood);
  v.box(0, H0, -1, W, H0 + cell + 1, 0, C.woodD);
  for (let i = 0; i <= n; i++) v.box(1 + i * cell, H0, 0, 1 + i * cell, H0 + cell + 1, 1, C.wood);
  v.box(0, H0, 0, W, H0, 1, C.wood); v.box(0, H0 + cell + 1, 0, W, H0 + cell + 1, 1, C.wood);
  const frame = v.mesh({ offset: [W / 2, 0, 0] }); g.add(frame);
  const lamps = [];
  for (let i = 0; i < n; i++) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(cell - 2.6, cell - 2.6, 1.2), new THREE.MeshLambertMaterial({ color: C.lampOff }));
    m.position.set(1 + i * cell + cell / 2 + 0.5 - W / 2, H0 + cell / 2 + 1, 0.9); m.castShadow = false; m.receiveShadow = true;
    g.add(m); lamps.push(m);
  }
  g.userData.lamps = lamps; g.userData.top = H0 + cell + 4; g.userData.lampY = H0 + cell / 2 + 1; g.userData.cell = cell; g.userData.W = W;
  g.userData.set = (bits) => { // bits: array of 0/1 or number
    if (typeof bits === 'number') bits = [...bits.toString(2).padStart(n, '0')].map(Number);
    lamps.forEach((m, i) => { const on = bits[i] > 0; m.material.color.setHex(on ? C.lampOn : C.lampOff); m.material.emissive.setHex(on ? 0x8a6a10 : 0); });
  };
  return g;
}

// paint wall: n x n tiles; tiles via InstancedMesh
export function paintWall(n = 8, size = 64) {
  const g = new THREE.Group(); const v = new VB(); const W = size + 6;
  v.box(-3, 0, -2, -1, W + 18, 0, C.woodD); v.box(W - 3, 0, -2, W - 1, W + 18, 0, C.woodD);
  v.box(-1, 14, -2, W - 3, W + 16, -1, rgb(40, 38, 52));
  v.box(-2, 13, -1, W - 2, 13, 0, C.wood); v.box(-2, W + 17, -1, W - 2, W + 17, 0, C.wood);
  v.box(-2, 13, -1, -2, W + 17, 0, C.wood); v.box(W - 2, 13, -1, W - 2, W + 17, 0, C.wood);
  g.add(v.mesh({ offset: [W / 2 - 2, 0, 0] }));
  const inst = makeTiles(n, size, 1.6);
  inst.position.set(0, 15 + size / 2 + 1, 0.2); g.add(inst);
  g.userData.tiles = inst; g.userData.center = new THREE.Vector3(0, 15 + size / 2 + 1, 0);
  return g;
}

// grid of tiles (InstancedMesh) centered at origin in XY plane. API: setTile(i, color, scale)
export function makeTiles(n, size, depth = 1.5, gap = 0.12, cols = n, rows = n) {
  const ts = size / Math.max(cols, rows);
  const geo = new THREE.BoxGeometry(ts * (1 - gap), ts * (1 - gap), depth);
  geo.translate(0, 0, depth / 2);
  const mat = new THREE.MeshLambertMaterial({ color: 0xffffff });
  const inst = new THREE.InstancedMesh(geo, mat, cols * rows);
  inst.castShadow = false; inst.receiveShadow = true; inst.frustumCulled = false;
  const o = new THREE.Object3D(); const col = new THREE.Color();
  inst.userData = {
    n, cols, rows, ts,
    layout(c2, r2) { inst.userData.cols = c2; inst.userData.rows = r2; },
    set(i, color, sc = 1, lift = 0) {
      const { cols: cc, rows: rr } = inst.userData; const ts2 = size / Math.max(cc, rr);
      const cx = i % cc, cy = Math.floor(i / cc);
      o.position.set((cx - (cc - 1) / 2) * ts2, ((rr - 1) / 2 - cy) * ts2, lift);
      o.scale.setScalar(Math.max(0.0001, sc) * ts2 / ts); o.updateMatrix(); inst.setMatrixAt(i, o.matrix);
      inst.setColorAt(i, col.setHex(color)); inst.instanceMatrix.needsUpdate = true; if (inst.instanceColor) inst.instanceColor.needsUpdate = true;
    },
    hideAll() { for (let i = 0; i < inst.count; i++) { o.scale.setScalar(0.0001); o.position.set(0, 0, 0); o.updateMatrix(); inst.setMatrixAt(i, o.matrix); inst.setColorAt(i, col.setHex(0)); } inst.instanceMatrix.needsUpdate = true; },
  };
  inst.userData.hideAll();
  return inst;
}

export function cactus(seed = 1, h = 14) {
  const v = new VB();
  const col = (x, y, z) => (hash3(x, y, z + seed) > 0.5 ? C.cactus : C.cactusD);
  v.box(-1, 0, -1, 1, h, 1, col);
  const ah = Math.floor(h * 0.45);
  v.box(2, ah, 0, 3, ah + 1, 0, col); v.box(3, ah, -0, 4, ah + 5, 0, col);
  v.box(-3, ah + 2, 0, -2, ah + 3, 0, col); v.box(-4, ah + 2, 0, -3, ah + 7, 0, col);
  v.set(0, h + 1, 0, C.flower); v.set(4, ah + 6, 0, C.flower); v.set(-4, ah + 8, 0, C.flower);
  return v.mesh();
}
export function rock(seed = 1, s = 5) {
  const v = new VB();
  for (let x = -s; x <= s; x++) for (let z = -s; z <= s; z++) for (let y = 0; y <= s; y++) {
    const d = Math.sqrt(x * x * 0.8 + z * z + (y * 1.6) ** 2) + hash3(x, y, z + seed) * 1.6;
    if (d < s) v.set(x, y, z, hash3(x, y, z) > 0.5 ? C.stone : C.stoneD);
  }
  return v.mesh();
}
export function house() {
  const v = new VB();
  v.box(-10, 0, -9, 10, 15, 9, C.wall);
  v.box(-3, 0, 9, 2, 9, 9, C.woodD); // door
  v.box(5, 7, 9, 8, 10, 9, rgb(90, 140, 190)); v.box(-8, 7, 9, -6, 10, 9, rgb(90, 140, 190));
  for (let k = 0; k < 7; k++) v.box(-12 + k, 16 + k, -11 + k, 12 - k, 16 + k, 11 - k, (x, y, z) => ((x + y) % 3 === 0 ? C.roofD : C.roof));
  v.box(-12, 15, -11, 12, 15, 11, C.roofD);
  return v.mesh();
}
export function flag(color = rgb(220, 50, 50)) {
  const g = new THREE.Group(); const v = new VB();
  v.box(0, 0, 0, 0, 22, 0, C.woodD); v.box(-1, 0, -1, 1, 0, 1, C.stoneD);
  g.add(v.mesh());
  const cloth = new THREE.Group(); cloth.position.set(0.5, 22, 0.5); g.add(cloth);
  const segs = [];
  for (let i = 0; i < 6; i++) {
    const s = new THREE.Mesh(new THREE.BoxGeometry(1.6, 7, 0.8), new THREE.MeshLambertMaterial({ color }));
    s.castShadow = true; s.position.set(0.8 + i * 1.6, -3.5, 0); cloth.add(s); segs.push(s);
  }
  g.userData.wave = (t) => segs.forEach((s, i) => { s.position.z = Math.sin(t * 6 - i * 0.9) * 0.35 * i; s.position.y = -3.5 - i * 0.12; });
  g.userData.wave(0);
  return g;
}

// phone standing upright, screen faces +z. returns group with userData.screen (mesh, plane) w=26,h=50
export function phone() {
  const g = new THREE.Group(); const v = new VB();
  const W = 28, H = 54;
  v.box(0, 0, -2, W - 1, H - 1, 1, (x, y) => ((x === 0 || x === W - 1 || y === 0 || y === H - 1) ? rgb(50, 52, 64) : rgb(34, 36, 46)));
  v.box(W / 2 - 3, H - 3, 2, W / 2 + 2, H - 3, 2, rgb(20, 20, 26));
  g.add(v.mesh({ offset: [W / 2, 0, 0] }));
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(W - 4, H - 8), new THREE.MeshBasicMaterial({ color: 0xffffff }));
  scr.position.set(0, H / 2 - 0.5, 2.05); g.add(scr);
  g.userData.screen = scr; g.userData.sw = W - 4; g.userData.sh = H - 8; g.userData.H = H;
  return g;
}

export function pedestal(r = 24) {
  const v = new VB();
  for (let x = -r; x <= r; x++) for (let z = -r; z <= r; z++) {
    const d = Math.sqrt(x * x + z * z); if (d > r) continue;
    for (let y = 0; y < 6; y++) {
      let c = (y < 5) ? ((hash3(x, y, z) > 0.5) ? rgb(112, 64, 196) : rgb(96, 52, 176)) : rgb(124, 78, 210);
      if (y === 5 && d > r - 2.2) c = (hash3(x, 0, z) > 0.5 ? rgb(246, 196, 70) : rgb(232, 178, 52));
      if (y === 4 && d > r - 1) c = rgb(232, 178, 52);
      v.set(x, y, z, c);
    }
  }
  return v.mesh();
}
