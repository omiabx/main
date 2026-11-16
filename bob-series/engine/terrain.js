// Terrain builders (block size TS units).
import * as THREE from 'three';
import { VB, rgb, hash3, shade, mix } from './vox.js';
import { C } from './models.js';

export const TS = 4;

function noise2(x, z, s) { // smooth value noise
  const xi = Math.floor(x / s), zi = Math.floor(z / s), fx = x / s - xi, fz = z / s - zi;
  const h = (a, b) => hash3(a, 7, b);
  const u = fx * fx * (3 - 2 * fx), v = fz * fz * (3 - 2 * fz);
  return (h(xi, zi) * (1 - u) + h(xi + 1, zi) * u) * (1 - v) + (h(xi, zi + 1) * (1 - u) + h(xi + 1, zi + 1) * u) * v;
}
export { noise2 };

const strata = [C.rock3, C.rock1, C.rock1, C.rock2, C.rock1, C.rock3, C.rock2, C.rock2];
export function sandCol(x, y, z) { const n = hash3(x, y, z); return n > 0.66 ? C.sand : n > 0.33 ? C.sand2 : shade(C.sand, 0.97); }
export function cliffCol(x, y, z) { const band = strata[((-y) % strata.length + strata.length) % strata.length]; return shade(band, 0.94 + hash3(x, y, z) * 0.1); }

// plateau: inside(x,z) -> bool, height(x,z) -> top y (blocks), depth = how far cliffs go down
export function plateau(vb, x0, z0, x1, z1, inside, height, depth = 14) {
  for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++) {
    if (!inside(x, z)) continue;
    const top = height(x, z);
    const edge = !inside(x + 1, z) || !inside(x - 1, z) || !inside(x, z + 1) || !inside(x, z - 1);
    for (let y = -depth; y <= top; y++) {
      // only keep surface-ish voxels to save geometry
      if (y < top - 1 && !edge && !(!inside(x + 1, z) || !inside(x - 1, z))) { if (y < top - 2) continue; }
      const c = y >= top - 1 ? sandCol(x, y, z) : cliffCol(x, y, z);
      vb.set(x, y, z, c);
    }
  }
}

// floating desert island (rounded blob with terraces)
export function island(vb, cx, cz, r, seed = 3, depth = 10) {
  const inside = (x, z) => { const d = Math.hypot(x - cx, z - cz) + (noise2(x + seed * 31, z, 6) - 0.5) * 6; return d < r; };
  const height = (x, z) => { const n = noise2(x + seed * 17, z + 5, 9); return n > 0.62 ? 1 : 0; };
  for (let x = cx - r - 4; x <= cx + r + 4; x++) for (let z = cz - r - 4; z <= cz + r + 4; z++) {
    if (!inside(x, z)) continue;
    const top = height(x, z);
    const dEdge = r - Math.hypot(x - cx, z - cz);
    const bottom = -Math.max(1, Math.min(depth, Math.floor(dEdge * 0.9 + 2 + noise2(x, z, 4) * 3)));
    for (let y = bottom; y <= top; y++) {
      const exposed = !inside(x + 1, z) || !inside(x - 1, z) || !inside(x, z + 1) || !inside(x, z - 1) || y >= top - 1 || y === bottom || true;
      if (!exposed) continue;
      vb.set(x, y, z, y >= top - 1 ? sandCol(x, y, z) : cliffCol(x, y, z));
    }
  }
  return { inside, height };
}

export function terrainMesh(vb) { return vb.mesh({ scale: TS }); }
