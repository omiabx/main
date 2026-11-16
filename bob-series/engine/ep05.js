// Episode 5 — "How Numbers Became Pictures". Shot list, overlays and sound cues, all anchored to voice words.
import * as THREE from 'three';
import { W, H, clamp, lerp, ease, easeOut, smooth, backOut, ramp, pop, v3, aim, project, text, bubble, tag, vignette, SKY, setSky, g2, Y, G, R, B, WH, CY } from './core.js';
import { pose } from './models.js';
import { FACE8, LIGHT, DARK, face16, photoCanvas, galleryCanvas, lunchCanvas, digitsCanvas, sample } from './pics.js';

const K = (t, a, b) => clamp((t - a) / (b - a));
function cm(S, t, a, b, P0, L0, P1, L1, e = ease) { const k = e(K(t, a, b)); aim(S.cam, P0.clone().lerp(P1, k), L0.clone().lerp(L1, k)); }
const F8 = FACE8.join('').split('').map((c) => (c === '1' ? LIGHT : DARK));
const BITS = FACE8.join('').split('').map(Number);
const gray = (v) => (v << 16) | (v << 8) | v;
let _f16 = null, _photoTiles = null, _gal = null, _lunch = null, _photo = null, _galTiles = null;
const f16 = () => _f16 || (_f16 = face16());
const photo = () => _photo || (_photo = photoCanvas());
const gal = () => _gal || (_gal = galleryCanvas());
const lunch = () => _lunch || (_lunch = lunchCanvas());
const photoTiles = () => _photoTiles || (_photoTiles = sample(photo(), 24, 46));
const galTiles = () => _galTiles || (_galTiles = sample(gal(), 24, 46));

// ---------- canyon helpers ----------
const CAM = {
  wide: [v3(0, 70, 310), v3(0, 32, -10)],
  wall: [v3(64, 56, 104), v3(118, 50, -20)],
  lamps: [v3(-66, 44, 108), v3(-112, 34, -16)],
};
function canyonReset(S, t, o = {}) {
  const O = S.O;
  S.scene.background = setSky(o.dusk ?? 0);
  const dk = o.dusk ?? 0;
  S.L.sun.color.setRGB(1, lerp(0.94, 0.66, dk), lerp(0.85, 0.48, dk)); S.L.sun.intensity = lerp(2.5, 2.0, dk);
  S.L.hemi.intensity = lerp(1.35, 1.0, dk); S.L.hemi.color.setRGB(lerp(0.81, 0.85, dk), lerp(0.9, 0.62, dk), lerp(1, 0.75, dk));
  O.wall8.visible = !o.w16; O.wall16.visible = !!o.w16;
  O.wall8.userData.tiles.userData.layout(8, 8); O.wall8.userData.tiles.userData.hideAll();
  O.wall16.userData.tiles.userData.hideAll();
  O.lamps.userData.set(0);
  if (S.cam.fov !== 32) { S.cam.fov = 32; S.cam.updateProjectionMatrix(); }
}
function paint(wall, colors, cols, rows, prog) {
  const T = wall.userData.tiles.userData; T.layout(cols, rows);
  for (let i = 0; i < cols * rows; i++) { const p = prog(i); if (p <= 0) T.set(i, 0, 0.0001); else T.set(i, colors[i], backOut(p), (1 - clamp(p)) * 8); }
}
const rowProg = (t, rowTimes, cols, d = 0.4) => (i) => { const r = Math.floor(i / cols), c = i % cols; const t0 = rowTimes[r]; return t0 == null ? 0 : K(t, t0 + c * d / cols, t0 + c * d / cols + 0.25); };
function cellWorld(wall, cols, rows, i, size = 64) {
  const ts = size / Math.max(cols, rows); const cx = i % cols, cy = Math.floor(i / cols);
  const p = v3((cx - (cols - 1) / 2) * ts, ((rows - 1) / 2 - cy) * ts, 1.5).add(wall.userData.center);
  wall.updateMatrixWorld(); return p.applyMatrix4(wall.matrixWorld);
}
function lampDigits(S, bits, sc = 1, size = 34) {
  const L = S.O.lamps; L.updateMatrixWorld();
  L.userData.lamps.forEach((m, i) => { const p = m.getWorldPosition(v3(0, 0, 0)).add(v3(0, 8, 0)); const [x, y] = project(S.cam, p); text(String(bits[i]), x, y - 26, { size, color: bits[i] ? Y : '#b9b2d8', scale: sc }); });
}
function headPos(S, ch, up = 34) { return project(S.cam, ch.getWorldPosition(v3(0, 0, 0)).add(v3(0, up, 0))); }

// ---------- 2D digit board ----------
function digitBoard(t, o = {}) {
  const cell = 76, n = 8, w = cell * n, x0 = W / 2 - w / 2 + (o.dx ?? 0), y0 = H / 2 - w / 2 + 10 + (o.dy ?? 0);
  const a = o.alpha ?? 1; if (a <= 0) return;
  g2.save(); g2.globalAlpha = a;
  g2.fillStyle = '#0d0b1e'; g2.fillRect(x0 - 34, y0 - 34, w + 68, w + 68);
  g2.fillStyle = '#1d1640'; g2.fillRect(x0 - 26, y0 - 26, w + 52, w + 52);
  g2.strokeStyle = '#f2c14e'; g2.lineWidth = 6; g2.strokeRect(x0 - 26, y0 - 26, w + 52, w + 52);
  g2.restore();
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
    const i = r * n + c; const vis = o.rows ? o.rows(r, c) : 1; if (vis <= 0) continue;
    const rv = o.reveal ? o.reveal(r, c) : 0; const cx = x0 + c * cell + cell / 2, cy = y0 + r * cell + cell / 2;
    if (rv > 0) { const s = cell * 0.92 * backOut(rv); g2.fillStyle = BITS[i] ? '#f4e6c4' : '#2a2840'; g2.fillRect(cx - s / 2, cy - s / 2, s, s); }
    if (rv < 1) text(String(BITS[i]), cx, cy + 3, { size: 44, color: BITS[i] ? Y : '#7d73ad', scale: backOut(vis) * (1 - rv), stroke: 8, shadow: 4, glow: o.glow && BITS[i] ? o.glow : 0 });
  }
}

// ---------- stage helpers ----------
function stageReset(S, t) {
  const O = S.O; O.phone.visible = true; O.tiles.visible = false; O.sub.visible = false; O.rgb.visible = false; S.setBlocks([]);
  O.phone.userData.screen.visible = true; O.phone.position.set(0, 6, 0); O.phone.rotation.set(0, 0, 0);
}
const SCR = v3(0, 32.5, 0); // phone screen centre (world)

export const EPISODE = {
  gaps: { pre: 0.5, default: 0.45, after: { '01': 0.8, '02': 0.35, '04': 0.5, '05': 1.6, '06': 0.4, '08': 0.5, '10': 0.5, '11': 4.6, '12': 0.7, '13': 0.6, '14': 0.8 }, endHold: 13 },
  shots({ cue, start, end, fx, duration }) {
    const sh = []; const add = (o) => { sh.push(o); return o; };
    const c = cue;

    // ================= 01 HOOK =================
    add({ scene: 'stage', t0: 0, act(t, S) {
      stageReset(S, t);
      const tNever = c('01', 'never'), tNum = c('01', 'numbers');
      let mode = 'gal';
      if (t > tNum) mode = 'dig';
      if (mode === 'gal') S.screen(gal(), (x) => {
        const k = K(t, c('01', 'screenshots'), c('01', 'screenshots') + 0.3) * (1 - K(t, tNever - 0.2, tNever));
        if (k > 0) { x.lineWidth = 6; x.strokeStyle = `rgba(255,74,74,${k})`; gal().userData.screenshots.forEach(([X, Yy, s]) => x.strokeRect(X + 3, Yy + 3, s - 6, s - 6)); }
        const gk = K(t, tNever, tNever + 0.25); if (gk > 0) { for (let k2 = 0; k2 < 14; k2++) { x.fillStyle = `rgba(${k2 % 2 ? 79 : 255},${k2 % 2 ? 240 : 210},${k2 % 2 ? 122 : 63},${gk * 0.7})`; const yy = (k2 * 53 + Math.floor(t * 40) * 17) % 460; x.fillRect(0, yy, 240, 6 + (k2 % 3) * 4); } }
      });
      else S.screen(digitsCanvas(t));
      cm(S, t, 0, c('01', 'like'), v3(30, 58, 210), v3(0, 34, 0), v3(6, 40, 92), v3(0, 33, 0), smooth);
    }, overlay(t, g, S) {
      const ts = c('01', 'screenshots'); const k = pop(t, ts + 0.15);
      if (t < c('01', 'never')) tag('SCREENSHOTS: 2,911', W / 2 + 330, 300, { scale: k, size: 30, color: R });
      const tp = c('01', 'picture'); if (t > tp) text([['PICTURES STORED: ', WH], ['0', R]], W / 2, 930, { size: 46, scale: pop(t, tp) });
      vignette(0.4);
    } });
    fx('glitch', c('01', 'never'), 0.7); fx('pop', c('01', 'screenshots') + 0.15, 0.8); fx('pop', c('01', 'picture'), 0.9);
    fx('zoom', 0.6, 0.35);

    const tLike = c('01', 'like');
    add({ scene: 'stage', t0: tLike, trans: 0.4, act(t, S) {
      stageReset(S, t); S.O.phone.visible = false;
      cm(S, t, tLike, end('01') + 1, v3(-20, 70, 230), v3(0, 20, 0), v3(20, 64, 210), v3(0, 22, 0), smooth);
    }, overlay(t, g) {
      g.fillStyle = 'rgba(10,6,24,0.45)'; g.fillRect(0, 0, W, H);
      const t0 = tLike + 0.1; const tr = c('01', 'read');
      digitBoard(t, { rows: (r, cc) => K(t, t0 + r * 0.14 + cc * 0.012, t0 + r * 0.14 + cc * 0.012 + 0.25), glow: t > tr ? 14 + Math.sin(t * 8) * 8 : 0 });
      const tp = c('01', 'picture', 2); if (t > tp && t < tr) text('?', W / 2 + 420, H / 2 - 260, { size: 120, color: Y, scale: pop(t, tp), rot: Math.sin(t * 5) * 0.12 });
    } });
    for (let r = 0; r < 8; r++) fx('tick', tLike + 0.1 + r * 0.14, 0.5);
    fx('whoosh', tLike - 0.1, 0.6); fx('sparkle', c('01', 'read'), 0.7);

    // ================= 02 MAP RECAP =================
    const t02 = start('02') - 0.35, tFlags = c('02', 'four'), tFirst = c('02', 'first'), tSecond = c('02', 'second'), tCount = c('02', 'count'), tLast = c('02', 'last');
    add({ scene: 'map', t0: t02, trans: 0.5, act(t, S) {
      const O = S.O; O.bob.visible = true; O.newFlag.scale.setScalar(0.0001);
      // Bob walks from stop 4 to stop 5
      const wk = K(t, t02 + 0.6, tFlags + 1.2); const f = smooth(wk);
      const p = S.between(4, 5, f), p2 = S.between(4, 5, Math.min(1, f + 0.02));
      O.bob.position.copy(p); O.bob.rotation.y = Math.atan2(p2.x - p.x, p2.z - p.z) * (wk < 1 ? 1 : 0) + (wk >= 1 ? 0.3 : 0);
      pose(O.bob, t, wk > 0 && wk < 1 ? { walk: t * 11 } : (t > tFlags + 1.4 && t < tFlags + 2.6 ? { wave: smooth(K(t, tFlags + 1.4, tFlags + 1.8)) * (1 - K(t, tFlags + 2.3, tFlags + 2.6)) } : {}));
      // camera: overview -> desert -> along flags
      const ov = [v3(248, 470, 520), v3(248, 0, 150)];
      const ds = [v3(118, 200, 360), v3(118, 0, 228)];
      const fl = (n) => { const w = S.wpPos(n); return [w.clone().add(v3(30, 110, 120)), w.clone().add(v3(0, 4, 0))]; };
      if (t < tFlags) cm(S, t, t02 + 0.8, tFlags, ov[0], ov[1], ds[0], ds[1]);
      else if (t < tFirst) cm(S, t, tFlags, tFirst, ds[0], ds[1], fl(1)[0], fl(1)[1]);
      else if (t < tSecond) cm(S, t, tFirst, tSecond, fl(1)[0], fl(1)[1], fl(2)[0], fl(2)[1]);
      else if (t < tCount) cm(S, t, tSecond, tCount, fl(2)[0], fl(2)[1], fl(3)[0], fl(3)[1]);
      else cm(S, t, tCount, tLast, fl(3)[0], fl(3)[1], fl(4)[0], fl(4)[1]);
    }, overlay(t, g, S) {
      const k = pop(t, t02 + 0.4) * (1 - K(t, tFlags - 0.4, tFlags));
      if (k > 0) { text([['STOP ', WH], ['5', Y]], W / 2, 150, { size: 84, scale: k }); tag('THE DESERT', W / 2, 250, { scale: k, size: 34 }); }
      const titles = [[tFirst, 1, 'WHAT IS A COMPUTER?'], [tSecond, 2, 'WHY 1s AND 0s?'], [tCount, 3, 'COUNTING IN BINARY'], [tLast - 0.9, 4, 'BINARY TO TEXT']];
      titles.forEach(([tt, n, s], i) => {
        const nx = i < 3 ? titles[i + 1][0] : tLast + 0.4; if (t < tt || t > nx + 0.2) return;
        const [x, y] = project(S.cam, S.wpPos(n).add(v3(2, 22, 0)));
        tag(`STOP ${n}`, x, y - 100, { scale: pop(t, tt), size: 24, color: WH });
        tag(s, x, y - 52, { scale: pop(t, tt + 0.08), size: 30 });
      });
      vignette(0.3);
    } });
    fx('whoosh', t02, 0.7); fx('pop', t02 + 0.4, 0.8);
    for (let k = 0; k < 9; k++) fx('step', t02 + 0.6 + k * ((tFlags + 0.6 - t02) / 9), 0.45);
    [tFirst, tSecond, tCount, tLast - 0.9].forEach((tt) => fx('flagpop', tt, 0.7));

    add({ scene: 'canyon', t0: tLast, trans: 0.45, act(t, S) {
      canyonReset(S, t);
      const tm = c('02', 'message'), tl = c('02', 'letter');
      S.O.lamps.userData.set(t > tl + 0.5 ? 73 : t > tm ? 72 : 0);
      pose(S.O.bob, t, { point: smooth(K(t, tm - 0.3, tm)) * 0.7 });
      cm(S, t, tLast, end('02') + 0.4, v3(-30, 80, 330), v3(-10, 30, -10), v3(10, 66, 300), v3(0, 32, -10), smooth);
    }, overlay(t, g, S) {
      tag('LAST EPISODE', 210, 80, { size: 26, color: WH, scale: pop(t, tLast + 0.2) });
      const tm = c('02', 'message'), tl = c('02', 'letter');
      if (t > tm) { const v = t > tl + 0.5 ? 73 : 72; lampDigits(S, [...v.toString(2).padStart(8, '0')].map(Number), 1, 26); }
      const tL = c('02', 'lamps'); if (t > tL) { const [x, y] = headPos(S, S.O.friend, 36); bubble('HI!', x, y, { scale: pop(t, tL), size: 44 }); }
    } });
    fx('whoosh', tLast - 0.1, 0.5); fx('lamp', c('02', 'message'), 0.7); fx('lamp', c('02', 'letter') + 0.5, 0.7); fx('pop', c('02', 'lamps'), 0.8);

    // ================= 03 THE PROBLEM =================
    const t03 = start('03') - 0.2, tSee = c('03', 'see'), tFair = c('03', 'fair'), tBut = c('03', 'but'), tFace = c('03', 'face');
    add({ scene: 'canyon', t0: t03, act(t, S) {
      canyonReset(S, t);
      pose(S.O.friend, t + 1.3, { tilt: Math.sin(t * 3) * 0.05 });
      cm(S, t, t03, tFair, v3(0, 40, 140), v3(56, 26, 22), v3(10, 38, 122), v3(56, 26, 22), smooth);
    }, overlay(t, g, S) {
      if (t > tSee - 0.3) { const [x, y] = headPos(S, S.O.friend, 34); bubble(['WHAT DO YOU', 'LOOK LIKE?'], x, y - 10, { scale: pop(t, tSee - 0.3), size: 40 }); }
    } });
    fx('pop', tSee - 0.3, 0.8);
    add({ scene: 'canyon', t0: tFair, act(t, S) {
      canyonReset(S, t);
      pose(S.O.bob, t, { wave: smooth(K(t, tFair + 0.6, tFair + 1)) * (1 - K(t, tBut - 0.4, tBut)) });
      S.cam.fov = 58; S.cam.updateProjectionMatrix();
      cm(S, t, tFair, tBut, v3(98, 40, 46), v3(-40, 14, 16), v3(95, 39, 43), v3(-40, 14, 16), smooth);
    }, overlay(t, g, S) {
      const tb = c('03', 'bean');
      if (t > tb - 0.2) { const [x, y] = headPos(S, S.O.bob, 36); const k = pop(t, tb - 0.2); text('BOB', x, y - 120, { size: 40, color: Y, scale: k }); g.fillStyle = Y; g.strokeStyle = '#14102a'; g.lineWidth = 6; if (k > 0.5) { g.beginPath(); g.moveTo(x - 16, y - 78); g.lineTo(x + 16, y - 78); g.lineTo(x, y - 52); g.closePath(); g.stroke(); g.fill(); } }
    } });
    fx('whoosh', tFair - 0.1, 0.4); fx('pop', c('03', 'bean') - 0.2, 0.8);
    add({ scene: 'canyon', t0: tBut, act(t, S) {
      canyonReset(S, t);
      const tl = c('03', 'lamps'); const idx = Math.floor((t - tl) * 4);
      const vals = [72, 66, 203, 9, 128, 255, 17, 90, 61, 144];
      if (t > tl && t < tFace) S.O.lamps.userData.set(vals[((idx % vals.length) + vals.length) % vals.length]);
      pose(S.O.bob, t, { think: smooth(K(t, tFace - 0.2, tFace + 0.2)) });
      cm(S, t, tBut, end('03') + 0.5, ...CAM.lamps, v3(-58, 40, 98), v3(-100, 30, -10), smooth);
    }, overlay(t, g, S) {
      const tl = c('03', 'lamps'); const vals = [72, 66, 203, 9, 128, 255, 17, 90, 61, 144];
      if (t > tl && t < tFace) { const v = vals[((Math.floor((t - tl) * 4) % vals.length) + vals.length) % vals.length]; const [x, y] = project(S.cam, S.O.lamps.getWorldPosition(v3(0, 0, 0)).add(v3(0, 46, 0))); tag(String(v), x, y - 30, { size: 34 }); }
      if (t > tFace) { const [x, y] = headPos(S, S.O.bob, 34); bubble('?', x, y, { scale: pop(t, tFace), size: 56 }); text([['FACE ', WH], ['-> ', Y], ['NUMBERS?', G]], W / 2, 960, { size: 52, scale: pop(t, tFace + 0.25) }); }
    } });
    { const tl = c('03', 'lamps'); for (let k = 0; k < Math.floor((tFace - tl) * 4); k++) fx('lamp', tl + k / 4, 0.35); }
    fx('pop', tFace, 0.8); fx('pop', tFace + 0.25, 0.6);

    // ================= 04 PIXELS =================
    const t04 = start('04') - 0.2, tClose = c('04', 'close'), tBreaks = c('04', 'breaks'), tPixel = c('04', 'pixel'), tColor = c('04', 'color'), tThats = c('04', "that's"), tBlend = c('04', 'blend');
    const pickI = 14 * 24 + 8; // a tile near Bob's eye
    add({ scene: 'stage', t0: t04, trans: 0.45, act(t, S) {
      stageReset(S, t); S.screen(photo());
      const open = K(t, tBreaks, tBreaks + 0.9) * (1 - K(t, tThats + 0.6, tBlend));
      const showTiles = t > tBreaks - 0.05 && t < tBlend + 0.4;
      S.O.tiles.visible = showTiles; S.O.phone.userData.screen.visible = !showTiles;
      if (showTiles) S.setTiles(photoTiles(), (i) => {
        const r = ((i * 2654435761) >>> 0) / 4294967296; const lift = (open * (0.5 + r * 1.1));
        let z = lift, s = 1 - 0.16 * open;
        if (i === pickI) { const k = smooth(K(t, tPixel - 0.1, tPixel + 0.3)) * (1 - K(t, tThats, tThats + 0.4)); z += k * 5; s *= 1 + k * 0.25; }
        return { s, z, d: 0.4 + open * 0.6 };
      });
      S.O.tiles.material.emissive.setHex(0x000000);
      const far = [v3(-26, 44, 150), SCR.clone()], near = [v3(-16, 44, 36), v3(-1, 35, 0)], nearer = [v3(-14, 38, 26), v3(-2.5, 33, 2)];
      if (t < tClose) cm(S, t, t04, tClose, far[0], far[1], v3(-18, 42, 120), SCR.clone(), smooth);
      else if (t < tBreaks + 1) cm(S, t, tClose, tBreaks + 0.6, v3(-18, 42, 120), SCR.clone(), near[0], near[1]);
      else if (t < tThats) cm(S, t, tPixel - 0.4, tPixel + 0.6, near[0], near[1], nearer[0], nearer[1]);
      else cm(S, t, tThats, tBlend + 0.3, nearer[0], nearer[1], v3(24, 46, 150), SCR.clone());
    }, overlay(t, g, S) {
      if (t > tPixel - 0.1 && t < tThats + 0.2) {
        S.O.phone.updateMatrixWorld(); const cx = pickI % 24, cy = Math.floor(pickI / 24);
        const p = v3(cx - 11.5, 22.5 - cy, 5).applyMatrix4(S.O.tiles.matrixWorld); const [x, y] = project(S.cam, p);
        const k = pop(t, tPixel); const a = 1 - K(t, tThats, tThats + 0.2);
        g.save(); g.globalAlpha = a; g.strokeStyle = Y; g.lineWidth = 8; const bs = 120 * k; g.strokeRect(x - bs / 2, y - bs / 2, bs, bs); g.restore();
        text('PIXEL', x + 330, y - 140, { size: 64, color: Y, scale: k, alpha: a });
        if (t > tColor) { tag('= ONE COLOR', x + 330, y - 50, { scale: pop(t, tColor), size: 34, alpha: a }); }
      }
      if (t > tThats + 0.3) { const k = pop(t, c('04', 'grid')); text([['PICTURE ', WH], ['= ', Y], ['GRID OF SQUARES', G]], W / 2, 960, { size: 44, scale: k * (1 - K(t, end('04') + 0.2, end('04') + 0.4)) }); }
      vignette(0.35);
    } });
    fx('whoosh', t04, 0.5); fx('zoom', tClose, 0.8); fx('shatter', tBreaks, 0.9); fx('pop', tPixel, 0.9); fx('pop', tColor, 0.7); fx('zoomout', tThats, 0.7); fx('settle', tBlend, 0.6); fx('pop', c('04', 'grid'), 0.6);

    // ================= 05 ONES AND ZEROS =================
    const t05 = start('05') - 0.2, tLight = c('05', 'light'), tDark = c('05', 'dark'), tOne = c('05', 'one'), tZero = c('05', 'zero'), tBob5 = c('05', 'bob'), tFlash = c('05', 'flashes'), tIf = c('05', 'if');
    add({ scene: 'stage', t0: t05, trans: 0.45, act(t, S) {
      stageReset(S, t); S.O.phone.visible = false;
      S.setBlocks([{ x: -22, y: 6, c: LIGHT, s: backOut(K(t, tLight, tLight + 0.35)), ry: 0.3 }, { x: 22, y: 6, c: DARK, s: backOut(K(t, tDark, tDark + 0.35)), ry: -0.3 }]);
      cm(S, t, t05, tBob5, v3(0, 50, 150), v3(0, 16, 0), v3(0, 44, 128), v3(0, 16, 0), smooth);
    }, overlay(t, g, S) {
      text([['2 COLORS', WH]], W / 2, 170, { size: 54, scale: pop(t, c('05', 'two')) });
      const L = project(S.cam, v3(-22, 30, 0)), D = project(S.cam, v3(22, 30, 0));
      if (t > tOne - 0.1) text('1', L[0], L[1] - 60, { size: 110, color: Y, scale: pop(t, tOne - 0.1) });
      if (t > tZero - 0.1) text('0', D[0], D[1] - 60, { size: 110, color: '#b9b2d8', scale: pop(t, tZero - 0.1) });
      if (t > tLight) tag('LIGHT', L[0], L[1] + 250, { scale: pop(t, tLight), size: 28 });
      if (t > tDark) tag('DARK', D[0], D[1] + 250, { scale: pop(t, tDark), size: 28 });
      vignette(0.35);
    } });
    fx('whoosh', t05, 0.5); fx('pop', c('05', 'two'), 0.6); fx('block', tLight, 0.8); fx('block', tDark, 0.8); fx('pop', tOne - 0.1, 0.8); fx('pop', tZero - 0.1, 0.8);

    const tRow = c('05', 'row');
    add({ scene: 'canyon', t0: tBob5, trans: 0.4, act(t, S) {
      canyonReset(S, t);
      if (t > tRow) S.O.lamps.userData.set(BITS.slice(0, 8));
      pose(S.O.bob, t, { point: smooth(K(t, tRow - 0.3, tRow)) * 0.8 });
      cm(S, t, tBob5, tFlash, v3(-72, 50, 150), v3(-110, 32, -16), ...CAM.lamps, smooth);
    }, overlay(t, g, S) {
      if (t > tRow) lampDigits(S, BITS.slice(0, 8), pop(t, tRow), 38);
      if (t > tRow + 0.4) text([['1 ROW ', WH], ['= ', Y], ['8 SQUARES', G]], W / 2, 960, { size: 46, scale: pop(t, tRow + 0.4) });
    } });
    fx('whoosh', tBob5 - 0.1, 0.4); fx('lamp', tRow, 0.8); fx('pop', tRow + 0.4, 0.6);

    const tPaint = c('05', 'paints'), tN1 = c('05', 'next', 1), tN2 = c('05', 'next', 2);
    const rowT = [tPaint, tN1, tN2];
    add({ scene: 'canyon', t0: tFlash, trans: 0.35, act(t, S) {
      canyonReset(S, t);
      const r = t > tN2 - 0.5 ? 2 : t > tN1 - 0.5 ? 1 : 0;
      S.O.lamps.userData.set(BITS.slice(r * 8, r * 8 + 8));
      paint(S.O.wall8, F8, 8, 8, rowProg(t, rowT, 8));
      pose(S.O.friend, t + 1.3, { point: 0.6 * smooth(K(t, tPaint - 0.3, tPaint)) });
      cm(S, t, tFlash, tIf, ...CAM.wide, v3(10, 64, 290), v3(10, 34, -10), smooth);
    }, overlay(t, g, S) {
      const r = t > tN2 - 0.5 ? 2 : t > tN1 - 0.5 ? 1 : 0; lampDigits(S, BITS.slice(r * 8, r * 8 + 8), 1, 22);
      tag(`ROW ${r + 1}`, 300, 90, { size: 30 });
    } });
    rowT.forEach((tt, r) => { fx('lamp', tt - 0.5, 0.6); for (let k = 0; k < 8; k++) fx('tile', tt + k * 0.05, 0.35); });

    add({ scene: 'stage', t0: tIf, trans: 0.35, act(t, S) {
      stageReset(S, t); S.O.phone.visible = false;
      aim(S.cam, v3(0, 66, 220), v3(0, 22, 0));
    }, overlay(t, g) {
      g.fillStyle = 'rgba(10,6,24,0.45)'; g.fillRect(0, 0, W, H);
      digitBoard(t, { dx: -230 });
      const k = pop(t, tIf + 0.1);
      const bx = W / 2 + 470, by = H / 2 - 120;
      g.save(); g.translate(bx, by); g.scale(k, k);
      g.fillStyle = '#14102a'; g.fillRect(-56, -56, 112, 112); g.fillStyle = '#f4e6c4'; g.fillRect(-48, -48, 96, 96); g.restore();
      text('= 1', bx + 140, by + 4, { size: 44, color: Y, scale: k });
      g.save(); g.translate(bx, by + 170); g.scale(k, k); g.fillStyle = '#14102a'; g.fillRect(-56, -56, 112, 112); g.fillStyle = '#2a2840'; g.fillRect(-48, -48, 96, 96); g.strokeStyle = '#6a62a0'; g.lineWidth = 4; g.strokeRect(-48, -48, 96, 96); g.restore();
      text('= 0', bx + 140, by + 174, { size: 44, color: '#b9b2d8', scale: k });
      const pk = pop(t, c('05', 'pause'));
      if (t > c('05', 'pause') && Math.floor(t * 2) % 2 === 0) { g.save(); g.translate(bx + 40, by + 380); g.scale(pk, pk); g.fillStyle = '#14102a'; g.fillRect(-46, -54, 36, 108); g.fillRect(10, -54, 36, 108); g.fillStyle = WH; g.fillRect(-40, -48, 24, 96); g.fillRect(16, -48, 24, 96); g.restore(); }
      if (t > c('05', 'pause')) text('PAUSE', bx + 40, by + 470, { size: 36, scale: pk });
    } });
    fx('whoosh', tIf - 0.1, 0.5); fx('pop', tIf + 0.1, 0.6); fx('pop', c('05', 'pause'), 0.9);

    // ================= 06 REVEAL =================
    const t06 = start('06') - 0.1, tRead = c('06', 'read'), tIts = c('06', "it's"), tHat = c('06', 'hat'), tSmile = c('06', 'smile');
    add({ scene: 'stage', t0: t06, act(t, S) {
      stageReset(S, t); S.O.phone.visible = false; aim(S.cam, v3(0, 66, 220), v3(0, 22, 0));
    }, overlay(t, g) {
      g.fillStyle = 'rgba(10,6,24,0.45)'; g.fillRect(0, 0, W, H);
      digitBoard(t, { reveal: (r, cc) => K(t, tRead + (r + cc) * 0.05, tRead + (r + cc) * 0.05 + 0.3) });
    } });
    for (let k = 0; k < 15; k++) fx('tile', tRead + k * 0.05, 0.3); fx('chime', tRead + 0.75, 0.8);
    add({ scene: 'canyon', t0: tIts, trans: 0.4, act(t, S) {
      canyonReset(S, t); paint(S.O.wall8, F8, 8, 8, () => 1);
      pose(S.O.friend, t + 1.3, { cheer: smooth(K(t, tIts, tIts + 0.3)) * (1 - K(t, tIts + 1.2, tIts + 1.5)) });
      cm(S, t, tIts, end('06') + 0.4, v3(58, 52, 118), v3(112, 50, -20), ...CAM.wall, smooth);
    }, overlay(t, g, S) {
      const box = (i0, i1, tt, label) => { if (t < tt) return; const a = project(S.cam, cellWorld(S.O.wall8, 8, 8, i0)), b = project(S.cam, cellWorld(S.O.wall8, 8, 8, i1)); const k = pop(t, tt); const pad = 34; g.save(); g.strokeStyle = Y; g.lineWidth = 7; g.globalAlpha = Math.min(1, k); g.strokeRect(Math.min(a[0], b[0]) - pad, a[1] - pad, Math.abs(b[0] - a[0]) + pad * 2, b[1] - a[1] + pad * 2); g.restore(); tag(label, Math.max(a[0], b[0]) + 150, (a[1] + b[1]) / 2, { scale: k, size: 30 }); };
      box(0, 15, tHat, 'HAT'); box(41, 54, tSmile, 'SMILE');
    } });
    fx('whoosh', tIts - 0.1, 0.4); fx('pop', tHat, 0.8); fx('pop', tSmile, 0.8);

    // ================= 07 WIDTH =================
    const t07 = start('07') - 0.1, tEnds = c('07', 'ends'), tFour = c('07', 'four'), tThis = c('07', 'this'), tSo7 = c('07', 'so'), tWide2 = c('07', 'wide', 2), tTall = c('07', 'tall');
    add({ scene: 'canyon', t0: t07, act(t, S) {
      canyonReset(S, t);
      const bad = t > tThis - 0.1 && t < tSo7 + 0.2;
      if (bad) paint(S.O.wall8, F8, 4, 16, (i) => K(t, tThis - 0.1 + i * 0.012, tThis + i * 0.012 + 0.15));
      else paint(S.O.wall8, F8, 8, 8, (i) => (t > tSo7 ? K(t, tSo7 + 0.2 + i * 0.008, tSo7 + 0.35 + i * 0.008) : 1));
      pose(S.O.friend, t + 1.3, { tilt: bad ? 0.25 : 0, think: bad ? 0.7 : 0 });
      cm(S, t, t07, end('07'), ...CAM.wall, v3(66, 60, 128), v3(118, 52, -20), smooth);
    }, overlay(t, g, S) {
      if (t > tEnds - 0.2 && t < tFour) { const k = pop(t, tEnds - 0.2); for (let r = 0; r < 8; r++) { const [x, y] = project(S.cam, cellWorld(S.O.wall8, 8, 8, r * 8 + 7)); text('|', x + 46, y, { size: 40, color: Y, scale: k }); } tag('WHERE DOES A ROW END?', W / 2, 120, { size: 30, scale: k }); }
      if (t > tFour && t < tSo7) text([['4 WIDE?', R]], W / 2, 120, { size: 52, scale: pop(t, tFour) });
      if (t > tThis + 0.4 && t < tSo7) { const [x, y] = project(S.cam, S.O.wall8.userData.center.clone().applyMatrix4(S.O.wall8.matrixWorld)); const k = pop(t, tThis + 0.4); g.save(); g.translate(x, y); g.scale(k, k); g.lineCap = 'square'; g.strokeStyle = '#14102a'; g.lineWidth = 46; g.beginPath(); g.moveTo(-120, -120); g.lineTo(120, 120); g.moveTo(120, -120); g.lineTo(-120, 120); g.stroke(); g.strokeStyle = R; g.lineWidth = 30; g.stroke(); g.restore(); const [fx2, fy] = headPos(S, S.O.friend, 34); bubble('?', fx2, fy, { scale: k, size: 52 }); }
      // header strip
      if (t > tSo7 + 0.3) {
        const k = pop(t, tSo7 + 0.3); const y = 975; const cells = ['8', '8', ...BITS.slice(0, 14).map(String), '...'];
        const cw = 64; const x0 = W / 2 - (cells.length * cw) / 2;
        cells.forEach((s, i) => { const x = x0 + i * cw + cw / 2; const hd = i < 2; const hk = hd ? pop(t, i === 0 ? tWide2 : tTall) : k;
          g.save(); g.translate(x, y); g.scale(k, k); g.fillStyle = '#0d0b1e'; g.fillRect(-30, -34, 60, 68); g.fillStyle = hd ? (t > (i === 0 ? tWide2 : tTall) ? '#f2c14e' : '#3a3260') : '#1d1640'; g.fillRect(-26, -30, 52, 60); g.restore();
          text(s, x, y + 2, { size: 26, color: hd ? '#14102a' : (s === '1' ? Y : '#b9b2d8'), scale: k, stroke: hd ? 0.1 : 6, shadow: 0 });
          if (hd && t > (i === 0 ? tWide2 : tTall)) tag(i === 0 ? 'WIDTH' : 'HEIGHT', x + (i === 0 ? -50 : 40), y - 76, { size: 22, scale: hk });
        });
      }
    } });
    fx('pop', tEnds - 0.2, 0.6); fx('pop', tFour, 0.7); for (let k = 0; k < 10; k++) fx('tile', tThis - 0.1 + k * 0.08, 0.25); fx('buzz', tThis + 0.4, 0.8); fx('whoosh', tSo7 + 0.2, 0.4); fx('pop', tSo7 + 0.3, 0.6); fx('pop', tWide2, 0.8); fx('pop', tTall, 0.8);

    // ================= 08 GRAY =================
    const t08 = start('08') - 0.1, tSo8 = c('08', 'so'), tCount8 = c('08', 'count'), tFive = c('08', 'five', 1), tZero2 = c('08', 'zero', 2), tWhite = c('08', 'white'), tEvery = c('08', 'every'), tGray = c('08', 'gray');
    add({ scene: 'canyon', t0: t08, act(t, S) {
      canyonReset(S, t); paint(S.O.wall8, F8, 8, 8, () => 1);
      cm(S, t, t08, tSo8, v3(66, 60, 128), v3(118, 52, -20), v3(72, 62, 150), v3(118, 52, -20), smooth);
    }, overlay(t) { text([['ONLY ', WH], ['2', R], [' COLORS...', WH]], W / 2, 130, { size: 50, scale: pop(t, t08 + 0.5) }); } });
    fx('pop', t08 + 0.5, 0.6);
    const cv = (t) => Math.round(255 * clamp((t - tCount8) / (tFive + 0.3 - tCount8)) ** 1.6);
    add({ scene: 'canyon', t0: tSo8, trans: 0.4, act(t, S) {
      canyonReset(S, t);
      const v = t < tCount8 ? 0b10110100 : cv(t); S.O.lamps.userData.set(t < c('08', 'eight') ? 0 : v);
      pose(S.O.bob, t, { point: 0.8 });
      cm(S, t, tSo8, tZero2, ...CAM.lamps, v3(-64, 46, 120), v3(-112, 34, -16), smooth);
    }, overlay(t, g, S) {
      const te = c('08', 'eight'); if (t < te) return;
      const v = t < tCount8 ? 0b10110100 : cv(t);
      lampDigits(S, [...v.toString(2).padStart(8, '0')].map(Number), 1, 24);
      const [x, y] = project(S.cam, S.O.lamps.getWorldPosition(v3(0, 0, 0)).add(v3(0, 4, 0)));
      const k = pop(t, te);
      g.save(); g.translate(x - 120, y + 120); g.scale(k, k); g.fillStyle = '#14102a'; g.fillRect(-64, -64, 128, 128); g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(-56, -56, 112, 112); g.restore();
      tag(String(v), x + 60, y + 120, { size: 48, scale: k });
    } });
    fx('whoosh', tSo8 - 0.1, 0.4); fx('lamp', c('08', 'eight'), 0.7); fx('count', tCount8, 0.7, { dur: tFive + 0.3 - tCount8 });
    add({ scene: 'stage', t0: tZero2 - 0.15, trans: 0.35, act(t, S) {
      stageReset(S, t); S.O.phone.visible = false;
      const vals = [0, 32, 64, 96, 128, 160, 192, 224, 255];
      const at = (i) => (i === 0 ? tZero2 : i === 8 ? tWhite : lerp(tEvery, tGray, (i - 1) / 7));
      S.setBlocks(vals.map((v, i) => ({ x: (i - 4) * 16.5, y: 0, z: 36, c: gray(v), s: 0.85 * backOut(K(t, at(i), at(i) + 0.35)) })));
      cm(S, t, tZero2 - 0.15, end('08') + 0.5, v3(0, 52, 210), v3(0, 10, 36), v3(0, 46, 190), v3(0, 10, 36), smooth);
    }, overlay(t, g, S) {
      const vals = [0, 32, 64, 96, 128, 160, 192, 224, 255];
      const at = (i) => (i === 0 ? tZero2 : i === 8 ? tWhite : lerp(tEvery, tGray, (i - 1) / 7));
      vals.forEach((v, i) => { if (t < at(i)) return; const [x, y] = project(S.cam, v3((i - 4) * 16.5, 18, 36)); text(String(v), x, y - 50, { size: i === 0 || i === 8 ? 36 : 26, color: i === 0 || i === 8 ? Y : WH, scale: pop(t, at(i)) }); });
      if (t > tZero2) tag('BLACK', project(S.cam, v3(-66, 0, 40))[0], 860, { scale: pop(t, tZero2), size: 26 });
      if (t > tWhite) tag('WHITE', project(S.cam, v3(66, 0, 40))[0], 860, { scale: pop(t, tWhite), size: 26 });
      if (t > tGray) text('SHADES OF GRAY', W / 2, 180, { size: 50, scale: pop(t, tGray) });
      vignette(0.35);
    } });
    for (let i = 0; i < 9; i++) fx('block', i === 0 ? tZero2 : i === 8 ? tWhite : lerp(tEvery, tGray, (i - 1) / 7), 0.45);
    fx('pop', tGray, 0.6);

    // ================= 09 RGB =================
    const t09 = start('09') - 0.2, tThree = c('09', 'three'), tR1 = c('09', 'red'), tG1 = c('09', 'green'), tB1 = c('09', 'blue'), tY1 = c('09', 'yellow'), tWhen = c('09', 'when'), tY2 = c('09', 'yellow', 2), tTurn = c('09', 'turn', 2), tWhite9 = c('09', 'white'), tOff = c('09', 'off'), tBlack = c('09', 'black');
    const lv9 = (t) => {
      if (t < tR1) return [0, 0, 0];
      if (t < tY1) return [1, t > tG1 ? 1 : 0, t > tB1 ? 1 : 0];
      if (t < tWhen) return [0.15, 0.15, 0.15];
      if (t < c('09', 'all')) return [t > tWhen + 0.3 ? 1 : 0, t > c('09', 'green', 2) ? 1 : 0, 0];
      if (t < tOff) return [1, 1, 1];
      return [0, 0, 0];
    };
    add({ scene: 'stage', t0: t09, trans: 0.4, act(t, S) {
      stageReset(S, t); S.O.phone.visible = false;
      const split = K(t, tThree, tThree + 0.4);
      S.setBlocks([{ x: 0, y: 6, c: 0xf6f6ff, s: split < 1 ? 2.6 * (1 - split) : 0 }]);
      S.O.rgb.visible = split > 0; S.O.rgb.scale.setScalar(backOut(split)); S.setBars(lv9(t));
      cm(S, t, t09, tWhen, v3(-30, 50, 170), v3(0, 28, 0), v3(0, 44, 136), v3(0, 28, 0), smooth);
      if (t > tWhen) cm(S, t, tWhen, end('09'), v3(0, 44, 136), v3(0, 28, 0), v3(18, 42, 124), v3(0, 28, 0), smooth);
    }, overlay(t, g, S) {
      if (t < tThree) text('1 PIXEL', W / 2, 160, { size: 60, scale: pop(t, t09 + 0.4) });
      else text([['1 PIXEL = ', WH], ['3 LIGHTS', Y]], W / 2, 160, { size: 54, scale: pop(t, tThree) });
      [[tR1, 'R', R, -1], [tG1, 'G', G, 0], [tB1, 'B', B, 1]].forEach(([tt, s, col, k]) => { if (t > tt) { const [x, y] = project(S.cam, v3(k * 9, 6, 6)); text(s, x, y + 50, { size: 44, color: col, scale: pop(t, tt) }); } });
      if (t > tY1 && t < tWhen) { const k = pop(t, tY1); text('YELLOW LIGHT?', W / 2, 960, { size: 52, color: Y, scale: k }); if (t > tY1 + 0.5) { g.save(); g.strokeStyle = R; g.lineWidth = 12; g.globalAlpha = Math.min(1, pop(t, tY1 + 0.5)); g.beginPath(); g.moveTo(W / 2 - 360, 960); g.lineTo(W / 2 + 360, 960); g.stroke(); g.restore(); text('NOPE', W / 2 + 430, 950, { size: 36, color: R, scale: pop(t, tY1 + 0.5), rot: -0.15 }); } }
      // far-away swatch
      if (t > tWhen + 0.3) {
        const lv = lv9(t); const col = `rgb(${lv.map((v) => Math.round(v * 255)).join(',')})`; const k = pop(t, tWhen + 0.3);
        const x = W - 330, y = H / 2 - 30; g.save(); g.translate(x, y); g.scale(k, k); g.fillStyle = '#0d0b1e'; g.fillRect(-110, -110, 220, 220); g.fillStyle = col; g.fillRect(-98, -98, 196, 196); g.restore();
        text('FROM FAR AWAY', x, y - 150, { size: 22, scale: k });
        const lab = t < c('09', 'all') ? (t > tY2 ? 'YELLOW' : '') : t < tOff ? (t > tWhite9 ? 'WHITE' : '') : (t > tBlack ? 'BLACK' : '');
        if (lab) text(lab, x, y + 160, { size: 34, color: lab === 'YELLOW' ? Y : lab === 'WHITE' ? WH : '#9a92c8', scale: pop(t, lab === 'YELLOW' ? tY2 : lab === 'WHITE' ? tWhite9 : tBlack) });
        if (t > tY2 && t < c('09', 'all')) text([['R', R], [' + ', WH], ['G', G]], 330, H / 2 - 30, { size: 60, scale: pop(t, tY2) });
      }
      vignette(0.35);
    } });
    fx('whoosh', t09, 0.5); fx('pop', t09 + 0.4, 0.5); fx('split', tThree, 0.9); fx('lighton', tR1, 0.7); fx('lighton', tG1, 0.7); fx('lighton', tB1, 0.7); fx('pop', tY1, 0.6); fx('buzz', tY1 + 0.5, 0.5); fx('lightoff', tY1 - 0.05, 0.5);
    fx('lighton', tWhen + 0.3, 0.6); fx('lighton', c('09', 'green', 2), 0.6); fx('chime', tY2, 0.55); fx('lighton', c('09', 'all'), 0.7); fx('lightoff', tOff, 0.7);

    // ================= 10 THREE NUMBERS =================
    const t10 = start('10') - 0.2, tR10 = c('10', 'red'), tG10 = c('10', 'green'), tB10 = c('10', 'blue'), tShirt = c('10', "bob's");
    const lv10 = [255, 160, 0];
    add({ scene: 'stage', t0: t10, act(t, S) {
      stageReset(S, t); S.O.phone.visible = false; S.O.rgb.visible = true; S.O.rgb.scale.setScalar(1);
      S.setBars([t > tR10 ? 1 : 0.15, t > tG10 ? 160 / 255 : 0.15, t > tB10 ? 0 : 0.15]);
      aim(S.cam, v3(0, 44, 140), v3(0, 26, 0));
    }, overlay(t, g, S) {
      text([['ANY COLOR = ', WH], ['3 NUMBERS', Y]], W / 2, 160, { size: 52, scale: pop(t, t10 + 0.3) });
      [[tR10, lv10[0], R, -1], [tG10, lv10[1], G, 0], [tB10, lv10[2], B, 1]].forEach(([tt, v, col, k]) => { if (t > tt) { const [x, y] = project(S.cam, v3(k * 9, 6, 6)); tag(String(v), x, y + 60 + (k === 0 ? 56 : 0), { size: 24, color: col, scale: pop(t, tt) }); } });
      if (t > tB10 + 0.3) { const k = pop(t, tB10 + 0.3); const x = W - 330, y = H / 2 - 30; g.save(); g.translate(x, y); g.scale(k, k); g.fillStyle = '#0d0b1e'; g.fillRect(-110, -110, 220, 220); g.fillStyle = 'rgb(255,160,0)'; g.fillRect(-98, -98, 196, 196); g.restore(); text('ORANGE', x, y + 160, { size: 30, color: '#ffa000', scale: k }); }
      vignette(0.35);
    } });
    fx('pop', t10 + 0.3, 0.6); fx('lighton', tR10, 0.6); fx('lighton', tG10, 0.6); fx('lightoff', tB10, 0.4); fx('chime', tB10 + 0.3, 0.45);
    add({ scene: 'canyon', t0: tShirt - 0.1, trans: 0.4, act(t, S) {
      canyonReset(S, t);
      pose(S.O.bob, t, { lookY: -0.2 });
      cm(S, t, tShirt - 0.1, end('10') + 0.5, v3(-6, 30, 80), v3(-44, 20, 6), v3(-10, 27, 72), v3(-44, 18, 6), smooth);
    }, overlay(t, g, S) {
      const p = S.O.bob.getWorldPosition(v3(0, 0, 0)).add(v3(1, 10, 3)); const [x, y] = project(S.cam, p);
      const k = pop(t, tShirt + 0.2);
      g.save(); g.strokeStyle = WH; g.lineWidth = 8; g.globalAlpha = Math.min(1, k); g.beginPath(); g.arc(x, y, 40 * k, 0, 7); g.stroke(); g.strokeStyle = '#14102a'; g.lineWidth = 3; g.stroke(); g.beginPath(); g.moveTo(x + 30, y - 30); g.lineTo(x + 200, y - 170); g.strokeStyle = WH; g.lineWidth = 6; g.stroke(); g.restore();
      const bx = x + 470, by = y - 250;
      g.save(); g.translate(bx, by); g.scale(k, k); g.fillStyle = '#0d0b1e'; g.fillRect(-90, -90, 180, 180); g.fillStyle = 'rgb(40,100,200)'; g.fillRect(-80, -80, 160, 160); g.restore();
      [['forty', 'R 40', R], ['hundred', 'G 100', G], ['two', 'B 200', B]].forEach(([w, s, col], i) => { const tt = c('10', w, w === 'hundred' ? 1 : w === 'two' ? 1 : 1); if (t > tt) tag(s, bx + 230, by - 70 + i * 70, { size: 30, color: col, scale: pop(t, tt) }); });
    } });
    fx('whoosh', tShirt - 0.1, 0.4); fx('pick', tShirt + 0.2, 0.8); fx('pop', c('10', 'forty'), 0.6); fx('pop', c('10', 'hundred'), 0.6); fx('pop', c('10', 'two'), 0.6);

    // ================= 11 + montage + 12 =================
    const t11 = start('11') - 0.2, tTall11 = c('11', 'tall'), tThree11 = c('11', 'three'), tSeven = c('11', 'seven'), tWhile = c('11', 'while'), tM0 = end('11') + 0.1, tM1 = start('12') - 0.2;
    const montageK = (t) => K(t, tWhile, tM1);
    const F16 = () => f16();
    add({ scene: 'canyon', t0: t11, trans: 0.4, act(t, S) {
      const dk = 0.85 * smooth(K(t, tWhile, tM1));
      canyonReset(S, t, { dusk: dk, w16: true });
      const mk = montageK(t);
      if (mk > 0) { const n = Math.floor((t - tWhile) * 14); const i = Math.min(255, Math.floor(mk * 256)); const c0 = F16()[i]; S.O.lamps.userData.set(((c0 >> ((n % 3) * 8)) & 255) ^ (n * 37 & 0)); }
      paint(S.O.wall16, F16(), 16, 16, (i) => K(mk * 256 - i, 0, 2.5));
      pose(S.O.bob, t, mk > 0 ? { point: 0.8 } : {});
      pose(S.O.friend, t + 1.3, mk > 0 ? { point: 0.6 + Math.sin(t * 9) * 0.1 } : {});
      if (t < tWhile) cm(S, t, t11, tWhile, v3(-20, 76, 330), v3(-10, 32, -10), ...CAM.wide, smooth);
      else cm(S, t, tWhile, tM1, ...CAM.wide, v3(40, 62, 230), v3(60, 40, -14), smooth);
    }, overlay(t, g, S) {
      const k1 = pop(t, tTall11), k2 = pop(t, tThree11), k3 = pop(t, tSeven); const fade = 1 - K(t, tWhile + 0.4, tWhile + 0.8);
      if (t > tTall11 && fade > 0) text([['16 x 16', WH], t > tThree11 ? [' x 3', Y] : ['', WH]], W / 2, 140, { size: 60, scale: k1, alpha: fade });
      if (t > tSeven && fade > 0) text([['= ', WH], ['768', G], [' NUMBERS', WH]], W / 2, 240, { size: 52, scale: k3, alpha: fade });
      const mk = montageK(t);
      if (mk > 0) { const n = Math.min(768, Math.floor(mk * 768)); tag(`SENT: ${n} / 768`, 330, 90, { size: 30, scale: pop(t, tWhile + 0.3) }); }
    } });
    fx('pop', tTall11, 0.7); fx('pop', tThree11, 0.6); fx('pop', tSeven, 0.8);
    fx('flicker', tWhile, 0.4, { dur: tM1 - tWhile }); fx('paintloop', tWhile + 0.2, 0.35, { dur: tM1 - tWhile - 0.2 });

    const t12 = tM1, tLucky = c('12', 'lucky'), tSq12 = c('12', 'squares');
    add({ scene: 'canyon', t0: t12, act(t, S) {
      canyonReset(S, t, { dusk: 0.85, w16: true }); paint(S.O.wall16, F16(), 16, 16, () => 1);
      pose(S.O.friend, t + 1.3, { cheer: smooth(K(t, t12 + 0.2, t12 + 0.5)) });
      cm(S, t, t12, tLucky, v3(70, 56, 112), v3(118, 50, -20), ...CAM.wall, smooth);
    }, overlay() {} });
    fx('chime', t12 + 0.1, 0.9); fx('whoosh', t12 - 0.05, 0.4);
    add({ scene: 'canyon', t0: tLucky, act(t, S) {
      canyonReset(S, t, { dusk: 0.85, w16: true }); paint(S.O.wall16, F16(), 16, 16, () => 1);
      pose(S.O.bob, t, { wave: smooth(K(t, tSq12, tSq12 + 0.3)), lookY: -0.4 });
      cm(S, t, tLucky, end('12') + 0.7, v3(-14, 24, 54), v3(-62, 22, 18), v3(-18, 22, 50), v3(-62, 22, 18), smooth);
    }, overlay(t, g) {
      if (t > tSq12) {
        // the received picture as an inset next to Bob's real face
        const k = pop(t, tSq12 - 0.1); const f = F16(); const s = 16; const x0 = W - 520, y0 = 230;
        g.save(); g.translate(x0 + 128, y0 + 128); g.scale(k, k); g.translate(-128, -128); g.fillStyle = '#0d0b1e'; g.fillRect(-12, -12, 280, 280);
        f.forEach((c0, i) => { g.fillStyle = '#' + c0.toString(16).padStart(6, '0'); g.fillRect((i % 16) * s, Math.floor(i / 16) * s, s - 1, s - 1); }); g.restore();
        tag('RECEIVED', x0 + 128, y0 - 50, { size: 24, scale: k });
      }
    } });
    fx('whoosh', tLucky - 0.1, 0.3); fx('pop', tSq12 - 0.1, 0.7);

    // ================= 13 YOUR PHONE =================
    const t13 = start('13') - 0.2, tSq13 = c('13', 'squares'), tNormal = c('13', 'normal'), tTwelve = c('13', 'twelve'), tThree13 = c('13', 'three'), tThirty = c('13', 'thirty'), tLunch = c('13', 'lunch'), tAnd13 = c('13', 'and', 1), tSixty = c('13', 'sixty');
    add({ scene: 'stage', t0: t13, trans: 0.45, act(t, S) {
      stageReset(S, t);
      if (t < tLunch - 0.05) S.screen(photo());
      else S.screen(lunch(), t > tAnd13 ? (x) => { const ph = ((t - tAnd13) * 1.4) % 1; const yy = ph * 460; const gr = x.createLinearGradient(0, yy - 60, 0, yy); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(1, 'rgba(255,255,255,0.75)'); x.fillStyle = gr; x.fillRect(0, yy - 60, 240, 60); } : null);
      const gk = K(t, tSq13 - 0.3, tSq13) * (1 - K(t, tNormal, tNormal + 0.6));
      S.O.tiles.visible = gk > 0.01; S.O.phone.userData.screen.visible = gk <= 0.01;
      if (gk > 0.01) S.setTiles(photoTiles(), () => ({ s: 1 - 0.3 * gk, z: 0, d: 0.4 }));
      cm(S, t, t13, end('13') + 0.5, v3(-36, 48, 150), SCR.clone(), v3(30, 44, 120), SCR.clone(), smooth);
    }, overlay(t, g) {
      const x = 420;
      if (t > tTwelve) text([['12,000,000', G]], x, 360, { size: 50, scale: pop(t, tTwelve) });
      if (t > tTwelve) text('PIXELS', x, 430, { size: 30, scale: pop(t, tTwelve + 0.1) });
      if (t > tThree13) text([['x 3', Y]], x, 530, { size: 50, scale: pop(t, tThree13) });
      if (t > tThirty) { text([['36,000,000', G]], x, 640, { size: 50, scale: pop(t, tThirty) }); text('NUMBERS', x, 710, { size: 30, scale: pop(t, tThirty + 0.1) }); }
      if (t > tLunch) tag('(YOUR LUNCH)', W - 420, 300, { size: 28, scale: pop(t, tLunch), color: WH });
      if (t > tSixty) text([['60', Y], [' TIMES', WH]], W - 420, 760, { size: 50, scale: pop(t, tSixty) });
      if (t > tSixty) text('EVERY SECOND', W - 420, 830, { size: 28, scale: pop(t, tSixty + 0.1) });
      vignette(0.35);
    } });
    fx('whoosh', t13, 0.5); fx('shatter', tSq13 - 0.3, 0.4); fx('pop', tTwelve, 0.7); fx('pop', tThree13, 0.6); fx('pop', tThirty, 0.8); fx('boop', tLunch, 0.8); fx('pop', tSixty, 0.7);
    { for (let k = 0; k < 8; k++) fx('scan', tAnd13 + k / 1.4, 0.18); }

    // ================= 14 CLOSE =================
    const t14 = start('14') - 0.2, tList = c('14', 'list'), tWidth = c('14', 'width'), tHeight = c('14', 'height'), tYour14 = c('14', 'your'), tThats14 = c('14', "that's");
    add({ scene: 'stage', t0: t14, trans: 0.45, act(t, S) {
      stageReset(S, t);
      const sub = t > tYour14 + 0.2 && t < tThats14 + 0.15;
      S.screen(gal(), (x) => { const [X, Yy, s] = gal().userData.screenshots[1]; const k = K(t, t14 + 0.4, t14 + 0.7); if (k > 0) { x.lineWidth = 6; x.strokeStyle = `rgba(255,210,63,${k})`; x.strokeRect(X + 3, Yy + 3, s - 6, s - 6); } });
      S.O.sub.visible = sub; S.O.phone.userData.screen.visible = !sub;
      if (sub) S.setSub(galTiles(), 1.3);
      if (t < tYour14) cm(S, t, t14, tYour14, v3(-30, 46, 150), SCR.clone(), v3(-10, 40, 110), SCR.clone(), smooth);
      else if (t < tThats14) cm(S, t, tYour14, tYour14 + 1.4, v3(-10, 40, 110), SCR.clone(), v3(-2, 37, 13), v3(0, 37, 0));
      else cm(S, t, tThats14, end('14') + 0.4, v3(-2, 37, 13), v3(0, 37, 0), v3(0, 46, 150), SCR.clone(), easeOut);
    }, overlay(t, g) {
      if (t > tList && t < tYour14 + 0.3) {
        const k = pop(t, tList) * (1 - K(t, tYour14, tYour14 + 0.3)); const cells = ['1080', '2400', '255', '255', '255', '31', '41', '59', '255', '...'];
        let x = W / 2 - 700; const y = 975;
        cells.forEach((s, i) => { const w = s.length * 26 + 40; const hd = i < 2; const lit = hd && t > (i === 0 ? tWidth : tHeight);
          g.save(); g.globalAlpha = Math.min(1, k); g.fillStyle = '#0d0b1e'; g.fillRect(x - 4, y - 38, w + 8, 76); g.fillStyle = lit ? '#f2c14e' : '#1d1640'; g.fillRect(x, y - 34, w, 68); g.restore();
          text(s, x + w / 2, y + 2, { size: 26, color: lit ? '#14102a' : WH, scale: Math.min(1, k), stroke: lit ? 0.1 : 6, shadow: 0 });
          if (lit) tag(i === 0 ? 'WIDTH' : 'HEIGHT', x + w / 2, y - 80, { size: 22, scale: pop(t, i === 0 ? tWidth : tHeight) });
          x += w + 14; });
      }
      if (t > tThats14) text([["THAT'S A PICTURE.", WH]], W / 2, 960, { size: 50, scale: pop(t, tThats14 + 0.1) });
      vignette(0.35);
    } });
    fx('whoosh', t14, 0.5); fx('pop', t14 + 0.4, 0.5); fx('pop', tList, 0.6); fx('pop', tWidth, 0.7); fx('pop', tHeight, 0.7); fx('zoom', tYour14, 0.7); fx('lighton', tYour14 + 0.6, 0.5); fx('zoomout', tThats14, 0.7);

    // ================= 15 MAP OUTRO + END HOLD =================
    const t15 = start('15') - 0.3, tPlant = c('15', 'plants'), tDesert = c('15', "desert's"), tAhead = c('15', 'ahead'), tSmoking = c('15', 'smoking');
    add({ scene: 'map', t0: t15, trans: 0.6, act(t, S) {
      const O = S.O; O.bob.visible = true; const p = S.wpPos(5); O.bob.position.copy(p).add(v3(-6, 0, 3)); O.bob.rotation.y = 0.5;
      const pk = K(t, tPlant + 0.1, tPlant + 0.5); O.newFlag.scale.setScalar(Math.max(0.0001, 0.55 * backOut(pk)));
      pose(O.bob, t, t > tPlant + 0.5 && t < tPlant + 2 ? { cheer: smooth(K(t, tPlant + 0.5, tPlant + 0.8)) * (1 - K(t, tPlant + 1.6, tPlant + 2)) } : { point: pk < 1 ? smooth(K(t, tPlant - 0.2, tPlant + 0.1)) * 0.8 : 0, lookY: t > tAhead ? 1.2 * smooth(K(t, tAhead, tAhead + 0.6)) : 0 });
      const w5 = S.wpPos(5);
      const c1 = [w5.clone().add(v3(-10, 70, 80)), w5.clone().add(v3(0, 8, 0))];
      const c2 = [v3(140, 230, 390), v3(140, 0, 220)];
      const c3 = [v3(250, 250, 390), v3(250, 20, 200)];
      const c4 = [v3(240, 300, 430), v3(250, 20, 190)];
      if (t < tDesert) cm(S, t, t15, tDesert, c1[0].clone().add(v3(0, 10, 20)), c1[1], c1[0], c1[1], smooth);
      else if (t < tAhead) cm(S, t, tDesert, tAhead, c1[0], c1[1], c2[0], c2[1]);
      else if (t < end('15') + 1) cm(S, t, tAhead, end('15') + 1, c2[0], c2[1], c3[0], c3[1]);
      else cm(S, t, end('15') + 1, duration, c3[0], c3[1], c4[0], c4[1], (x) => x);
    }, overlay(t, g, S) {
      if (t > tPlant + 0.3 && t < tAhead) { const [x, y] = project(S.cam, S.wpPos(5).add(v3(3, 22, -2))); tag('STOP 5 CLEARED', x, y - 70, { size: 28, scale: pop(t, tPlant + 0.4) }); }
      if (t > tSmoking) { const k = pop(t, tSmoking); const [x, y] = project(S.cam, v3(240, 70, 225)); text('NEXT STOP', x, y - 90, { size: 40, scale: k }); text('???', x, y - 20, { size: 64, color: Y, scale: pop(t, tSmoking + 0.2) }); }
      vignette(0.3);
      const fo = K(t, duration - 1.2, duration); if (fo > 0) { g.fillStyle = `rgba(0,0,0,${fo})`; g.fillRect(0, 0, W, H); }
    } });
    fx('whoosh', t15, 0.6); fx('flag', tPlant + 0.1, 1.0); fx('chime', tPlant + 0.4, 0.6); fx('whoosh', tAhead, 0.4); fx('rumble', tSmoking - 0.6, 0.6); fx('pop', tSmoking, 0.6);

    // ambience beds by scene
    const beds = [];
    sh.slice().sort((a, b) => a.t0 - b.t0).forEach((s, i, arr) => { const t1 = i < arr.length - 1 ? arr[i + 1].t0 : duration; beds.push({ scene: s.scene, t0: s.t0, t1 }); });
    beds.forEach((b) => fx(b.scene === 'stage' ? 'bed_stage' : b.scene === 'map' ? 'bed_map' : 'bed_canyon', b.t0, 1, { dur: b.t1 - b.t0 }));
    return sh;
  },
};
