// Scene builders. Each returns {scene, cam, L, O (objects), update(t, shot)}
import * as THREE from 'three';
import { VB, rgb, hash3, shade } from './vox.js';
import { C, character, pose, lampBoard, paintWall, cactus, rock, house, flag, phone, pedestal, makeTiles, hornRecorder, speakerBox, airRow } from './models.js';
import { TS, plateau, noise2, sandCol, cliffCol, island } from './terrain.js';
import { SKY, lights, makeCam, aim, v3 } from './core.js';
import { buildMap } from './map.js';
import { thumbA, thumbB, thumbC, thumbD, thumbE, thumbF, thumbG, thumbFnt, thumbI, thumbJ, thumbK } from './thumbs.js';

function base(sky = 'day', preset = 'day') {
  const scene = new THREE.Scene(); scene.background = SKY[sky];
  const L = lights(scene, preset); const cam = makeCam(32);
  return { scene, L, cam, O: {} };
}
const run = (S) => (t, shot) => { if (shot.act) shot.act(t, S); };

// ---------------- canyon (Bob left, friend right) ----------------
export function canyon() {
  const S = base(); const { scene, O } = S;
  const vb = new VB();
  const edgeL = (z) => -8 + Math.round((noise2(3, z, 5) - 0.5) * 4);
  const edgeR = (z) => 8 + Math.round((noise2(9, z, 5) - 0.5) * 4);
  const hL = (x, z) => (x < -42 || z < -26) && noise2(x, z, 7) > 0.45 ? 1 : 0;
  const hR = (x, z) => (x > 44 || z < -24) && noise2(x + 50, z, 7) > 0.45 ? 1 : 0;
  plateau(vb, -75, -45, -6, 30, (x, z) => x <= edgeL(z) && z <= 30 - Math.round(noise2(x, 1, 4) * 3), hL, 30);
  plateau(vb, 6, -45, 75, 30, (x, z) => x >= edgeR(z) && z <= 30 - Math.round(noise2(x, 2, 4) * 3), hR, 30);
  // river + canyon floor
  for (let x = -12; x <= 12; x++) for (let z = -45; z <= 32; z++) {
    vb.set(x, -26, z, Math.abs(x + Math.round(Math.sin(z * 0.2) * 2)) < 4 ? (hash3(x, 1, z) > 0.5 ? rgb(70, 140, 210) : rgb(84, 156, 222)) : cliffCol(x, -26, z));
  }
  O.terrain = vb.mesh({ scale: TS }); scene.add(O.terrain);
  const G = 4; // ground surface y in units
  O.bob = character('bob'); O.bob.position.set(-62, G, 18); O.bob.rotation.y = 0.9; scene.add(O.bob);
  O.friend = character('friend'); O.friend.position.set(56, G, 24); O.friend.rotation.y = -1.0; scene.add(O.friend);
  O.lamps = lampBoard(8); O.lamps.position.set(-118, G, -18); O.lamps.rotation.y = 0.42; scene.add(O.lamps);
  O.wall8 = paintWall(8, 64); O.wall8.position.set(118, G, -20); O.wall8.rotation.y = -0.42; scene.add(O.wall8);
  O.wall16 = paintWall(16, 64); O.wall16.position.copy(O.wall8.position); O.wall16.rotation.copy(O.wall8.rotation); O.wall16.visible = false; scene.add(O.wall16);
  O.house = house(); O.house.position.set(200, G, -90); O.house.rotation.y = -0.5; scene.add(O.house);
  O.horn = hornRecorder(); O.horn.position.set(-88, G, 6); O.horn.rotation.y = 0.35; O.horn.visible = false; scene.add(O.horn);
  O.speaker = speakerBox(); O.speaker.position.set(92, G, -2); O.speaker.rotation.y = -0.6; O.speaker.visible = false; scene.add(O.speaker);
  const props = [[cactus(1, 16), -175, -60], [cactus(2, 12), -40, -70], [cactus(3, 14), 160, 10], [cactus(4, 18), 60, -80], [rock(1, 5), -150, 30], [rock(2, 4), 120, 40], [rock(3, 6), -200, -10], [cactus(5, 10), 230, -20], [rock(4, 4), 40, -40]];
  for (const [m, x, z] of props) { m.position.set(x, G, z); m.rotation.y = hash3(x, 0, z) * 6; scene.add(m); }
  S.L.fitShadow(0, 0, -20, 260);
  aim(S.cam, v3(0, 70, 310), v3(0, 32, -10));
  S.update = (t, shot) => {
    pose(S.O.bob, t, {}); pose(S.O.friend, t + 1.3, {});
    if (shot.act) shot.act(t, S);
  };
  return S;
}

// ---------------- purple concept stage ----------------
export function stage() {
  const S = base('stage', 'stage'); const { scene, O } = S;
  const vb = new VB();
  for (let x = -40; x <= 40; x++) for (let z = -40; z <= 20; z++) {
    const c = ((Math.floor(x / 3) + Math.floor(z / 3)) & 1) ? rgb(74, 42, 138) : rgb(88, 52, 158);
    vb.set(x, -1, z, shade(c, 0.97 + hash3(x, 0, z) * 0.06));
  }
  O.floor = vb.mesh({ scale: 6, receive: true, cast: false }); scene.add(O.floor);
  scene.fog = new THREE.Fog(0x2b1652, 300, 620);
  O.ped = pedestal(26); scene.add(O.ped);
  O.phone = phone(); O.phone.position.set(0, 6, 0); scene.add(O.phone);
  const scr = O.phone.userData.screen; const SW = 24, SH = 46;
  // screen texture
  const tc = document.createElement('canvas'); tc.width = 240; tc.height = 460; const tx = tc.getContext('2d');
  const tex = new THREE.CanvasTexture(tc); tex.colorSpace = THREE.SRGBColorSpace; scr.material = new THREE.MeshBasicMaterial({ map: tex });
  S.screen = (cv, extra) => { tx.drawImage(cv, 0, 0, 240, 460); if (extra) extra(tx); tex.needsUpdate = true; };
  // tiles on the screen
  const tgeo = new THREE.BoxGeometry(1, 1, 1); tgeo.translate(0, 0, 0.5);
  O.tiles = new THREE.InstancedMesh(tgeo, new THREE.MeshLambertMaterial({ color: 0xffffff, emissive: 0x000000 }), SW * SH);
  O.tiles.position.set(0, scr.position.y, 2.1); O.phone.add(O.tiles); O.tiles.visible = false; O.tiles.castShadow = true; O.tiles.frustumCulled = false;
  O.sub = new THREE.InstancedMesh(tgeo, new THREE.MeshBasicMaterial({ color: 0xffffff }), SW * SH * 3);
  O.sub.position.copy(O.tiles.position); O.phone.add(O.sub); O.sub.visible = false; O.sub.frustumCulled = false;
  const o = new THREE.Object3D(), col = new THREE.Color();
  S.SW = SW; S.SH = SH;
  // colors: array SW*SH; f(i) -> {s: scale, z: lift}
  S.setTiles = (colors, f) => {
    for (let i = 0; i < SW * SH; i++) {
      const cx = i % SW, cy = Math.floor(i / SW); const q = f ? f(i, cx, cy) : { s: 1, z: 0 };
      o.position.set(cx - (SW - 1) / 2 + (q.dx || 0), (SH - 1) / 2 - cy + (q.dy || 0), q.z || 0); o.scale.set(q.s, q.s, Math.max(0.2, q.d ?? 0.4)); o.updateMatrix();
      O.tiles.setMatrixAt(i, o.matrix); O.tiles.setColorAt(i, col.setHex(colors[i]));
    }
    O.tiles.instanceMatrix.needsUpdate = true; O.tiles.instanceColor.needsUpdate = true;
  };
  S.setSub = (colors, gain = 1) => {
    for (let i = 0; i < SW * SH; i++) {
      const cx = i % SW, cy = Math.floor(i / SW); const c = colors[i];
      const ch = [(c >> 16) & 255, (c >> 8) & 255, c & 255];
      for (let k = 0; k < 3; k++) {
        o.position.set(cx - (SW - 1) / 2 + (k - 1) * 0.3, (SH - 1) / 2 - cy, 0); o.scale.set(0.26, 0.86, 0.3); o.updateMatrix();
        O.sub.setMatrixAt(i * 3 + k, o.matrix);
        const v = Math.min(1, ch[k] / 255 * gain); col.setRGB(k === 0 ? v : 0, k === 1 ? v : 0, k === 2 ? v : 0, THREE.SRGBColorSpace);
        O.sub.setColorAt(i * 3 + k, col);
      }
    }
    O.sub.instanceMatrix.needsUpdate = true; O.sub.instanceColor.needsUpdate = true;
  };
  // big blocks (legend / grays): up to 12 cubes of size 16
  const bgeo = new THREE.BoxGeometry(16, 16, 16); bgeo.translate(0, 8, 0);
  O.blocks = new THREE.InstancedMesh(bgeo, new THREE.MeshLambertMaterial({ color: 0xffffff }), 12); O.blocks.castShadow = true; O.blocks.receiveShadow = true; O.blocks.frustumCulled = false; scene.add(O.blocks);
  S.setBlocks = (list) => { // list of {x,y,z,c,s}
    for (let i = 0; i < 12; i++) { const b = list[i]; if (!b || b.s <= 0.001) { o.position.set(0, -999, 0); o.scale.setScalar(0.001); } else { o.position.set(b.x, b.y ?? 6, b.z ?? 0); o.scale.setScalar(b.s); o.rotation.set(0, b.ry ?? 0, 0); } o.updateMatrix(); o.rotation.set(0, 0, 0); O.blocks.setMatrixAt(i, o.matrix); O.blocks.setColorAt(i, col.setHex(b ? b.c : 0)); }
    O.blocks.instanceMatrix.needsUpdate = true; O.blocks.instanceColor.needsUpdate = true;
  };
  S.setBlocks([]);
  // RGB pixel: frame + three bars
  O.rgb = new THREE.Group(); O.rgb.position.set(0, 6, 0); scene.add(O.rgb); O.rgb.visible = false;
  const fv = new VB(); fv.box(-15, 0, -4, 14, 1, 3, rgb(40, 40, 52)); fv.box(-15, 44, -4, 14, 45, 3, rgb(40, 40, 52)); fv.box(-15, 0, -4, -14, 45, 3, rgb(40, 40, 52)); fv.box(13, 0, -4, 14, 45, 3, rgb(40, 40, 52)); fv.box(-14, 1, -4, 13, 44, -3, rgb(18, 18, 26));
  O.rgb.add(fv.mesh());
  O.bars = [0xff2a2a, 0x2aff4a, 0x2a6aff].map((c, k) => { const m = new THREE.Mesh(new THREE.BoxGeometry(8, 40, 4), new THREE.MeshBasicMaterial({ color: c })); m.position.set((k - 1) * 9, 22.5, 0); O.rgb.add(m); m.userData.c = new THREE.Color(c); return m; });
  S.setBars = (lv) => O.bars.forEach((m, k) => { const v = Math.max(0.08, lv[k]); m.material.color.copy(m.userData.c).multiplyScalar(v); });
  // sound episode extras: graph board, air row, speaker, 16-lamp board
  const bc = document.createElement('canvas'); bc.width = 1500; bc.height = 700; const btex = new THREE.CanvasTexture(bc); btex.colorSpace = THREE.SRGBColorSpace;
  O.board = new THREE.Group(); O.board.position.set(0, 4, -6); O.board.visible = false; scene.add(O.board);
  const bv = new VB(); bv.box(-78, 0, -2, -76, 84, 0, C.woodD); bv.box(76, 0, -2, 78, 84, 0, C.woodD); bv.box(-77, 8, -2, 77, 84, -1, rgb(30, 26, 48)); O.board.add(bv.mesh());
  const bplane = new THREE.Mesh(new THREE.PlaneGeometry(150, 70), new THREE.MeshBasicMaterial({ map: btex })); bplane.position.set(0, 46, 0.1); O.board.add(bplane);
  S.boardCanvas = bc; S.boardDraw = (fn) => { fn(bc.getContext('2d'), bc.width, bc.height); btex.needsUpdate = true; };
  S.boardToWorld = (u, v) => v3(-75 + u * 150, 46 + 35 - v * 70, 0.5).add(O.board.position); // u,v in 0..1 canvas coords
  O.air = airRow(36, 5, 3.2); O.air.position.set(-40, 14, 10); O.air.visible = false; scene.add(O.air);
  O.spk = speakerBox(); O.spk.position.set(-62, 0, 10); O.spk.rotation.y = Math.PI / 2; O.spk.visible = false; scene.add(O.spk);
  O.lamps16 = lampBoard(16); O.lamps16.position.set(0, 0, 0); O.lamps16.visible = false; scene.add(O.lamps16);
  S.mkFriend = () => { const f = character('friend'); scene.add(f); return f; };
  S.L.fitShadow(0, 0, 0, 140);
  aim(S.cam, v3(0, 50, 190), v3(0, 30, 0));
  S.update = (t, shot) => { if (shot.act) shot.act(t, S); };
  return S;
}

// ---------------- character close-up test ----------------
export function bobtest() {
  const S = base(); const vb = new VB();
  island(vb, 0, 0, 22, 5, 8);
  S.scene.add(vb.mesh({ scale: TS }));
  S.O.bob = character('bob'); S.O.bob.position.set(-14, 4, 0); S.O.bob.rotation.y = 0.35; S.scene.add(S.O.bob);
  S.O.friend = character('friend'); S.O.friend.position.set(16, 4, 0); S.O.friend.rotation.y = -0.35; S.scene.add(S.O.friend);
  const c = cactus(2, 14); c.position.set(-30, 4, -30); S.scene.add(c);
  S.L.fitShadow(0, 0, 0, 120);
  aim(S.cam, v3(0, 38, 120), v3(0, 18, 0));
  S.update = (t) => { pose(S.O.bob, t, { wave: 1 }); pose(S.O.friend, t, {}); };
  return S;
}

// ---------------- the Foundry (episode 7+) ----------------
import { furnace, crucible, ingot, wafer } from './props7.js';
export function foundry() {
  const S = base('day'); const { scene, O } = S;
  const c = document.createElement('canvas'); c.width = 4; c.height = 512; const x = c.getContext('2d');
  const gr = x.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, '#2a2236'); gr.addColorStop(0.55, '#5a3a40'); gr.addColorStop(0.85, '#b0603a'); gr.addColorStop(1, '#e09050');
  x.fillStyle = gr; x.fillRect(0, 0, 4, 512); const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; scene.background = tex;
  S.L.sun.color.setRGB(1, 0.78, 0.6); S.L.sun.intensity = 1.8; S.L.hemi.color.setRGB(0.75, 0.68, 0.8); S.L.hemi.groundColor.setRGB(0.5, 0.3, 0.2); S.L.hemi.intensity = 1.2;
  const vb = new VB();
  const stone = (x, y, z) => { const h = hash3(x, y, z); return h > 0.66 ? rgb(108, 96, 92) : h > 0.33 ? rgb(96, 86, 84) : rgb(118, 106, 98); };
  for (let x = -40; x <= 40; x++) for (let z = -32; z <= 20; z++) {
    const edge = Math.hypot(x / 40, z / 30) + (noise2(x, z, 5) - 0.5) * 0.12; if (edge > 1.02) continue;
    const lava = Math.abs(z - 8 - Math.round(Math.sin(x * 0.25) * 2)) < 1 && x < -6 || Math.abs(x - 26 - Math.round(Math.sin(z * 0.3) * 1.5)) < 1 && z < 2;
    for (let y = -6; y <= 0; y++) vb.set(x, y, z, y === 0 && lava ? (hash3(x, 1, z) > 0.5 ? rgb(255, 140, 40) : rgb(255, 180, 70)) : y === 0 ? stone(x, y, z) : cliffCol(x, y, z));
    if (!lava && noise2(x + 9, z, 6) > 0.72 && Math.hypot(x, z) > 18) vb.set(x, 1, z, stone(x, 1, z));
  }
  O.ground = vb.mesh({ scale: TS }); scene.add(O.ground);
  const G = 4;
  O.furnace = furnace(); O.furnace.position.set(-70, G, -80); O.furnace.rotation.y = 0.3; scene.add(O.furnace);
  O.crucible = crucible(); O.crucible.position.set(0, G, -30); scene.add(O.crucible);
  const fv = new VB(); fv.box(-16, 0, -2, -15, 70, -1, C.woodD); fv.box(15, 0, -2, 16, 70, -1, C.woodD); fv.box(-16, 70, -2, 16, 72, -1, C.wood); fv.box(-1, 72, -2, 0, 76, -1, rgb(80, 80, 90));
  O.puller = fv.mesh(); O.puller.position.set(0, G, -30); scene.add(O.puller);
  O.ingot = ingot(); O.ingot.position.set(0, G + 9, -30); scene.add(O.ingot);
  O.sand = new VB(); for (let x = -9; x <= 9; x++) for (let z = -9; z <= 9; z++) { const h = Math.round(7 - Math.hypot(x, z) * 0.8 + hash3(x, 0, z) * 1.5); for (let y = 0; y < h; y++) O.sand.set(x, y, z, sandCol(x, y, z)); }
  O.sandM = O.sand.mesh(); O.sandM.position.set(-48, G, -6); scene.add(O.sandM);
  O.wafers = []; for (let k = 0; k < 6; k++) { const w = wafer(14); w.position.set(52, G + 1 + k * 1.2, -20); scene.add(w); O.wafers.push(w); }
  O.bigWafer = wafer(24); O.bigWafer.position.set(52, G + 30, -10); O.bigWafer.rotation.x = Math.PI / 2 - 0.25; O.bigWafer.visible = false; scene.add(O.bigWafer);
  O.beam = new THREE.Mesh(new THREE.ConeGeometry(26, 60, 24, 1, true), new THREE.MeshBasicMaterial({ color: 0xb48cff, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide }));
  O.beam.position.set(52, G + 62, -10); scene.add(O.beam);
  O.bob = character('bob'); O.bob.position.set(-22, G, 22); O.bob.rotation.y = 0.6; scene.add(O.bob);
  // chimney smoke
  const puffs = 10; O.smoke = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshLambertMaterial({ color: 0x8a8590, transparent: true, opacity: 0.7 }), puffs); O.smoke.frustumCulled = false; scene.add(O.smoke);
  const o3 = new THREE.Object3D();
  S.L.fitShadow(0, 0, -20, 170);
  aim(S.cam, v3(0, 60, 200), v3(0, 20, -20));
  S.update = (t, shot) => {
    pose(O.bob, t, {});
    O.furnace.updateMatrixWorld(); const top = v3(6.5, 53, -1.5).applyMatrix4(O.furnace.matrixWorld);
    for (let k = 0; k < puffs; k++) { const ph = (t * 0.25 + k / puffs) % 1; o3.position.set(top.x + ph * 30 + Math.sin(ph * 6 + k) * 3, top.y + ph * 90, top.z - ph * 10); o3.scale.setScalar(4 + ph * 14); o3.rotation.set(ph * 2, ph * 3, 0); o3.updateMatrix(); O.smoke.setMatrixAt(k, o3.matrix); }
    O.smoke.instanceMatrix.needsUpdate = true;
    O.crucible.userData.glow(0.5 + 0.5 * Math.sin(t * 3));
    if (shot.act) shot.act(t, S);
  };
  return S;
}

export function map() { return buildMap({ episode: window.EP_NUM || 5 }); }

export const SCENES = { canyon, stage, bobtest, map, foundry, thumbA, thumbB, thumbC, thumbD, thumbE, thumbF, thumbG, thumbFnt, thumbI, thumbJ, thumbK };
