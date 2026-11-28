// Short 1: How Much Money Do You Need to Day Trade?
const G = 'green', R = 'red', B = 'blue', N = 'gray';
const days = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
module.exports = {
  tag: 'DAY TRADING',
  scenes: [
    { hdr: { date: 'JUN 4', step: 'STEP 1', label: 'THE OLD RULE' }, els: [
      { type: 'icon', name: 'calendar', x: 540, y: 760, s: 2.0, color: G, top: 'JUNE', big: '4', bigSize: 84, label: '2026', ly: 135, lsize: 40, delay: 0.1, out: '$25,000' },
      { type: 'hero', text: '$25,000', color: R, y: 760, size: 200, count: true, at: '$25,000', sub: 'FINRA RULE 4210' },
      { type: 'strike', x1: 120, y1: 830, x2: 960, y2: 690, at: 'removed.' },
    ]},
    { at: 'Day trading means', hdr: { date: '9:30', step: 'STEP 1', label: 'THE BASICS' }, els: [
      { type: 'icon', name: 'chip', x: 540, y: 640, s: 2.0, color: B, at: 'stock' },
      { type: 'timeline', x1: 140, x2: 940, y: 1080, at: 'Day', ticks: [{ f: 0, label: '9:30' }, { f: 1, label: '4:00' }],
        marks: [{ f: 0.25, kind: 'up', color: G, at: 'buy' }, { f: 0.7, kind: 'down', color: R, at: 'sell' }] },
    ]},
    { at: 'Under the old rule,', hdr: { date: '2001', step: 'STEP 1', label: 'THE OLD RULE' }, els: [
      ...days.map((d, k) => ({ type: 'prism', x: 185 + k * 178, y: 800, w: 92, d: 92, h: 110, color: N, fill: 0.06, label: d, lcolor: 'dim', lsize: 24, delay: 0.1 + k * 0.06 })),
      ...[0, 1, 2, 3].map(k => ({ type: 'prism', x: 185 + k * 178, y: 800, w: 92, d: 92, h: 110, color: G, fill: 0.18, at: 'four', dt: k * 0.16, dur: 0.3 })),
      { type: 'label', text: '4 / 5', y: 560, font: 'hero', size: 80, color: G, glow: 20, at: 'five' },
      { type: 'icon', name: 'person', x: 340, y: 1200, s: 1.7, color: R, label: 'PDT', ly: 100, lsize: 40, at: 'pattern' },
      { type: 'icon', name: 'lock', x: 760, y: 1180, s: 1.6, color: R, label: '$25,000', ly: 110, lsize: 44, at: '$25,000' },
    ]},
    { at: 'The new rule checks', hdr: { date: 'JUN 4', step: 'STEP 2', label: 'THE NEW RULE' }, els: [
      { type: 'label', text: '4 / 5', y: 540, font: 'hero', size: 80, color: N, typing: false, delay: 0.05 },
      { type: 'strike', x1: 400, y1: 535, x2: 680, y2: 485, lw: 10, at: 'instead' },
      { type: 'gauge', x: 540, y: 1060, r: 320, v: 0.45, label: 'INTRADAY MARGIN', at: 'risk' },
    ]},
    { at: 'You still need', hdr: { date: 'JUN 4', step: 'STEP 2', label: 'THE NEW RULE' }, els: [
      { type: 'hero', text: '$2,000', color: B, y: 620, size: 200, count: true, at: '$2,000', sub: 'MINIMUM EQUITY' },
      { type: 'icon', name: 'building', x: 280, y: 1100, s: 1.5, color: B, label: 'BROKER', ly: 135, lsize: 28, at: 'broker' },
      { type: 'icon', name: 'person', x: 810, y: 1120, s: 1.7, color: G, label: 'YOU', ly: 100, lsize: 28, at: 'borrow' },
      { type: 'arrow', x1: 470, y1: 1100, x2: 690, y2: 1100, color: B, at: 'borrow', dt: 0.2 },
    ]},
    { at: 'With a cash account,', hdr: { date: 'JUN 4', step: 'STEP 2', label: 'THE NEW RULE' }, els: [
      { type: 'prism', x: 430, y: 1130, w: 250, d: 210, h: 240, color: G, segs: 5, label: 'NO MARGIN', ly: 30, lsize: 28, at: 'cash' },
      { type: 'icon', name: 'clock', x: 790, y: 640, s: 1.6, color: B, spin: true, label: 'T+1', ly: 125, lsize: 48, at: 'settle.' },
    ]},
    { at: 'Say you buy', hdr: { date: '9:30', step: 'STEP 2', label: 'EXAMPLE' }, els: [
      { type: 'icon', name: 'coin', x: 540, y: 720, s: 1.6, stack: 5, color: G, label: '$500', ly: 105, lsize: 56, at: '$500' },
      { type: 'timeline', x1: 140, x2: 940, y: 1180, at: 'Say', ticks: [{ f: 0, label: '9:30' }, { f: 1, label: '12:00' }],
        marks: [{ f: 0.2, kind: 'up', color: G, at: 'buy' }, { f: 0.75, kind: 'down', color: R, at: 'sell' }] },
    ]},
    { at: 'If you buy again', hdr: { date: '9:30', step: 'STEP 2', label: 'EXAMPLE' }, els: [
      { type: 'icon', name: 'hourglass', x: 310, y: 880, s: 2.2, color: N, label: 'T+1', ly: 100, lsize: 44, lcolor: 'dim', at: 'settles,' },
      { type: 'icon', name: 'flag', x: 760, y: 880, s: 2.4, color: R, label: 'GFV', ly: 95, lsize: 56, at: 'mark' },
    ]},
    { at: 'The trap is', hdr: { date: 'OCT 20', step: 'STEP 3', label: 'THE CATCH' }, els: [
      ...[0, 1, 2, 3, 4, 5].map(k => ({ type: 'icon', name: 'phone', x: 250 + (k % 3) * 290, y: 620 + Math.floor(k / 3) * 380, s: 1.05, color: k < 2 ? G : N, delay: 0.1 + k * 0.07 })),
      ...[0, 1].map(k => ({ type: 'icon', name: 'check', x: 250 + k * 290, y: 620, s: 1.5, color: G, at: 'switched', dt: k * 0.12 })),
      ...[2, 3, 4, 5].map(k => ({ type: 'icon', name: 'hourglass', x: 250 + (k % 3) * 290, y: 620 + Math.floor(k / 3) * 380, s: 0.7, color: 'amber', at: 'switched', dt: 0.3 + k * 0.08 })),
      { type: 'hero', text: '2027', color: B, y: 1330, size: 150, at: '2027', split: 3 },
    ]},
    { at: 'More breakdowns', hdr: {}, els: [ { type: 'end', at: 'More' } ] },
  ],
};
