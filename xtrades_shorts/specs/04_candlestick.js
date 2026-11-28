// Short 4: How to Read a Candlestick in 60 Seconds
const G = 'green', R = 'red', B = 'blue', N = 'gray';
const area = { yLo: 1330, yHi: 520, pLo: 95, pHi: 108 };
const big = (extra = {}) => ({ type: 'candle', x: 540, w: 180, ohlc: [100, 106, 97, 104], ...area, ...extra });
module.exports = {
  tag: 'CANDLES',
  scenes: [
    { hdr: { date: '9:30', step: 'STEP 1', label: 'ONE CANDLE' }, els: [
      big({ at: 'candle', tags: [
        { at: 'open,', side: 'L', p: 100, text: 'O', size: 60, color: 'white' }, { at: 'high,', side: 'R', p: 106, text: 'H', size: 60, color: 'white' },
        { at: 'low,', side: 'R', p: 97, text: 'L', size: 60, color: 'white' }, { at: 'close.', side: 'L', p: 104, text: 'C', size: 60, color: 'white' } ] }),
    ]},
    { at: 'The thick part', hdr: { date: '9:30', step: 'STEP 1', label: 'ONE CANDLE' }, els: [
      big({ delay: 0, tags: [ { side: 'R', p: 100, text: 'O', size: 60, color: 'white' }, { side: 'R', p: 104, text: 'C', size: 60, color: 'white' } ] }),
      { type: 'bracket', vertical: true, x: 410, y1: 520 + (108 - 104) / 13 * 810, y2: 520 + (108 - 100) / 13 * 810, side: 'L', color: G, at: 'body,' },
    ]},
    { at: 'If the close is above', hdr: { date: '9:30', step: 'STEP 2', label: 'THE COLOR' }, els: [
      { type: 'candle', x: 400, w: 170, ohlc: [99, 105, 98, 104], ...area, at: 'above' },
      { type: 'icon', name: 'arrow-up', x: 780, y: 880, s: 2.2, color: G, at: 'buyers' },
    ]},
    { at: 'If the close is below', hdr: { date: '9:30', step: 'STEP 2', label: 'THE COLOR' }, els: [
      { type: 'candle', x: 400, w: 170, ohlc: [104, 105, 98, 99], ...area, at: 'below' },
      { type: 'icon', name: 'arrow-down', x: 780, y: 880, s: 2.2, color: R, at: 'sellers' },
    ]},
    { at: 'The thin lines', hdr: { date: '9:30', step: 'STEP 2', label: 'THE WICKS' }, els: [
      big({ delay: 0, tags: [ { at: 'highest', side: 'R', p: 106, text: 'H', size: 60, color: 'white' }, { at: 'lowest', side: 'R', p: 97, text: 'L', size: 60, color: 'white' } ] }),
    ]},
    { at: 'Say a stock opens', hdr: { date: '9:30', step: 'STEP 3', label: 'EXAMPLE' }, els: [
      { type: 'candle', x: 470, w: 180, ...area, priceTag: true, keys: [ { at: 'opens', p: 100 }, { at: '$106,', p: 106 }, { at: '$97,', p: 97 }, { at: '$104.', p: 104 } ] },
    ]},
    { at: 'You get a green body', hdr: { date: '4:00', step: 'STEP 3', label: 'EXAMPLE' }, els: [
      big({ x: 470, delay: 0, tags: [
        { at: '$100', side: 'L', p: 100, text: '$100', color: G, glow: 10 }, { at: '$104,', side: 'L', p: 104, text: '$104', color: G, glow: 10 },
        { at: '$106', side: 'R', p: 106, text: '$106', color: 'white' }, { at: '$97.', side: 'R', p: 97, text: '$97', color: 'white' } ] }),
    ]},
    { at: 'A long top wick', hdr: { date: '4:00', step: 'STEP 3', label: 'THE WICKS' }, els: [
      { type: 'candle', x: 420, w: 170, ohlc: [100, 107.2, 99.4, 101], ...area, at: 'long' },
      { type: 'icon', name: 'arrow-up', x: 790, y: 680, s: 1.8, color: G, at: 'pushed' },
      { type: 'icon', name: 'arrow-down', x: 790, y: 1020, s: 1.8, color: R, at: 'could' },
    ]},
    { at: 'The trap is', hdr: { date: '4:00', step: 'STEP 4', label: 'THE TRAP' }, els: [
      { type: 'icon', name: 'phone', x: 220, y: 820, s: 1.35, color: N, candles: 'normal', delay: 0.1 },
      { type: 'icon', name: 'phone', x: 540, y: 820, s: 1.35, color: N, candles: 'flip', at: 'flip' },
      { type: 'icon', name: 'phone', x: 860, y: 820, s: 1.35, color: N, candles: 'hollow', at: 'hollow' },
      { type: 'label', text: '■ UP', x: 400, y: 1260, font: 'bold', size: 46, color: G, at: 'legend', typing: false },
      { type: 'label', text: '■ DOWN', x: 690, y: 1260, font: 'bold', size: 46, color: R, at: 'legend', dt: 0.15, typing: false },
    ]},
    { at: 'More breakdowns', hdr: {}, els: [ { type: 'end', at: 'More' } ] },
  ],
};
