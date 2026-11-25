import * as THREE from 'three/webgpu';
import { CATWALK, STAGE } from './concert-state.js';

export function addConcertBackline(root) {
  const group = new THREE.Group();
  group.name = 'concert-stage-backline';
  root.add(group);
  const cabinets = [], grilles = [], trim = [], indicators = [], jogWheels = [];
  function box(parts, x, y, z, w, h, d, pitch = 0) {
    parts.push({ x, y, z, w, h, d, pitch });
  }

  const stageY = STAGE.deckHeight + .12;
  for (const x of [-23, -14, -6, 6, 14, 23]) {
    addMonitor(x, stageY, STAGE.frontZ + 1.15);
  }
  for (const x of [-1.55, 1.55]) for (const z of [20, 30]) {
    addMonitor(x, CATWALK.top, z);
  }
  function addMonitor(x, y, z) {
    box(cabinets, x, y + .13, z, .66, .26, .49);
    box(grilles, x, y + .254, z + .04, .61, .044, .40, -.61);
    box(trim, x + .315, y + .16, z, .03, .07, .16);
  }

  for (const x of [-18, 18]) {
    for (const y of [.39, 1.17]) {
      box(cabinets, x, stageY + y, 43.8, 1.1, .78, .57);
      box(trim, x, stageY + y, 43.507, 1.025, .696, .022);
      box(grilles, x, stageY + y, 43.49, .986, .66, .024);
    }
    box(cabinets, x, stageY + 1.69, 43.8, 1.0, .26, .48);
    box(trim, x, stageY + 1.69, 43.55, .79, .09, .023);
    for (let i = 0; i < 7; i++) box(cabinets, x + (i - 3) * .097, stageY + 1.685, 43.531, .028, .028, .017);
  }
  box(cabinets, -15.8, stageY + .85, 43.92, .82, 1.7, .64);
  box(grilles, -15.8, stageY + .85, 43.59, .74, 1.54, .035);
  for (const y of [.4, .78, 1.16, 1.54]) box(cabinets, -15.8, stageY + y, 43.567, .73, .024, .018);

  // Low console profile leaves the lead and backdrop unobstructed.
  const djZ = 44.1;
  const waveforms = [], meters = [];
  for (const x of [-.76, .76]) for (const z of [djZ - .29, djZ + .29]) {
    box(trim, x, stageY + .53, z, .065, 1.06, .065);
  }
  box(cabinets, 0, stageY + 1.05, djZ, 1.75, .11, .71);
  for (const side of [-1, 1]) {
    const x = side * .41;
    box(cabinets, x, stageY + 1.164, djZ, .329, .118, .453);
    box(grilles, x, stageY + 1.227, djZ + .135, .192, .012, .105);
    for (let column = 0; column < 16; column++) {
      waveforms.push({ index: indicators.length, column, side });
      box(indicators, x + (column - 7.5) * .011, stageY + 1.235, djZ + .135, .008, .004, .035);
    }
    jogWheels.push(x);
    box(trim, x, stageY + 1.242, djZ - .035, .073, .011, .073);
  }
  box(cabinets, 0, stageY + 1.159, djZ, .407, .107, .458);
  for (let i = 0; i < 4; i++) {
    const x = (i - 1.5) * .078;
    box(trim, x, stageY + 1.218, djZ - .07, .025, .013, .103);
    for (let segment = 0; segment < 12; segment++) {
      meters.push({ index: indicators.length, channel: i, segment });
      box(indicators, x + .026, stageY + 1.218, djZ + .01 + segment * .007, .009, .015, .005);
    }
    for (const z of [.05, .10, .15]) box(grilles, x, stageY + 1.22, djZ + z, .031, .026, .031);
  }

  box(cabinets, 0, stageY + 1.118, djZ + .29, .31, .025, .18);
  box(cabinets, 0, stageY + 1.236, djZ + .38, .32, .22, .024, -.18);
  box(indicators, 0, stageY + 1.239, djZ + .367, .283, .177, .006, -.18);

  const keyboardX = 15.5, keyboardZ = 43.85;
  for (const side of [-1, 1]) {
    box(trim, keyboardX + side * .52, stageY + .56, keyboardZ, .045, 1.12, .045);
    box(trim, keyboardX + side * .52, stageY + .03, keyboardZ, .07, .06, .58);
  }
  for (const y of [.82, 1.13]) {
    box(cabinets, keyboardX, stageY + y, keyboardZ, 1.46, .11, .36);
    box(trim, keyboardX, stageY + y + .056, keyboardZ + .072, 1.32, .016, .17);
    for (let key = 0; key < 36; key++) {
      if (key % 7 === 2 || key % 7 === 6) continue;
      box(cabinets, keyboardX + (key - 17.5) * .035, stageY + y + .071, keyboardZ + .03, .019, .013, .092);
    }
  }

  const dummy = new THREE.Object3D();
  let indicatorMesh;
  for (const [name, color, parts] of [
    ['equipment-housings', '#181a20', cabinets],
    ['speaker-grilles', '#414550', grilles],
    ['equipment-trim', '#8b8068', trim],
    ['console-indicators', '#8edcef', indicators],
  ]) {
    const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial({ color }), parts.length);
    mesh.name = name;
    if (parts === indicators) {
      indicatorMesh = mesh;
      const cyan = new THREE.Color(color);
      mesh.material.color.set(0xffffff);
      parts.forEach((_, i) => mesh.setColorAt(i, cyan));
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      mesh.instanceColor.setUsage(THREE.DynamicDrawUsage);
    }
    parts.forEach(({ x, y, z, w, h, d, pitch }, index) => {
      dummy.position.set(x, y, z);
      dummy.scale.set(w, h, d);
      dummy.rotation.x = pitch;
      dummy.updateMatrix();
      mesh.setMatrixAt(index, dummy.matrix);
    });
    group.add(mesh);
  }
  const jogs = new THREE.InstancedMesh(new THREE.CylinderGeometry(.103, .103, .021, 16),
    new THREE.MeshBasicMaterial({ color: '#414550' }), jogWheels.length);
  jogs.name = 'console-jog-wheels';
  dummy.rotation.set(0, 0, 0);
  dummy.scale.set(1, 1, 1);
  jogWheels.forEach((x, index) => {
    dummy.position.set(x, stageY + 1.23, djZ - .035);
    dummy.updateMatrix();
    jogs.setMatrixAt(index, dummy.matrix);
  });
  group.add(jogs);
  const dark = new THREE.Color('#142125');
  const green = new THREE.Color('#61e797'), yellow = new THREE.Color('#f4c653'), red = new THREE.Color('#fc603e');
  const waveformColor = new THREE.Color('#8edcef');
  function draw({ beat, pulse, led }) {
    for (const { index, channel, segment } of meters) {
      const variation = Math.sin(beat * (1.8 + channel * .12) + channel * 1.7);
      const level = Math.round(2 + led.energy * (4 + pulse * (5 + 2 * variation)));
      const peakColor = segment < 8 ? green : segment < 10 ? yellow : red;
      indicatorMesh.setColorAt(index, segment < level ? peakColor : dark);
    }
    for (const { index, column, side } of waveforms) {
      const part = indicators[index];
      const phase = column * .83 - beat * 5 + side;
      const amplitude = .01 + .07 * Math.abs(Math.sin(phase) * Math.cos(phase * .37)) * (.45 + pulse * .55);
      dummy.position.set(part.x, part.y, part.z);
      dummy.rotation.set(0, 0, 0);
      dummy.scale.set(part.w, part.h, amplitude);
      dummy.updateMatrix();
      indicatorMesh.setMatrixAt(index, dummy.matrix);
      indicatorMesh.setColorAt(index, waveformColor);
    }
    indicatorMesh.instanceMatrix.needsUpdate = true;
    indicatorMesh.instanceColor.needsUpdate = true;
  }
  return { group, draw };
}
