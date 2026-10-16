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

// Rounded tree crowns as one instanced mesh (painted-relief look). Data: x, y, z, scale.
export function makeTrees(data, maxCount) {
  const n = Math.min(data.length / 4, maxCount);
  const geo = new THREE.IcosahedronGeometry(1, 1);
  geo.scale(3.2, 3.6, 3.2); geo.translate(0, 4.2, 0);
  const mat = new THREE.MeshStandardMaterial({ color: 0x4f6b3a, roughness: 1, flatShading: true });
  const mesh = new THREE.InstancedMesh(geo, mat, n);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3();
  const col = new THREE.Color();
  const step = (data.length / 4) / n;
  for (let i = 0; i < n; i++) {
    const j = Math.floor(i * step) * 4;
    const sc = data[j + 3];
    p.set(data[j], data[j + 1] - 0.5, data[j + 2]);
    s.set(sc, sc * (0.85 + ((i * 7919) % 30) / 100), sc);
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), (i * 2.39996) % 6.283);
    m.compose(p, q, s);
    mesh.setMatrixAt(i, m);
    const t = ((i * 104729) % 100) / 100;
    col.setRGB(0.27 + 0.1 * t, 0.38 + 0.08 * t, 0.2 + 0.05 * t);
    mesh.setColorAt(i, col);
  }
  mesh.castShadow = true;
  mesh.userData.kind = 'trees';
  return mesh;
}
