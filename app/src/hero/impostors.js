import * as THREE from 'three/webgpu';
import { attribute, texture, uv, color } from 'three/tsl';

export function useImpostor(distance, switchDistance, wasFar = false) {
  return distance >= switchDistance * (wasFar ? .9 : 1);
}

export function isTreeGroup(name) {
  return /^(trees|suburbs_trees|fc_retained_site_trees|fc_retained_palms)__/.test(name);
}

// The v1 canopy LOD0 keeps texture maps but drops UVs (texCoord:-1 in the GLB).
// Supply a planar fallback only for those meshes, without changing shared geometry.
function nearTreeUVs(mesh, cache) {
  const source = mesh.geometry;
  if (source.hasAttribute('uv')) return;
  const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  if (!materials.some(material => material.map)) return;
  if (!cache.has(source)) {
    const geometry = source.clone();
    geometry.computeBoundingBox();
    const { min, max } = geometry.boundingBox;
    const spans = ['x', 'y', 'z'].sort((a, b) => (max[b] - min[b]) - (max[a] - min[a]));
    const [uAxis, vAxis] = spans;
    const position = geometry.attributes.position, point = new THREE.Vector3();
    const coords = new Float32Array(position.count * 2);
    for (let i = 0; i < position.count; i++) {
      point.fromBufferAttribute(position, i);
      coords[i * 2] = (point[uAxis] - min[uAxis]) / (max[uAxis] - min[uAxis] || 1);
      coords[i * 2 + 1] = (point[vAxis] - min[vAxis]) / (max[vAxis] - min[vAxis] || 1);
    }
    geometry.setAttribute('uv', new THREE.BufferAttribute(coords, 2));
    cache.set(source, geometry);
  }
  mesh.geometry = cache.get(source);
}

// Reuse the exported far LOD atlas. One quad replaces two crossed quads.
// Sources stay immutable so compacting near instances never loses tree transforms.
export function installTreeImpostors(root, camera) {
  root.updateWorldMatrix(true, true);
  const sources = [], batches = new Map(), uvFallbacks = new WeakMap();
  root.traverse(lod => {
    if (!lod.isLOD || !isTreeGroup(lod.name)) return;
    const levels = lod.levels.filter(l => l.object.isMesh || l.object.children.length);
    if (levels.length < 2) return;
    const near = levels[0].object, farLevel = levels.at(-1), far = farLevel.object;
    if (!far.isInstancedMesh) return;
    const nearMeshes = [];
    near.traverse(mesh => { if (mesh.isInstancedMesh) nearMeshes.push(mesh); });
    if (!nearMeshes.length || nearMeshes.some(mesh => mesh.count !== far.count)) return;
    const mat = far.material;
    if (Array.isArray(mat) || !mat.map) return;
    const index = far.geometry.index;
    if ((index?.count ?? far.geometry.attributes.position.count) !== 12) return;
    const bounds = new THREE.Box3(), p = new THREE.Vector3(), rect = new THREE.Vector4(Infinity, Infinity, -Infinity, -Infinity);
    const pos = far.geometry.attributes.position, tex = far.geometry.attributes.uv;
    if (!tex) return;
    for (let i = 0; i < 6; i++) {
      const n = index ? index.getX(i) : i;
      bounds.expandByPoint(p.fromBufferAttribute(pos, n));
      rect.x = Math.min(rect.x, tex.getX(n)); rect.y = Math.min(rect.y, tex.getY(n));
      rect.z = Math.max(rect.z, tex.getX(n)); rect.w = Math.max(rect.w, tex.getY(n));
    }
    rect.z -= rect.x; rect.w -= rect.y;
    const centre = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3());
    const key = `${mat.map.uuid}:${mat.color.getHex()}:${mat.alphaTest}`;
    if (!batches.has(key)) batches.set(key, { material: mat, capacity: 0, count: 0 });
    const batch = batches.get(key); batch.capacity += far.count;
    for (const mesh of nearMeshes) nearTreeUVs(mesh, uvFallbacks);
    const originals = nearMeshes.map(mesh => ({ mesh, matrices: mesh.instanceMatrix.array.slice(), colors: mesh.instanceColor?.array.slice() }));
    const world = new THREE.Matrix4(), instance = new THREE.Matrix4();
    const parentInverse = root.matrixWorld.clone().invert();
    const farToRoot = parentInverse.multiply(far.matrixWorld);
    const entries = [];
    for (let i = 0; i < far.count; i++) {
      far.getMatrixAt(i, instance); world.multiplyMatrices(farToRoot, instance);
      const scale = new THREE.Vector3().setFromMatrixScale(world);
      entries.push({ centre: centre.clone().applyMatrix4(world), width: Math.max(size.x, size.z) * Math.max(scale.x, scale.z), height: size.y * scale.y, far: false });
    }
    lod.autoUpdate = false;
    for (const level of lod.levels) level.object.visible = false;
    near.visible = true;
    sources.push({ near, originals, entries, rect, batch, switchDistance: farLevel.distance,
      max: lod.levels.find(l => !l.object.isMesh && l.object.children.length === 0)?.distance ?? Infinity });
  });
  for (const batch of batches.values()) {
    const g = new THREE.PlaneGeometry(1, 1);
    const rects = new THREE.InstancedBufferAttribute(new Float32Array(batch.capacity * 4), 4);
    rects.setUsage(THREE.DynamicDrawUsage); g.setAttribute('heroAtlasRect', rects);
    const material = new THREE.MeshBasicNodeMaterial({ alphaTest: batch.material.alphaTest || .5, side: THREE.DoubleSide });
    const rect = attribute('heroAtlasRect', 'vec4');
    const sample = texture(batch.material.map, uv().mul(rect.zw).add(rect.xy));
    material.colorNode = sample.rgb.mul(color(batch.material.color)); material.opacityNode = sample.a;
    const mesh = new THREE.InstancedMesh(g, material, batch.capacity);
    mesh.name = 'hero-tree-impostors'; mesh.count = 0; mesh.frustumCulled = false;
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); root.add(mesh);
    batch.mesh = mesh; batch.rects = rects;
  }
  const cameraLocal = new THREE.Vector3(), positionWorld = new THREE.Vector3(), worldCamera = new THREE.Vector3();
  const matrix = new THREE.Matrix4(), quaternion = new THREE.Quaternion(), scale = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  const lastCamera = new THREE.Vector3(Infinity, Infinity, Infinity);
  function update() {
    root.updateWorldMatrix(true, false); camera.getWorldPosition(worldCamera);
    // Billboards depend on the camera position only: skip the pass while it stays within 0.5 m.
    if (worldCamera.distanceToSquared(lastCamera) < 0.25) return;
    lastCamera.copy(worldCamera);
    cameraLocal.copy(worldCamera); root.worldToLocal(cameraLocal);
    for (const batch of batches.values()) batch.count = 0;
    for (const source of sources) {
      let nearCount = 0;
      source.entries.forEach((entry, i) => {
        positionWorld.copy(entry.centre).applyMatrix4(root.matrixWorld);
        const distance = worldCamera.distanceTo(positionWorld);
        entry.far = useImpostor(distance, source.switchDistance, entry.far);
        if (distance >= source.max) return;
        if (!entry.far) {
          for (const original of source.originals) {
            matrix.fromArray(original.matrices, i * 16); original.mesh.setMatrixAt(nearCount, matrix);
            if (original.colors) original.mesh.instanceColor.array.set(original.colors.subarray(i * 3, i * 3 + 3), nearCount * 3);
          }
          nearCount++;
        } else {
          const batch = source.batch, slot = batch.count++;
          quaternion.setFromAxisAngle(up, Math.atan2(cameraLocal.x - entry.centre.x, cameraLocal.z - entry.centre.z));
          matrix.compose(entry.centre, quaternion, scale.set(entry.width, entry.height, 1));
          batch.mesh.setMatrixAt(slot, matrix);
          batch.rects.setXYZW(slot, source.rect.x, source.rect.y, source.rect.z, source.rect.w);
        }
      });
      source.near.visible = nearCount > 0;
      for (const { mesh, colors } of source.originals) {
        mesh.count = nearCount; mesh.instanceMatrix.needsUpdate = true;
        if (colors) mesh.instanceColor.needsUpdate = true;
      }
    }
    for (const batch of batches.values()) {
      batch.mesh.count = batch.count; batch.mesh.visible = batch.count > 0;
      batch.mesh.instanceMatrix.needsUpdate = true; batch.rects.needsUpdate = true;
    }
  }
  update();
  console.info('hero tree impostors:', { sources: sources.length, atlasBatches: batches.size });
  return { update };
}
