import * as THREE from 'three/webgpu';
import { bumpMap, color, mix, texture, uv, vec2 } from 'three/tsl';

export const PITCH_DECKING = { width: 80, depth: 90, centreZ: 6.5, top: .12 };

// A single height tile repeats with the same offset as the visible panel seams.
function panelHeightTexture() {
  const size = 128;
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const u = (x + .5) / size, v = (y + .5) / size;
      const edge = Math.min(u * 2, (1 - u) * 2, v * 1.5, (1 - v) * 1.5);
      const panel = Math.min(1, Math.max(0, (edge - .009) / .013));
      const tread = Math.abs((u * 10) % 1 - .5) + .75 * Math.abs((v * 7.5) % 1 - .5);
      const raised = Math.min(1, Math.max(0, (.28 - tread) / .13));
      const h = Math.round(panel * (176 + 54 * raised));
      data.set([h, h, h, 255], (y * size + x) * 4);
    }
  }
  const result = new THREE.DataTexture(data, size, size);
  result.magFilter = THREE.LinearFilter;
  result.minFilter = THREE.LinearMipmapLinearFilter;
  result.generateMipmaps = true;
  result.needsUpdate = true;
  return result;
}

export function addConcertDecking(root) {
  const { width, depth, centreZ, top } = PITCH_DECKING;
  const material = new THREE.MeshStandardNodeMaterial({ roughness: .78 });
  const metres = uv().mul(vec2(width, depth));
  const rows = metres.y.div(1.5);
  const columns = metres.x.div(2).add(rows.floor().mod(2).mul(.5));
  const inPanel = vec2(columns.fract(), rows.fract());
  const edge = inPanel.min(inPanel.oneMinus());
  const seams = edge.x.mul(2).min(edge.y.mul(1.5)).smoothstep(.009, .022);
  const panelTone = columns.floor().add(rows.floor().mul(7)).mod(5).mul(.12);
  const panel = mix(color('#343943'), color('#444a54'), panelTone);
  const tread = inPanel.mul(vec2(10, 7.5)).fract().sub(.5).abs();
  const diamond = tread.x.add(tread.y.mul(.75)).smoothstep(.15, .28).oneMinus();
  material.colorNode = mix(color('#232731'), panel.add(diamond.mul(.013)), seams);
  material.emissiveNode = material.colorNode.mul(.5);
  const relief = panelHeightTexture();
  material.normalNode = bumpMap(texture(relief, inPanel), .055);
  material.addEventListener('dispose', () => relief.dispose());

  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), material);
  mesh.name = 'concert-pitch-decking';
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.set(0, top, centreZ);
  root.add(mesh);
  return mesh;
}
