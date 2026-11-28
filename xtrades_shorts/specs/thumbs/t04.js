const area = { yLo: 1340, yHi: 400, pLo: 95, pHi: 108 };
module.exports = { tag: 'CANDLES', thumbT: 2.5, scenes: [ { hdr: {}, els: [
  { type: 'candle', x: 470, w: 240, ohlc: [100, 106, 97, 104], ...area, delay: 0, tags: [
    { side: 'L', p: 104, text: 'C', size: 96, color: 'white', glow: 10 }, { side: 'R', p: 106, text: 'H', size: 96, color: 'white', glow: 10 },
    { side: 'L', p: 100, text: 'O', size: 96, color: 'white', glow: 10 }, { side: 'R', p: 97, text: 'L', size: 96, color: 'white', glow: 10 } ] },
  { type: 'stamp', text: '4 PRICES', x: 540, y: 1480, size: 84, color: 'green', rot: -5, delay: 0.3 },
] } ] };
