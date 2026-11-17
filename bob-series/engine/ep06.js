// Episode 6 — "How Numbers Became Sound". Shot list, overlays and sound cues anchored to voice words.
import * as THREE from 'three';
import { W, H, clamp, lerp, ease, easeOut, smooth, backOut, pop, v3, aim, project, text, bubble, tag, vignette, setSky, g2, Y, G, R, B, WH } from './core.js';
import { pose } from './models.js';
import { face16, photoCanvas } from './pics.js';

const K = (t, a, b) => clamp((t - a) / (b - a));
function cm(S, t, a, b, P0, L0, P1, L1, e = ease) { const k = e(K(t, a, b)); aim(S.cam, P0.clone().lerp(P1, k), L0.clone().lerp(L1, k)); }
const TAU = Math.PI * 2;

// Bob's "voice" wave on 0..1
const env = (u) => 0.3 + 0.7 * Math.abs(Math.sin(Math.PI * 2.6 * u + 0.4)) * (0.75 + 0.25 * Math.sin(TAU * 1.3 * u));
const voice = (u) => env(u) * (0.62 * Math.sin(TAU * 6 * u) + 0.26 * Math.sin(TAU * 15 * u + 1) + 0.12 * Math.sin(TAU * 29 * u + 2));
const sampleVal = (u) => Math.round(128 + 118 * voice(u));

// ---------- graph board drawing ----------
// o: {wave:0..1 drawn, waves:[...], n: samples, show: 0..1 fraction of stems, recon:0..1 staircase alpha, quant: levels, compare:'loud'|'high', hl: index}
function drawBoard(S, o) {
  S.boardDraw((x, w, h) => {
    x.fillStyle = '#141024'; x.fillRect(0, 0, w, h);
    x.strokeStyle = 'rgba(140,120,220,0.18)'; x.lineWidth = 2;
    for (let gx = 0; gx <= w; gx += 75) { x.beginPath(); x.moveTo(gx, 0); x.lineTo(gx, h); x.stroke(); }
    for (let gy = 0; gy <= h; gy += 70) { x.beginPath(); x.moveTo(0, gy); x.lineTo(w, gy); x.stroke(); }
    const m = 60, X = (u) => m + u * (w - 2 * m), mid = h / 2, A = 250, Yv = (v) => mid - v * A;
    x.strokeStyle = 'rgba(255,255,255,0.35)'; x.lineWidth = 3; x.beginPath(); x.moveTo(m, mid); x.lineTo(w - m, mid); x.stroke();
    const line = (f, upto, col, lw, from = 0) => { x.strokeStyle = col; x.lineWidth = lw; x.lineJoin = 'round'; x.beginPath(); for (let i = 0; i <= 600; i++) { const u = from + (upto - from) * i / 600; const yy = Yv(f(u)); if (!i) x.moveTo(X(u), yy); else x.lineTo(X(u), yy); } x.stroke(); };
    if (o.compare) {
      const half = (w - 2 * m) / 2; const fa = o.compare === 'loud' ? [(u) => 0.25 * Math.sin(TAU * 4 * u), (u) => 0.85 * Math.sin(TAU * 4 * u)] : [(u) => 0.6 * Math.sin(TAU * 2 * u), (u) => 0.6 * Math.sin(TAU * 9 * u)];
      [0, 1].forEach((k) => { x.save(); x.beginPath(); x.rect(m + k * half + 10, 0, half - 20, h); x.clip(); x.strokeStyle = k ? '#ffd23f' : '#5fd0ff'; x.lineWidth = 9; x.beginPath(); for (let i = 0; i <= 300; i++) { const u = i / 300; const px = m + k * half + 20 + u * (half - 40); const py = mid - fa[k](u) * A; if (!i) x.moveTo(px, py); else x.lineTo(px, py); } x.stroke(); x.restore(); });
      x.strokeStyle = 'rgba(255,255,255,0.5)'; x.lineWidth = 4; x.beginPath(); x.moveTo(w / 2, 20); x.lineTo(w / 2, h - 20); x.stroke();
      return;
    }
    if (o.wave > 0) line(voice, o.wave, o.waveCol || '#ffd23f', o.waveW || 8);
    const n = o.n || 0;
    if (n && o.show > 0) {
      const shown = Math.floor(n * o.show + 1e-6);
      for (let i = 0; i < shown; i++) {
        const u = (i + 0.5) / n; let v = voice(u); if (o.quant) v = Math.round(v * o.quant) / o.quant;
        x.strokeStyle = i === o.hl ? '#ffffff' : '#4ff07a'; x.lineWidth = n > 40 ? 4 : 7; x.beginPath(); x.moveTo(X(u), mid); x.lineTo(X(u), Yv(v)); x.stroke();
        x.fillStyle = i === o.hl ? '#ffffff' : '#4ff07a'; const r = n > 40 ? 6 : 12; x.fillRect(X(u) - r, Yv(v) - r, 2 * r, 2 * r);
      }
    }
    if (o.recon > 0 && n) {
      x.globalAlpha = o.recon; x.strokeStyle = o.reconCol || '#ff4a4a'; x.lineWidth = 8; x.beginPath();
      for (let i = 0; i < n; i++) { let v = voice((i + 0.5) / n); if (o.quant) v = Math.round(v * o.quant) / o.quant; const x0 = X(i / n), x1 = X((i + 1) / n); if (!i) x.moveTo(x0, Yv(v)); else x.lineTo(x0, Yv(v)); x.lineTo(x1, Yv(v)); }
      x.stroke(); x.globalAlpha = 1;
    }
  });
}
const stemWorld = (S, n, i) => { const u = (i + 0.5) / n, v = voice(u); return S.boardToWorld((60 + u * 1380) / 1500, (350 - v * 250) / 700); };

// speaker cone driven by the narrator: vibrates only while a word is being spoken
function talking(words, t) { for (const w of words) if (t >= w.s - 0.02 && t <= w.e + 0.02) return 1; return 0; }

function stageReset(S) {
  const O = S.O; O.phone.visible = false; O.tiles.visible = false; O.sub.visible = false; O.rgb.visible = false; S.setBlocks([]);
  O.board.visible = false; O.air.visible = false; O.spk.visible = false; O.lamps16.visible = false;
  O.ped.visible = true; O.phone.position.set(0, 6, 0); O.phone.rotation.set(0, 0, 0);
  if (S.O.listener) S.O.listener.visible = false;
}
function canyonReset(S, o = {}) {
  const O = S.O; S.scene.background = setSky(o.dusk ?? 0); const dk = o.dusk ?? 0;
  S.L.sun.color.setRGB(1, lerp(0.94, 0.66, dk), lerp(0.85, 0.48, dk)); S.L.sun.intensity = lerp(2.5, 2.0, dk);
  S.L.hemi.intensity = lerp(1.35, 1.0, dk); S.L.hemi.color.setRGB(lerp(0.81, 0.85, dk), lerp(0.9, 0.62, dk), lerp(1, 0.75, dk));
  O.wall8.visible = false; O.wall16.visible = true; O.horn.visible = true; O.speaker.visible = true;
  const T = O.wall16.userData.tiles.userData; T.layout(16, 16); const f = face16(); for (let i = 0; i < 256; i++) T.set(i, f[i], 1, 0);
  O.lamps.userData.set(0); O.speaker.userData.push(0);
  if (S.cam.fov !== 32) { S.cam.fov = 32; S.cam.updateProjectionMatrix(); }
}
const SCR = v3(0, 32.5, 0);

export const EPISODE = {
  gaps: { pre: 0.5, default: 0.45, after: { '01': 0.7, '02': 0.35, '03': 0.5, '06': 0.5, '07': 0.6, '08': (al) => demoLen(al) + 1.3, '09': (al) => demoLen(al) + 1.3, '10': 0.5, '12': 0.8 }, endHold: 13 },
  shots({ cue: c, start, end, fx, duration, CH }) {
    const sh = []; const add = (o) => { sh.push(o); return o; };
    const wordsOf = (id) => CH[id].words.map((w) => ({ s: CH[id].t0 + w.s, e: CH[id].t0 + w.e, w: w.w }));
    // the demo line: first sentence of the video
    const w01 = CH['01'].words; const demoA = Math.max(0, w01[0].s - 0.08), demoB = w01[5].e + 0.25;

    // ================= 01 HOOK: speaker pumping with the narrator =================
    const t01 = 0, w1 = wordsOf('01');
    add({ scene: 'stage', t0: t01, act(t, S) {
      stageReset(S); const O = S.O; O.spk.visible = true; O.spk.position.set(0, 6, 0); O.spk.rotation.set(0, 0, 0);
      const tk = talking(w1, t); O.spk.userData.push(tk * Math.sin(t * 70) * 0.9 + tk * Math.sin(t * 23) * 0.5);
      cm(S, t, 0, end('01') + 0.5, v3(-24, 34, 120), v3(0, 18, 0), v3(14, 28, 82), v3(0, 18, 0), smooth);
    }, overlay(t, g, S) {
      // numbers streaming into the speaker
      const tn = c('01', 'numbers'); const k = K(t, 0.3, 1.0); const thin = K(t, c('01', 'enough') - 0.2, c('01', 'enough') + 0.5);
      if (k > 0) { g.save(); g.globalAlpha = k; for (let r = 0; r < 9; r++) { const y = 270 + r * 70; const off = ((t * 520 + r * 137) % 900); for (let j = 0; j < 4; j++) { if (thin > 0 && (r + j) % 3) continue; const x = -100 + off + j * 230 - 230; if (x < 0 || x > 760) continue; const v = sampleVal(((r * 31 + j * 7 + Math.floor(t * 9)) % 97) / 97); text(String(v), x, y, { size: 30, color: (r + j) % 2 ? Y : G, alpha: Math.min(1, (760 - x) / 120) }); } } g.restore(); }
      if (t > tn) text([['YOU ARE HEARING ', WH], ['NUMBERS', G]], W / 2, 120, { size: 52, scale: pop(t, tn) });
      const tf = c('01', 'forty'); if (t > tf) tag('40,000+ NUMBERS EVERY SECOND', W / 2, 960, { size: 30, scale: pop(t, tf) });
      vignette(0.4);
    } });
    fx('pop', c('01', 'numbers'), 0.7); fx('pop', c('01', 'forty'), 0.6); fx('zoom', 0.4, 0.3);

    // ================= 02 MAP =================
    const t02 = start('02') - 0.35, tLastStop = c('02', 'last'), tWords = c('02', 'words'), tPic = c('02', 'picture'), tAnd2 = c('02', 'and');
    add({ scene: 'map', t0: t02, trans: 0.5, act(t, S) {
      const O = S.O; O.bob.visible = true; O.newFlag.scale.setScalar(0.0001);
      const wk = K(t, t02 + 0.5, tLastStop + 1.5); const f = smooth(wk);
      const p = S.between(5, 6, f), p2 = S.between(5, 6, Math.min(1, f + 0.02)); O.bob.position.copy(p);
      O.bob.rotation.y = wk < 1 ? Math.atan2(p2.x - p.x, p2.z - p.z) : 0.3;
      pose(O.bob, t, wk > 0 && wk < 1 ? { walk: t * 11 } : {});
      const w6 = S.wpPos(6), w4 = S.wpPos(4), w5 = S.wpPos(5);
      const ov = [v3(248, 470, 520), v3(248, 0, 150)], near6 = [w6.clone().add(v3(-20, 120, 130)), w6.clone()];
      if (t < tWords) cm(S, t, t02 + 0.6, tLastStop + 0.8, ov[0], ov[1], near6[0], near6[1]);
      else cm(S, t, tWords, tAnd2, near6[0], near6[1], w4.clone().lerp(w5, 0.5).add(v3(10, 110, 120)), w4.clone().lerp(w5, 0.5));
    }, overlay(t, g, S) {
      const k = pop(t, t02 + 0.4) * (1 - K(t, tWords - 0.4, tWords));
      if (k > 0) { text([['STOP ', WH], ['6', Y]], W / 2, 150, { size: 84, scale: k }); if (t > tLastStop) tag('LAST STOP IN THE DESERT', W / 2, 250, { scale: pop(t, tLastStop), size: 32 }); }
      [[tWords, 4, 'TEXT'], [tPic, 5, 'PICTURES']].forEach(([tt, n, s]) => { if (t < tt) return; const [x, y] = project(S.cam, S.wpPos(n).add(v3(2, 22, 0))); tag(`STOP ${n}`, x, y - 100, { scale: pop(t, tt), size: 24, color: WH }); tag(s, x, y - 52, { scale: pop(t, tt + 0.08), size: 30 }); });
      vignette(0.3);
    } });
    fx('whoosh', t02, 0.7); fx('pop', t02 + 0.4, 0.8); fx('pop', tLastStop, 0.6); fx('flagpop', tWords, 0.6); fx('flagpop', tPic, 0.6);
    for (let k = 0; k < 8; k++) fx('step', t02 + 0.5 + k * ((tLastStop + 1 - t02) / 8), 0.4);

    add({ scene: 'canyon', t0: tAnd2, trans: 0.45, act(t, S) {
      canyonReset(S);
      cm(S, t, tAnd2, end('02') + 0.6, v3(-10, 70, 320), v3(0, 32, -10), v3(10, 62, 290), v3(10, 34, -10), smooth);
    }, overlay(t, g, S) { const th = c('02', 'hear') - 0.3; if (t > th) { const [x, y] = headPos(S, S.O.friend); bubble(['CAN I HEAR', 'YOUR VOICE?'], x, y - 8, { scale: pop(t, th), size: 34 }); } } });
    fx('whoosh', tAnd2 - 0.1, 0.4); fx('pop', c('02', 'hear') - 0.3, 0.7);

    // ================= 03 THE SHOUT =================
    const t03 = start('03') - 0.2, tShouts = c('03', 'shouts'), tBut3 = c('03', 'but'), tNothing = c('03', 'nothing'), tHes = c('03', "he's"), tWhat3 = c('03', 'what');
    add({ scene: 'canyon', t0: t03, act(t, S) {
      canyonReset(S);
      const sk = smooth(K(t, tShouts - 0.3, tShouts)) * (1 - K(t, tNothing, tNothing + 0.4));
      pose(S.O.bob, t, { cheer: sk * 0.55, nod: -0.25 * sk });
      if (t > tHes) { const n = Math.floor((t - tHes) * 5); S.O.lamps.userData.set([72, 69, 76, 76, 79, 33][n % 6]); }
      if (t < tHes) cm(S, t, t03, tHes, v3(-30, 66, 300), v3(-6, 30, -10), v3(0, 70, 320), v3(0, 32, -10), smooth);
      else cm(S, t, tHes, end('03') + 0.5, v3(-40, 52, 170), v3(-90, 28, -10), v3(-50, 48, 140), v3(-95, 30, -14), smooth);
    }, overlay(t, g, S) {
      if (t > tShouts && t < tNothing + 1.2) {
        const [bx, by] = headPos(S, S.O.bob, 36), [fx2, fy] = headPos(S, S.O.friend, 36);
        const p = K(t, tShouts + 0.1, tNothing); const x = lerp(bx + 60, fx2 - 60, p), y = lerp(by - 40, fy - 40, p) + Math.sin(t * 9) * 18 * p;
        const letters = 'HELLO!!!'; g.save();
        [...letters].forEach((ch, i) => { const a = clamp(1 - p * 1.25 + (i % 3) * 0.05); if (a <= 0) return; const drift = p * p * (i - 3.5) * 26; text(ch, x + (i - 3.5) * 46 * (1 - 0.6 * p) + drift, y + p * p * ((i * 37) % 5 - 2) * 30, { size: Math.max(14, 60 * (1 - 0.7 * p)), color: Y, alpha: a, rot: Math.sin(t * 6 + i) * 0.25 * p }); });
        g.restore();
      }
      if (t > tNothing) { const [x, y] = headPos(S, S.O.friend); bubble('?', x, y, { scale: pop(t, tNothing) * (t < tHes ? 1 : 0), size: 52 }); }
      if (t > c('03', 'numbers')) text([['VOICE ', WH], ['-> ', Y], ['NUMBERS?', G]], W / 2, 960, { size: 50, scale: pop(t, c('03', 'numbers')) });
    } });
    fx('gust', tShouts, 0.9); fx('pop', tNothing, 0.7); fx('flicker', tHes, 0.35, { dur: Math.max(0.5, end('03') - tHes) }); fx('pop', c('03', 'numbers'), 0.6);

    // ================= 04 WHAT SOUND IS =================
    const t04 = start('04') - 0.2, tShaking = c('04', 'shaking'), tBumps = c('04', 'bumps'), tEar = c('04', "someone's"), tBrain = c('04', 'brain'), w4w = wordsOf('04');
    add({ scene: 'stage', t0: t04, trans: 0.45, act(t, S) {
      stageReset(S); const O = S.O; O.ped.visible = false;
      O.spk.visible = true; O.spk.position.set(-62, 0, 10); O.spk.rotation.set(0, Math.PI / 2, 0);
      const on = K(t, tBumps - 0.6, tEar + 0.3); const amp = t > tShaking ? 1 : 0;
      O.air.visible = true; O.air.userData.update(t, 1.1 * amp, 0.55, 9, on);
      O.spk.userData.push(amp * Math.sin(9 * t) * 0.8);
      if (!O.listener) { O.listener = S.mkFriend(); }
      O.listener.visible = true; O.listener.position.set(74, 0, 18); O.listener.rotation.y = -Math.PI / 2;
      pose(O.listener, t, { tilt: Math.sin(t * 9) * 0.04 * on, cheer: t > tBrain ? smooth(K(t, tBrain, tBrain + 0.3)) * 0.6 : 0 });
      cm(S, t, t04, end('04') + 0.4, v3(-10, 60, 190), v3(10, 16, 10), v3(10, 52, 166), v3(10, 16, 10), smooth);
    }, overlay(t, g, S) {
      text([['SOUND = ', WH], ['SHAKING AIR', CYc]], W / 2, 140, { size: 56, scale: pop(t, tShaking) });
      if (t > tEar) { const p = project(S.cam, v3(70, 20, 18)); tag('EAR', p[0], p[1] - 160, { scale: pop(t, tEar), size: 28 }); }
      if (t > tBrain) { const p = project(S.cam, v3(74, 34, 18)); bubble('!', p[0], p[1] - 10, { scale: pop(t, tBrain), size: 50 }); }
      vignette(0.35);
    } });
    fx('whoosh', t04, 0.5); fx('pop', tShaking, 0.7); fx('hum', tShaking, 0.35, { dur: Math.max(1, end('04') - tShaking) }); fx('pop', tEar, 0.6); fx('pop', tBrain, 0.7);

    // ================= 05 HORN + NEEDLE =================
    const t05 = start('05') - 0.2, tHorn = c('05', 'horn'), tNeedle = c('05', 'needle'), tWiggly = c('05', 'wiggly'), tLoud = c('05', 'loud'), tHigh = c('05', 'high');
    add({ scene: 'canyon', t0: t05, trans: 0.45, act(t, S) {
      canyonReset(S); const hr = S.O.horn;
      // Bob stands at the horn's mouth
      hr.updateMatrixWorld(); const mouth = v3(-31, 0, 0).applyMatrix4(hr.matrixWorld); S.O.bob.position.set(mouth.x, 4, mouth.z); S.O.bob.rotation.y = 0.35 + Math.PI / 2;
      const talk = t > tHorn - 0.3; pose(S.O.bob, t, { nod: talk ? Math.sin(t * 14) * 0.05 : 0 });
      const drawP = K(t, tNeedle - 0.3, tWiggly + 0.5);
      hr.userData.needle.position.z = talk ? Math.sin(t * 40) * 1.4 * env((t * 0.3) % 1) : 0;
      hr.userData.draw((x, w, h) => { x.fillStyle = '#f2ead8'; x.fillRect(0, 0, w, h); x.strokeStyle = 'rgba(120,110,90,0.25)'; for (let k = 0; k < w; k += 64) { x.beginPath(); x.moveTo(k, 0); x.lineTo(k, h); x.stroke(); }
        x.strokeStyle = '#2a2430'; x.lineWidth = 4; x.beginPath(); const cut = w * 0.82; for (let i = 0; i <= 500; i++) { const px = i / 500 * cut; const u = (drawP * 0.9 - (cut - px) / w * 0.6); if (u < 0) continue; const py = h / 2 - voice(u % 1) * h * 0.4; if (i === 0 || u - 0.002 < 0) x.moveTo(px, py); else x.lineTo(px, py); } x.stroke(); });
      if (t < tNeedle) cm(S, t, t05, tNeedle, v3(-40, 60, 140), v3(-88, 14, 6), v3(-64, 34, 70), v3(-88, 14, 4), smooth);
      else cm(S, t, tNeedle, tWiggly, v3(-70, 34, 44), v3(-86, 15, 4), v3(-78, 30, 34), v3(-86, 13, 4), smooth);
    }, overlay(t, g, S) {
      tag('1857', 250, 100, { size: 34, scale: pop(t, t05 + 0.5) });
      if (t > tNeedle) { const p = project(S.cam, S.O.horn.userData.needle.getWorldPosition(v3(0, 0, 0))); tag('NEEDLE', p[0] + 160, p[1] - 120, { size: 28, scale: pop(t, tNeedle) }); }
    } });
    fx('whoosh', t05, 0.5); fx('pop', t05 + 0.5, 0.6); fx('scratch', tNeedle, 0.5, { dur: Math.max(1, tWiggly + 0.4 - tNeedle) }); fx('pop', tNeedle, 0.5);
    add({ scene: 'stage', t0: tWiggly, trans: 0.4, act(t, S) {
      stageReset(S); S.O.ped.visible = false; S.O.board.visible = true;
      const mode = t > tHigh - 0.2 ? 'high' : t > tLoud - 0.2 ? 'loud' : null;
      drawBoard(S, mode ? { compare: mode } : { wave: K(t, tWiggly, tWiggly + 0.8) });
      aim(S.cam, v3(0, 52, 190), v3(0, 48, -6));
    }, overlay(t, g, S) {
      const L = project(S.cam, S.boardToWorld(0.27, 0.95)), Rr = project(S.cam, S.boardToWorld(0.73, 0.95));
      if (t > tLoud - 0.2 && t < tHigh - 0.2) { tag('QUIET', L[0], L[1] + 60, { size: 30, color: '#5fd0ff' }); tag('LOUD', Rr[0], Rr[1] + 60, { size: 30, scale: pop(t, tLoud) }); text([['BIG WIGGLE = ', WH], ['LOUD', Y]], W / 2, 120, { size: 48, scale: pop(t, tLoud) }); }
      if (t > tHigh - 0.2) { tag('LOW', L[0], L[1] + 60, { size: 30, color: '#5fd0ff' }); tag('HIGH', Rr[0], Rr[1] + 60, { size: 30, scale: pop(t, tHigh) }); text([['FAST WIGGLE = ', WH], ['HIGH', Y]], W / 2, 120, { size: 48, scale: pop(t, tHigh) }); }
      vignette(0.35);
    } });
    fx('whoosh', tWiggly - 0.1, 0.4); fx('pop', tLoud - 0.2, 0.7); fx('pop', tHigh - 0.2, 0.7);

    // ================= 06 MEASURING =================
    const t06 = start('06') - 0.2, tRuler = c('06', 'ruler'), tHere = c('06', 'here'), tA1 = c('06', 'again', 1), tA2 = c('06', 'again', 2), tA3 = c('06', 'again', 3), tEvery = c('06', 'every'), tRow = c('06', 'row'), tVoice6 = c('06', 'voice', 2);
    const N6 = 24;
    const shown6 = (t) => t < tHere ? 0 : t < tA1 ? 1 : t < tA2 ? 2 : t < tA3 ? 3 : t < tEvery ? 4 : 4 + Math.floor((N6 - 4) * K(t, tEvery, tEvery + 1.6));
    add({ scene: 'stage', t0: t06, act(t, S) {
      stageReset(S); S.O.ped.visible = false; S.O.board.visible = true;
      const n = shown6(t);
      drawBoard(S, { wave: 1, waveCol: t > tEvery ? 'rgba(255,210,63,0.45)' : '#ffd23f', n: N6, show: n / N6, hl: n - 1 });
      cm(S, t, t06, tEvery, v3(-20, 50, 150), v3(-20, 48, -6), v3(-10, 50, 170), v3(-6, 48, -6), smooth);
      if (t > tEvery) cm(S, t, tEvery, end('06') + 0.5, v3(-10, 50, 170), v3(-6, 48, -6), v3(0, 48, 196), v3(0, 46, -6), smooth);
    }, overlay(t, g, S) {
      const n = shown6(t);
      if (t > tRuler && t < tEvery) { // ruler at the current sample
        const i = Math.max(0, n - 1); const top = project(S.cam, S.boardToWorld((60 + (i + 0.5) / N6 * 1380) / 1500, 0.08)), bot = project(S.cam, S.boardToWorld((60 + (i + 0.5) / N6 * 1380) / 1500, 0.92));
        const k = pop(t, tRuler); g.save(); g.globalAlpha = Math.min(1, k); g.fillStyle = '#e8c070'; g.fillRect(top[0] + 16, top[1], 22, bot[1] - top[1]); g.fillStyle = '#5a3a1a'; for (let yy = top[1]; yy < bot[1]; yy += 14) g.fillRect(top[0] + 16, yy, (yy - top[1]) % 70 < 14 ? 16 : 9, 3); g.restore();
      }
      for (let i = 0; i < Math.min(n, 12); i++) { const p = project(S.cam, stemWorld(S, N6, i)); const v = sampleVal((i + 0.5) / N6); text(String(v), p[0], p[1] + (voice((i + 0.5) / N6) >= 0 ? -40 : 44), { size: 26, color: WH, scale: pop(t, i === 0 ? tHere : i === 1 ? tA1 : i === 2 ? tA2 : i === 3 ? tA3 : tEvery + (i - 4) * 0.07) }); }
      if (t > tRow) { const vals = Array.from({ length: 10 }, (_, i) => sampleVal((i + 0.5) / N6)).join(' '); tag(vals + ' ...', W / 2, 990, { size: 26, scale: pop(t, tRow) }); }
      if (t > tVoice6) text([['THIS ROW ', WH], ['= HIS VOICE', G]], W / 2, 120, { size: 50, scale: pop(t, tVoice6) });
      vignette(0.35);
    } });
    [tHere, tA1, tA2, tA3].forEach((tt) => fx('tick', tt, 0.8)); for (let k = 0; k < 20; k++) fx('tick', tEvery + k * 0.08, 0.35); fx('pop', tRow, 0.6); fx('chime', tVoice6, 0.5);

    // ================= 07 SPEAKER (push / pull) =================
    const t07 = start('07') - 0.2, tSpeaker = c('07', 'speaker'), tPaper = c('07', 'paper'), tPush1 = c('07', 'push', 2), tHears = c('07', 'hears');
    const pp = wordsOf('07').filter((w) => w.w === 'push' || w.w === 'pull').slice(1); // the "push, pull, push, pull" run
    add({ scene: 'canyon', t0: t07, trans: 0.45, act(t, S) {
      canyonReset(S);
      const n = Math.floor((t - t07) * 12); S.O.lamps.userData.set(sampleVal((n % 97) / 97));
      let push = Math.sin(t * 50) * 0.45 * (t > tSpeaker ? 1 : 0);
      for (const w of pp) if (t >= w.s - 0.05 && t <= w.e + 0.25) push = (w.w === 'push' ? 1 : -1) * Math.sin(Math.PI * clamp((t - w.s + 0.05) / (w.e - w.s + 0.3)));
      if (pp.length && t > pp[pp.length - 1].e + 0.3) push = Math.sin(t * 60) * 0.7;
      S.O.speaker.userData.push(push);
      pose(S.O.friend, t + 1.3, { cheer: t > tHears ? smooth(K(t, tHears, tHears + 0.3)) : 0 });
      if (t < tSpeaker) cm(S, t, t07, tSpeaker, v3(-20, 70, 320), v3(0, 32, -10), v3(10, 66, 300), v3(20, 30, -10), smooth);
      else if (t < tHears) cm(S, t, tSpeaker, tPaper + 0.5, v3(40, 46, 120), v3(90, 16, -2), v3(66, 26, 50), v3(92, 15, -2), smooth);
      else cm(S, t, tHears, end('07') + 0.6, v3(66, 26, 50), v3(92, 15, -2), v3(40, 44, 110), v3(70, 18, 6), smooth);
    }, overlay(t, g, S) {
      if (t > tSpeaker - 0.2 && t < tHears) { const p = project(S.cam, S.O.speaker.getWorldPosition(v3(0, 0, 0)).add(v3(0, 30, 0))); tag('SPEAKER', p[0], p[1] - 40, { size: 30, scale: pop(t, tSpeaker - 0.2) }); }
      for (const w of pp) if (t >= w.s - 0.05 && t <= w.e + 0.35) text(w.w.toUpperCase() + '!', W / 2 + (w.w === 'push' ? -260 : 260), 300, { size: 64, color: w.w === 'push' ? Y : CYc, scale: pop(t, w.s - 0.05, 0.2) });
      if (t > tHears) { const [x, y] = headPos(S, S.O.friend); bubble('"HELLO!"', x, y, { scale: pop(t, tHears), size: 36 }); }
    } });
    fx('flicker', t07 + 0.2, 0.3, { dur: Math.max(0.5, tSpeaker - t07) }); fx('pop', tSpeaker - 0.2, 0.6); pp.forEach((w) => fx('thump', w.s, 0.8)); fx('chime', tHears, 0.6);

    // ================= 08 / 09 TOO FEW vs ENOUGH (with audio demos) =================
    const t08 = start('08') - 0.2, tOften = c('08', 'often'), tNowThen = c('08', 'then'), tMisses = c('08', 'misses'), tBlocky = c('08', 'blocky'), tAwful = c('08', 'awful'), tTwoK = c('08', 'two'), demo1 = end('08') + 0.45, demo2 = end('09') + 0.45, demoLen = demoB - demoA;
    const t09 = start('09') - 0.2;
    add({ scene: 'stage', t0: t08, trans: 0.4, act(t, S) {
      stageReset(S); S.O.ped.visible = false; S.O.board.visible = true;
      const few = t > tNowThen - 0.2; const n = few ? 7 : 0;
      drawBoard(S, { wave: 1, waveCol: few ? 'rgba(255,210,63,0.55)' : '#ffd23f', n, show: K(t, tNowThen - 0.2, tNowThen + 0.4), recon: K(t, tMisses, tMisses + 0.5), reconCol: '#ff4a4a' });
      cm(S, t, t08, end('08') + demoLen + 0.8, v3(-10, 52, 180), v3(0, 48, -6), v3(10, 50, 200), v3(0, 46, -6), smooth);
    }, overlay(t, g, S) {
      if (t > tOften && t < tNowThen) text('HOW OFTEN?', W / 2, 120, { size: 56, color: Y, scale: pop(t, tOften) });
      if (t > tBlocky) text([['BLOCKY ', R], ['COPY', WH]], W / 2, 120, { size: 52, scale: pop(t, tBlocky) });
      if (t > tTwoK) tag('2,000 TIMES A SECOND', W / 2, 990, { size: 30, scale: pop(t, tTwoK), color: R });
      if (t > demo1 - 0.3 && t < demo1 + demoLen + 0.4) { listenIcon(t, demo1 - 0.3, W / 2, 250); quoteLine(t, demo1 - 0.2); }
      vignette(0.35);
    } });
    fx('pop', tOften, 0.6); fx('tick', tNowThen, 0.6); fx('buzz', tAwful, 0.5); fx('pop', tTwoK, 0.6);
    fx('vclip', demo1, 1, { sec: '01', a: demoA, b: demoB, rate: 2000 });
    add({ scene: 'stage', t0: t09, act(t, S) {
      stageReset(S); S.O.ped.visible = false; S.O.board.visible = true;
      drawBoard(S, { wave: 1, waveCol: 'rgba(255,210,63,0.55)', n: 90, show: K(t, t09 + 0.2, t09 + 1.2), recon: K(t, t09 + 1.2, t09 + 1.8), reconCol: '#4ff07a' });
      aim(S.cam, v3(10, 50, 200), v3(0, 46, -6));
    }, overlay(t, g) {
      const tf = c('09', 'forty'); if (t > tf) tag('44,000 TIMES A SECOND', W / 2, 990, { size: 30, scale: pop(t, tf), color: G });
      if (t > demo2 - 0.3 && t < demo2 + demoLen + 0.4) { listenIcon(t, demo2 - 0.3, W / 2, 250); quoteLine(t, demo2 - 0.2); }
      if (t > c('09', 'music')) text([['MUSIC ', WH], ['QUALITY', G]], W / 2, 120, { size: 52, scale: pop(t, c('09', 'music')) });
      vignette(0.35);
    } });
    for (let k = 0; k < 14; k++) fx('tick', t09 + 0.2 + k * 0.07, 0.25); fx('pop', c('09', 'forty'), 0.6);
    fx('vclip', demo2, 1, { sec: '01', a: demoA, b: demoB, rate: 0 });

    // ================= 10 PRECISION =================
    const t10 = start('10') - 0.2, tEach = c('10', 'each'), tJagged = c('10', 'jagged'), tSixteen = c('10', 'sixteen'), tSixty = c('10', 'sixty');
    add({ scene: 'stage', t0: t10, trans: 0.35, act(t, S) {
      stageReset(S); S.O.ped.visible = false;
      if (t < tSixteen - 0.3) { S.O.board.visible = true; drawBoard(S, { wave: 1, waveCol: 'rgba(255,210,63,0.5)', n: 90, show: 1, recon: 1, reconCol: t > tEach ? '#ff8a3d' : '#4ff07a', quant: t > tJagged - 0.6 ? 4 : 0 }); aim(S.cam, v3(10, 50, 200), v3(0, 46, -6)); }
      else { const L = S.O.lamps16; L.visible = true; L.position.set(0, 0, 0); const n = Math.floor((t - tSixteen) * 8); L.userData.set([...((n * 2654435761) >>> 16 & 65535).toString(2).padStart(16, '0')].map(Number)); cm(S, t, tSixteen - 0.3, end('10') + 0.5, v3(0, 46, 190), v3(0, 30, 0), v3(0, 42, 170), v3(0, 30, 0), smooth); }
    }, overlay(t, g, S) {
      if (t < tEach) text([['FAST ENOUGH ', G], ['FOR YOUR EARS', WH]], W / 2, 120, { size: 46, scale: pop(t, t10 + 0.3) });
      if (t > tEach && t < tSixteen - 0.3) text([['8 LAMPS ', WH], ['= JAGGED', R]], W / 2, 120, { size: 50, scale: pop(t, c('10', 'eight')) });
      if (t > tSixteen - 0.3) text([['16 LAMPS', Y]], W / 2, 140, { size: 64, scale: pop(t, tSixteen - 0.3) });
      if (t > tSixty) tag('COUNTS UP TO 65,535', W / 2, 980, { size: 32, scale: pop(t, tSixty) });
      vignette(0.35);
    } });
    fx('pop', t10 + 0.3, 0.5); fx('pop', c('10', 'eight'), 0.6); fx('glitch', tJagged - 0.6, 0.4); fx('whoosh', tSixteen - 0.35, 0.4); fx('lamp', tSixteen, 0.7); fx('flicker', tSixteen + 0.1, 0.3, { dur: Math.max(0.5, end('10') - tSixteen) }); fx('pop', tSixty, 0.7);

    // ================= 11 ONE SONG =================
    const t11 = start('11') - 0.2, tSong = c('11', 'song'), tFortyFour = c('11', 'forty'), tEar11 = c('11', 'ear'), tMin = c('11', 'minutes'), tSixteenM = c('11', 'sixteen');
    add({ scene: 'stage', t0: t11, trans: 0.45, act(t, S) {
      stageReset(S); S.O.phone.visible = true; S.screen(songCanvas(t - t11));
      cm(S, t, t11, end('11') + 0.5, v3(30, 46, 150), SCR.clone(), v3(-20, 42, 130), SCR.clone(), smooth);
    }, overlay(t) {
      const x = 440;
      if (t > tFortyFour) text('44,100', x, 330, { size: 52, color: G, scale: pop(t, tFortyFour) });
      if (t > tFortyFour) text('EVERY SECOND', x, 395, { size: 24, scale: pop(t, tFortyFour + 0.1) });
      if (t > tEar11) text([['x 2 ', Y], ['EARS', WH]], x, 490, { size: 44, scale: pop(t, tEar11) });
      if (t > tMin) text([['x 180 ', Y], ['SECONDS', WH]], x, 580, { size: 44, scale: pop(t, tMin) });
      if (t > tSixteenM) { text('15,876,000', x, 700, { size: 54, color: G, scale: pop(t, tSixteenM) }); text('NUMBERS', x, 765, { size: 28, scale: pop(t, tSixteenM + 0.1) }); }
      vignette(0.35);
    } });
    fx('whoosh', t11, 0.5); fx('pop', tFortyFour, 0.6); fx('pop', tEar11, 0.6); fx('pop', tMin, 0.6); fx('pop', tSixteenM, 0.8); fx('chime', tSixteenM + 0.3, 0.4);

    // ================= 12 CLOSE: speaker pumps with the narrator again =================
    const t12 = start('12') - 0.2, w12 = wordsOf('12'), tWhich = c('12', 'which');
    add({ scene: 'stage', t0: t12, trans: 0.45, act(t, S) {
      stageReset(S); const O = S.O; O.spk.visible = true; O.spk.position.set(0, 6, 0); O.spk.rotation.set(0, 0, 0);
      const tk = talking(w12, t); O.spk.userData.push(tk * Math.sin(t * 70) * 0.9 + tk * Math.sin(t * 23) * 0.5);
      if (t < tWhich) cm(S, t, t12, tWhich, v3(30, 40, 130), v3(0, 18, 0), v3(10, 32, 100), v3(0, 18, 0), smooth);
      else cm(S, t, tWhich, end('12') + 0.6, v3(10, 32, 100), v3(0, 18, 0), v3(0, 22, 46), v3(0, 19, 0), smooth);
    }, overlay(t, g) {
      const k = K(t, t12, t12 + 0.6); if (k > 0) { g.save(); g.globalAlpha = k * (1 - K(t, tWhich, tWhich + 0.8)); for (let r = 0; r < 9; r++) { const y = 270 + r * 70; const off = ((t * 520 + r * 137) % 900); for (let j = 0; j < 4; j++) { const x = -100 + off + j * 230 - 230; if (x < 0 || x > 760) continue; text(String(sampleVal(((r * 31 + j * 7 + Math.floor(t * 9)) % 97) / 97)), x, y, { size: 30, color: (r + j) % 2 ? Y : G }); } } g.restore(); }
      vignette(0.4);
    } });
    fx('whoosh', t12, 0.5); fx('zoom', tWhich, 0.5);

    // ================= 13 MAP OUTRO: flag 6, fog lifts off the Foundry =================
    const t13 = start('13') - 0.3, tPlant = c('13', 'plants'), tEvery13 = c('13', 'every'), tWhen13 = c('13', 'when'), tNext = c('13', 'next'), tLifts = c('13', 'lifts');
    add({ scene: 'map', t0: t13, trans: 0.6, act(t, S) {
      const O = S.O; O.bob.visible = true; const p = S.wpPos(6); O.bob.position.copy(p).add(v3(-6, 0, 3)); O.bob.rotation.y = 0.5;
      const pk = K(t, tPlant + 0.1, tPlant + 0.5); O.newFlag.scale.setScalar(Math.max(0.0001, 0.55 * backOut(pk)));
      pose(O.bob, t, t > tPlant + 0.5 && t < tPlant + 2 ? { cheer: smooth(K(t, tPlant + 0.5, tPlant + 0.8)) * (1 - K(t, tPlant + 1.6, tPlant + 2)) } : { lookY: t > tNext ? 1.2 * smooth(K(t, tNext, tNext + 0.6)) : 0 });
      S.lift[1] = smooth(K(t, tNext, tNext + 7));
      const w6 = S.wpPos(6);
      const c1 = [w6.clone().add(v3(-10, 70, 80)), w6.clone().add(v3(0, 8, 0))], c2 = [v3(110, 270, 420), v3(110, 0, 230)], c3 = [v3(230, 250, 400), v3(240, 20, 210)], c4 = [v3(240, 220, 360), v3(250, 20, 200)];
      if (t < tEvery13) cm(S, t, t13, tEvery13, c1[0].clone().add(v3(0, 10, 20)), c1[1], c1[0], c1[1], smooth);
      else if (t < tNext) cm(S, t, tEvery13, tWhen13 + 1, c1[0], c1[1], c2[0], c2[1]);
      else if (t < end('13') + 1) cm(S, t, tNext, end('13') + 1, c2[0], c2[1], c3[0], c3[1]);
      else cm(S, t, end('13') + 1, duration, c3[0], c3[1], c4[0], c4[1], (x) => x);
    }, overlay(t, g, S) {
      if (t > tPlant + 0.3 && t < tWhen13) { const [x, y] = project(S.cam, S.wpPos(6).add(v3(3, 22, -2))); tag('STOP 6 CLEARED', x, y - 70, { size: 28, scale: pop(t, tPlant + 0.4) }); }
      if (t > tEvery13 && t < tNext) text([['THE DESERT: ', WH], ['COMPLETE', G]], W / 2, 130, { size: 54, scale: pop(t, tEvery13) });
      if (t > tWhen13 && t < tNext) { const items = [['words', 'TEXT'], ['pictures', 'PICTURES'], ['voice', 'SOUND']]; items.forEach(([w, s], i) => { const tt = c('13', w); if (t > tt) tag(s, W / 2 + (i - 1) * 300, 230, { size: 32, scale: pop(t, tt), color: G }); }); }
      if (t > tLifts) { const k = pop(t, tLifts); const [x, y] = project(S.cam, v3(240, 70, 225)); text('NEXT STOP', x, y - 90, { size: 40, scale: k }); text('THE FOUNDRY', x, y - 20, { size: 56, color: Y, scale: pop(t, tLifts + 0.2) }); }
      vignette(0.3);
      const fo = K(t, duration - 1.2, duration); if (fo > 0) { g.fillStyle = `rgba(0,0,0,${fo})`; g.fillRect(0, 0, W, H); }
    } });
    fx('whoosh', t13, 0.6); fx('flag', tPlant + 0.1, 1.0); fx('chime', tPlant + 0.4, 0.6); fx('pop', tEvery13, 0.6);
    ['words', 'pictures', 'voice'].forEach((w) => fx('pop', c('13', w), 0.5)); fx('gust', tNext, 0.7); fx('rumble', tLifts, 0.6); fx('pop', tLifts, 0.6);

    const beds = []; sh.slice().sort((a, b) => a.t0 - b.t0).forEach((s, i, arr) => { const t1 = i < arr.length - 1 ? arr[i + 1].t0 : duration; beds.push({ scene: s.scene, t0: s.t0, t1 }); });
    beds.forEach((b) => fx(b.scene === 'stage' ? 'bed_stage' : b.scene === 'map' ? 'bed_map' : 'bed_canyon', b.t0, 1, { dur: b.t1 - b.t0 }));
    return sh;
  },
};

const CYc = '#5ff2ff';
function demoLen(al) { const w = al['01'].words; return (w[5].e + 0.25) - Math.max(0, w[0].s - 0.08); }
function headPos(S, ch, up = 36) { return project(S.cam, ch.getWorldPosition(v3(0, 0, 0)).add(v3(0, up, 0))); }
function quoteLine(t, t0) { text('"RIGHT NOW, YOU\'RE LISTENING', W / 2, 860, { size: 34, scale: pop(t, t0) }); text('TO NUMBERS."', W / 2, 910, { size: 34, scale: pop(t, t0 + 0.05) }); }
function listenIcon(t, t0, x, y) {
  const k = pop(t, t0); if (k <= 0) return; g2.save(); g2.translate(x - 190, y); g2.scale(k, k);
  g2.fillStyle = '#14102a'; g2.fillRect(-40, -32, 48, 64); g2.beginPath(); g2.moveTo(0, -32); g2.lineTo(44, -62); g2.lineTo(44, 62); g2.lineTo(0, 32); g2.fill();
  g2.fillStyle = WH; g2.fillRect(-34, -26, 38, 52); g2.beginPath(); g2.moveTo(4, -26); g2.lineTo(38, -50); g2.lineTo(38, 50); g2.lineTo(4, 26); g2.fill();
  g2.strokeStyle = WH; g2.lineWidth = 8; for (let r = 0; r < 3; r++) { const a = 0.5 + 0.5 * Math.sin(t * 8 - r); g2.globalAlpha = a; g2.beginPath(); g2.arc(44, 0, 34 + r * 24, -0.7, 0.7); g2.stroke(); }
  g2.restore(); text('LISTEN', x + 110, y + 4, { size: 48, scale: k });
}
const _songC = document.createElement('canvas'); _songC.width = 240; _songC.height = 460;
function songCanvas(t) {
  const x = _songC.getContext('2d'); x.fillStyle = '#1b1530'; x.fillRect(0, 0, 240, 460);
  const gr = x.createLinearGradient(0, 40, 0, 240); gr.addColorStop(0, '#ff8a5c'); gr.addColorStop(1, '#ffd36b'); x.fillStyle = gr; x.fillRect(30, 50, 180, 180);
  x.fillStyle = '#4a3a6a'; x.fillRect(30, 180, 180, 50); x.fillStyle = '#fff3c4'; x.fillRect(100, 120, 40, 40);
  x.fillStyle = '#ffffff'; x.font = '14px "PS2P"'; x.fillText('Desert Song', 30, 270); x.fillStyle = '#9a92c8'; x.font = '10px "PS2P"'; x.fillText('3:00', 30, 292);
  const p = clamp(t / 20); x.fillStyle = '#3a3260'; x.fillRect(30, 320, 180, 8); x.fillStyle = '#4ff07a'; x.fillRect(30, 320, 180 * p, 8);
  for (let i = 0; i < 18; i++) { const hgt = 10 + 40 * Math.abs(Math.sin(t * 6 + i * 0.9)) * (0.5 + 0.5 * Math.sin(i)); x.fillStyle = i % 2 ? '#ffd23f' : '#4ff07a'; x.fillRect(30 + i * 10, 420 - hgt, 7, hgt); }
  return _songC;
}
