import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { readFileSync } from 'node:fs';
import { heroDuskParameters, installHeroLighting } from '../src/hero/dusk.js';
import { panoramaManifest, choosePanorama, limitEnvToSpecular } from '../src/hero/environment.js';
import { cameraPoseFromManifest } from '../src/world/cameras.js';

test('day stays unchanged; dusk dims, warms and lights lamps continuously', () => {
  for (const minute of [450, 630, 750, 990]) {
    const day = heroDuskParameters(minute);
    assert.equal(day.lightMapIntensity, 1); assert.deepEqual(day.tint, [1, 1, 1]);
    assert.equal(day.lamps, 0); assert.equal(day.gradeWarmth, 0); assert.equal(day.panorama, 'day');
  }
  let previous = heroDuskParameters(990);
  for (let minute = 991; minute <= 1140; minute++) {
    const dusk = heroDuskParameters(minute);
    assert.ok(dusk.lightMapIntensity <= previous.lightMapIntensity);
    assert.ok(dusk.lamps >= previous.lamps); assert.ok(dusk.tint[2] <= previous.tint[2]); previous = dusk;
  }
  for (const minute of [1050, 1085, 1140]) {
    const dusk = heroDuskParameters(minute);
    assert.equal(dusk.panorama, 'evening'); assert.ok(dusk.lamps > 0);
    assert.ok(dusk.gradeWarmth > 0); assert.ok(dusk.lightMapIntensity < 1);
  }
  assert.ok(Math.abs(heroDuskParameters(1140).lightMapIntensity - 0.32) < 1e-12);
});
test('night is continuous at midnight and returns to day at dawn', () => {
  assert.deepEqual(heroDuskParameters(0), heroDuskParameters(1440));
  assert.deepEqual(heroDuskParameters(0), heroDuskParameters(1439));
  assert.ok(heroDuskParameters(390).dusk < heroDuskParameters(330).dusk);
  assert.equal(heroDuskParameters(450).dusk, 0);
});
test('installed bundle selects only 17:30 panorama at dusk', () => {
  const manifest = JSON.parse(readFileSync(new URL('../public/models/manifest.json', import.meta.url)));
  assert.equal(panoramaManifest(manifest, 'day'), manifest);
  const dusk = panoramaManifest(manifest, 'evening');
  assert.deepEqual(choosePanorama(dusk), ['env/talanta_pano_1730_2048.hdr']);
  assert.deepEqual(choosePanorama(dusk, { desktopGPU: true, maxTextureSize: 16384, memoryGB: 8, phone: false }), ['env/talanta_pano_1730.exr', 'env/talanta_pano_1730_2048.hdr']);
  assert.match(manifest.environment.file, /0730/);
});
test('dusk/day restores material baselines after panorama conversion; vehicles toggle', () => {
  const root = new THREE.Group();
  const facade = new THREE.MeshStandardMaterial({ color: '#eeeeee', lightMap: new THREE.Texture(), lightMapIntensity: 1.4 });
  const lamp = new THREE.MeshStandardMaterial({ emissive: 0, emissiveIntensity: 1 }); lamp.name = 'night_lamp_warm@site_layout.108';
  const car = new THREE.Mesh(new THREE.BoxGeometry(), facade); car.name = 'layout_cars_visualization';
  car.userData.heroLightmapped = true; root.add(car, new THREE.Mesh(new THREE.BoxGeometry(), lamp));
  const color = facade.color.toArray();
  let lighting = installHeroLighting(root); lighting.update(heroDuskParameters(1140));
  assert.ok(facade.lightMapIntensity < 1.4); assert.ok(facade.color.b < color[2]); assert.equal(lamp.emissiveIntensity, 6);
  lighting.setVehiclesVisible(false); assert.equal(car.visible, false);
  lighting.setVehiclesVisible(true); assert.equal(car.visible, true);
  limitEnvToSpecular(root, new THREE.Texture()); lighting = installHeroLighting(root);
  lighting.update(heroDuskParameters(630));
  assert.equal(car.material.lightMapIntensity, 1.4); assert.deepEqual(car.material.color.toArray(), color);
  assert.equal(lamp.emissiveIntensity, 1); assert.equal(lamp.emissive.getHex(), 0);
});
test('L06/L07 include Cycles position, target and vertical field of view', () => {
  const manifest = JSON.parse(readFileSync(new URL('../cameras/manifest.json', import.meta.url)));
  for (const [id, position, target, fov] of [
    ['L06', [328.05, 80.62, -293.24], [-1.24, 41.25, -1.2], 32.269],
    ['L07', [-124.22, 105.93, 472.69], [-17.39, 37.96, -4.93], 29.839],
  ]) {
    const pose = cameraPoseFromManifest(manifest, id);
    assert.deepEqual(pose.pos.toArray(), position); assert.deepEqual(pose.target.toArray(), target); assert.equal(pose.fov, fov);
  }
});
