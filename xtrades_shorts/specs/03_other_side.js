// Short 3: Who's on the Other Side of Your Trade?
const G = 'green', R = 'red', B = 'blue', N = 'gray';
const ladder = (y, opt = {}) => ({ type: 'ladder', x: 160, y, w: 760, rh: 140, gap: opt.gap || 20, delay: 0,
  rows: [ { l: 'ASK', v: opt.ask || '', color: R, ...(opt.askAt ? { at: opt.askAt } : {}), ...(opt.askV ? { val: { at: opt.askV } } : {}) },
          { l: 'BID', v: opt.bid || '', color: G, ...(opt.bidAt ? { at: opt.bidAt } : {}), ...(opt.bidV ? { val: { at: opt.bidV } } : {}) } ] });
module.exports = {
  tag: 'ORDER FLOW',
  scenes: [
    { hdr: { date: '9:30', step: 'STEP 1', label: 'THE ROUTE' }, els: [
      { type: 'icon', name: 'phone', x: 220, y: 1060, s: 1.4, color: G, button: 'BUY', delay: 0.1 },
      { type: 'hero', text: '90%+', color: 'white', y: 560, size: 230, count: true, at: '90%', sub: 'SEC · 2022', split: 5 },
      { type: 'icon', name: 'building', x: 810, y: 1040, s: 1.3, color: N, label: 'NYSE · NASDAQ', ly: 140, lsize: 24, lcolor: 'dim', at: 'stock' },
      { type: 'arrow', x1: 340, y1: 1010, x2: 660, y2: 1010, color: N, dash: true, at: 'not' },
      { type: 'icon', name: 'cross', x: 500, y: 1010, s: 1.4, color: R, at: 'exchange.' },
    ]},
    { at: 'They go to', hdr: { date: '9:30', step: 'STEP 1', label: 'THE ROUTE' }, els: [
      { type: 'icon', name: 'phone', x: 220, y: 1060, s: 1.4, color: G, button: 'BUY', delay: 0 },
      { type: 'icon', name: 'server', x: 810, y: 1120, s: 1.3, stack: 3, color: B, label: 'MARKET MAKERS', ly: 75, lsize: 24, at: 'small' },
      { type: 'arrow', x1: 340, y1: 1010, x2: 660, y2: 1010, color: G, at: 'go' },
    ]},
    { at: 'Every stock has', hdr: { date: '9:30', step: 'STEP 2', label: 'THE SPREAD' }, els: [
      ladder(640, { bidAt: 'bid,', askAt: 'ask,' }),
    ]},
    { at: 'Say a stock', hdr: { date: '9:30', step: 'STEP 2', label: 'EXAMPLE' }, els: [
      ladder(640, { bid: '$10.00', ask: '$10.02', bidV: '$10.00', askV: '$10.02.' }),
    ]},
    { at: 'The wholesaler can', hdr: { date: '9:30', step: 'STEP 2', label: 'EXAMPLE' }, els: [
      { type: 'icon', name: 'person', x: 190, y: 1140, s: 1.4, color: G, label: 'YOU', ly: 100, lsize: 26, delay: 0.05 },
      { type: 'icon', name: 'server', x: 540, y: 1220, s: 1.1, stack: 3, color: B, delay: 0.1 },
      { type: 'icon', name: 'person', x: 890, y: 1140, s: 1.4, color: N, label: 'TRADER', ly: 100, lsize: 26, lcolor: 'dim', at: 'someone' },
      { type: 'arrow', x1: 440, y1: 1010, x2: 270, y2: 1010, color: R, at: 'sell', label: '$10.02', lsize: 34, ly: -34 },
      { type: 'arrow', x1: 810, y1: 1010, x2: 640, y2: 1010, color: G, at: 'buy', label: '$10.00', lsize: 34, ly: -34 },
      { type: 'hero', text: '$0.02', color: G, y: 560, size: 200, at: 'gap.', sub: 'THE SPREAD' },
    ]},
    { at: 'Then it pays', hdr: { date: '9:30', step: 'STEP 3', label: 'THE FEE' }, els: [
      { type: 'icon', name: 'server', x: 300, y: 1130, s: 1.2, stack: 3, color: B, delay: 0.05 },
      { type: 'icon', name: 'building', x: 800, y: 1040, s: 1.3, color: B, label: 'BROKER', ly: 140, lsize: 26, at: 'broker' },
      { type: 'arrow', x1: 430, y1: 1000, x2: 650, y2: 1000, color: G, at: 'pays' },
      { type: 'icon', name: 'coin', x: 540, y: 900, s: 0.6, stack: 3, color: G, at: 'fee' },
      { type: 'label', text: 'PFOF', y: 600, font: 'hero', size: 150, color: B, glow: 26, at: 'payment', typing: false },
    ]},
    { at: 'That fee is', hdr: { date: '9:30', step: 'STEP 3', label: 'THE FEE' }, els: [
      { type: 'hero', text: '$0', color: G, y: 760, size: 330, at: 'zero', sub: 'PER TRADE' },
    ]},
    { at: 'By law,', hdr: { date: '9:30', step: 'STEP 3', label: 'THE RULE' }, els: [
      { type: 'hero', text: 'NBBO', color: B, y: 560, size: 170, at: 'best', sub: 'REG NMS', split: 4 },
      ladder(800, { bid: '$10.00', ask: '$10.02' }),
    ]},
    { at: 'The trap is', hdr: { date: '9:30', step: 'STEP 4', label: 'THE TRAP' }, els: [
      ladder(560, { gap: 380 }),
      { type: 'bracket', vertical: true, x: 950, y1: 680, y2: 1080, side: 'R', color: R, at: 'huge,' },
    ]},
    { at: 'A limit order', hdr: { date: '9:30', step: 'STEP 4', label: 'THE FIX' }, els: [
      ladder(560, { gap: 380 }),
      { type: 'strike', x1: 180, y1: 880, x2: 900, y2: 880, color: G, lw: 6, at: 'set' },
      { type: 'icon', name: 'lock', x: 540, y: 880, s: 1.2, color: G, at: 'most' },
    ]},
    { at: 'More breakdowns', hdr: {}, els: [ { type: 'end', at: 'More' } ] },
  ],
};
