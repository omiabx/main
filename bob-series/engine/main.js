import * as THREE from 'three';
import { renderer, out, octx, ov, g2, buf, bctx, W, H, aim, v3 } from './core.js';
import { SCENES } from './scenes.js';
import { buildTimeline } from './timeline.js';

const cache = {};
function getScene(name) { if (!cache[name]) cache[name] = SCENES[name](); return cache[name]; }

// draw one shot at global time t into ctx
function drawShot(shot, t, ctx) {
  const S = getScene(shot.scene);
  g2.clearRect(0, 0, W, H);
  S.update(t, shot, g2);
  if (shot.camv) { const c = shot.camv; aim(S.cam, v3(c[0], c[1], c[2]), v3(c[3], c[4], c[5])); }
  renderer.render(S.scene, S.cam);
  ctx.drawImage(renderer.domElement, 0, 0);
  if (S.post) S.post(t, shot, g2);
  if (shot.overlay) shot.overlay(t, g2, S);
  ctx.drawImage(ov, 0, 0);
}

let TL = null;
window.API = {
  async init(align, gaps) {
    await document.fonts.load('40px "PS2P"');
    TL = buildTimeline(align, gaps);
    return { duration: TL.duration, shots: TL.shots.map((s) => [s.scene, +s.t0.toFixed(2), +s.t1.toFixed(2)]), sfx: TL.sfx, voice: TL.voice };
  },
  frame(t, q = 0.93) {
    const i = TL.shots.findIndex((s) => t >= s.t0 && t < s.t1);
    const shot = TL.shots[i < 0 ? TL.shots.length - 1 : i];
    drawShot(shot, t, octx);
    // pixel-dissolve transition into this shot from previous
    const prev = TL.shots[i - 1];
    if (prev && shot.trans && t < shot.t0 + shot.trans) {
      drawShot(prev, t, bctx);
      const p = (t - shot.t0) / shot.trans; const cell = 60; const cols = Math.ceil(W / cell), rows = Math.ceil(H / cell);
      // cells of prev remain if their hash > p
      for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
        const h = ((x * 7919 + y * 104729) % 1000) / 1000;
        if (h >= p) octx.drawImage(buf, x * cell, y * cell, cell, cell, x * cell, y * cell, cell, cell);
      }
    }
    return out.toDataURL('image/jpeg', q);
  },
  still(scene, t, extra) {
    const shot = { scene, t0: 0, t1: 999, ...(extra || {}) };
    drawShot(shot, t, octx); return out.toDataURL('image/jpeg', 0.95);
  },
  get TL() { return TL; },
};
window.READY = true;
