// Stage 00 check: every critic camera loads in three.js and frames its target at the centre.
// Run from app/: node cameras/check.mjs
import fs from 'node:fs';
import { cameraFromManifest } from '../src/world/cameras.js';
import * as THREE from 'three/webgpu';
const m = JSON.parse(fs.readFileSync(new URL('./manifest.json', import.meta.url)));
let bad = 0;
for (const c of m.cameras) {
  const cam = cameraFromManifest(m, c.id); cam.updateMatrixWorld();
  const p = new THREE.Vector3().fromArray(c.target).project(cam);
  const ok = Math.abs(p.x) < 1e-6 && Math.abs(p.y) < 1e-6 && p.z > -1 && p.z < 1;
  if (!ok) bad++;
  console.log(c.id, cam.type, ok ? 'target at centre' : 'FAIL', cam.isPerspectiveCamera ? `vfov ${cam.fov.toFixed(2)} (manifest ${c.vfov_deg})` : '');
}
process.exit(bad);
