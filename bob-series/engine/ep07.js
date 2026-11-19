// Episode 7 — "How Sand Became a Switch". First stop in the Foundry: the transistor.
import * as THREE from 'three';
import { W, H, clamp, lerp, ease, easeOut, smooth, backOut, pop, v3, aim, project, text, bubble, tag, vignette, setSky, g2, Y, G, R, B, WH } from './core.js';
import { pose } from './models.js';
import { face16, photoCanvas, sample } from './pics.js';
import { battery, knifeSwitch, bulb, wire, dots, transistor, COPPER, SILICON } from './props7.js';
import { VB, rgb, hash3 } from './vox.js';

const K = (t, a, b) => clamp((t - a) / (b - a));
function cm(S, t, a, b, P0, L0, P1, L1, e = ease) { const k = e(K(t, a, b)); aim(S.cam, P0.clone().lerp(P1, k), L0.clone().lerp(L1, k)); }
const CYc = '#5ff2ff';
const SCR = v3(0, 32.5, 0);
function headPos(S, ch, up = 36) { return project(S.cam, ch.getWorldPosition(v3(0, 0, 0)).add(v3(0, up, 0))); }

// ---------- lazily built stage sets ----------
function sets(S) {
  if (S.O.e7) return S.O.e7;
  const scene = S.scene; const E = {};
  // 1) simple circuit: battery -> wire loop -> bulb, knife switch in the front run
  E.circuit = new THREE.Group(); scene.add(E.circuit);
  const loop = [v3(-50, 2, 5), v3(-50, 2, -10), v3(50, 2, -10), v3(50, 2, 20), v3(-50, 2, 20), v3(-50, 2, 5)];
  E.cWire = wire(loop); E.circuit.add(E.cWire);
  E.cBat = battery(); E.cBat.position.set(-50, 0, 5); E.circuit.add(E.cBat);
  E.cBulb = bulb(); E.cBulb.position.set(50, 2, 5); E.circuit.add(E.cBulb);
  E.cSw = knifeSwitch(); E.cSw.position.set(0, 2.5, 20); E.circuit.add(E.cSw);
  E.cDots = dots(E.cWire, 36); E.circuit.add(E.cDots);
  E.cGap = (15 + 100 + 30 + 42) / 260;
  // 2) materials: three short wires with a block in the middle
  E.mat = new THREE.Group(); scene.add(E.mat); E.rows = [];
  const mats = [['COPPER', COPPER, 1], ['GLASS', rgb(190, 226, 240), 0], ['SILICON', SILICON, 0.5]];
  mats.forEach(([name, col, pass], r) => {
    const z = -30 + r * 30; const w = wire([v3(-40, 2, z), v3(40, 2, z)]); E.mat.add(w);
    const v = new VB(); v.box(-6, 0, -5, 6, 8, 5, (x, y, zz) => (name === 'SILICON' && hash3(x, y, zz) > 0.7 ? rgb(120, 134, 182) : col));
    const m = v.mesh(); m.position.set(0, 0, z); if (name === 'GLASS') { m.material = new THREE.MeshLambertMaterial({ vertexColors: true, transparent: true, opacity: 0.7 }); } E.mat.add(m);
    const d = dots(w, 14); E.mat.add(d); E.rows.push({ name, z, w, d, m, pass });
  });
  const sv = new VB(); for (let x = -7; x <= 7; x++) for (let z = -7; z <= 7; z++) { const h = Math.round(5 - Math.hypot(x, z) * 0.7); for (let y = 0; y < h; y++) sv.set(x, y, z, hash3(x, y, z) > 0.5 ? rgb(234, 202, 142) : rgb(220, 186, 124)); }
  E.sand = sv.mesh(); E.sand.position.set(56, 0, 58); E.mat.add(E.sand);
  // 3) the transistor rig
  E.tr = new THREE.Group(); scene.add(E.tr);
  E.T = transistor(2.2); E.T.position.set(0, 0, 0); E.tr.add(E.T);
  E.tBat = battery(); E.tBat.position.set(-62, 0, 0); E.tr.add(E.tBat);
  E.tIn = wire([v3(-57, 2, 0), v3(-25, 2, 0)]); E.tOut = wire([v3(25, 2, 0), v3(58, 2, 0)]); E.tr.add(E.tIn, E.tOut);
  E.tBulb = bulb(); E.tBulb.position.set(62, 0, 0); E.tBulb.scale.setScalar(1.3); E.tr.add(E.tBulb);
  E.tPath = wire([v3(-57, 2, 0), v3(-25, 2, 0), v3(-25, 15, 0), v3(25, 15, 0), v3(25, 2, 0), v3(58, 2, 0)]); E.tPath.visible = false; E.tr.add(E.tPath);
  E.tDots = dots(E.tPath, 30); E.tr.add(E.tDots);
  E.gBat = battery(); E.gBat.scale.setScalar(0.8); E.gBat.position.set(-40, 0, -24); E.tr.add(E.gBat);
  E.gWire = wire([v3(-40, 14, -24), v3(-40, 50, -24), v3(-1, 50, -24), v3(-1, 50, -1), v3(-1, 44, -1)], 1.4, rgb(90, 200, 230)); E.tr.add(E.gWire);
  E.gDots = dots(E.gWire, 16, 0x7ff6ff); E.tr.add(E.gDots);
  E.tStop = (32) / (32 + 13); // fraction of path where the in-pad sits
  // 4) chain of transistors
  E.ch = new THREE.Group(); scene.add(E.ch); E.chain = [];
  const xs = [-66, -22, 22, 66];
  xs.forEach((x, i) => {
    const T = transistor(1.2); T.position.set(x, 0, 0); E.ch.add(T);
    const ox = x + 14; const nx = i < 3 ? xs[i + 1] : 98;
    const pts = i < 3 ? [v3(ox, 2, 0), v3(ox + 4, 2, 0), v3(ox + 4, 34, 0), v3(nx - 0.6, 34, 0), v3(nx - 0.6, 25, 0)] : [v3(ox, 2, 0), v3(nx - 4, 2, 0)];
    const w = wire(pts, 1.4); E.ch.add(w); const d = dots(w, 14); E.ch.add(d);
    E.chain.push({ T, w, d });
  });
  E.chBulb = bulb(); E.chBulb.position.set(100, 0, 0); E.ch.add(E.chBulb);
  E.chBat = battery(); E.chBat.position.set(-104, 0, -2); E.ch.add(E.chBat);
  E.chIn = wire([v3(-104, 18, -1), v3(-104, 34, -1), v3(-66.6, 34, -1), v3(-66.6, 25, -1)], 1.4); E.ch.add(E.chIn); E.chInD = dots(E.chIn, 12); E.ch.add(E.chInD);
  for (const k of ['circuit', 'mat', 'tr', 'ch']) E[k].visible = false;
  S.O.e7 = E; return E;
}
function stageReset(S) {
  const O = S.O; O.phone.visible = false; O.tiles.visible = false; O.sub.visible = false; O.rgb.visible = false; S.setBlocks([]);
  O.board.visible = false; O.air.visible = false; O.spk.visible = false; O.lamps16.visible = false; O.ped.visible = false;
  O.phone.position.set(0, 6, 0); O.phone.rotation.set(0, 0, 0);
  const E = sets(S); for (const k of ['circuit', 'mat', 'tr', 'ch']) E[k].visible = false;
  return E;
}
function canyonReset(S, dusk) {
  const O = S.O; S.scene.background = setSky(dusk); const dk = dusk;
  S.L.sun.color.setRGB(1, lerp(0.94, 0.66, dk), lerp(0.85, 0.48, dk)); S.L.sun.intensity = lerp(2.5, 2.0, dk);
  S.L.hemi.intensity = lerp(1.35, 1.0, dk); S.L.hemi.color.setRGB(lerp(0.81, 0.85, dk), lerp(0.9, 0.62, dk), lerp(1, 0.75, dk));
  O.wall8.visible = false; O.wall16.visible = true; O.lamps.userData.set(0);
  if (S.cam.fov !== 32) { S.cam.fov = 32; S.cam.updateProjectionMatrix(); }
}

export const EPISODE = {
  gaps: { pre: 0.5, default: 0.45, after: { '01': 0.7, '02': 0.35, '03': 0.5, '04': 0.5, '06': 0.6, '07': 0.6, '08': 0.6, '09': 0.8 }, endHold: 13 },
  shots({ cue: c, start, end, fx, duration, CH }) {
    const sh = []; const add = (o) => { sh.push(o); return o; };

    // ================= 01 HOOK: phone -> switches -> sand =================
    const tSw = c('01', 'switches'), tPeople = c('01', 'people'), tHair = c('01', 'hair'), tSand = c('01', 'sand'), tToday = c('01', 'today');
    let _pt = null; const photoT = () => _pt || (_pt = sample(photoCanvas(), 24, 46));
    add({ scene: 'stage', t0: 0, act(t, S) {
      stageReset(S); const O = S.O; O.phone.visible = true; O.ped.visible = true; S.screen(photoCanvas());
      const fall = K(t, tSand - 0.1, tSand + 1.6);
      const sandCol = (i) => ((i * 2654435761) >>> 0) % 3 === 0 ? 0xeac98e : ((i * 40503) >>> 0) % 2 ? 0xe2c084 : 0xd8b476;
      O.tiles.visible = fall > 0; O.phone.userData.screen.visible = fall <= 0;
      if (fall > 0) { const base = photoT(); S.setTiles(base.map((c0, i) => (K(t, tSand - 0.1 + ((i * 7) % 23) * 0.01, tSand + 0.3 + ((i * 7) % 23) * 0.01) > 0.5 ? sandCol(i) : c0)), (i, cx, cy) => { const r = ((i * 2654435761) >>> 0) / 4294967296; const f = clamp((fall - r * 0.35) / 0.65); return { s: 1 - 0.35 * f, z: f * (2 + r * 6), dy: -f * f * (60 - cy * 0.6 + r * 10), dx: f * (r - 0.5) * 12, d: 0.6 }; }); }
      if (t < tHair) cm(S, t, 0, tHair, v3(-30, 46, 170), SCR.clone(), v3(-10, 40, 120), SCR.clone(), smooth);
      else cm(S, t, tHair, end('01') + 0.6, v3(-10, 40, 120), SCR.clone(), v3(20, 46, 150), v3(0, 22, 0), smooth);
    }, overlay(t, g) {
      if (t > tSw && t < tHair) { text([['SWITCHES ', Y], ['> ', WH], ['PEOPLE ON EARTH', G]], W / 2, 130, { size: 50, scale: pop(t, tPeople - 0.2) }); }
      if (t > tHair - 0.2 && t < tSand) {
        const k = pop(t, tHair - 0.2); g.save(); g.globalAlpha = Math.min(1, k); const hx = W / 2 + 420;
        g.fillStyle = '#14102a'; g.fillRect(hx - 66, 0, 132, H); g.fillStyle = '#6b4a2a'; g.fillRect(hx - 58, 0, 116, H); g.fillStyle = '#80583a'; g.fillRect(hx - 58, 0, 30, H); g.restore();
        tag('1 HAIR', hx, 160, { scale: k, size: 30 }); tag('1 SWITCH: TOO SMALL TO SEE', hx - 330, 560, { scale: pop(t, tHair + 0.4), size: 26 });
        g.fillStyle = Y; if (k > 0.5) g.fillRect(hx - 1, 600, 2, 2);
      }
      if (t > tSand) text([['MADE FROM ', WH], ['SAND', Y]], W / 2, 130, { size: 56, scale: pop(t, tSand + 0.3) });
      vignette(0.4);
    } });
    fx('zoom', 0.4, 0.3); fx('pop', tPeople - 0.2, 0.7); fx('whoosh', tHair - 0.3, 0.4); fx('pop', tHair + 0.4, 0.5); fx('shatter', tSand - 0.1, 0.8); fx('settle', tSand + 0.9, 0.5);

    // ================= 02 MAP: into the Foundry =================
    const t02 = start('02') - 0.35, tFog = c('02', 'fog'), tWelcome = c('02', 'welcome');
    add({ scene: 'map', t0: t02, trans: 0.5, act(t, S) {
      const O = S.O; O.bob.visible = true; O.newFlag.scale.setScalar(0.0001);
      const wk = K(t, t02 + 0.4, tWelcome + 0.3); const f = smooth(wk);
      const p = S.between(6, 7, f), p2 = S.between(6, 7, Math.min(1, f + 0.02)); O.bob.position.copy(p); O.bob.rotation.y = wk < 1 ? Math.atan2(p2.x - p.x, p2.z - p.z) : 0.4;
      pose(O.bob, t, wk > 0 && wk < 1 ? { walk: t * 11 } : (t > tWelcome + 0.4 ? { cheer: smooth(K(t, tWelcome + 0.4, tWelcome + 0.7)) * 0.6 } : {}));
      const w6 = S.wpPos(6), w7 = S.wpPos(7);
      cm(S, t, t02 + 0.2, end('02'), w6.clone().add(v3(-30, 140, 150)), w6.clone(), w7.clone().add(v3(10, 95, 110)), w7.clone());
    }, overlay(t, g, S) {
      const k = pop(t, tWelcome); if (t > tWelcome) { text([['STOP ', WH], ['7', Y]], W / 2, 140, { size: 80, scale: k }); tag('THE FOUNDRY', W / 2, 240, { scale: pop(t, tWelcome + 0.15), size: 34 }); }
      if (t > tFog && t < tWelcome) text([['THE FOG ', WH], ['IS GONE', G]], W / 2, 140, { size: 52, scale: pop(t, tFog) });
      vignette(0.3);
    } });
    fx('whoosh', t02, 0.7); for (let k = 0; k < 9; k++) fx('step', t02 + 0.4 + k * ((tWelcome - t02) / 9), 0.4); fx('pop', tFog, 0.6); fx('chime', tWelcome, 0.5); fx('pop', tWelcome + 0.15, 0.6);

    // ================= 03 RECAP: Bob flipping lamps by hand at dusk =================
    const t03 = start('03') - 0.2, tOn = c('03', 'on'), tOff = c('03', 'off'), tFlip = c('03', 'flipping'), tDown = c('03', 'down'), tBill = c('03', 'billions'), tHands = c('03', 'hands'), tFinger = c('03', 'finger');
    add({ scene: 'canyon', t0: t03, trans: 0.45, act(t, S) {
      const dk = 0.85 * smooth(K(t, tFlip - 0.5, tDown + 0.3)); canyonReset(S, dk);
      const n = Math.floor((t - t03) * (t > tFlip ? 6 : 1.5)); S.O.lamps.userData.set(((n * 2654435761) >>> 24) & 255);
      pose(S.O.bob, t, { point: 0.55 + 0.35 * Math.abs(Math.sin(t * (t > tFlip ? 12 : 4))) });
      if (t < tBill) cm(S, t, t03, tBill, v3(-40, 50, 150), v3(-100, 30, -12), v3(-56, 44, 120), v3(-104, 32, -14), smooth);
      else cm(S, t, tBill, end('03') + 0.5, v3(-56, 44, 120), v3(-104, 32, -14), v3(-30, 30, 70), v3(-62, 20, 18), smooth);
    }, overlay(t, g, S) {
      if (t > tOn && t < tFlip) { tag('ON = 1', W / 2 - 220, 120, { size: 34, scale: pop(t, tOn), color: Y }); if (t > tOff) tag('OFF = 0', W / 2 + 220, 120, { size: 34, scale: pop(t, tOff), color: '#b9b2d8' }); }
      if (t > tFlip && t < tBill) tag('FLIPPED BY HAND, ALL EVENING', W / 2, 120, { size: 30, scale: pop(t, tFlip) });
      if (t > tBill) text([['BILLIONS ', Y], ['EVERY SECOND', WH]], W / 2, 130, { size: 50, scale: pop(t, tBill) });
      if (t > tHands) text([['NO HANDS', R]], W / 2, 220, { size: 46, scale: pop(t, tHands) });
      if (t > tFinger - 0.2) text([['ELECTRICITY ', CYc], ['INSTEAD OF A FINGER', WH]], W / 2, 960, { size: 40, scale: pop(t, tFinger - 0.2) });
    } });
    fx('whoosh', t03, 0.4); fx('pop', tOn, 0.5); fx('pop', tOff, 0.5); fx('flicker', tFlip, 0.35, { dur: Math.max(0.5, tBill - tFlip) }); fx('pop', tBill, 0.6); fx('buzz', tHands, 0.4); fx('pop', tFinger - 0.2, 0.6);

    // ================= 04 ELECTRICITY: a simple circuit =================
    const t04 = start('04') - 0.2, tWater = c('04', 'water'), tLamp4 = c('04', 'lamp'), tGap = c('04', 'gap'), tClose2 = c('04', 'close', 2), tOne4 = c('04', 'one'), tOpen2 = c('04', 'open', 2), tZero4 = c('04', 'zero');
    const closed4 = (t) => (t < tGap - 0.1 ? 1 : t < tClose2 ? 0 : t < tOpen2 ? 1 : 0);
    add({ scene: 'stage', t0: t04, trans: 0.45, act(t, S) {
      const E = stageReset(S); E.circuit.visible = true;
      const cl = closed4(t); const lev = t < tGap - 0.1 ? 1 : t < tClose2 ? 1 - K(t, tGap - 0.1, tGap + 0.2) : t < tOpen2 ? K(t, tClose2, tClose2 + 0.2) : 1 - K(t, tOpen2, tOpen2 + 0.2);
      E.cSw.userData.set(lev); E.cBulb.userData.set(cl ? K(t, (t < tGap ? t04 + 0.6 : tClose2 + 0.15), (t < tGap ? t04 + 0.9 : tClose2 + 0.4)) : 0);
      E.cDots.userData.update(t, 1, cl ? { speed: 0.18 } : { speed: 0.18, stopAt: E.cGap, frozen: 0, always: true });
      if (!cl) E.cDots.userData.update(t, 1, { speed: 0.18, stopAt: E.cGap });
      cm(S, t, t04, tGap, v3(0, 110, 170), v3(0, 0, 5), v3(-20, 80, 140), v3(0, 2, 8), smooth);
      if (t > tGap) cm(S, t, tGap, end('04') + 0.5, v3(-20, 80, 140), v3(0, 2, 8), v3(10, 52, 92), v3(0, 4, 16), smooth);
    }, overlay(t, g, S) {
      if (t > tWater && t < tGap) text([['LIKE WATER ', CYc], ['IN A PIPE', WH]], W / 2, 120, { size: 50, scale: pop(t, tWater) });
      if (t > tGap) { const p = project(S.cam, v3(0, 14, 20)); tag('SWITCH = A GAP', p[0], p[1] - 90, { size: 30, scale: pop(t, tGap) }); }
      if (t > tOne4 - 0.1 && t < tOpen2) text([['CLOSED ', WH], ['= 1', Y]], W / 2, 120, { size: 56, scale: pop(t, tOne4 - 0.1) });
      if (t > tZero4 - 0.1) text([['OPEN ', WH], ['= 0', '#b9b2d8']], W / 2, 120, { size: 56, scale: pop(t, tZero4 - 0.1) });
      vignette(0.35);
    } });
    fx('whoosh', t04, 0.5); fx('lighton', t04 + 0.6, 0.6); fx('hum', t04 + 0.6, 0.25, { dur: Math.max(0.5, tGap - t04 - 0.6) }); fx('thump', tGap - 0.1, 0.6); fx('lightoff', tGap, 0.5); fx('thump', tClose2, 0.7); fx('lighton', tClose2 + 0.15, 0.6); fx('pop', tOne4 - 0.1, 0.6); fx('thump', tOpen2, 0.7); fx('lightoff', tOpen2 + 0.05, 0.5); fx('pop', tZero4 - 0.1, 0.6);

    // ================= 05 MATERIALS =================
    const t05 = start('05') - 0.2, tCopper = c('05', 'copper'), tGlass = c('05', 'glass'), tSilicon = c('05', 'silicon'), tSand5 = c('05', 'sand'), tPicky = c('05', 'picky'), tDecide = c('05', 'decide');
    add({ scene: 'stage', t0: t05, trans: 0.45, act(t, S) {
      const E = stageReset(S); E.mat.visible = true;
      E.rows.forEach((r, i) => {
        const tt = [tCopper, tGlass, tSilicon][i]; const on = t > tt - 0.4;
        r.m.visible = true; r.w.visible = true;
        if (r.name === 'COPPER') r.d.userData.update(t, on ? 1 : 0, { speed: 0.3 });
        else if (r.name === 'GLASS') r.d.userData.update(t, on ? 1 : 0, { speed: 0.3, stopAt: 0.42 });
        else { const allow = t > tDecide ? (Math.sin(t * 4) > 0 ? 1 : 0) : (Math.sin(t * 9) > 0.6 ? 1 : 0); r.d.userData.update(t, on ? 1 : 0, allow ? { speed: 0.3 } : { speed: 0.3, stopAt: 0.42 }); }
      });
      E.sand.visible = t > tSand5 - 0.2; E.sand.scale.setScalar(Math.max(0.001, backOut(K(t, tSand5 - 0.2, tSand5 + 0.2))));
      cm(S, t, t05, end('05') + 0.5, v3(-10, 110, 150), v3(4, 0, 0), v3(10, 100, 130), v3(8, 0, 4), smooth);
    }, overlay(t, g, S) {
      const names = [[tCopper, 'COPPER', '#ffa060'], [tGlass, 'GLASS', '#bfe6ff'], [tSilicon, 'SILICON', '#9aa8e0']];
      E7rows(S).forEach((r, i) => { const [tt, n, col] = names[i]; if (t < tt - 0.3) return; const p = project(S.cam, v3(-52, 4, r.z)); tag(n, p[0] - 40, p[1], { size: 30, color: col, scale: pop(t, tt - 0.3) });
        const q = project(S.cam, v3(56, 4, r.z)); const res = i === 0 ? ['LETS IT THROUGH', G] : i === 1 ? ['BLOCKS IT', R] : t > tPicky ? ['PICKY', Y] : null; if (res && t > tt + 0.6) tag(res[0], q[0] + 60, q[1], { size: 24, color: res[1], scale: pop(t, i === 2 ? tPicky : tt + 0.6) }); });
      if (t > tSand5) { const p = project(S.cam, v3(56, 8, 58)); tag('SAND', p[0] + 90, p[1] + 10, { size: 26, scale: pop(t, tSand5) }); }
      if (t > tDecide) text([['YOU DECIDE ', Y], ['WHEN IT FLOWS', WH]], W / 2, 120, { size: 46, scale: pop(t, tDecide) });
      vignette(0.35);
    } });
    fx('whoosh', t05, 0.5); fx('pop', tCopper - 0.3, 0.6); fx('pop', tGlass - 0.3, 0.6); fx('buzz', tGlass + 0.6, 0.3); fx('pop', tSilicon - 0.3, 0.6); fx('pop', tSand5, 0.5); fx('pop', tPicky, 0.6); fx('chime', tDecide, 0.4);

    // ================= 06 THE TRANSISTOR =================
    const t06 = start('06') - 0.2, tBlocks = c('06', 'blocks'), tThird = c('06', 'third'), tLittle = c('06', 'little'), tStarts = c('06', 'starts'), tCloses = c('06', 'closes'), tTurn = c('06', 'turn'), tTrans = c('06', 'transistor'), tLever = c('06', 'lever'), tFlips = c('06', 'flips');
    const gate6 = (t) => (t < tLittle ? 0 : t < tTurn ? 1 : t < tFlips - 0.1 ? 0 : 1);
    add({ scene: 'stage', t0: t06, trans: 0.45, act(t, S) {
      const E = stageReset(S); E.tr.visible = true;
      const gw = t > tThird - 0.2; E.gWire.visible = gw; E.gBat.visible = gw; E.gWire.scale.y = gw ? Math.max(0.001, backOut(K(t, tThird - 0.2, tThird + 0.2))) : 0.001;
      const gt = gate6(t); const gk = gt ? K(t, t < tTurn ? tLittle : tFlips - 0.1, (t < tTurn ? tLittle : tFlips - 0.1) + 0.5) : 1 - K(t, tTurn, tTurn + 0.25);
      const conduct = gt ? K(t, (t < tTurn ? tStarts - 0.2 : tFlips), (t < tTurn ? tStarts + 0.2 : tFlips + 0.3)) : 0;
      E.T.userData.set(conduct); E.tBulb.userData.set(conduct);
      E.gDots.visible = gw; E.gDots.userData.update(t, gk > 0.05 ? 1 : 0, { speed: 0.25 });
      E.tDots.userData.update(t, 1, conduct > 0.5 ? { speed: 0.16 } : { speed: 0.16, stopAt: E.tStop });
      if (t < tThird) cm(S, t, t06, tThird, v3(-20, 70, 170), v3(0, 14, 0), v3(-10, 66, 160), v3(0, 16, 0), smooth);
      else if (t < tTrans) cm(S, t, tThird, tStarts, v3(-10, 66, 160), v3(0, 16, 0), v3(-30, 76, 150), v3(-6, 24, -4), smooth);
      else cm(S, t, tTrans, end('06') + 0.5, v3(-30, 76, 150), v3(-6, 24, -4), v3(10, 60, 130), v3(0, 20, 0), smooth);
    }, overlay(t, g, S) {
      if (t > tBlocks && t < tThird) { const p = project(S.cam, v3(0, 34, 0)); tag('SILICON', p[0], p[1] - 40, { size: 28, scale: pop(t, tBlocks - 0.4) }); text([['GAP ', WH], ['OPEN', R]], W / 2, 120, { size: 50, scale: pop(t, tBlocks) }); }
      if (t > tThird && t < tTrans) { const p = project(S.cam, v3(-40, 22, -24)); tag('3RD WIRE', p[0] - 120, p[1] + 20, { size: 26, scale: pop(t, tThird), color: CYc }); }
      if (t > tCloses - 0.1 && t < tTurn) text([['GAP ', WH], ['CLOSED', G]], W / 2, 120, { size: 50, scale: pop(t, tCloses - 0.1) });
      if (t > tTurn && t < tTrans) text([['GAP ', WH], ['OPEN', R]], W / 2, 120, { size: 50, scale: pop(t, tTurn) });
      if (t > tTrans) text('TRANSISTOR', W / 2, 130, { size: 76, color: Y, scale: pop(t, tTrans) });
      if (t > tLever) tag('A SWITCH WITH NO LEVER', W / 2, 960, { size: 32, scale: pop(t, tLever) });
      vignette(0.35);
    } });
    fx('whoosh', t06, 0.5); fx('buzz', tBlocks, 0.35); fx('pop', tThird - 0.2, 0.6); fx('lighton', tLittle, 0.5); fx('lighton', tStarts, 0.7); fx('chime', tCloses, 0.4); fx('lightoff', tTurn, 0.6); fx('pop', tTrans, 0.8); fx('lighton', tFlips, 0.6);

    // ================= 07 SWITCHES FLIPPING SWITCHES =================
    const t07 = start('07') - 0.2, tFlip7 = c('07', 'flip'), tSwitches7 = c('07', 'switches'), tIdea = c('07', 'idea');
    add({ scene: 'stage', t0: t07, trans: 0.45, act(t, S) {
      const E = stageReset(S); E.ch.visible = true;
      // cascade: first run timed to the words, then it repeats as a loop
      const run0 = tFlip7 - 0.3, step = 0.55; const per = step * 5 + 0.8;
      const loopT = t < run0 + per ? t - run0 : (t - run0) % per;
      const stageOn = (i) => loopT > i * step; // 0 = input, 1..4 transistors
      E.chInD.userData.update(t, stageOn(0) ? 1 : 0, { speed: 0.5 });
      E.chain.forEach((q, i) => { const on = stageOn(i + 1); q.T.userData.set(on ? 1 : 0); q.d.userData.update(t, on ? 1 : 0, { speed: 0.5 }); });
      E.chBulb.userData.set(stageOn(5) ? 1 : 0);
      cm(S, t, t07, end('07') + 0.5, v3(-40, 80, 210), v3(-10, 14, 0), v3(30, 70, 200), v3(10, 14, 0), smooth);
    }, overlay(t, g, S) {
      if (t > tSwitches7 - 0.2) text([['SWITCHES ', Y], ['FLIPPING ', WH], ['SWITCHES', Y]], W / 2, 130, { size: 52, scale: pop(t, tSwitches7 - 0.2) });
      if (t > tIdea) tag('THE IDEA BEHIND EVERY COMPUTER', W / 2, 960, { size: 30, scale: pop(t, tIdea) });
      vignette(0.35);
    } });
    { const run0 = tFlip7 - 0.3; for (let k = 0; k < 6; k++) fx('lamp', run0 + k * 0.55, 0.6); fx('chime', run0 + 5 * 0.55, 0.45); }
    fx('whoosh', t07, 0.5); fx('pop', tSwitches7 - 0.2, 0.6); fx('pop', tIdea, 0.5);

    // ================= 08 MAKING CHIPS (the Foundry) =================
    const t08 = start('08') - 0.2, tSand8 = c('08', 'sand'), tMelted = c('08', 'melted'), tPure = c('08', 'pure'), tCrystal = c('08', 'crystal'), tSliced = c('08', 'sliced'), tCoin = c('08', 'coin'), tPrinted = c('08', 'printed'), tLight = c('08', 'light'), tChip = c('08', 'chip');
    add({ scene: 'foundry', t0: t08, trans: 0.5, act(t, S) {
      const O = S.O; O.bob.position.set(16, 4, 40); O.bob.rotation.y = -2.92;
      pose(O.bob, t, { lookY: t > tSliced ? -0.6 : 0, nod: t > tCrystal && t < tSliced ? -0.25 : 0 });
      O.crucible.userData.glow(t > tMelted ? 1 : 0.5 + 0.5 * Math.sin(t * 3));
      O.ingot.visible = t > tCrystal - 0.3;
      const gk = K(t, tCrystal - 0.3, tSliced - 0.2); O.ingot.userData.grow(t < tCrystal - 0.3 ? 0.08 : 0.08 + 0.92 * smooth(gk)); O.ingot.position.y = 4 + 9 + (t < tCrystal - 0.3 ? 0 : 6 * smooth(gk));
      O.wafers.forEach((w, k) => { const on = K(t, tSliced + k * 0.12, tSliced + k * 0.12 + 0.25); w.scale.setScalar(Math.max(0.001, backOut(on))); w.userData.chips(0); });
      const pr = t > tPrinted - 0.3; O.bigWafer.visible = pr; O.bigWafer.scale.setScalar(Math.max(0.001, backOut(K(t, tPrinted - 0.3, tPrinted + 0.2)))); O.bigWafer.userData.chips(K(t, tLight - 0.2, tLight + 1.2)); O.beam.material.opacity = pr ? 0.3 * (1 - K(t, tChip, tChip + 0.6)) * K(t, tPrinted - 0.3, tPrinted) : 0;
      if (t < tMelted) cm(S, t, t08, tMelted, v3(-10, 70, 200), v3(-10, 20, -20), v3(-70, 34, 60), v3(-48, 8, -6), smooth);
      else if (t < tCrystal) cm(S, t, tMelted, tCrystal, v3(-70, 34, 60), v3(-48, 8, -6), v3(-6, 40, 50), v3(0, 14, -30), smooth);
      else if (t < tSliced) cm(S, t, tCrystal - 0.2, tSliced, v3(-6, 40, 50), v3(0, 14, -30), v3(-10, 58, 72), v3(0, 34, -30), smooth);
      else if (t < tCoin) cm(S, t, tSliced - 0.1, tCoin, v3(-10, 58, 72), v3(0, 34, -30), v3(40, 30, 30), v3(52, 6, -20), smooth);
      else if (t < tPrinted - 0.3) cm(S, t, tCoin, tPrinted - 0.3, v3(40, 30, 30), v3(52, 6, -20), v3(42, 32, 46), v3(52, 12, -18), (x) => x);
      else cm(S, t, tPrinted - 0.3, end('08') + 0.6, v3(42, 32, 46), v3(52, 12, -18), v3(52, 40, 105), v3(52, 32, -10), smooth);
    }, overlay(t, g, S) {
      if (t > tSand8 && t < tMelted + 0.5) { const p = project(S.cam, v3(-48, 14, -6)); tag('SAND', p[0], p[1] - 40, { size: 28, scale: pop(t, tSand8) }); }
      if (t > tPure && t < tCrystal) text([['99.9999999% ', G], ['PURE', WH]], W / 2, 130, { size: 52, scale: pop(t, tPure) });
      if (t > tCrystal && t < tSliced) { const p = project(S.cam, v3(0, 40, -30)); tag('ONE BIG CRYSTAL', p[0] + 240, p[1], { size: 28, scale: pop(t, tCrystal) }); }
      if (t > tCoin - 0.2 && t < tPrinted - 0.3) tag('THINNER THAN A COIN', W / 2, 130, { size: 34, scale: pop(t, tCoin - 0.2) });
      if (t > tLight) text([['PRINTED WITH ', WH], ['LIGHT', '#c9a8ff']], W / 2, 120, { size: 48, scale: pop(t, tLight) });
      if (t > tChip) { const p = project(S.cam, v3(52, 30, -10)); const k = pop(t, tChip); g.save(); g.strokeStyle = Y; g.lineWidth = 7; g.globalAlpha = Math.min(1, k); g.strokeRect(p[0] - 30, p[1] - 30, 60, 60); g.restore(); tag('1 CHIP', p[0] + 140, p[1] - 30, { size: 30, scale: k }); }
      vignette(0.3);
    } });
    fx('whoosh', t08, 0.6); fx('rumble', tMelted - 0.4, 0.5); fx('hum', tMelted, 0.3, { dur: Math.max(1, tCrystal - tMelted) }); fx('pop', tPure, 0.6); fx('sparkle', tCrystal, 0.5);
    for (let k = 0; k < 6; k++) fx('tile', tSliced + k * 0.12, 0.6); fx('pop', tCoin - 0.2, 0.5); fx('zoom', tPrinted - 0.3, 0.5); fx('sparkle', tLight, 0.6); fx('pop', tChip, 0.7);

    // ================= 09 SPEED: before you finish blinking =================
    const t09 = start('09') - 0.2, tSeven = c('09', 'seven'), tEach = c('09', 'each'), tBlink = c('09', 'blinking');
    add({ scene: 'foundry', t0: t09, trans: 0.4, act(t, S) {
      const O = S.O; O.bob.position.set(-22, 4, 22); O.bob.rotation.y = 0.6;
      const bl = t > tBlink - 0.1 ? Math.sin(Math.PI * K(t, tBlink - 0.1, tBlink + 0.45)) : 0;
      pose(O.bob, t, { blink: bl });
      O.bigWafer.visible = false; O.beam.material.opacity = 0; O.ingot.visible = true; O.ingot.userData.grow(1); O.ingot.position.y = 19;
      cm(S, t, t09, end('09') + 0.5, v3(-4, 30, 72), v3(-22, 22, 22), v3(-8, 28, 62), v3(-22, 22, 22), smooth);
    }, overlay(t, g) {
      if (t > tSeven) text([['768 ', G], ['NUMBERS', WH]], 430, 330, { size: 48, scale: pop(t, tSeven) });
      if (t > tEach) text([['x 8 ', Y], ['LAMPS', WH]], 430, 420, { size: 44, scale: pop(t, tEach) });
      if (t > tEach + 0.5) text([['= 6,144 ', G], ['FLIPS', WH]], 430, 510, { size: 44, scale: pop(t, tEach + 0.5) });
      if (t > tBlink - 0.1) { const n = Math.min(6144, Math.floor(6144 * K(t, tBlink - 0.1, tBlink + 0.05))); tag(`CHIP: ${n.toLocaleString('en-US')} / 6,144`, 430, 640, { size: 30, color: n >= 6144 ? G : WH }); if (n >= 6144) text('DONE', 430, 720, { size: 54, color: G, scale: pop(t, tBlink + 0.05) }); }
      vignette(0.3);
    } });
    fx('whoosh', t09, 0.4); fx('pop', tSeven, 0.6); fx('pop', tEach, 0.6); fx('pop', tEach + 0.5, 0.6); fx('count', tBlink - 0.1, 0.5, { dur: 0.15 }); fx('chime', tBlink + 0.05, 0.6);

    // ================= 10 MAP OUTRO =================
    const t10 = start('10') - 0.3, tPlant = c('10', 'plants'), tFirst = c('10', 'first'), tNext = c('10', 'next'), tDecisions = c('10', 'decisions');
    add({ scene: 'map', t0: t10, trans: 0.6, act(t, S) {
      const O = S.O; O.bob.visible = true; const p = S.wpPos(7); O.bob.position.copy(p).add(v3(-6, 0, 3)); O.bob.rotation.y = 0.5;
      const pk = K(t, tPlant + 0.1, tPlant + 0.5); O.newFlag.scale.setScalar(Math.max(0.0001, 0.55 * backOut(pk)));
      pose(O.bob, t, t > tPlant + 0.5 && t < tPlant + 2 ? { cheer: smooth(K(t, tPlant + 0.5, tPlant + 0.8)) * (1 - K(t, tPlant + 1.6, tPlant + 2)) } : { lookY: t > tNext ? 1.0 * smooth(K(t, tNext, tNext + 0.6)) : 0 });
      const w7 = S.wpPos(7), w8 = S.wpPos(8);
      const c1 = [w7.clone().add(v3(-10, 70, 80)), w7.clone().add(v3(0, 8, 0))], c2 = [w7.clone().lerp(w8, 0.5).add(v3(-20, 150, 170)), w7.clone().lerp(w8, 0.5)], c3 = [w8.clone().add(v3(-30, 170, 190)), w8.clone()];
      if (t < tNext) cm(S, t, t10, tNext, c1[0].clone().add(v3(0, 10, 20)), c1[1], c1[0], c1[1], smooth);
      else if (t < end('10') + 1) cm(S, t, tNext, end('10') + 1, c1[0], c1[1], c2[0], c2[1]);
      else cm(S, t, end('10') + 1, duration, c2[0], c2[1], c3[0], c3[1], (x) => x);
    }, overlay(t, g, S) {
      if (t > tPlant + 0.3 && t < tNext) { const [x, y] = project(S.cam, S.wpPos(7).add(v3(3, 22, -2))); tag('STOP 7 CLEARED', x, y - 70, { size: 28, scale: pop(t, tPlant + 0.4) }); }
      if (t > tFirst && t < tNext) tag('FIRST FLAG IN THE FOUNDRY', W / 2, 160, { size: 30, scale: pop(t, tFirst) });
      if (t > tDecisions) { const k = pop(t, tDecisions); const [x, y] = project(S.cam, S.wpPos(8).add(v3(0, 30, 0))); text('NEXT STOP', x, y - 90, { size: 40, scale: k }); text('???', x, y - 20, { size: 64, color: Y, scale: pop(t, tDecisions + 0.2) }); }
      vignette(0.3);
      const fo = K(t, duration - 1.2, duration); if (fo > 0) { g.fillStyle = `rgba(0,0,0,${fo})`; g.fillRect(0, 0, W, H); }
    } });
    fx('whoosh', t10, 0.6); fx('flag', tPlant + 0.1, 1.0); fx('chime', tPlant + 0.4, 0.6); fx('pop', tFirst, 0.5); fx('whoosh', tNext, 0.4); fx('pop', tDecisions, 0.6);

    const beds = []; sh.slice().sort((a, b) => a.t0 - b.t0).forEach((s, i, arr) => { const t1 = i < arr.length - 1 ? arr[i + 1].t0 : duration; beds.push({ scene: s.scene, t0: s.t0, t1 }); });
    beds.forEach((b) => fx(b.scene === 'stage' ? 'bed_stage' : b.scene === 'map' ? 'bed_map' : b.scene === 'foundry' ? 'bed_foundry' : 'bed_canyon', b.t0, 1, { dur: b.t1 - b.t0 }));
    return sh;
  },
};
function E7rows(S) { return S.O.e7 ? S.O.e7.rows : []; }
