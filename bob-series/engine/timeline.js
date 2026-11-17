// Generic timeline: lays voice chunks end-to-end with gaps, exposes word cues, collects shots + sfx.

export function buildTimeline(align, EPISODE) {
  const ids = Object.keys(align).sort();
  const G = EPISODE.gaps; let cur = G.pre; const CH = {};
  for (const id of ids) {
    CH[id] = { t0: cur, t1: cur + align[id].dur, words: align[id].words, file: align[id].file };
    const gap = G.after[id] ?? G.default;
    cur = CH[id].t1 + (typeof gap === 'function' ? gap(align) : gap);
  }
  const last = ids[ids.length - 1];
  const duration = CH[last].t1 + G.endHold;
  const cue = (id, w, occ = 1, which = 's') => {
    const c = CH[id]; if (!c) throw new Error('no chunk ' + id);
    let n = 0;
    for (const x of c.words) if (x.w === w && ++n === occ) return c.t0 + x[which];
    throw new Error(`cue not found: ${id} "${w}" #${occ}`);
  };
  const start = (id) => CH[id].t0, end = (id) => CH[id].t1;
  const sfx = [];
  const fx = (n, t, g = 1, extra = {}) => sfx.push({ n, t: +t.toFixed(3), g, ...extra });
  const shots = EPISODE.shots({ cue, start, end, fx, duration, CH });
  shots.sort((a, b) => a.t0 - b.t0);
  shots.forEach((s, i) => { s.t1 = i < shots.length - 1 ? shots[i + 1].t0 : duration; });
  const voice = ids.map((id) => ({ id, t: +CH[id].t0.toFixed(3), file: CH[id].file }));
  return { duration, shots, sfx, voice, CH };
}
