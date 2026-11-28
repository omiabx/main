// Xtrades Shorts motion-graphics engine.
// Pure canvas renderer: compile(spec, words) then render(t). Deterministic per frame.
(function () {
const W = 1080, H = 1920;
const COL = {
  green: '#7be35c', red: '#ff4d4f', blue: '#4ea8ff', gray: '#5f6368', white: '#f2f2f2',
  dim: '#9a9a9a', hdr: '#7ad65a', hdrDim: '#6dbb50', bg: '#070807', amber: '#ffbf3c'
};
const FONT = { dot: 'Doto', hero: 'Archivo Black', mono: 'Space Mono', jb: 'JetBrains Mono' };

let cv, ctx, S = null, LOGO = null, GRAIN = [], SCAN = null, VIG = null, GLITCH = null, TINT = null;

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, k) => a + (b - a) * k;
const E = {
  out: t => 1 - Math.pow(1 - t, 3),
  back: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  inout: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
};
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function col(c) { return COL[c] || c; }
function rgba(hex, a) { hex = col(hex); const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; }

// ---------------------------------------------------------------- compile
function normTok(s) { return s.toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9$%.,']/g, '').replace(/[.,]+$/, ''); }
function compile(spec, words) {
  const toks = words.map(w => normTok(w.w));
  const find = (phrase, from, ctxName) => {
    const p = phrase.split(/\s+/).map(normTok);
    for (let i = from; i < toks.length; i++) {
      let ok = true;
      for (let k = 0; k < p.length; k++) if (toks[i + k] !== p[k]) { ok = false; break; }
      if (ok) return i;
    }
    throw new Error(`trigger not found: "${phrase}" (after token ${from}) in ${ctxName}`);
  };
  const total = spec.duration || (words[words.length - 1].end + 1.2);
  let cursor = 0;
  spec.scenes.forEach((sc, i) => {
    const idx = i === 0 ? 0 : find(sc.at, cursor, `scene ${i + 1}`);
    sc.idx = idx; sc.t = i === 0 ? 0 : Math.max(0, words[idx].start - 0.06); cursor = idx;
  });
  spec.scenes.forEach((sc, i) => {
    sc.end = i + 1 < spec.scenes.length ? spec.scenes[i + 1].t : total;
    const walk = (o, name) => {
      if (Array.isArray(o)) { o.forEach((x, k) => walk(x, name + '[' + k + ']')); return; }
      if (!o || typeof o !== 'object') return;
      if (typeof o.at === 'string') {
        const j = find(o.at, sc.idx, `scene ${i + 1} ${name}`);
        o.t = (o.atEnd ? words[j].end : words[j].start) + (o.dt || 0);
        o.wi = j;
      } else if (typeof o.at === 'number') o.t = sc.t + o.at;
      if (typeof o.out === 'string') { const j = find(o.out, sc.idx, `scene ${i + 1} out`); o.tOut = words[j].start; }
      for (const k in o) if (k !== 'at' && typeof o[k] === 'object') walk(o[k], name + '.' + k);
    };
    (sc.els || []).forEach((el, k) => {
      walk(el, `el${k}:${el.type}`);
      if (el.t === undefined) el.t = sc.t + (el.delay !== undefined ? el.delay : 0.12);
      el.ph = (i * 7 + k * 13) % 17;
    });
  });
  spec.total = total;
  S = spec;
  return { total, scenes: spec.scenes.map(s => ({ t: s.t, end: s.end })) };
}

// ---------------------------------------------------------------- assets
async function init(opts) {
  cv = document.getElementById('c'); ctx = cv.getContext('2d');
  await document.fonts.load(`800 96px ${FONT.dot}`); await document.fonts.load(`100px "${FONT.hero}"`);
  await document.fonts.load(`700 30px "${FONT.mono}"`); await document.fonts.load(`400 30px "${FONT.mono}"`);
  await document.fonts.ready;
  LOGO = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = opts.logo; });
  const r = rng(7);
  for (let g = 0; g < 6; g++) {
    const c = document.createElement('canvas'); c.width = 540; c.height = 960;
    const x = c.getContext('2d'), id = x.createImageData(540, 960);
    for (let p = 0; p < id.data.length; p += 4) { const v = r() * 255; id.data[p] = id.data[p + 1] = id.data[p + 2] = v; id.data[p + 3] = 255; }
    x.putImageData(id, 0, 0); GRAIN.push(c);
  }
  SCAN = document.createElement('canvas'); SCAN.width = W; SCAN.height = H;
  { const x = SCAN.getContext('2d'); x.fillStyle = 'rgba(0,0,0,0.16)'; for (let y = 0; y < H; y += 4) x.fillRect(0, y, W, 2); }
  VIG = document.createElement('canvas'); VIG.width = W; VIG.height = H;
  { const x = VIG.getContext('2d'); const g = x.createRadialGradient(W / 2, H * 0.42, H * 0.22, W / 2, H * 0.5, H * 0.78);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.78)'); x.fillStyle = g; x.fillRect(0, 0, W, H); }
  GLITCH = document.createElement('canvas'); GLITCH.width = W; GLITCH.height = H;
  TINT = document.createElement('canvas'); TINT.width = W; TINT.height = H;
}

// ---------------------------------------------------------------- text helpers
function setFont(kind, size) {
  const f = { dot: `800 ${size}px ${FONT.dot}`, hero: `${size}px "${FONT.hero}"`, mono: `400 ${size}px "${FONT.mono}"`,
    bold: `700 ${size}px "${FONT.mono}"` }[kind] || kind;
  ctx.font = f;
}
function txt(s, x, y, o = {}) {
  setFont(o.font || 'mono', o.size || 30);
  ctx.letterSpacing = (o.spacing || 0) + 'px';
  ctx.textAlign = o.align || 'left'; ctx.textBaseline = o.base || 'alphabetic';
  const c = col(o.color || 'white');
  if (o.split) {
    ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha *= 0.75;
    ctx.fillStyle = '#ff2a3a'; ctx.fillText(s, x - o.split, y);
    ctx.fillStyle = '#2ad8ff'; ctx.fillText(s, x + o.split, y); ctx.restore();
  }
  if (o.glow) { ctx.save(); ctx.shadowColor = rgba(c, 0.9); ctx.shadowBlur = o.glow; ctx.fillStyle = c; ctx.fillText(s, x, y); ctx.restore(); }
  ctx.fillStyle = c; ctx.fillText(s, x, y);
  ctx.letterSpacing = '0px';
}
function measure(s, o = {}) { setFont(o.font || 'mono', o.size || 30); ctx.letterSpacing = (o.spacing || 0) + 'px'; const w = ctx.measureText(s).width; ctx.letterSpacing = '0px'; return w; }
function stroke(c, w, glow) { ctx.strokeStyle = col(c); ctx.lineWidth = w; if (glow) { ctx.shadowColor = rgba(c, 0.85); ctx.shadowBlur = glow; } }

// ---------------------------------------------------------------- iso helpers
const CS = 0.866, SN = 0.5;
function iso(ox, oy, x, y, z) { return [ox + (x - y) * CS, oy + (x + y) * SN - z]; }
function poly(pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath(); }
// prism standing on ground point (ox,oy) = front-bottom corner
function prism(ox, oy, w, d, h, c, o = {}) {
  const P = (x, y, z) => iso(ox, oy, x - w, y - d, z);
  const top = [P(0, 0, h), P(w, 0, h), P(w, d, h), P(0, d, h)];
  const left = [P(0, d, 0), P(w, d, 0), P(w, d, h), P(0, d, h)];
  const right = [P(w, 0, 0), P(w, d, 0), P(w, d, h), P(w, 0, h)];
  ctx.save();
  const fa = o.fill !== undefined ? o.fill : 0.10;
  ctx.fillStyle = rgba(c, fa * 1.6); poly(top); ctx.fill();
  ctx.fillStyle = rgba(c, fa); poly(left); ctx.fill();
  ctx.fillStyle = rgba(c, fa * 0.6); poly(right); ctx.fill();
  stroke(c, o.lw || 2.2, o.glow === undefined ? 14 : o.glow);
  ctx.globalAlpha *= 0.95;
  [top, left, right].forEach(f => { poly(f); ctx.stroke(); });
  if (o.segs && h > 4) {
    ctx.shadowBlur = 0; ctx.globalAlpha *= 0.55; ctx.lineWidth = 1.4;
    const n = o.segs;
    for (let k = 1; k < n; k++) {
      const z = h * k / n;
      ctx.beginPath(); const a = P(0, d, z), b = P(w, d, z), e = P(w, 0, z);
      ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.lineTo(e[0], e[1]); ctx.stroke();
    }
  }
  ctx.restore();
  return { top: P(w / 2, d / 2, h), bottom: P(w, d, 0) };
}
function cylinder(cx, cy, rx, h, c, o = {}) { // iso coin/cylinder, cy = bottom center
  const ry = rx * 0.5;
  ctx.save(); stroke(c, 2.2, 12);
  ctx.fillStyle = rgba(c, 0.12);
  ctx.beginPath(); ctx.ellipse(cx, cy - h, rx, ry, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx - rx, cy - h); ctx.lineTo(cx - rx, cy); ctx.ellipse(cx, cy, rx, ry, 0, Math.PI, 0, true); ctx.lineTo(cx + rx, cy - h); ctx.stroke();
  ctx.restore();
}

// ---------------------------------------------------------------- icons (outline)
function icon(name, x, y, s, c, el, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); stroke(c, 3 / s * Math.max(1, s * 0.9), 12); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  const fillA = (a) => { ctx.fillStyle = rgba(c, a); };
  switch (name) {
    case 'person': {
      ctx.beginPath(); ctx.arc(0, -58, 26, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-48, 30); ctx.quadraticCurveTo(-48, -22, 0, -22); ctx.quadraticCurveTo(48, -22, 48, 30); ctx.closePath(); fillA(0.08); ctx.fill(); ctx.stroke();
      break; }
    case 'phone': {
      ctx.beginPath(); ctx.roundRect(-70, -130, 140, 260, 22); fillA(0.06); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-18, -114); ctx.lineTo(18, -114); ctx.stroke();
      if (el.button) { ctx.shadowBlur = 18; ctx.beginPath(); ctx.roundRect(-48, 50, 96, 46, 10); fillA(0.25); ctx.fill(); ctx.stroke();
        ctx.shadowBlur = 0; txt(el.button, 0, 82, { font: 'bold', size: 24, align: 'center', color: c, spacing: 2 }); }
      if (el.candles) { const st = el.candles; const data = [[0, 30, -10, 20], [20, 40, 10, 15], [15, 22, -30, -20], [-20, 0, -40, -5], [-5, 35, -10, 30]];
        data.forEach((d, k) => { const up = d[3] > d[0]; let cc = up ? COL.green : COL.red; if (st === 'flip') cc = up ? COL.red : COL.green;
          const xx = -48 + k * 24, sc = 1.2; ctx.strokeStyle = cc; ctx.shadowColor = cc; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.moveTo(xx, -d[1] * sc); ctx.lineTo(xx, -d[2] * sc); ctx.stroke();
          const y0 = -Math.max(d[0], d[3]) * sc, hh = Math.abs(d[3] - d[0]) * sc;
          ctx.fillStyle = cc; if (st === 'hollow' && up) { ctx.fillStyle = '#070807'; }
          ctx.beginPath(); ctx.rect(xx - 7, y0, 14, Math.max(3, hh)); ctx.fill(); ctx.stroke(); });
        stroke(c, 3, 12); }
      break; }
    case 'flag': { ctx.beginPath(); ctx.moveTo(-30, 60); ctx.lineTo(-30, -60); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-30, -60); ctx.lineTo(40, -42); ctx.lineTo(-30, -20); ctx.closePath(); fillA(0.3); ctx.fill(); ctx.stroke(); break; }
    case 'calendar': {
      ctx.beginPath(); ctx.roundRect(-80, -80, 160, 160, 14); fillA(0.07); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-80, -38); ctx.lineTo(80, -38); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-40, -96); ctx.lineTo(-40, -66); ctx.moveTo(40, -96); ctx.lineTo(40, -66); ctx.stroke();
      ctx.shadowBlur = 0;
      if (el.top) txt(el.top, 0, -48, { font: 'bold', size: 26, align: 'center', color: c, spacing: 3 });
      if (el.big) txt(el.big, 0, 48, { font: 'hero', size: el.bigSize || 70, align: 'center', color: c, glow: 16 });
      break; }
    case 'building': {
      ctx.beginPath(); ctx.moveTo(-100, -40); ctx.lineTo(0, -95); ctx.lineTo(100, -40); ctx.closePath(); fillA(0.08); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.rect(-100, -40, 200, 14); ctx.stroke();
      for (let k = 0; k < 4; k++) { const xx = -72 + k * 48; ctx.beginPath(); ctx.rect(xx - 9, -20, 18, 100); ctx.stroke(); }
      ctx.beginPath(); ctx.rect(-110, 82, 220, 16); ctx.stroke(); break; }
    case 'clock': {
      ctx.beginPath(); ctx.arc(0, 0, 70, 0, Math.PI * 2); fillA(0.06); ctx.fill(); ctx.stroke();
      const a = (el.spin ? t * 2.2 : 0) - Math.PI / 2;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * 50, Math.sin(a) * 50); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a / 12 + 1) * 32, Math.sin(a / 12 + 1) * 32); ctx.stroke(); break; }
    case 'hourglass': {
      ctx.beginPath(); ctx.moveTo(-40, -60); ctx.lineTo(40, -60); ctx.lineTo(-40, 60); ctx.lineTo(40, 60); ctx.closePath(); ctx.stroke();
      const k = (t * 0.6) % 1; fillA(0.5); ctx.beginPath(); ctx.moveTo(-30 * (1 - k), -50 + 45 * k); ctx.lineTo(30 * (1 - k), -50 + 45 * k); ctx.lineTo(0, -6); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-30 * k, 52); ctx.lineTo(30 * k, 52); ctx.lineTo(0, 52 - 40 * k); ctx.closePath(); ctx.fill(); break; }
    case 'lock': {
      ctx.beginPath(); ctx.roundRect(-55, -20, 110, 90, 12); fillA(0.12); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.arc(0, -20, 36, Math.PI, 0); ctx.stroke();
      ctx.beginPath(); ctx.arc(0, 18, 9, 0, Math.PI * 2); ctx.stroke(); break; }
    case 'check': { ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(-30, 0); ctx.lineTo(-8, 24); ctx.lineTo(34, -26); ctx.stroke(); break; }
    case 'cross': { ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(-28, -28); ctx.lineTo(28, 28); ctx.moveTo(28, -28); ctx.lineTo(-28, 28); ctx.stroke(); break; }
    case 'notebook': {
      ctx.beginPath(); ctx.roundRect(-90, -120, 180, 240, 10); fillA(0.06); ctx.fill(); ctx.stroke();
      for (let k = 0; k < 6; k++) { ctx.beginPath(); ctx.arc(-90, -95 + k * 38, 7, 0, Math.PI * 2); ctx.stroke(); }
      const prog = el.write ? clamp((t - el.t) / 2.2) : 1;
      for (let k = 0; k < 6; k++) { const L = clamp(prog * 6 - k) * 120; if (L <= 0) continue; ctx.beginPath(); ctx.moveTo(-60, -90 + k * 36); ctx.lineTo(-60 + L, -90 + k * 36); ctx.stroke(); }
      break; }
    case 'gauge': break;
    case 'coin': { for (let k = 0; k < (el.stack || 4); k++) cylinder(0, -k * 22, 70, 18, c); break; }
    case 'server': { for (let k = 0; k < (el.stack || 3); k++) prism(0, -k * 46, 120, 90, 40, c, { fill: 0.08, glow: 10 }); break; }
    case 'tri-up': { ctx.beginPath(); ctx.moveTo(0, -26); ctx.lineTo(24, 16); ctx.lineTo(-24, 16); ctx.closePath(); fillA(0.85); ctx.fill(); ctx.stroke(); break; }
    case 'tri-down': { ctx.beginPath(); ctx.moveTo(0, 26); ctx.lineTo(24, -16); ctx.lineTo(-24, -16); ctx.closePath(); fillA(0.85); ctx.fill(); ctx.stroke(); break; }
    case 'arrow-up': { ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(0, 50); ctx.lineTo(0, -50); ctx.moveTo(-26, -24); ctx.lineTo(0, -50); ctx.lineTo(26, -24); ctx.stroke(); break; }
    case 'arrow-down': { ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(0, -50); ctx.lineTo(0, 50); ctx.moveTo(-26, 24); ctx.lineTo(0, 50); ctx.lineTo(26, 24); ctx.stroke(); break; }
    case 'chip': { ctx.beginPath(); ctx.roundRect(-50, -50, 100, 100, 10); fillA(0.1); ctx.fill(); ctx.stroke();
      for (let k = -2; k <= 2; k++) { ctx.beginPath(); ctx.moveTo(k * 18, -50); ctx.lineTo(k * 18, -66); ctx.moveTo(k * 18, 50); ctx.lineTo(k * 18, 66); ctx.moveTo(-50, k * 18); ctx.lineTo(-66, k * 18); ctx.moveTo(50, k * 18); ctx.lineTo(66, k * 18); ctx.stroke(); } break; }
  }
  ctx.restore();
}

// ---------------------------------------------------------------- elements
function countText(text, k) {
  const m = text.match(/^([^0-9]*)([0-9][0-9,]*\.?[0-9]*)(.*)$/);
  if (!m) return text;
  const dec = (m[2].split('.')[1] || '').length, target = parseFloat(m[2].replace(/,/g, ''));
  const v = target * E.out(k);
  let s = v.toFixed(dec); if (m[2].includes(',')) s = Number(s).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
  return m[1] + s + m[3];
}
const DRAW = {
  hero(el, t, a) {
    const k = clamp((t - el.t) / 0.32), sc = lerp(1.22, 1, E.out(k));
    ctx.save(); ctx.translate(el.x || 540, el.y || 760); ctx.scale(sc, sc); ctx.globalAlpha *= a;
    const s = el.count ? countText(el.text, clamp((t - el.t) / 0.7)) : el.text;
    const jitter = (t - el.t) < 0.25 ? (rng(Math.floor(t * 60))() - 0.5) * 10 : 0;
    txt(s, jitter, 0, { font: 'hero', size: el.size || 220, align: 'center', color: el.color || 'green', glow: 46, split: el.split === undefined ? 5 : el.split, base: 'middle' });
    ctx.restore();
    if (el.sub) { ctx.save(); ctx.globalAlpha *= clamp((t - el.t - 0.25) / 0.3) * a;
      txt(el.sub, el.x || 540, (el.y || 760) + (el.size || 220) * 0.62, { size: el.subSize || 28, align: 'center', color: el.subColor || 'dim', spacing: 7 }); ctx.restore(); }
  },
  label(el, t, a) {
    let s = el.text; if (el.typing !== false) { const n = Math.floor((t - el.t) / 0.028); s = s.slice(0, Math.max(0, n)); }
    ctx.save(); ctx.globalAlpha *= a;
    txt(s, el.x || 540, el.y, { font: el.font || 'mono', size: el.size || 30, align: el.align || 'center', color: el.color || 'dim', spacing: el.spacing === undefined ? 6 : el.spacing, glow: el.glow });
    ctx.restore();
  },
  rows(el, t) {
    el.items.forEach((it, k) => {
      const tt = it.t !== undefined ? it.t : el.t + k * 0.3; const a = clamp((t - tt) / 0.3); if (a <= 0) return;
      const y = el.y + k * (el.gap || 95); ctx.save(); ctx.globalAlpha *= a; ctx.translate((1 - E.out(a)) * -30, 0);
      txt(it.l, el.x || 110, y, { font: 'bold', size: el.size || 42, color: it.lc || 'white', spacing: 1 });
      txt(it.v, (el.x || 110) + (el.w || 860), y, { font: 'hero', size: el.vsize || 60, align: 'right', color: it.color || 'green', glow: 26, split: 3 });
      ctx.restore();
    });
  },
  prism(el, t, a) {
    const g = el.grow === false ? 1 : E.out(clamp((t - el.t) / (el.dur || 0.6)));
    ctx.save(); ctx.globalAlpha *= a;
    const h = (el.h || 200) * g;
    prism(el.x, el.y, el.w || 120, el.d || 120, h, col(el.color || 'green'), { segs: el.segs, fill: el.fill, glow: el.glow });
    if (el.label) txt(el.label, el.x + (el.lx || 0), el.y + 50 + (el.ly || 0), { size: el.lsize || 24, align: 'center', color: el.lcolor || el.color || 'green', spacing: 5 });
    if (el.top) txt(el.top, el.x + (el.tx || 0), el.y - h - 60 - (el.d || 120) * 0.3, { font: 'hero', size: el.tsize || 56, align: 'center', color: el.tcolor || el.color || 'green', glow: 24, split: 2 });
    ctx.restore();
  },
  icon(el, t, a) {
    const k = E.back(clamp((t - el.t) / 0.35));
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(el.x, el.y); ctx.scale(lerp(0.6, 1, k), lerp(0.6, 1, k)); ctx.translate(-el.x, -el.y);
    icon(el.name, el.x, el.y, el.s || 1, col(el.color || 'green'), el, t);
    if (el.label) txt(el.label, el.x, el.y + (el.ly || 120) * (el.s || 1), { size: el.lsize || 24, align: 'center', color: el.lcolor || el.color || 'green', spacing: 5 });
    ctx.restore();
  },
  arrow(el, t, a) {
    const k = E.inout(clamp((t - el.t) / (el.dur || 0.45))); if (k <= 0) return;
    const x = lerp(el.x1, el.x2, k), y = lerp(el.y1, el.y2, k);
    ctx.save(); ctx.globalAlpha *= a; stroke(el.color || 'green', el.lw || 5, 16); ctx.lineCap = 'round';
    if (el.dash) ctx.setLineDash([14, 14]);
    ctx.beginPath(); ctx.moveTo(el.x1, el.y1); ctx.lineTo(x, y); ctx.stroke(); ctx.setLineDash([]);
    const ang = Math.atan2(el.y2 - el.y1, el.x2 - el.x1), L = 26;
    ctx.beginPath(); ctx.moveTo(x - L * Math.cos(ang - 0.5), y - L * Math.sin(ang - 0.5)); ctx.lineTo(x, y); ctx.lineTo(x - L * Math.cos(ang + 0.5), y - L * Math.sin(ang + 0.5)); ctx.stroke();
    if (el.label && k > 0.6) txt(el.label, (el.x1 + el.x2) / 2 + (el.lx || 0), (el.y1 + el.y2) / 2 + (el.ly || -24), { size: el.lsize || 24, align: 'center', color: el.lcolor || el.color || 'green', spacing: 4 });
    ctx.restore();
  },
  strike(el, t, a) {
    const k = E.out(clamp((t - el.t) / 0.28)); if (k <= 0) return;
    ctx.save(); ctx.globalAlpha *= a; stroke(el.color || 'red', el.lw || 12, 30); ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(el.x1, el.y1); ctx.lineTo(lerp(el.x1, el.x2, k), lerp(el.y1, el.y2, k)); ctx.stroke(); ctx.restore();
  },
  timeline(el, t, a) {
    const k = E.out(clamp((t - el.t) / 0.5));
    ctx.save(); ctx.globalAlpha *= a; stroke(el.color || 'gray', 3, 8);
    ctx.beginPath(); ctx.moveTo(el.x1, el.y); ctx.lineTo(lerp(el.x1, el.x2, k), el.y); ctx.stroke();
    (el.ticks || []).forEach(tk => { const x = lerp(el.x1, el.x2, tk.f); if (k < tk.f) return;
      ctx.beginPath(); ctx.moveTo(x, el.y - 14); ctx.lineTo(x, el.y + 14); ctx.stroke();
      txt(tk.label, x, el.y + 64, { size: 32, align: 'center', color: 'dim', spacing: 3 }); });
    (el.marks || []).forEach(m => { const ma = clamp((t - (m.t !== undefined ? m.t : el.t)) / 0.3); if (ma <= 0) return;
      const x = lerp(el.x1, el.x2, m.f); ctx.save(); ctx.globalAlpha *= ma;
      icon(m.kind === 'down' ? 'tri-down' : 'tri-up', x, el.y - 70, el.ms || 1.6, col(m.color || 'green'), {}, t);
      if (m.label) txt(m.label, x, el.y - 110, { font: 'bold', size: 30, align: 'center', color: m.color || 'green', spacing: 2 });
      ctx.restore(); });
    ctx.restore();
  },
  gauge(el, t, a) {
    const r = el.r || 220, x = el.x, y = el.y;
    ctx.save(); ctx.globalAlpha *= a; stroke('gray', 18, 0); ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(x, y, r, Math.PI, 0); ctx.stroke();
    const segs = [['green', 0, 0.55], ['amber', 0.55, 0.8], ['red', 0.8, 1]];
    segs.forEach(([c, s0, s1]) => { stroke(c, 18, 14); ctx.globalAlpha = a * 0.85; ctx.beginPath(); ctx.arc(x, y, r, Math.PI + s0 * Math.PI + 0.03, Math.PI + s1 * Math.PI - 0.03); ctx.stroke(); });
    ctx.globalAlpha = a;
    const kk = clamp((t - el.t) / 1.6); const v = lerp(0.05, el.v || 0.4, E.out(kk)) + Math.sin(t * 2.3) * 0.04 * kk;
    const ang = Math.PI + v * Math.PI; stroke('white', 6, 12);
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(ang) * (r - 40), y + Math.sin(ang) * (r - 40)); ctx.stroke();
    ctx.beginPath(); ctx.arc(x, y, 12, 0, Math.PI * 2); ctx.fillStyle = COL.white; ctx.fill();
    if (el.label) txt(el.label, x, y + 70, { size: 26, align: 'center', color: el.lcolor || 'blue', spacing: 6 });
    ctx.restore();
  },
  dots(el, t, a) {
    const n = el.n, cols = el.cols, g = el.gap || 20, s = el.size || 11;
    const k = clamp((t - el.t) / 1.0); const shown = Math.floor(n * E.out(k));
    const lit = el.lit, litK = lit && lit.t !== undefined ? clamp((t - lit.t) / 0.8) : 0;
    const r = rng(11); const litSet = new Set(); if (lit) { while (litSet.size < lit.n) litSet.add(Math.floor(r() * n)); }
    ctx.save(); ctx.globalAlpha *= a;
    for (let i = 0; i < shown; i++) {
      const x = el.x + (i % cols) * g, y = el.y + Math.floor(i / cols) * g;
      if (litSet.has(i) && litK > 0) { ctx.fillStyle = COL.green; ctx.shadowColor = COL.green; ctx.shadowBlur = 16 * litK; ctx.fillRect(x - s * 0.1 * litK, y - s * 0.1 * litK, s * (1 + 0.2 * litK), s * (1 + 0.2 * litK)); ctx.shadowBlur = 0; }
      else { ctx.fillStyle = rgba(el.color || 'red', litK > 0 ? lerp(0.55, 0.22, litK) : 0.55); ctx.fillRect(x, y, s, s); }
    }
    ctx.restore();
  },
  line(el, t, a) {
    const k = clamp((t - el.t) / (el.dur || 1.0)); const pts = el.pts, n = pts.length;
    const P = i => [el.x + el.w * i / (n - 1), el.y + el.h - pts[i] * el.h];
    ctx.save(); ctx.globalAlpha *= a;
    if (el.axis) { stroke('gray', 2, 0); ctx.beginPath(); ctx.moveTo(el.x, el.y); ctx.lineTo(el.x, el.y + el.h); ctx.lineTo(el.x + el.w, el.y + el.h); ctx.stroke();
      if (el.axisX) txt(el.axisX, el.x + el.w, el.y + el.h + 46, { size: 24, align: 'right', color: 'dim', spacing: 5 });
      if (el.axisY) txt(el.axisY, el.x, el.y - 22, { size: 24, color: 'dim', spacing: 5 }); }
    const upto = k * (n - 1); const last = Math.floor(upto);
    stroke(el.color || 'red', el.lw || 5, 18); ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(...P(0));
    for (let i = 1; i <= last; i++) ctx.lineTo(...P(i));
    if (last < n - 1) { const p0 = P(last), p1 = P(last + 1), f = upto - last; ctx.lineTo(lerp(p0[0], p1[0], f), lerp(p0[1], p1[1], f)); }
    ctx.stroke();
    if (el.fill) { ctx.lineTo(lerp(el.x, el.x + el.w, k), el.y + el.h); ctx.lineTo(el.x, el.y + el.h); ctx.closePath();
      const g = ctx.createLinearGradient(0, el.y, 0, el.y + el.h); g.addColorStop(0, rgba(el.color || 'red', 0.28)); g.addColorStop(1, rgba(el.color || 'red', 0)); ctx.fillStyle = g; ctx.shadowBlur = 0; ctx.fill(); }
    (el.tags || []).forEach(tg => { if (k * (n - 1) < tg.i) return; const p = P(tg.i); txt(tg.text, p[0] + (tg.dx || 0), p[1] + (tg.dy || -26), { size: 24, align: 'center', color: tg.color || 'dim', spacing: 4 }); });
    ctx.restore();
  },
  candle(el, t, a) {
    // price -> y
    const Y = p => lerp(el.yLo, el.yHi, (p - el.pLo) / (el.pHi - el.pLo));
    let o, h, l, c;
    if (el.keys) { // live path through keyframes
      const ks = el.keys; o = ks[0].p; h = o; l = o; c = o;
      for (let i = 1; i < ks.length; i++) {
        const t0 = ks[i - 1].t, t1 = ks[i].t; if (t <= t0) break;
        const f = clamp((t - t0) / Math.max(0.05, (t1 - t0))); const p = lerp(ks[i - 1].p, ks[i].p, E.inout(f)); c = p; h = Math.max(h, p); l = Math.min(l, p);
      }
      if (t < ks[0].t) return;
    } else { [o, h, l, c] = el.ohlc; }
    const up = c >= o; let cc = col(el.color || (up ? 'green' : 'red'));
    const w = el.w || 150, x = el.x;
    ctx.save(); ctx.globalAlpha *= a * E.out(clamp((t - el.t) / 0.3));
    stroke(cc, 5, 22); ctx.beginPath(); ctx.moveTo(x, Y(h)); ctx.lineTo(x, Y(l)); ctx.stroke();
    const yb = Math.min(Y(o), Y(c)), hb = Math.max(4, Math.abs(Y(o) - Y(c)));
    ctx.fillStyle = el.hollow ? COL.bg : rgba(cc, 0.85); ctx.beginPath(); ctx.rect(x - w / 2, yb, w, hb); ctx.fill(); ctx.stroke();
    if (el.priceTag && el.keys) { txt('$' + c.toFixed(0), x + w / 2 + 40, Y(c) + 12, { font: 'bold', size: 40, color: cc, glow: 14 }); }
    (el.tags || []).forEach(tg => {
      const tk = clamp((t - (tg.t !== undefined ? tg.t : el.t)) / 0.3); if (tk <= 0) return;
      const yy = Y(tg.p), side = tg.side === 'L' ? -1 : 1, x0 = x + side * (w / 2 + 16), x1 = x + side * (w / 2 + 70);
      ctx.save(); ctx.globalAlpha *= tk; stroke(tg.color || 'white', 2, 0); ctx.setLineDash([6, 6]); ctx.beginPath(); ctx.moveTo(x0, yy); ctx.lineTo(x1, yy); ctx.stroke(); ctx.setLineDash([]);
      txt(tg.text, x1 + side * 14, yy + 13, { font: tg.font || 'bold', size: tg.size || 38, align: side < 0 ? 'right' : 'left', color: tg.color || 'white', glow: tg.glow || 0, spacing: 1 });
      ctx.restore(); });
    ctx.restore();
  },
  bracket(el, t, a) {
    const k = E.out(clamp((t - el.t) / 0.35)); if (k <= 0) return;
    ctx.save(); ctx.globalAlpha *= a * k; stroke(el.color || 'green', 3, 14);
    if (el.vertical) { const x = el.x, s = el.side === 'L' ? -1 : 1;
      ctx.beginPath(); ctx.moveTo(x, el.y1); ctx.lineTo(x + 18 * s, el.y1); ctx.lineTo(x + 18 * s, el.y2); ctx.lineTo(x, el.y2); ctx.stroke();
      if (el.text) txt(el.text, x + 40 * s, (el.y1 + el.y2) / 2 + 12, { font: el.font || 'bold', size: el.size || 32, align: s < 0 ? 'right' : 'left', color: el.color || 'green', glow: 14, spacing: 3 }); }
    else { const y = el.y;
      ctx.beginPath(); ctx.moveTo(el.x1, y - 16); ctx.lineTo(el.x1, y); ctx.lineTo(el.x2, y); ctx.lineTo(el.x2, y - 16); ctx.stroke();
      if (el.text) txt(el.text, (el.x1 + el.x2) / 2, y + (el.ty || 56), { font: el.font || 'hero', size: el.size || 56, align: 'center', color: el.color || 'green', glow: 22, split: 2 }); }
    ctx.restore();
  },
  ladder(el, t, a) {
    ctx.save(); ctx.globalAlpha *= a;
    const x = el.x || 160, w = el.w || 760, rh = el.rh || 120;
    el.rows.forEach((r, k) => {
      const rowA = clamp((t - (r.t !== undefined ? r.t : el.t)) / 0.3); if (rowA <= 0) return;
      const ra = r.val ? clamp((t - r.val.t) / 0.3) : rowA; const y = el.y + k * (rh + (el.gap || 0));
      ctx.save(); ctx.globalAlpha *= rowA; stroke(r.color || 'gray', 2.5, 10); ctx.fillStyle = rgba(r.color || 'gray', 0.07); ctx.beginPath(); ctx.roundRect(x, y, w, rh - 16, 12); ctx.fill(); ctx.stroke();
      txt(r.l, x + 36, y + rh / 2 + 6, { font: 'bold', size: 40, color: r.color || 'white', spacing: 4, base: 'middle' });
      if (ra > 0 && r.v) { ctx.save(); ctx.globalAlpha *= ra; txt(r.v, x + w - 36, y + rh / 2 + 4, { font: 'hero', size: 64, align: 'right', color: r.color || 'white', glow: 22, split: 2, base: 'middle' }); ctx.restore(); }
      ctx.restore();
    });
    ctx.restore();
  },
  stamp(el, t, a) {
    const k = clamp((t - el.t) / 0.22), sc = lerp(1.6, 1, E.out(k));
    ctx.save(); ctx.globalAlpha *= a * k; ctx.translate(el.x, el.y); ctx.rotate((el.rot || -6) * Math.PI / 180); ctx.scale(sc, sc);
    const s = el.size || 64, w = measure(el.text, { font: 'hero', size: s, spacing: 4 }) + 60, h = s * 1.45;
    stroke(el.color || 'green', 7, 24); ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2, w, h, 10); ctx.stroke();
    txt(el.text, 0, 4, { font: 'hero', size: s, align: 'center', color: el.color || 'green', glow: 24, base: 'middle', spacing: 4, split: 2 });
    ctx.restore();
  },
  end(el, t, a) {
    const k = E.out(clamp((t - el.t) / 0.5));
    const lw = 460, lh = lw * LOGO.height / LOGO.width, y = 560;
    ctx.save(); ctx.globalAlpha *= a * k; ctx.shadowColor = 'rgba(255,255,255,0.25)'; ctx.shadowBlur = 30;
    ctx.drawImage(LOGO, 540 - lw / 2, y + (1 - k) * 30, lw, lh); ctx.restore();
    ctx.save(); ctx.globalAlpha *= a * clamp((t - el.t - 0.35) / 0.3);
    txt('FREE XTRADES SERVER', 540, y + lh + 120, { font: 'bold', size: 54, align: 'center', color: 'white', spacing: 6, glow: 10 }); ctx.restore();
    ctx.save(); ctx.globalAlpha *= a * clamp((t - el.t - 0.7) / 0.3);
    const bob = Math.sin(t * 5) * 6;
    txt('LINK IN CAPTION', 520, y + lh + 200, { font: 'bold', size: 40, align: 'center', color: 'green', spacing: 6, glow: 16 });
    stroke('green', 4, 12); const ax = 540 + measure('LINK IN CAPTION', { font: 'bold', size: 40, spacing: 6 }) / 2 + 12, ay = y + lh + 172 + bob;
    ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(ax, ay + 30); ctx.moveTo(ax - 12, ay + 18); ctx.lineTo(ax, ay + 30); ctx.lineTo(ax + 12, ay + 18); ctx.stroke(); ctx.restore();
    ctx.save(); ctx.globalAlpha *= a * clamp((t - el.t - 0.9) / 0.3) * 0.6;
    txt('NOT FINANCIAL ADVICE', 540, y + lh + 268, { size: 17, align: 'center', color: 'dim', spacing: 5 }); ctx.restore();
  },
};

// ---------------------------------------------------------------- frame parts
function grid(t) {
  ctx.fillStyle = COL.bg; ctx.fillRect(0, 0, W, H);
  const off = (t * 6) % 60;
  ctx.strokeStyle = 'rgba(255,255,255,0.035)'; ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = -60 + off * 0.3; x < W + 60; x += 60) { ctx.moveTo(x, 0); ctx.lineTo(x, H); }
  for (let y = -60 + off; y < H + 60; y += 60) { ctx.moveTo(0, y); ctx.lineTo(W, y); }
  ctx.stroke();
}
function sceneAt(t) { let i = 0; for (let k = 0; k < S.scenes.length; k++) if (t >= S.scenes[k].t) i = k; return i; }
function headerText(i, key) { return (S.scenes[i].hdr || {})[key] || ''; }
function typed(i, key, t, cps) {
  const s = headerText(i, key); if (i > 0 && headerText(i - 1, key) === s) return s;
  const n = Math.floor((t - S.scenes[i].t) * cps); return s.slice(0, Math.max(0, n));
}
function header(t, i) {
  if (S.scenes[i].noHeader) return;
  const date = typed(i, 'date', t, 22), step = typed(i, 'step', t, 40), lab = typed(i, 'label', t, 40);
  txt(date, 60, 172, { font: 'dot', size: 100, color: 'hdr', glow: 18, spacing: 6 });
  txt(step, 66, 228, { size: 26, color: 'hdrDim', spacing: 5 });
  const sw = measure(headerText(i, 'step'), { size: 26, spacing: 5 });
  if (step) { ctx.save(); ctx.strokeStyle = COL.hdrDim; ctx.lineWidth = 2; ctx.setLineDash([7, 5]); ctx.beginPath(); ctx.moveTo(66, 246); ctx.lineTo(66 + sw - 5, 246); ctx.stroke(); ctx.restore(); }
  if (lab) txt('·   ' + lab, 66 + sw + 30, 228, { size: 26, color: 'hdrDim', spacing: 5 });
  const lw = 140, lh = lw * LOGO.height / LOGO.width;
  ctx.drawImage(LOGO, 1030 - lw, 86, lw, lh);
  if (S.tag) txt(S.tag, 1032, 86 + lh + 44, { size: 26, align: 'right', color: '#cfcfcf', spacing: 3 });
}
function post(t, frame) {
  ctx.save(); ctx.globalAlpha = 1; ctx.drawImage(SCAN, 0, 0);
  ctx.globalAlpha = 0.055; ctx.drawImage(GRAIN[frame % GRAIN.length], 0, 0, W, H);
  ctx.globalAlpha = 1; ctx.drawImage(VIG, 0, 0); ctx.restore();
}
function glitch(t, i, frame) {
  const dt = t - S.scenes[i].t; if (i === 0 || dt > 0.2 || dt < 0) return;
  const amt = 1 - dt / 0.2, r = rng(frame * 31 + 5);
  const g = GLITCH.getContext('2d'); g.clearRect(0, 0, W, H); g.drawImage(cv, 0, 0);
  const tc = TINT.getContext('2d');
  // RGB split of the whole frame
  [['#ff0000', -14], ['#00ffff', 14]].forEach(([c, dx]) => {
    tc.globalCompositeOperation = 'source-over'; tc.clearRect(0, 0, W, H); tc.drawImage(GLITCH, 0, 0);
    tc.globalCompositeOperation = 'multiply'; tc.fillStyle = c; tc.fillRect(0, 0, W, H);
    ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = 0.55 * amt; ctx.drawImage(TINT, dx * amt, 0); ctx.restore();
  });
  // slice displacement
  for (let k = 0; k < 9; k++) {
    const y = Math.floor(r() * H), h = 8 + Math.floor(r() * 70), dx = (r() - 0.5) * 120 * amt;
    ctx.drawImage(GLITCH, 0, y, W, h, dx, y, W, h);
  }
}

function render(t, frame = 0) {
  grid(t);
  const i = sceneAt(t), sc = S.scenes[i];
  const sceneA = 1; // hard cuts with glitch
  (sc.els || []).forEach(el => {
    if (t < el.t) return;
    let a = 1; if (el.tOut !== undefined) a = 1 - clamp((t - el.tOut) / 0.3); if (a <= 0) return;
    const fade = el.type === 'hero' || el.type === 'stamp' ? 1 : clamp((t - el.t) / 0.25);
    ctx.save();
    const dr = el.drift === 0 ? 0 : (el.drift || 1);
    ctx.translate(Math.sin(t * 0.6 + el.ph) * 4 * dr, Math.cos(t * 0.47 + el.ph * 1.3) * 5 * dr);
    DRAW[el.type](el, t, a * fade * sceneA);
    ctx.restore();
  });
  header(t, i);
  post(t, frame);
  glitch(t, i, frame);
}

// SFX events derived from the timeline
function events() {
  const ev = [];
  S.scenes.forEach((sc, i) => {
    if (i > 0) ev.push({ t: sc.t, k: 'thump' });
    ['date', 'step', 'label'].forEach((key, ki) => {
      const s = headerText(i, key); if (!s || (i > 0 && headerText(i - 1, key) === s)) return;
      const cps = key === 'date' ? 22 : 40; const every = key === 'date' ? 1 : 3;
      for (let c = 0; c < s.length; c += every) if (s[c] !== ' ') ev.push({ t: sc.t + c / cps, k: 'tick', g: key === 'date' ? 1 : 0.6 });
    });
    (sc.els || []).forEach(el => {
      if (el.type === 'hero') ev.push({ t: el.t, k: 'impact' });
      else if (el.type === 'stamp') ev.push({ t: el.t, k: 'impact', g: 0.8 });
      else if (el.type === 'arrow' || el.type === 'strike') ev.push({ t: el.t, k: 'whoosh' });
      else if (el.type === 'label' && el.typing !== false) { for (let c = 0; c < el.text.length; c += 3) if (el.text[c] !== ' ') ev.push({ t: el.t + c * 0.028, k: 'tick', g: 0.45 }); }
      else if (el.type === 'rows') el.items.forEach((it, k) => ev.push({ t: it.t !== undefined ? it.t : el.t + k * 0.3, k: 'impact', g: 0.55 }));
      else if (el.type === 'ladder') el.rows.forEach(r => { if (r.val) ev.push({ t: r.val.t, k: 'impact', g: 0.5 }); if (r.t !== undefined) ev.push({ t: r.t, k: 'pop', g: 0.5 }); });
      else if (el.type === 'candle' && el.tags) el.tags.forEach(tg => { if (tg.t !== undefined) ev.push({ t: tg.t, k: 'tick', g: 0.8 }); });
      else if (el.type === 'end') ev.push({ t: el.t, k: 'impact', g: 0.7 });
      else if (['icon', 'prism', 'timeline', 'dots', 'line', 'gauge', 'bracket'].includes(el.type)) ev.push({ t: el.t, k: 'pop', g: 0.5 });
    });
  });
  return ev.filter(e => e.t >= 0 && e.t < S.total).sort((a, b) => a.t - b.t);
}

window.XT = { init, compile, render, events, W, H };
})();
