// Voxel builder + mesher with baked ambient occlusion.
import * as THREE from 'three';

const K = (x, y, z) => ((x + 1024) * 2048 + (y + 1024)) * 2048 + (z + 1024);

export function rgb(r, g, b) { return (r << 16) | (g << 8) | b; }

// deterministic RNG
export function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}
export function hash3(x, y, z) {
  let h = (x * 374761393 + y * 668265263 + z * 2147483647) | 0;
  h = (h ^ (h >>> 13)) * 1274126177 | 0;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
// tint a color int by factor f (multiplicative) with optional jitter
export function shade(c, f) {
  const r = Math.min(255, Math.max(0, Math.round(((c >> 16) & 255) * f)));
  const g = Math.min(255, Math.max(0, Math.round(((c >> 8) & 255) * f)));
  const b = Math.min(255, Math.max(0, Math.round((c & 255) * f)));
  return (r << 16) | (g << 8) | b;
}
export function mix(a, b, t) {
  const f = (s) => [(s >> 16) & 255, (s >> 8) & 255, s & 255];
  const A = f(a), B = f(b);
  return rgb(...A.map((v, i) => Math.round(v + (B[i] - v) * t)));
}
export function desat(c, amt, dim) {
  const r = (c >> 16) & 255, g = (c >> 8) & 255, b = c & 255;
  const l = 0.3 * r + 0.59 * g + 0.11 * b;
  const m = (v) => Math.round((v + (l - v) * amt) * dim);
  return rgb(m(r), m(g), m(b));
}

export class VB {
  constructor() { this.m = new Map(); }
  set(x, y, z, c) { if (c == null) this.m.delete(K(x, y, z)); else this.m.set(K(x, y, z), { x, y, z, c }); return this; }
  get(x, y, z) { const v = this.m.get(K(x, y, z)); return v ? v.c : undefined; }
  has(x, y, z) { return this.m.has(K(x, y, z)); }
  // inclusive box; c may be a color or fn(x,y,z)->color|null
  box(x0, y0, z0, x1, y1, z1, c) {
    for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++)
      for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++)
        for (let z = Math.min(z0, z1); z <= Math.max(z0, z1); z++)
          this.set(x, y, z, typeof c === 'function' ? c(x, y, z) : c);
    return this;
  }
  // paint only existing voxels
  paint(x0, y0, z0, x1, y1, z1, c) {
    for (let x = Math.min(x0, x1); x <= Math.max(x0, x1); x++)
      for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++)
        for (let z = Math.min(z0, z1); z <= Math.max(z0, z1); z++)
          if (this.has(x, y, z)) this.set(x, y, z, typeof c === 'function' ? c(x, y, z) : c);
    return this;
  }
  each(fn) { for (const v of this.m.values()) fn(v.x, v.y, v.z, v.c); }
  map(fn) { for (const v of this.m.values()) v.c = fn(v.x, v.y, v.z, v.c); return this; }
  // returns BufferGeometry. opts: scale, offset [x,y,z] (in voxel units, subtracted), ao strength
  geometry(opts = {}) {
    const s = opts.scale ?? 1, off = opts.offset ?? [0, 0, 0], aoS = opts.ao ?? 1;
    const AO = [0.52, 0.7, 0.85, 1.0].map((v) => 1 - (1 - v) * aoS);
    const pos = [], nor = [], col = [], idx = [];
    const dirs = [
      { n: [1, 0, 0], u: [0, 1, 0], v: [0, 0, 1] }, { n: [-1, 0, 0], u: [0, 0, 1], v: [0, 1, 0] },
      { n: [0, 1, 0], u: [0, 0, 1], v: [1, 0, 0] }, { n: [0, -1, 0], u: [1, 0, 0], v: [0, 0, 1] },
      { n: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0] }, { n: [0, 0, -1], u: [0, 1, 0], v: [1, 0, 0] },
    ];
    const tmp = new THREE.Color();
    const has = (x, y, z) => this.m.has(K(x, y, z));
    for (const vx of this.m.values()) {
      const { x, y, z, c } = vx;
      tmp.setHex(c); // converts sRGB -> linear working space
      for (const d of dirs) {
        const [nx, ny, nz] = d.n;
        if (has(x + nx, y + ny, z + nz)) continue;
        // face origin: voxel occupies [x,x+1]; face on positive side if n positive
        const ox = x + (nx > 0 ? 1 : 0), oy = y + (ny > 0 ? 1 : 0), oz = z + (nz > 0 ? 1 : 0);
        const corners = [[0, 0], [1, 0], [1, 1], [0, 1]];
        const base = pos.length / 3; const aos = [];
        for (const [a, b] of corners) {
          const px = ox + d.u[0] * a + d.v[0] * b, py = oy + d.u[1] * a + d.v[1] * b, pz = oz + d.u[2] * a + d.v[2] * b;
          pos.push((px - off[0]) * s, (py - off[1]) * s, (pz - off[2]) * s);
          nor.push(nx, ny, nz);
          // AO neighbours in the layer in front of the face
          const su = a ? 1 : -1, sv = b ? 1 : -1;
          const fx = x + nx, fy = y + ny, fz = z + nz;
          const s1 = has(fx + d.u[0] * su, fy + d.u[1] * su, fz + d.u[2] * su) ? 1 : 0;
          const s2 = has(fx + d.v[0] * sv, fy + d.v[1] * sv, fz + d.v[2] * sv) ? 1 : 0;
          const cc = has(fx + d.u[0] * su + d.v[0] * sv, fy + d.u[1] * su + d.v[1] * sv, fz + d.u[2] * su + d.v[2] * sv) ? 1 : 0;
          const ao = s1 && s2 ? 0 : 3 - (s1 + s2 + cc);
          aos.push(ao); const f = AO[ao];
          col.push(tmp.r * f, tmp.g * f, tmp.b * f);
        }
        if (aos[0] + aos[2] > aos[1] + aos[3]) idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
        else idx.push(base + 1, base + 2, base + 3, base + 1, base + 3, base);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    g.setIndex(idx);
    g.computeBoundingSphere();
    return g;
  }
  mesh(opts = {}) {
    const m = new THREE.Mesh(this.geometry(opts), opts.material ?? MAT.vox);
    m.castShadow = opts.cast ?? true; m.receiveShadow = opts.receive ?? true;
    return m;
  }
}

export const MAT = {
  vox: new THREE.MeshLambertMaterial({ vertexColors: true }),
};
