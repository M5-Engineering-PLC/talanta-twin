import * as THREE from 'three/webgpu';
import { BARRICADES, BARRICADE_SECTION_LENGTH } from './concert-state.js';
import { PITCH_DECKING } from './concert-decking.js';

export function addConcertBarricades(root) {
  const group = new THREE.Group();
  group.name = 'concert-crowd-barricades';
  group.position.y = PITCH_DECKING.top;
  root.add(group);
  const runs = BARRICADES.map(([[fromX, fromZ], [toX, toZ]]) => {
    const dx = toX - fromX, dz = toZ - fromZ;
    return { fromX, fromZ, dx, dz, sections: Math.ceil(Math.hypot(dx, dz) / BARRICADE_SECTION_LENGTH) };
  });
  const count = runs.reduce((sum, run) => sum + run.sections, 0);
  const frame = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial({ color: '#9098a3' }), count * 9);
  const infill = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial({ color: '#49515b' }), count);
  group.add(frame, infill);

  const dummy = new THREE.Object3D();
  let section = 0;
  for (const { fromX, fromZ, dx, dz, sections } of runs) {
    const width = Math.hypot(dx, dz) / sections;
    const yaw = Math.atan2(-dz, dx);
    dummy.rotation.y = yaw;
    for (let i = 0; i < sections; i++, section++) {
      const x = fromX + dx * (i + .5) / sections;
      const z = fromZ + dz * (i + .5) / sections;
      const parts = [
        [0, 1.172, 0, width, .056, .065],
        [0, .15, 0, width, .05, .065],
        [-width / 2 + .03, .59, 0, .055, 1.18, .065],
        [width / 2 - .03, .59, 0, .055, 1.18, .065],
        [0, .026, 0, width, .052, .46],
        [0, .24, .17, width * .93, .06, .14],
        [-width * .25, .65, 0, .022, 1, .049],
        [0, .65, 0, .022, 1, .049],
        [width * .25, .65, 0, .022, 1, .049],
        [0, .65, 0, width - .105, .93, .027],
      ];
      parts.forEach(([localX, y, localZ, w, h, d], j) => {
        dummy.position.set(x + Math.cos(yaw) * localX + Math.sin(yaw) * localZ, y,
          z - Math.sin(yaw) * localX + Math.cos(yaw) * localZ);
        dummy.scale.set(w, h, d);
        dummy.updateMatrix();
        if (j === 9) infill.setMatrixAt(section, dummy.matrix);
        else frame.setMatrixAt(section * 9 + j, dummy.matrix);
      });
    }
  }
  return group;
}
