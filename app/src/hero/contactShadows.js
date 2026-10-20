import * as THREE from 'three/webgpu';

let texture;
function blobTexture() {
  if (texture) return texture;
  const size = 32, data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const i = (y * size + x) * 4, r = Math.hypot((x + .5) / size * 2 - 1, (y + .5) / size * 2 - 1);
    data[i + 3] = Math.round(Math.max(0, 1 - r) ** 2 * 150);
  }
  texture = new THREE.DataTexture(data, size, size);
  texture.magFilter = texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

// One unlit draw per population. These are visual contact cues, not sun shadows.
export function contactShadowBatch(capacity) {
  const geometry = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
  const material = new THREE.MeshBasicMaterial({ map: blobTexture(), transparent: true, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -3 });
  const mesh = new THREE.InstancedMesh(geometry, material, Math.max(1, capacity));
  mesh.name = 'hero-contact-shadows'; mesh.userData.claim = 'Visualization';
  mesh.count = 0; mesh.visible = false; mesh.frustumCulled = false; mesh.renderOrder = 3;
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const matrix = new THREE.Matrix4(), local = new THREE.Matrix4();
  let enabled = false;
  return {
    mesh,
    get enabled() { return enabled; },
    setEnabled(value) { enabled = Boolean(value); mesh.visible = enabled && mesh.count > 0; },
    set(i, surfaceMatrix, width, length) {
      local.makeScale(width, 1, length); local.setPosition(0, .04, 0);
      mesh.setMatrixAt(i, matrix.multiplyMatrices(surfaceMatrix, local));
    },
    finish(count) { mesh.count = count; mesh.visible = enabled && count > 0; mesh.instanceMatrix.needsUpdate = true; },
  };
}
