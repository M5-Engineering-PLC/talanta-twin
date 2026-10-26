import * as THREE from 'three/webgpu';
import { concert_cues } from './cues.js';
import { concertBudget, concertState } from './concert-state.js';
import { eventRoot, release, cards } from './draw.js';
import { playback } from './playback.js';
export { concertState, concertBudget, concert_cues };

export function installConcert({ scene, bearing = 0, pad = 0, tier = 'high', width = globalThis.innerWidth ?? 1024, getCrowd, onState }) {
  const root = eventRoot(scene, bearing, pad, 'EVT-01');
  let budget = concertBudget(tier, width), audience, heads, beams;
  const neutral = new THREE.MeshBasicMaterial({ color: '#252632' });
  function box(position, size, material = neutral) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material); mesh.position.set(...position); root.add(mesh); return mesh;
  }
  const initial = concertState(concert_cues, 0, budget);
  box(initial.stage.position.map((v, i) => i === 1 ? v + initial.stage.size[1] / 2 : v), initial.stage.size);
  const { position: [tx, ty, tz], width: tw, depth: td } = initial.truss;
  const silver = new THREE.MeshBasicMaterial({ color: '#7e8797' });
  for (const x of [-tw / 2, tw / 2]) for (const z of [-td / 2, td / 2]) box([tx + x, ty / 2, tz + z], [.3, ty, .3], silver);
  for (const z of [-td / 2, td / 2]) {
    box([tx, ty, tz + z], [tw, .35, .35], silver);
    // Diagonal braces make the crossbeam read as a truss at bowl distance.
    for (let i = 0; i < 12; i++) { const brace = box([-16.5 + i * 3, ty - .65, tz + z], [3.2, .1, .1], silver); brace.rotation.z = i % 2 ? -.35 : .35; }
  }
  const screens = initial.screens.map(s => box(s.position, s.size, new THREE.MeshBasicMaterial()));
  const dummy = new THREE.Object3D(), tint = new THREE.Color(), direction = new THREE.Vector3(), down = new THREE.Vector3(0, -1, 0);
  function buildMoving() {
    if (audience) {
      for (const mesh of [audience.mesh, heads, beams]) { root.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose(); mesh.dispose(); }
    }
    audience = cards(root, budget.crowd);
    heads = new THREE.InstancedMesh(new THREE.SphereGeometry(.3, 6, 4), new THREE.MeshBasicMaterial(), budget.heads);
    beams = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 1, 6, 1, true).translate(0, -.5, 0),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: .12, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending }), budget.heads);
    for (const mesh of [heads, beams]) { mesh.frustumCulled = false; root.add(mesh); }
  }
  buildMoving();
  const player = playback({ cues: concert_cues, sample: t => concertState(concert_cues, t, budget), getCrowd, onState,
    draw(state) {
      audience.draw(state.crowd);
      state.screens.forEach((s, i) => screens[i].material.color.setRGB(...s.color).multiplyScalar(s.intensity));
      state.lights.forEach((l, i) => {
        dummy.position.set(...l.position); dummy.quaternion.identity(); dummy.scale.setScalar(1); dummy.updateMatrix(); heads.setMatrixAt(i, dummy.matrix);
        tint.setRGB(...l.color).multiplyScalar(l.intensity * 3); heads.setColorAt(i, tint); beams.setColorAt(i, tint);
        direction.set(...l.target).sub(dummy.position); const length = direction.length();
        dummy.quaternion.setFromUnitVectors(down, direction.normalize()); dummy.scale.set(length * .07, length, length * .07);
        dummy.updateMatrix(); beams.setMatrixAt(i, dummy.matrix);
      });
      heads.instanceMatrix.needsUpdate = beams.instanceMatrix.needsUpdate = true;
      heads.instanceColor.needsUpdate = beams.instanceColor.needsUpdate = true;
    }, dispose: () => release(root),
  });
  return { ...player, setTier(next, nextWidth = globalThis.innerWidth ?? width) {
    const nextBudget = concertBudget(next, nextWidth);
    if (nextBudget.crowd === budget.crowd && nextBudget.heads === budget.heads) return;
    budget = nextBudget; buildMoving(); player.redraw();
  } };
}
