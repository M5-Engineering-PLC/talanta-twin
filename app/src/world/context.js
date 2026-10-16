import * as THREE from 'three/webgpu';

// src: height source per vertex (0 Open Buildings 2023, 1 OSM floors, 2 area default); see manifest.
export function makeBuildings(pos, col, idx, src) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3, true));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9 }));
  m.castShadow = false; m.receiveShadow = true;
  m.userData.kind = 'buildings'; m.userData.src = src;
  return m;
}

export function makeRoads(pos, w, idx) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const c = new Float32Array(w.length * 3);
  for (let i = 0; i < w.length; i++) {
    const major = w[i] >= 9, minor = w[i] <= 3;
    const v = major ? [0.86, 0.83, 0.77] : minor ? [0.72, 0.62, 0.50] : [0.80, 0.76, 0.70];
    c.set(v, i * 3);
  }
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
  m.receiveShadow = true;
  m.userData.kind = 'roads';
  return m;
}

// Trees from Sentinel-2 NDVI (x, y, z, scale). The nearest `detailCount` get a trunk, a raised
// main crown and a second, smaller crown; the rest stay single crowns (far, painted-relief look).
export function makeTrees(data, maxCount, detailCount = 2500) {
  const total = data.length / 4, n = Math.min(total, maxCount);
  const step = total / n;
  const picks = [];
  for (let i = 0; i < n; i++) { const j = Math.floor(i * step) * 4; picks.push({ j, i, d: Math.hypot(data[j], data[j + 2]) }); }
  picks.sort((a, b) => a.d - b.d);
  const near = picks.slice(0, Math.min(detailCount, n)), far = picks.slice(near.length);

  const mat = new THREE.MeshStandardMaterial({ color: 0x4f6b3a, roughness: 1, flatShading: true });
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5a4632, roughness: 1 });
  const blob = new THREE.IcosahedronGeometry(1, 1); blob.scale(3.2, 3.6, 3.2); blob.translate(0, 4.2, 0);
  const crownA = new THREE.IcosahedronGeometry(1, 1); crownA.scale(3.0, 2.6, 3.0); crownA.translate(0, 6.2, 0);
  const crownB = new THREE.IcosahedronGeometry(1, 1); crownB.scale(1.9, 1.7, 1.9); crownB.translate(1.7, 4.9, 0.9);
  const trunk = new THREE.CylinderGeometry(0.22, 0.34, 4.6, 6); trunk.translate(0, 2.3, 0);

  const group = new THREE.Group(); group.name = 'trees';
  const meshes = [[blob, mat, far], [crownA, mat, near], [crownB, mat, near], [trunk, trunkMat, near]]
    .filter(([, , list]) => list.length).map(([g, m, list]) => { const im = new THREE.InstancedMesh(g, m, list.length); im.userData.list = list; return im; });
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3(), yAx = new THREE.Vector3(0, 1, 0);
  const col = new THREE.Color();
  for (const im of meshes) {
    const isTrunk = im.material === trunkMat;
    im.userData.list.forEach(({ j, i }, k) => {
      const sc = data[j + 3];
      p.set(data[j], data[j + 1] - 0.5, data[j + 2]);
      s.set(sc, sc * (0.85 + ((i * 7919) % 30) / 100), sc);
      q.setFromAxisAngle(yAx, (i * 2.39996) % 6.283);
      m4.compose(p, q, s); im.setMatrixAt(k, m4);
      if (!isTrunk) { const t = ((i * 104729) % 100) / 100; col.setRGB(0.27 + 0.1 * t, 0.38 + 0.08 * t, 0.2 + 0.05 * t); if (im.geometry === crownB) col.multiplyScalar(1.12); im.setColorAt(k, col); }
    });
    im.castShadow = true; group.add(im);
  }
  group.userData.kind = 'trees'; group.userData.mats = [mat, trunkMat]; group.userData.detail = near.length;
  return group;
}
