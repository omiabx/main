// =====================================================================
//  THE OVERWORLD MAP  (persistent series asset — do not redesign)
//  One fixed, seeded world. Only the STATE changes per episode:
//    buildMap({ episode: N })  ->  waypoints 1..N-1 cleared (flags),
//    waypoint N is current, regions after the current one are fogged.
// =====================================================================
import * as THREE from 'three';
import { VB, rgb, hash3, shade, mix, desat, rng } from './vox.js';
import { C, character, flag } from './models.js';
import { SKY, lights, makeCam, aim, v3 } from './core.js';
import { noise2 } from './terrain.js';

export const BS = 4;               // block size in world units
export const MW = 124, MD = 72;    // map size in blocks (x = east, z = south)
export const REGIONS = [
  { key: 'desert',  name: 'THE DESERT',  cps: [[7, 64], [15, 56], [24, 62], [32, 54], [40, 60]] },
  { key: 'foundry', name: 'THE FOUNDRY', cps: [[48, 54], [56, 62], [66, 56], [74, 61]] },
  { key: 'village', name: 'THE VILLAGE', cps: [[84, 56], [94, 62], [104, 56], [112, 60], [116, 50]] },
  { key: 'town',    name: 'THE TOWN',    cps: [[109, 42], [99, 37], [89, 43], [79, 37]] },
  { key: 'city',    name: 'THE CITY',    cps: [[69, 41], [58, 35], [47, 41], [36, 35], [25, 39], [14, 35]] },
  { key: 'network', name: 'THE NETWORK', cps: [[9, 25], [18, 17], [30, 23], [42, 15], [54, 21]] },
  { key: 'capital', name: 'THE CAPITAL', cps: [[66, 15], [78, 21], [90, 13], [102, 19], [114, 10]] },
];
export const WAYPOINTS_PER_REGION = 6;   // 7 regions x 6 = 42 stops
// Episodes already published: 1 What is a computer? 2 Why 1s and 0s 3 Counting in binary 4 Binary -> text 5 Pictures

// ---------- path ----------
function catmull(p0, p1, p2, p3, t) {
  const t2 = t * t, t3 = t2 * t;
  return [0, 1].map((i) => 0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3));
}
export function pathData() {
  const cps = []; const regOf = [];
  REGIONS.forEach((r, ri) => r.cps.forEach((p) => { cps.push(p); regOf.push(ri); }));
  const pts = [];
  for (let i = 0; i < cps.length - 1; i++) {
    const p0 = cps[Math.max(0, i - 1)], p1 = cps[i], p2 = cps[i + 1], p3 = cps[Math.min(cps.length - 1, i + 2)];
    for (let k = 0; k < 40; k++) { const t = k / 40; pts.push({ p: catmull(p0, p1, p2, p3, t), seg: i + t }); }
  }
  pts.push({ p: cps[cps.length - 1], seg: cps.length - 1 });
  let L = 0; pts.forEach((q, i) => { if (i) L += Math.hypot(q.p[0] - pts[i - 1].p[0], q.p[1] - pts[i - 1].p[1]); q.s = L; });
  // region boundaries: halfway between last cp of region and first of next
  const segBound = []; let idx = 0;
  REGIONS.forEach((r, ri) => { idx += r.cps.length; if (ri < REGIONS.length - 1) segBound.push(idx - 0.5); });
  const sAtSeg = (sg) => { const q = pts.find((x) => x.seg >= sg) || pts[pts.length - 1]; return q.s; };
  const bounds = [0, ...segBound.map(sAtSeg), L];
  pts.forEach((q) => { q.r = bounds.findIndex((b, i) => q.s >= b && q.s < bounds[i + 1]); if (q.r < 0) q.r = REGIONS.length - 1; });
  const at = (s) => { let i = pts.findIndex((q) => q.s >= s); if (i <= 0) i = Math.max(1, i < 0 ? pts.length - 1 : 1); const a = pts[i - 1], b = pts[i]; const f = (s - a.s) / Math.max(1e-6, b.s - a.s); return [a.p[0] + (b.p[0] - a.p[0]) * f, a.p[1] + (b.p[1] - a.p[1]) * f]; };
  const wps = [];
  REGIONS.forEach((r, ri) => { const a = bounds[ri], b = bounds[ri + 1]; for (let k = 0; k < WAYPOINTS_PER_REGION; k++) { const s = a + (b - a) * (k + 0.5) / WAYPOINTS_PER_REGION; wps.push({ s, p: at(s), r: ri, n: wps.length + 1 }); } });
  return { pts, bounds, L, at, wps };
}

// ---------- palette per region ----------
const PAL = {
  desert:  { g: [rgb(234, 202, 142), rgb(226, 192, 130), rgb(220, 186, 124)], side: rgb(214, 132, 82), path: rgb(170, 118, 74) },
  foundry: { g: [rgb(132, 116, 104), rgb(120, 106, 96), rgb(142, 124, 110)], side: rgb(92, 80, 74), path: rgb(186, 170, 150) },
  village: { g: [rgb(116, 184, 84), rgb(104, 172, 74), rgb(128, 192, 92)], side: rgb(130, 96, 60), path: rgb(206, 178, 124) },
  town:    { g: [rgb(104, 168, 86), rgb(96, 158, 80), rgb(112, 176, 92)], side: rgb(120, 92, 62), path: rgb(176, 170, 160) },
  city:    { g: [rgb(132, 140, 150), rgb(122, 130, 140), rgb(140, 148, 158)], side: rgb(90, 96, 106), path: rgb(70, 74, 84) },
  network: { g: [rgb(46, 52, 78), rgb(40, 46, 70), rgb(52, 58, 86)], side: rgb(30, 34, 52), path: rgb(70, 220, 240) },
  capital: { g: [rgb(236, 236, 244), rgb(226, 228, 238), rgb(244, 242, 250)], side: rgb(190, 196, 214), path: rgb(250, 210, 90) },
};

// ---------- build ----------
export function buildMap(opts = {}) {
  const episode = opts.episode ?? 5;
  const scene = new THREE.Scene(); scene.background = SKY.map;
  const L = lights(scene, 'day'); L.sun.position.set(-120, 260, 160); L.sun.userData.dir = L.sun.position.clone().normalize(); L.sun.intensity = 2.3;
  const cam = makeCam(30);
  const PD = pathData(); const { pts, wps } = PD;
  const cur = wps[episode - 1]; const curR = cur.r;
  const state = (ri) => (ri < curR ? 'passed' : ri === curR ? 'current' : 'locked');
  const R = rng(5150);

  // tile -> nearest path sample
  const near = new Array(MW * MD);
  for (let x = 0; x < MW; x++) for (let z = 0; z < MD; z++) {
    let best = 1e9, bq = null;
    for (let i = 0; i < pts.length; i += 2) { const q = pts[i]; const d = (q.p[0] - x) ** 2 + (q.p[1] - z) ** 2; if (d < best) { best = d; bq = q; } }
    // dither region border with noise
    const jitter = (noise2(x, z, 3) - 0.5) * 7;
    let r = bq.r; const sj = bq.s + jitter; if (PD.bounds[r] > sj && r > 0) r--; else if (PD.bounds[r + 1] < sj && r < REGIONS.length - 1) r++;
    near[x * MD + z] = { d: Math.sqrt(best), r, s: bq.s };
  }
  const tile = (x, z) => (x < 0 || z < 0 || x >= MW || z >= MD) ? null : near[x * MD + z];
  const isLand = (x, z) => { const n = hash3(Math.floor(x / 3), 1, Math.floor(z / 3)); const m = 3 + n * 2; return x >= m && z >= m && x < MW - m && z < MD - m; };

  const terr = REGIONS.map(() => new VB()); const props = REGIONS.map(() => new VB());
  const water = new VB();
  const canyon = (x, z) => { // the canyon from episode 4: crosses the desert near stop 4/5
    const cx = 31 + Math.sin(z * 0.35) * 1.5; return Math.abs(x - cx) < 1.6 && z > 44 && z < 71;
  };
  for (let x = -40; x < MW + 40; x++) for (let z = -30; z < MD + 30; z++) {
    if (!isLand(x, z)) { water.set(x, -1, z, hash3(x, 9, z) > 0.5 ? rgb(56, 124, 196) : rgb(64, 134, 206)); continue; }
    const T = tile(x, z); const reg = REGIONS[T.r]; const P = PAL[reg.key];
    let h = 1 + (noise2(x + 40, z, 7) > 0.64 && T.d > 3 ? 1 : 0);
    const onPath = T.d < 1.25;
    if (T.d < 3) h = 1;
    if (reg.key === 'desert' && canyon(x, z) && !onPath) {
      terr[T.r].set(x, -2, z, rgb(70, 140, 210)); terr[T.r].set(x, -1, z, rgb(180, 96, 60)); continue;
    }
    const v = terr[T.r];
    for (let y = -1; y <= h; y++) {
      let c = y === h ? P.g[Math.floor(hash3(x, y, z) * 3)] : P.side;
      if (y === h && onPath) c = reg.key === 'network' ? (hash3(x, 0, z) > 0.5 ? rgb(60, 200, 224) : rgb(80, 230, 250)) : shade(P.path, 0.97 + hash3(x, 1, z) * 0.06);
      else if (y === h && T.d < 1.8) c = mix(c, P.path, 0.18);
      if (y < h && (x < 4 || z < 4 || x > MW - 5 || z > MD - 5)) c = shade(P.side, 0.9);
      v.set(x, y, z, c);
    }
    // bridge over canyon
    if (reg.key === 'desert' && canyon(x, z) && onPath) v.set(x, h, z, C.woodL);
  }
  // waypoint markers
  wps.forEach((w) => {
    const [wx, wz] = w.p; const x = Math.round(wx), z = Math.round(wz);
    const v = terr[w.r];
    for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) v.set(x + dx, 1, z + dz, rgb(168, 162, 156));
    v.set(x, 1, z, rgb(150, 144, 140)); v.set(x, 2, z, rgb(246, 204, 76));
  });

  // ---------- props per region (unit-scale voxels; coordinates in units) ----------
  const U = (bx) => bx * BS;
  const groundY = (x, z) => { const T = tile(Math.floor(x / BS), Math.floor(z / BS)); return T ? (terr[T.r].has(Math.floor(x / BS), 2, Math.floor(z / BS)) ? 3 : terr[T.r].has(Math.floor(x / BS), 1, Math.floor(z / BS)) ? 2 : 1) * BS : BS; };
  const freeSpot = (ri, minD = 3) => { for (let k = 0; k < 400; k++) { const x = 4 + R() * (MW - 8), z = 4 + R() * (MD - 8); const T = tile(Math.floor(x), Math.floor(z)); if (T && T.r === ri && T.d > minD && isLand(Math.floor(x), Math.floor(z)) && !canyon(Math.floor(x), Math.floor(z))) return [x * BS, z * BS]; } return null; };
  const anims = [];
  const addObj = (ri, build, n, minD) => { for (let i = 0; i < n; i++) { const s = freeSpot(ri, minD); if (!s) continue; build(props[ri], Math.round(s[0]), groundY(s[0], s[1]), Math.round(s[1]), i); } };
  const cactusV = (v, x, y, z, i) => { const h = 5 + (i % 3) * 2; v.box(x, y, z, x, y + h, z, C.cactus); v.box(x + 1, y + 3, z, x + 2, y + 3, z, C.cactus); v.box(x + 2, y + 3, z, x + 2, y + 5, z, C.cactus); v.set(x, y + h + 1, z, C.flower); };
  const rockV = (v, x, y, z) => { v.box(x - 1, y, z - 1, x + 1, y + 1, z + 1, C.stone); v.set(x, y + 2, z, C.stoneD); };
  const treeV = (v, x, y, z, i) => { v.box(x, y, z, x, y + 3, z, C.woodD); const g = i % 2 ? rgb(60, 140, 60) : rgb(72, 156, 66); v.box(x - 2, y + 4, z - 2, x + 2, y + 6, z + 2, g); v.box(x - 1, y + 7, z - 1, x + 1, y + 7, z + 1, g); };
  const houseV = (v, x, y, z, i, roof = C.roof) => { v.box(x - 3, y, z - 3, x + 3, y + 4, z + 3, C.wall); v.box(x, y, z + 3, x, y + 2, z + 3, C.woodD); for (let k = 0; k < 4; k++) v.box(x - 4 + k, y + 5 + k, z - 4 + k, x + 4 - k, y + 5 + k, z + 4 - k, roof); };
  const smokeSrc = [];
  const furnaceV = (v, x, y, z, i) => { v.box(x - 4, y, z - 3, x + 4, y + 6, z + 3, rgb(70, 62, 60)); v.box(x - 4, y, z + 3, x - 1, y + 3, z + 3, rgb(255, 140, 40)); v.box(x + 2, y, z - 2, x + 3, y + 16, z - 1, rgb(84, 74, 70)); v.box(x + 2, y + 16, z - 2, x + 3, y + 16, z - 1, rgb(40, 34, 32)); smokeSrc.push([x + 3, y + 17, z - 1]); };
  const lavaV = (v, x, y, z) => { v.box(x - 3, y - 1, z, x + 3, y - 1, z, rgb(255, 120, 30)); };
  const windmillV = (v, x, y, z) => { v.box(x - 2, y, z - 2, x + 2, y + 12, z + 2, C.wall); v.box(x - 3, y + 13, z - 3, x + 3, y + 14, z + 3, C.roof); v.box(x - 6, y + 9, z + 3, x + 6, y + 9, z + 3, C.woodL); v.box(x, y + 3, z + 3, x, y + 15, z + 3, C.woodL); };
  const fieldV = (v, x, y, z) => { for (let a = -5; a <= 5; a++) for (let b = -3; b <= 3; b++) v.set(x + a, y, z + b, (b & 1) ? rgb(230, 200, 80) : rgb(150, 190, 70)); };
  const townV = (v, x, y, z, i) => { const hh = 6 + (i % 3) * 3; const roofs = [rgb(60, 110, 200), rgb(220, 120, 50), C.roof]; v.box(x - 3, y, z - 3, x + 3, y + hh, z + 3, i % 2 ? rgb(236, 220, 190) : rgb(214, 196, 170)); for (let k = 0; k < 3; k++) v.box(x - 4 + k, y + hh + 1 + k, z - 4 + k, x + 4 - k, y + hh + 1 + k, z + 4 - k, roofs[i % 3]); for (let wy = y + 2; wy < y + hh; wy += 3) v.box(x - 2, wy, z + 3, x - 1, wy + 1, z + 3, rgb(90, 140, 190)); };
  const clockV = (v, x, y, z) => { v.box(x - 3, y, z - 3, x + 3, y + 24, z + 3, rgb(200, 186, 160)); v.box(x - 2, y + 18, z + 3, x + 2, y + 22, z + 3, rgb(250, 250, 240)); v.set(x, y + 20, z + 4, rgb(30, 30, 30)); for (let k = 0; k < 4; k++) v.box(x - 4 + k, y + 25 + k * 2, z - 4 + k, x + 4 - k, y + 26 + k * 2, z + 4 - k, rgb(60, 110, 200)); };
  const towerV = (v, x, y, z, i) => { const hh = 12 + Math.floor(hash3(x, 0, z) * 18); const col = [rgb(120, 170, 220), rgb(150, 160, 180), rgb(90, 140, 200)][i % 3]; v.box(x - 3, y, z - 3, x + 3, y + hh, z + 3, (xx, yy, zz) => (yy % 3 === 0 ? rgb(70, 80, 96) : ((xx + zz) & 1 ? col : shade(col, 1.12)))); v.box(x - 2, y + hh + 1, z - 2, x + 2, y + hh + 1, z + 2, rgb(70, 80, 96)); };
  const antennaV = (v, x, y, z) => { v.box(x, y, z, x, y + 20, z, rgb(160, 170, 190)); v.box(x - 2, y, z - 2, x + 2, y, z + 2, rgb(90, 96, 120)); v.set(x, y + 21, z, rgb(255, 80, 80)); for (let k = 4; k < 20; k += 5) v.box(x - 2, y + k, z, x + 2, y + k, z, rgb(160, 170, 190)); };
  const dishV = (v, x, y, z) => { v.box(x, y, z, x, y + 4, z, rgb(160, 170, 190)); v.box(x - 3, y + 5, z - 3, x + 3, y + 5, z + 3, rgb(230, 234, 240)); v.box(x - 4, y + 6, z - 4, x + 4, y + 6, z + 4, rgb(214, 220, 230)); };
  const spireV = (v, x, y, z, i) => { const hh = 26 + Math.floor(hash3(x, 1, z) * 30); for (let yy = 0; yy < hh; yy++) { const r = Math.max(1, Math.round(4 - yy / hh * 3)); v.box(x - r, y + yy, z - r, x + r, y + yy, z + r, yy % 6 === 5 ? rgb(250, 210, 90) : (yy % 2 ? rgb(240, 242, 250) : rgb(220, 226, 240))); } v.box(x, y + hh, z, x, y + hh + 6, z, rgb(110, 240, 255)); };
  const citadelV = (v, x, y, z) => { for (let k = 0; k < 7; k++) v.box(x - 10 + k, y + k * 4, z - 10 + k, x + 10 - k, y + k * 4 + 3, z + 10 - k, k % 2 ? rgb(240, 242, 250) : rgb(250, 214, 100)); v.box(x - 1, y + 28, z - 1, x + 1, y + 50, z + 1, rgb(240, 242, 250)); v.box(x - 2, y + 50, z - 2, x + 2, y + 53, z + 2, rgb(110, 240, 255)); };

  addObj(0, cactusV, 26, 2.5); addObj(0, rockV, 16, 2.5);
  addObj(1, furnaceV, 7, 4); addObj(1, lavaV, 10, 3); addObj(1, rockV, 12, 2.5);
  addObj(2, houseV, 12, 3.5); addObj(2, treeV, 22, 2.5); addObj(2, fieldV, 5, 4); addObj(2, windmillV, 1, 4);
  addObj(3, townV, 22, 3.5); addObj(3, treeV, 8, 2.5); addObj(3, clockV, 1, 5);
  addObj(4, towerV, 34, 3.2);
  addObj(5, antennaV, 10, 3); addObj(5, dishV, 7, 3);
  addObj(6, spireV, 16, 3.5); addObj(6, citadelV, 1, 6);
  // the friend's house from episode 4, by the canyon
  houseV(props[0], U(35), U(2), U(51), 0);

  // network cables + packets (animated when unlocked)
  const cables = [];
  for (let i = 0; i < 6; i++) { const a = freeSpot(5, 2), b = freeSpot(5, 2); if (a && b) cables.push([a, b]); }

  // ---------- assemble with state-dependent colouring ----------
  const root = new THREE.Group(); scene.add(root);
  const tone = (ri) => (c) => state(ri) === 'locked' ? desat(c, 0.8, 0.66) : c;
  REGIONS.forEach((r, ri) => {
    terr[ri].map((x, y, z, c) => tone(ri)(c)); props[ri].map((x, y, z, c) => tone(ri)(c));
    const tm = terr[ri].mesh({ scale: BS }); root.add(tm);
    const pm = props[ri].mesh({ scale: 1 }); root.add(pm);
  });
  root.add(water.mesh({ scale: BS, cast: false }));

  // fog clouds over locked regions
  const cloudGeo = new THREE.BoxGeometry(1, 1, 1);
  const cloudMat = new THREE.MeshLambertMaterial({ color: 0xdfe4ee, transparent: true, opacity: 0.62, depthWrite: false });
  const cloudList = [];
  for (let x = 0; x < MW; x += 4) for (let z = 0; z < MD; z += 4) {
    const T = tile(x, z); if (!T || state(T.r) !== 'locked') continue;
    if (noise2(x, z + 9, 10) < 0.45 || hash3(x, 5, z) < 0.35) continue;
    const sz = 3 + hash3(x, 6, z) * 3;
    cloudList.push([x * BS, 44 + hash3(x, 7, z) * 16, z * BS, sz * BS, sz * BS * 0.32]);
  }
  const clouds = new THREE.InstancedMesh(cloudGeo, cloudMat, cloudList.length);
  clouds.castShadow = true; clouds.receiveShadow = false; clouds.frustumCulled = false; root.add(clouds);
  const o3 = new THREE.Object3D();
  const placeClouds = (t) => { cloudList.forEach(([x, y, z, s, h], i) => { o3.position.set(x + Math.sin(t * 0.15 + i) * 6, y + Math.sin(t * 0.3 + i * 1.7) * 1.5, z + Math.cos(t * 0.12 + i) * 4); o3.scale.set(s, h, s * 0.8); o3.updateMatrix(); clouds.setMatrixAt(i, o3.matrix); }); clouds.instanceMatrix.needsUpdate = true; };
  placeClouds(0);

  // smoke puffs (foundry chimneys) — visible even through the fog: the tease
  const smokeMat = new THREE.MeshLambertMaterial({ color: 0x9a9aa4, transparent: true, opacity: 0.8 });
  const PUFFS = 7; const smoke = new THREE.InstancedMesh(cloudGeo, smokeMat, smokeSrc.length * PUFFS); smoke.frustumCulled = false; root.add(smoke);
  const placeSmoke = (t) => { smokeSrc.forEach(([x, y, z], si) => { for (let k = 0; k < PUFFS; k++) { const ph = ((t * 0.35 + k / PUFFS + si * 0.13) % 1); o3.position.set(x + ph * 10 + Math.sin(ph * 6 + si) * 2, y + ph * 46, z - ph * 4); const s = 2.5 + ph * 7; o3.scale.set(s, s, s); o3.rotation.set(ph * 2, ph * 3, 0); o3.updateMatrix(); smoke.setMatrixAt(si * PUFFS + k, o3.matrix); } }); o3.rotation.set(0, 0, 0); smoke.instanceMatrix.needsUpdate = true; };
  placeSmoke(0);

  // packets along network cables
  const pkMat = new THREE.MeshBasicMaterial({ color: 0x7ff6ff });
  const packets = new THREE.InstancedMesh(cloudGeo, pkMat, cables.length * 3); packets.frustumCulled = false; root.add(packets);
  const cableMat = new THREE.MeshBasicMaterial({ color: state(5) === 'locked' ? 0x3d4a5c : 0x3ad6f0 });
  cables.forEach(([a, b]) => { const len = Math.hypot(b[0] - a[0], b[1] - a[1]); const m = new THREE.Mesh(new THREE.BoxGeometry(len, 0.8, 0.8), cableMat); m.position.set((a[0] + b[0]) / 2, U(2) + 1, (a[1] + b[1]) / 2); m.rotation.y = -Math.atan2(b[1] - a[1], b[0] - a[0]); root.add(m); });
  const placePackets = (t) => { cables.forEach(([a, b], ci) => { for (let k = 0; k < 3; k++) { const f = state(5) === 'locked' ? -1 : ((t * 0.3 + k / 3 + ci * 0.21) % 1); o3.position.set(a[0] + (b[0] - a[0]) * f, U(2) + 2, a[1] + (b[1] - a[1]) * f); o3.scale.setScalar(f < 0 ? 0.0001 : 2.2); o3.updateMatrix(); packets.setMatrixAt(ci * 3 + k, o3.matrix); } }); packets.instanceMatrix.needsUpdate = true; };
  placePackets(0);

  // flags on cleared waypoints, ring on current
  const flags = [];
  wps.forEach((w) => {
    if (w.n >= episode) return;
    const f = flag(rgb(220, 50, 50)); f.scale.setScalar(0.55); f.position.set(w.p[0] * BS + BS / 2 + 3, U(3), w.p[1] * BS + BS / 2 - 2); root.add(f); flags.push({ f, n: w.n });
  });
  const ringMat = new THREE.MeshBasicMaterial({ color: 0xffd23f, transparent: true, opacity: 0.9 });
  const ring = new THREE.Mesh(new THREE.TorusGeometry(9, 1.1, 6, 24), ringMat); ring.rotation.x = -Math.PI / 2; root.add(ring);
  const wpPos = (n) => v3(Math.round(wps[n - 1].p[0]) * BS + BS / 2, U(3), Math.round(wps[n - 1].p[1]) * BS + BS / 2);
  ring.position.copy(wpPos(episode)).add(v3(0, 0.6, 0));
  // new flag for this episode (planted at the end)
  const newFlag = flag(rgb(220, 50, 50)); newFlag.scale.setScalar(0.0001); newFlag.position.copy(wpPos(episode)).add(v3(3, 0, -2)); root.add(newFlag);

  // Bob on the map
  const bob = character('bob'); bob.scale.setScalar(0.62); bob.visible = false; root.add(bob);
  // sample path between two waypoints
  const between = (a, b, f) => { const sa = wps[a - 1].s, sb = wps[b - 1].s; const p = PD.at(sa + (sb - sa) * f); return v3(p[0] * BS + BS / 2, U(3) - 4 + 4, p[1] * BS + BS / 2); };

  // current-region border sparkle
  const border = [];
  for (let x = 0; x < MW; x++) for (let z = 0; z < MD; z++) {
    const T = tile(x, z); if (!T || T.r !== curR || !isLand(x, z)) continue;
    const nb = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dz]) => { const N = tile(x + dx, z + dz); return N && N.r !== curR && isLand(x + dx, z + dz); });
    if (nb) border.push([x, z]);
  }
  const bMat = new THREE.MeshBasicMaterial({ color: 0xffe066, transparent: true, opacity: 0.3, depthWrite: false });
  const bMesh = new THREE.InstancedMesh(cloudGeo, bMat, border.length); root.add(bMesh);
  border.forEach(([x, z], i) => { o3.position.set(x * BS + BS / 2, U(3) + 0.3, z * BS + BS / 2); o3.scale.set(BS * 0.5, 0.4, BS * 0.5); o3.rotation.set(0, 0, 0); o3.updateMatrix(); bMesh.setMatrixAt(i, o3.matrix); });

  L.fitShadow(MW * BS / 2, 0, MD * BS / 2, 300);
  aim(cam, v3(MW * BS / 2, 420, MD * BS / 2 + 330), v3(MW * BS / 2, 0, MD * BS / 2 + 10));

  const S = {
    scene, cam, L, O: { bob, newFlag, ring, flags }, PD, wps, wpPos, between, episode, regions: REGIONS, state,
    update(t, shot) {
      flags.forEach(({ f }) => f.userData.wave(t));
      newFlag.userData.wave(t);
      placeClouds(t); placeSmoke(t); placePackets(t);
      ring.scale.setScalar(1 + Math.sin(t * 4) * 0.08); ringMat.opacity = 0.65 + Math.sin(t * 4) * 0.25;
      bMat.opacity = 0.22 + Math.sin(t * 2.5) * 0.12;
      if (shot.act) shot.act(t, S);
    },
  };
  return S;
}
