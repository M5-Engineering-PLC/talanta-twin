import * as THREE from 'three/webgpu';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export function figureGeometry() {
  const parts = [];
  function part(g, x, y, z, rise, kind) {
    g.translate(x, y, z);
    const n = g.attributes.position.count;
    g.setAttribute('rise', new THREE.Float32BufferAttribute(new Float32Array(n).fill(rise), 1));
    g.setAttribute('kind', new THREE.Float32BufferAttribute(new Float32Array(n).fill(kind), 1));
    g.deleteAttribute('uv');
    parts.push(g.index ? g.toNonIndexed() : g.clone());
    g.dispose();
  }
  part(new THREE.BoxGeometry(.32, .48, .22), 0, .77, 0, .5, 0);
  part(new THREE.OctahedronGeometry(.12), 0, 1.13, 0, .5, 1);
  for (const x of [-.1, .1]) part(new THREE.BoxGeometry(.12, .48, .14), x, .25, .22, 0, 2);
  for (const x of [-.21, .21]) part(new THREE.BoxGeometry(.09, .4, .1), x, .77, 0, .95, 0);
  part(new THREE.BoxGeometry(.65, .08, .025), 0, 1.95, 0, 0, 3);
  part(new THREE.BoxGeometry(.035, .055, .015), .22, 1.8, .06, 0, 4);
  const merged = mergeGeometries(parts);
  parts.forEach((g) => g.dispose());
  return merged;
}
