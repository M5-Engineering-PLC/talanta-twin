import * as THREE from 'three/webgpu';
import { uv, abs, step, float, max, mix, color, instanceColor, vec2 } from 'three/tsl';

export function eventRoot(scene, bearing, pad, id) {
  const root = new THREE.Group(); root.name = id;
  root.rotation.y = -bearing * Math.PI / 180; root.position.y = pad; scene.add(root);
  return root;
}
export function release(root) {
  const geometries = new Set(), materials = new Set();
  root.traverse(o => {
    if (o.geometry) geometries.add(o.geometry);
    for (const m of Array.isArray(o.material) ? o.material : o.material ? [o.material] : []) materials.add(m);
    if (o.isInstancedMesh) o.dispose();
  });
  root.removeFromParent(); geometries.forEach(g => g.dispose()); materials.forEach(m => m.dispose());
}
export function cards(root, count) {
  const material = new THREE.MeshBasicNodeMaterial({ side: THREE.DoubleSide, alphaTest: .5 });
  const p = uv(), x = abs(p.x.sub(.5)), y = p.y;
  // Circular head, torso, arms and two separate legs, in the seated crowd card style.
  const headMask = float(1).sub(step(.11, p.sub(vec2(.5, .88)).length()));
  const torso = float(1).sub(step(.23, x)).mul(step(.33, y)).mul(float(1).sub(step(.77, y)));
  const arms = step(.26, x).mul(float(1).sub(step(.4, x))).mul(step(.36, y)).mul(float(1).sub(step(.75, y)));
  const legs = step(.055, x).mul(float(1).sub(step(.21, x))).mul(float(1).sub(step(.33, y)));
  material.opacityNode = max(headMask, max(torso, max(arms, legs)));
  material.colorNode = mix(mix(instanceColor, color('#292934'), legs), color('#95633f'), headMask);
  const mesh = new THREE.InstancedMesh(new THREE.PlaneGeometry(.85, 1.8).translate(0, .9, 0), material, count);
  mesh.name = 'standing-pitch-crowd'; mesh.frustumCulled = false; root.add(mesh);
  const dummy = new THREE.Object3D(), tint = new THREE.Color();
  return { mesh, draw(state) {
    state.forEach((fan, i) => {
      dummy.position.set(...fan.position); dummy.rotation.set(0, fan.heading, Math.sin(fan.phase) * .025);
      dummy.updateMatrix(); mesh.setMatrixAt(i, dummy.matrix); mesh.setColorAt(i, tint.set(fan.color));
    });
    mesh.instanceMatrix.needsUpdate = true; mesh.instanceColor.needsUpdate = true;
  } };
}
export function figures(root, count) {
  const shirt = new THREE.MeshBasicMaterial(), skin = new THREE.MeshBasicMaterial({ color: '#95633f' });
  const dark = new THREE.MeshBasicMaterial({ color: '#292934' });
  const bodies = new THREE.InstancedMesh(new THREE.BoxGeometry(.5, .65, .3), shirt, count);
  const heads = new THREE.InstancedMesh(new THREE.OctahedronGeometry(.17), skin, count);
  const limbs = new THREE.InstancedMesh(new THREE.BoxGeometry(.14, .65, .16), dark, count * 4);
  for (const mesh of [bodies, heads, limbs]) { mesh.frustumCulled = false; root.add(mesh); }
  const dummy = new THREE.Object3D(), tint = new THREE.Color();
  return { draw(actors) {
    actors.forEach((a, i) => {
      const [x, y, z] = a.position, hop = a.celebrating ? Math.max(0, Math.sin(a.phase)) * .35 : 0;
      dummy.position.set(x, y + 1.05 + hop, z); dummy.rotation.set(0, a.heading, 0); dummy.updateMatrix();
      bodies.setMatrixAt(i, dummy.matrix); bodies.setColorAt(i, tint.set(a.color));
      dummy.position.y = y + 1.58 + hop; dummy.updateMatrix(); heads.setMatrixAt(i, dummy.matrix);
      for (let limb = 0; limb < 4; limb++) {
        const side = limb % 2 ? 1 : -1, arm = limb >= 2;
        const offset = side * (arm ? .35 : .15);
        dummy.position.set(x + Math.cos(a.heading) * offset, y + (arm ? 1.0 : .4) + hop, z - Math.sin(a.heading) * offset);
        dummy.rotation.set(Math.sin(a.phase + side) * (arm ? .45 : .6), a.heading, arm && a.celebrating ? side * 2.5 : 0);
        dummy.updateMatrix(); limbs.setMatrixAt(i * 4 + limb, dummy.matrix);
      }
    });
    bodies.instanceMatrix.needsUpdate = heads.instanceMatrix.needsUpdate = limbs.instanceMatrix.needsUpdate = true;
    bodies.instanceColor.needsUpdate = true;
  } };
}
