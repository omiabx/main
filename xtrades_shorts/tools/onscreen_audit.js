// Lists every on-screen string per scene and flags labels that restate the narration.
// Usage: node tools/onscreen_audit.js <spec.js> <script.txt> <words.json>  -> prints JSON report
const fs = require('fs'), path = require('path');
const spec = require(path.resolve(process.argv[2]));
const words = JSON.parse(fs.readFileSync(process.argv[4]));
const norm = s => s.toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9$%.,' ]/g, ' ').replace(/[.,](\s|$)/g, ' ').split(/\s+/).filter(Boolean);
const toks = words.map(w => norm(w.w)[0] || '');
const find = (phrase, from) => { const p = norm(phrase); for (let i = from; i < toks.length; i++) { if (p.every((x, k) => toks[i + k] === x)) return i; } return -1; };
const KEYS = ['text', 'label', 'sub', 'top', 'big', 'button', 'v', 'l'];
let cursor = 0; const out = [];
spec.scenes.forEach((sc, i) => {
  const idx = i === 0 ? 0 : find(sc.at, cursor); cursor = idx;
  const next = i + 1 < spec.scenes.length ? find(spec.scenes[i + 1].at, idx) : toks.length;
  const narr = words.slice(idx, next).map(w => w.w).join(' ');
  const nt = norm(narr);
  const strings = new Set();
  const walk = o => { if (Array.isArray(o)) return o.forEach(walk); if (!o || typeof o !== 'object') return;
    for (const k of KEYS) if (typeof o[k] === 'string' && o[k].trim()) strings.add(o[k].trim());
    for (const k in o) if (typeof o[k] === 'object') walk(o[k]); };
  walk(sc.els || []);
  if (sc.hdr) ['date', 'step', 'label'].forEach(k => sc.hdr[k] && strings.add(`[hdr] ${sc.hdr[k]}`));
  const flags = [];
  for (const s of strings) {
    if (s.startsWith('[hdr]')) continue;
    const lt = norm(s).filter(w => !['the', 'a', 'of', 'to', '·', '/'].includes(w));
    if (lt.length >= 2) { // any 2 consecutive label words spoken consecutively in this scene?
      for (let k = 0; k + 1 < lt.length; k++) { const j = nt.findIndex((w, m) => w === lt[k] && nt[m + 1] === lt[k + 1]); if (j >= 0) { flags.push(`RESTATES: "${s}"`); break; } }
    } else if (lt.length === 1 && !/[0-9$%]/.test(lt[0]) && nt.includes(lt[0])) flags.push(`object label also spoken: "${s}"`);
  }
  out.push({ scene: i + 1, narration: narr, onscreen: [...strings], flags });
});
console.log(JSON.stringify(out, null, 1));
