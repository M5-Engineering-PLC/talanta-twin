import * as THREE from 'three/webgpu';
import { FOH, FOH_CABLE } from './concert-state.js';

// Battens, braces and consoles share instanced boxes to keep the booth inexpensive.
export function addConcertFoh(root) {
  const booth = new THREE.Group();
  booth.name = 'concert-foh-booth';
  booth.position.set(0, .12, FOH.z);
  root.add(booth);

  const metal = [], black = [], screens = [], crews = [], skin = [];
  function box(parts, x, y, z, width, height, depth, roll = 0) {
    parts.push({ x, y, z, width, height, depth, roll });
  }

  const halfWidth = FOH.width / 2, halfDepth = FOH.depth / 2;
  box(black, 0, .06, 0, FOH.width, .12, FOH.depth);
  box(black, 0, FOH.height - .04, 0, FOH.width, .08, FOH.depth);
  for (const x of [-halfWidth + .16, halfWidth - .16]) {
    for (const z of [-halfDepth + .16, halfDepth - .16]) {
      for (const dx of [-.1, .1]) for (const dz of [-.1, .1]) {
        box(metal, x + dx, 1.55, z + dz, .045, 2.86, .045);
      }
      for (let i = 0; i < 7; i++) {
        box(metal, x, .38 + i * .39, z - .1, .035, .42, .035, i % 2 ? -.46 : .46);
        box(metal, x, .38 + i * .39, z + .1, .035, .42, .035, i % 2 ? .46 : -.46);
      }
    }
    for (const y of [2.86, 3.07]) box(metal, x, y, 0, .055, .055, FOH.depth - .3);
  }
  for (const z of [-halfDepth + .16, halfDepth - .16]) {
    for (const y of [2.86, 3.07]) box(metal, 0, y, z, FOH.width - .3, .055, .055);
    for (let i = 0; i < 14; i++) {
      box(metal, (i - 6.5) * .38, 2.965, z, .035, .43, .035, i % 2 ? -.98 : .98);
    }
  }

  for (const x of [-1.4, 1.4]) {
    box(black, x, .57, .65, 1.95, .91, .62);
    box(black, x, 1.06, .65, 2.12, .12, .85);
    for (let i = -1; i <= 1; i++) {
      box(black, x + i * .55, 1.33, .86, .51, .4, .10);
      box(screens, x + i * .55, 1.33, .797, .46, .33, .027);
    }
    for (let i = 0; i < 12; i++) box(metal, x + (i - 5.5) * .13, 1.129, .45, .045, .02, .11);

    // Chairs and seated operators face the stage, toward positive z.
    box(black, x, .49, -.51, .49, .085, .48);
    box(black, x, .78, -.73, .48, .50, .075);
    box(metal, x, .28, -.52, .07, .34, .075);
    box(metal, x, .16, -.52, .47, .08, .44);
    box(crews, x, .81, -.50, .38, .52, .23);
    box(skin, x, 1.18, -.47, .19, .24, .19);
    box(black, x, 1.303, -.48, .21, .035, .20);
    for (const side of [-1, 1]) {
      box(black, x + .105 * side, 1.19, -.48, .045, .10, .085);
      box(black, x + .105 * side, .55, -.26, .16, .16, .42);
      box(black, x + .105 * side, .35, -.055, .14, .38, .15);
      box(black, x + .105 * side, .17, .015, .15, .10, .25);
      box(crews, x + .23 * side, .91, -.43, .13, .28, .13, side * .15);
      box(skin, x + .23 * side, 1.047, -.24, .093, .09, .34);
    }
  }

  const dummy = new THREE.Object3D();
  for (const [name, color, parts] of [
    ['truss-and-faders', '#858b97', metal],
    ['canopy-and-consoles', '#141720', black],
    ['displays', '#62d7ee', screens],
    ['operator-jackets', '#375c67', crews],
    ['operator-faces-and-hands', '#80563e', skin],
  ]) {
    const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial({ color }), parts.length);
    mesh.name = name;
    parts.forEach(({ x, y, z, width, height, depth, roll }, index) => {
      dummy.position.set(x, y, z);
      dummy.scale.set(width, height, depth);
      dummy.rotation.z = roll;
      dummy.updateMatrix();
      mesh.setMatrixAt(index, dummy.matrix);
    });
    booth.add(mesh);
  }
  return booth;
}

// Route the cable protectors around the standing areas and into the booth's rear access lane.
export function addConcertCableRoute(root) {
  const route = new THREE.Group();
  route.name = 'concert-foh-cable-route';
  root.add(route);

  const dummy = new THREE.Object3D();
  const runs = FOH_CABLE.slice(1).map(([x, z], i) => {
    const [fromX, fromZ] = FOH_CABLE[i];
    const length = Math.hypot(x - fromX, z - fromZ);
    return { x: fromX, z: fromZ, dx: x - fromX, dz: z - fromZ, length };
  });
  const surface = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial({ color: '#e7b836' }), runs.length);
  const seams = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial({ color: '#202126' }),
    runs.reduce((count, run) => count + Math.ceil(run.length), 0));
  let seam = 0;
  runs.forEach(({ x, z, dx, dz, length }, index) => {
    dummy.position.set(x + dx / 2, .15, z + dz / 2);
    dummy.rotation.set(0, Math.atan2(dx, dz), 0);
    dummy.scale.set(.55, .06, length + .2);
    dummy.updateMatrix();
    surface.setMatrixAt(index, dummy.matrix);

    const sections = Math.ceil(length);
    for (let i = 0; i < sections; i++) {
      const fraction = (i + .5) / sections;
      dummy.position.set(x + dx * fraction, .181, z + dz * fraction);
      dummy.scale.set(.55, .008, .18);
      dummy.updateMatrix();
      seams.setMatrixAt(seam++, dummy.matrix);
    }
  });
  route.add(surface, seams);
  return route;
}
