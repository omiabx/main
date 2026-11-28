// Short 2: Can You Really Day Trade for a Living?
const G = 'green', R = 'red', B = 'blue', N = 'gray';
const fall = [0.82, 0.86, 0.74, 0.78, 0.63, 0.67, 0.55, 0.58, 0.44, 0.47, 0.36, 0.30, 0.33, 0.22, 0.18];
const flat = [0.40, 0.46, 0.38, 0.44, 0.36, 0.43, 0.39, 0.45, 0.37, 0.42, 0.38, 0.44, 0.36, 0.41, 0.39];
module.exports = {
  tag: 'DAY TRADING',
  scenes: [
    { hdr: { date: '2013', step: 'STEP 1', label: 'THE STUDY' }, els: [
      { type: 'line', x: 140, y: 920, w: 800, h: 380, pts: fall, color: R, fill: true, dur: 3.0, delay: 0.1 },
      { type: 'hero', text: '97%', color: R, y: 620, size: 270, count: true, at: '97%', sub: 'CHAGUE ET AL. · 2019' },
    ]},
    { at: 'Three economists', hdr: { date: '2013-15', step: 'STEP 1', label: 'THE STUDY' }, els: [
      ...['CHAGUE', 'DE-LOSSO', 'GIOVANNETTI'].map((n, k) => ({ type: 'icon', name: 'person', x: 220 + k * 320, y: 840, s: 1.6, color: B, label: n, ly: 100, lsize: 24, at: 'Three', dt: k * 0.18 })),
    ]},
    { at: 'Only 1,551', hdr: { date: 'DAY 300', step: 'STEP 1', label: 'THE STUDY' }, els: [
      { type: 'hero', text: '1,551', color: 'white', y: 520, size: 180, count: true, at: '1,551', split: 4 },
      { type: 'dots', x: 200, y: 700, cols: 40, n: 1551, gap: 17, size: 10, color: N, at: '1,551' },
    ]},
    { at: 'Out of that group,', hdr: { date: 'DAY 300', step: 'STEP 1', label: 'THE STUDY' }, els: [
      { type: 'dots', x: 200, y: 700, cols: 40, n: 1551, gap: 17, size: 10, color: R, lit: { n: 17, at: '17' }, delay: 0 },
      { type: 'hero', text: '17', color: G, x: 330, y: 520, size: 190, count: true, at: '17' },
      { type: 'label', text: '$16 / DAY', x: 740, y: 545, font: 'bold', size: 54, color: G, glow: 14, at: '$16' },
    ]},
    { at: 'The researchers also', hdr: { date: 'DAY 300', step: 'STEP 2', label: 'THE PATTERN' }, els: [
      { type: 'line', x: 140, y: 620, w: 800, h: 560, pts: flat, color: B, dur: 1.6, axis: true, axisX: 'TRADES', axisY: 'SKILL', at: 'better' },
    ]},
    { at: 'Part of the reason', hdr: { date: 'DAY 300', step: 'STEP 2', label: 'THE PATTERN' }, els: [
      { type: 'icon', name: 'person', x: 250, y: 1060, s: 1.5, color: G, label: 'YOU', ly: 100, lsize: 28, delay: 0.1 },
      { type: 'icon', name: 'server', x: 760, y: 1120, s: 1.5, stack: 4, color: B, label: 'HFT', ly: 70, lsize: 40, at: 'firms' },
      { type: 'arrow', x1: 640, y1: 760, x2: 360, y2: 860, color: B, at: 'faster', dur: 0.2 },
      { type: 'arrow', x1: 640, y1: 840, x2: 360, y2: 940, color: B, at: 'faster', dt: 0.15, dur: 0.2 },
    ]},
    { at: 'This study covers', hdr: { date: '2013-15', step: 'STEP 2', label: 'THE LIMITS' }, els: [
      ...[0, 1, 2, 3, 4, 5].map(k => ({ type: 'prism', x: 300 + (k % 3) * 240, y: 860 + Math.floor(k / 3) * 300, w: 110, d: 110, h: k === 1 ? 160 : 70, color: k === 1 ? G : N, fill: k === 1 ? 0.18 : 0.05, label: k === 1 ? 'BRAZIL' : '', lsize: 28, delay: 0.1 + k * 0.08 })),
    ]},
    { at: 'It does show', hdr: { date: '2013-15', step: 'STEP 2', label: 'THE LIMITS' }, els: [
      { type: 'hero', text: '1.1%', color: G, y: 760, size: 250, count: true, at: 'rare', sub: '17 OF 1,551' },
    ]},
    { at: 'The trap is', hdr: { date: 'MONTH 1', step: 'STEP 3', label: 'THE TRAP' }, els: [
      { type: 'line', x: 140, y: 700, w: 170, h: 520, pts: [0.35, 0.45, 0.58, 0.72, 0.85], color: G, dur: 0.8, at: 'good' },
      { type: 'line', x: 310, y: 700, w: 630, h: 520, pts: [0.85, 0.62, 0.7, 0.45, 0.55, 0.32, 0.4, 0.2, 0.28, 0.12], color: N, dur: 1.6, at: 'tells' },
    ]},
    { at: 'Start small', hdr: { date: 'DAY 1', step: 'STEP 3', label: 'THE PLAN' }, els: [
      { type: 'icon', name: 'notebook', x: 540, y: 860, s: 2.2, color: G, write: true, at: 'write' },
    ]},
    { at: 'More breakdowns', hdr: {}, els: [ { type: 'end', at: 'More' } ] },
  ],
};
