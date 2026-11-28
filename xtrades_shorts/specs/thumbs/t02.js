const fall = [0.82, 0.86, 0.74, 0.78, 0.63, 0.67, 0.55, 0.58, 0.44, 0.47, 0.36, 0.30, 0.33, 0.22, 0.18];
module.exports = { tag: 'DAY TRADING', thumbT: 4, scenes: [ { hdr: {}, els: [
  { type: 'line', x: 100, y: 980, w: 880, h: 420, pts: fall, color: 'red', fill: true, dur: 0.5, delay: 0 },
  { type: 'hero', text: '97%', color: 'red', y: 720, size: 360, delay: 0, split: 8 },
  { type: 'label', text: 'LOST MONEY', y: 990, font: 'hero', size: 96, color: 'white', glow: 18, typing: false, delay: 0 },
  { type: 'stamp', text: 'THE DATA', x: 540, y: 1480, size: 76, color: 'green', rot: -5, delay: 0.3 },
] } ] };
