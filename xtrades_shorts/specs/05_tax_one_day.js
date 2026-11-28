// Short 5: Why Holding a Stock One Extra Day Can Cut Your Tax
const G = 'green', R = 'red', B = 'blue', N = 'gray';
const bar = (x, h, color, top, at, extra = {}) => ({ type: 'prism', x, y: 1260, w: 110, d: 110, h, color, segs: Math.max(1, Math.round(h / 45)), top, tsize: 54, at, ...extra });
module.exports = {
  tag: 'TAXES',
  scenes: [
    { hdr: { date: 'MAR 3', step: 'STEP 1', label: 'SHORT-TERM' }, els: [
      { type: 'icon', name: 'calendar', x: 540, y: 760, s: 2.0, color: G, top: 'MARCH', big: '3', bigSize: 84, delay: 0.1, out: '37%.' },
      { type: 'hero', text: '37%', color: R, y: 740, size: 280, count: true, at: '37%.', sub: 'TOP FEDERAL RATE · 2026' },
    ]},
    { at: 'Hold it for', hdr: { date: 'MAR 4', step: 'STEP 2', label: 'LONG-TERM' }, els: [
      bar(210, 370, R, '37%', undefined, { delay: 0.1, label: '< 1 YR', lsize: 26 }),
      bar(470, 4, G, '0%', '0%,', { label: '> 1 YR', lsize: 26 }),
      bar(690, 150, G, '15%', '15%'),
      bar(910, 200, G, '20%', '20%.'),
    ]},
    { at: 'In 2026,', hdr: { date: 'MAR 4', step: 'STEP 2', label: 'LONG-TERM' }, els: [
      { type: 'hero', text: '$49,450', color: G, y: 640, size: 170, count: true, at: '$49,450.', sub: 'REV. PROC. 2025-32' },
      { type: 'icon', name: 'person', x: 540, y: 1110, s: 1.6, color: G, label: '0%', ly: 100, lsize: 56, at: 'single' },
    ]},
    { at: 'Say you are', hdr: { date: 'MAR 4', step: 'STEP 3', label: 'EXAMPLE' }, els: [
      { type: 'hero', text: '22%', color: B, y: 540, size: 170, at: '22%', split: 3 },
      { type: 'icon', name: 'coin', x: 540, y: 1000, s: 1.6, stack: 6, color: G, label: '$10,000', ly: 110, lsize: 56, at: '$10,000' },
    ]},
    { at: 'If you sell too early,', hdr: { date: 'MAR 4', step: 'STEP 3', label: 'EXAMPLE' }, els: [
      bar(400, 330, R, '$2,200', '$2,200', { w: 150, d: 150, label: '< 1 YR', lsize: 28 }),
    ]},
    { at: 'If you hold past', hdr: { date: 'MAR 4', step: 'STEP 3', label: 'EXAMPLE' }, els: [
      bar(400, 330, R, '$2,200', undefined, { w: 150, d: 150, label: '< 1 YR', lsize: 28, delay: 0, grow: false }),
      bar(760, 225, G, '$1,500', '$1,500,', { w: 150, d: 150, label: '> 1 YR', lsize: 28 }),
      { type: 'hero', text: '+$700', color: G, y: 520, size: 170, at: '$700' },
    ]},
    { at: 'The trap is', hdr: { date: 'MAR 3', step: 'STEP 4', label: 'THE TRAP' }, els: [
      { type: 'timeline', x1: 140, x2: 940, y: 1000, at: 'days', ticks: [{ f: 0, label: 'MAR 3' }, { f: 0.3, label: 'MAR 4' }, { f: 1, label: '+1 YR' }],
        marks: [{ f: 0, kind: 'up', color: G, at: 'buy.' }] },
      { type: 'icon', name: 'clock', x: 380, y: 700, s: 1.3, color: B, spin: true, at: 'clock' },
    ]},
    { at: 'If you bought', hdr: { date: 'MAR 3', step: 'STEP 4', label: 'THE TRAP' }, els: [
      { type: 'icon', name: 'calendar', x: 300, y: 820, s: 1.7, color: R, top: 'MAR', big: '3', label: '+1 YR', ly: 130, lsize: 36, at: 'selling' },
      { type: 'icon', name: 'cross', x: 300, y: 1200, s: 1.6, color: R, at: 'short-term,' },
    ]},
    { at: 'so you would', hdr: { date: 'MAR 4', step: 'STEP 4', label: 'THE FIX' }, els: [
      { type: 'icon', name: 'calendar', x: 300, y: 820, s: 1.7, color: R, top: 'MAR', big: '3', label: '+1 YR', ly: 130, lsize: 36, delay: 0 },
      { type: 'icon', name: 'cross', x: 300, y: 1200, s: 1.6, color: R, delay: 0 },
      { type: 'icon', name: 'calendar', x: 780, y: 820, s: 1.7, color: G, top: 'MAR', big: '4', label: '+1 YR', ly: 130, lsize: 36, at: 'until' },
      { type: 'icon', name: 'check', x: 780, y: 1200, s: 1.6, color: G, at: 'until', dt: 0.35 },
    ]},
    { at: 'Your state', hdr: { date: 'MAR 4', step: 'STEP 4', label: 'ALSO' }, els: [
      { type: 'prism', x: 540, y: 1160, w: 230, d: 230, h: 180, color: B, segs: 3, label: 'FEDERAL', ly: 10, lsize: 28, delay: 0.1 },
      { type: 'prism', x: 540, y: 980, w: 230, d: 230, h: 110, color: 'amber', segs: 2, top: 'STATE', tsize: 44, at: 'state' },
    ]},
    { at: 'More breakdowns', hdr: {}, els: [ { type: 'end', at: 'More' } ] },
  ],
};
