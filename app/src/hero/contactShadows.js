import * as THREE from 'three/webgpu';
import { materialOpacity, positionGeometry, texture as sampleTexture, vec3 } from 'three/tsl';

let texture;
function blobTexture() {
  if (texture) return texture;
  const size = 33, data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const i = (y * size + x) * 4, r = Math.hypot(x / (size - 1) * 2 - 1, y / (size - 1) * 2 - 1);
    data[i + 3] = Math.round(Math.max(0, 1 - r) ** 2 * 255);
  }
  texture = new THREE.DataTexture(data, size, size);
  texture.magFilter = texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

// One unlit draw per population. These are visual contact cues, not sun shadows.
export function contactShadowBatch(capacity) {
  const geometry = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
  const material = new THREE.MeshBasicNodeMaterial({ color: 0x000000, map: blobTexture(), opacity: .30,
    transparent: true, blending: THREE.NormalBlending, depthWrite: false, toneMapped: false, fog: false,
    polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -3 });
  // Local X/Z spans [-.5,.5] on the horizontal plane. No UV attribute is required.
  // Keep black out of the fog/lighting paths and preserve alpha in the transparent pass.
  material.colorNode = vec3(0);
  material.opacityNode = sampleTexture(material.map, positionGeometry.xz.add(.5)).a.mul(materialOpacity);
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
