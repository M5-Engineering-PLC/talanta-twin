import * as THREE from 'three/webgpu';

const R_EARTH = 6371000;

// One terrain level. Vertices that fall inside `hole` (an inner level's box) sink below it.
export function makeTerrain(meta, heights, texture, hole) {
  const { nx, nz, x0, z0, dx, dz } = meta;
  const g = new THREE.PlaneGeometry((nx - 1) * dx, (nz - 1) * dz, nx - 1, nz - 1);
  g.rotateX(-Math.PI / 2);
  const p = g.attributes.position;
  const uv = g.attributes.uv;
  const tex = texture.meta;
  for (let i = 0; i < p.count; i++) {
    const c = i % nx, r = Math.floor(i / nx);
    const x = x0 + (c + 0.5) * dx, z = z0 + (r + 0.5) * dz;
    let y = heights[r * nx + c];
    y -= (x * x + z * z) / (2 * R_EARTH); // earth curvature
    if (hole && x > hole.x0 + hole.pad && x < hole.x1 - hole.pad && z > hole.z0 + hole.pad && z < hole.z1 - hole.pad) y -= hole.drop;
    p.setXYZ(i, x, y, z);
    uv.setXY(i, (x - tex.x0) / tex.size, 1 - (z - tex.z0) / tex.size);
  }
  g.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ map: texture.tex, roughness: 0.95, metalness: 0 });
  const mesh = new THREE.Mesh(g, mat);
  mesh.receiveShadow = true;
  mesh.userData = { kind: 'terrain', meta };
  return mesh;
}

// Height lookup on the site grid (bilinear), relative to the origin ground.
export function heightSampler(meta, heights) {
  const { nx, nz, x0, z0, dx, dz } = meta;
  return (x, z) => {
    const fc = (x - x0) / dx - 0.5, fr = (z - z0) / dz - 0.5;
    const c = Math.max(0, Math.min(nx - 2, Math.floor(fc))), r = Math.max(0, Math.min(nz - 2, Math.floor(fr)));
    const tx = Math.min(1, Math.max(0, fc - c)), tz = Math.min(1, Math.max(0, fr - r));
    const h = (rr, cc) => heights[rr * nx + cc];
    return (h(r, c) * (1 - tx) + h(r, c + 1) * tx) * (1 - tz) + (h(r + 1, c) * (1 - tx) + h(r + 1, c + 1) * tx) * tz;
  };
}

export function boxOf(meta) {
  return { x0: meta.x0, z0: meta.z0, x1: meta.x0 + meta.nx * meta.dx, z1: meta.z0 + meta.nz * meta.dz };
}
