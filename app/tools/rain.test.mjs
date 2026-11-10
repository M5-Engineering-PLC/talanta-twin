// Software scene and uniform tests. These tests do not render GPU pixels.
import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { installRain, rainCount, rainPosition, installWetLook } from '../src/weather/rain.js';
import { overcastState, installOvercast } from '../src/weather/sky.js';
import { installHeroLighting, heroDuskParameters } from '../src/hero/dusk.js';
import { limitEnvToSpecular } from '../src/hero/environment.js';

test('rain uses one instanced line draw and scales counts with the active tier', () => {
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(); camera.position.set(300, 60, -200);
  const rain = installRain({ scene, camera });
  assert.equal(scene.children.length, 1); assert.equal(rain.group.isLineSegments, true);
  assert.equal(rain.group.geometry.isInstancedBufferGeometry, true);
  assert.equal(rain.group.material.isLineBasicNodeMaterial, true);
  assert.equal(rain.group.castShadow, false); assert.equal(rain.group.material.depthWrite, false);
  for (const tier of ['low', 'medium', 'high', 'ultra']) {
    rain.update(50, .7, tier); assert.equal(rain.group.geometry.instanceCount, rainCount(tier));
    assert.equal(rain.group.geometry.drawRange.count, 2);
    assert.deepEqual(rain.group.position.toArray(), camera.position.toArray());
    assert.equal(rain.uniforms.clock.value, 50); assert.equal(rain.uniforms.amount.value, .7);
  }
  assert.ok(rainCount('low') < rainCount('medium')); assert.ok(rainCount('medium') < rainCount('high'));
  rain.update(62, 0); assert.equal(rain.group.visible, false);
  rain.update(52, 1); assert.equal(rain.group.visible, true);
  rain.dispose(); assert.equal(scene.children.length, 0);
});

test('rain positions repeat on a backward seek and stay near the camera', () => {
  const samples = Array.from({ length: 160 }, (_, i) => rainPosition(i, 52.5));
  for (let i = 0; i < samples.length; i++) {
    rainPosition(i, 800); assert.deepEqual(rainPosition(i, 52.5), samples[i]);
    assert.ok(samples[i][0] >= -22 && samples[i][0] <= 24);
    assert.ok(samples[i][1] >= -12 && samples[i][1] <= 20);
    assert.ok(samples[i][2] >= -22 && samples[i][2] <= 22);
  }
  assert.notDeepEqual(rainPosition(0, 52), rainPosition(0, 52.1));
});

test('wetness changes existing uniforms without a material replacement or version change', () => {
  const root = new THREE.Group(), material = new THREE.MeshStandardMaterial({ color: '#d0bbaa', roughness: .8, envMapIntensity: 1.2, lightMap: new THREE.Texture() });
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(), material); mesh.name = 'seat_concourse'; root.add(mesh);
  const weather = installWetLook(); weather.collect(root); const version = material.version, color = material.color.clone();
  for (let i = 0; i < 4; i++) {
    weather.update(1, 1); assert.equal(mesh.material, material); assert.equal(material.version, version);
    assert.equal(material.roughness, .14); assert.ok(material.envMapIntensity > 1.2); assert.ok(material.color.r < color.r);
    weather.restore(); assert.equal(material.roughness, .8); assert.equal(material.envMapIntensity, 1.2); assert.ok(material.color.equals(color));
  }
});

test('wetness works with specular-only baked node materials and dusk without cumulative tint', () => {
  const root = new THREE.Group(), source = new THREE.MeshStandardMaterial({ color: '#cccccc', roughness: .7, lightMap: new THREE.Texture() });
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(), source); mesh.name = 'baked_seats'; mesh.userData.heroLightmapped = true; root.add(mesh);
  limitEnvToSpecular(root, new THREE.Texture()); const material = mesh.material, version = material.version;
  const lighting = installHeroLighting(root), weather = installWetLook(); weather.collect(root);
  lighting.update(heroDuskParameters(1170)); const dusk = material.color.clone();
  for (let i = 0; i < 5; i++) {
    lighting.update(heroDuskParameters(1170)); weather.update(.8, 1); weather.restore(); assert.ok(material.color.equals(dusk));
  }
  assert.equal(material.version, version); assert.equal(mesh.material, material); assert.ok(material.isNodeMaterial);
});

test('floodlight and shield uniforms advance then restore their baselines', () => {
  const root = new THREE.Group(), weather = installWetLook(), materials = [];
  for (const name of ['flood_west', 'flood_east', 'shield_red']) {
    const mat = new THREE.MeshStandardMaterial({ emissive: '#880000', emissiveIntensity: .2 }); mat.name = name;
    root.add(new THREE.Mesh(new THREE.BoxGeometry(), mat)); materials.push(mat);
  }
  weather.collect(root); weather.update(0, .25, 1.5);
  assert.ok(materials[0].emissiveIntensity > materials[1].emissiveIntensity);
  assert.equal(materials[2].emissiveIntensity, 1.7);
  weather.restore(); for (const mat of materials) { assert.equal(mat.emissiveIntensity, .2); assert.equal(mat.emissive.getHex(), 0x880000); }
});

test('overcast dims panoramas and restores background and fog without accumulation', () => {
  const scene = new THREE.Scene(); scene.background = new THREE.Texture(); scene.backgroundIntensity = 1.2; scene.fog = new THREE.Fog('#aabbcc', 5, 200);
  const baseline = scene.fog.color.clone(); const weather = installOvercast({ scene, sky: {}, paintSky() {} });
  for (let i = 0; i < 4; i++) {
    weather.update(1, 1); assert.ok(scene.backgroundIntensity < 1.2); assert.ok(!scene.fog.color.equals(baseline));
    weather.restore(); assert.equal(scene.backgroundIntensity, 1.2); assert.ok(scene.fog.color.equals(baseline));
  }
  assert.equal(overcastState(0).backgroundGain, 1); assert.ok(overcastState(1).backgroundGain < 1);
});

test('overcast dome returns to its dry vertex colors', () => {
  const scene = new THREE.Scene(), sky = new THREE.Mesh(new THREE.SphereGeometry(5), new THREE.MeshBasicMaterial());
  sky.geometry.setAttribute('color', new THREE.Float32BufferAttribute(new Float32Array(sky.geometry.attributes.position.count * 3).fill(.8), 3));
  const baseline = sky.geometry.attributes.color.array.slice();
  const weather = installOvercast({ scene, sky, paintSky() { sky.geometry.attributes.color.array.fill(.2); } });
  weather.update(.5, 0); assert.ok(sky.geometry.attributes.color.array[0] < .8); weather.restore();
  assert.deepEqual(sky.geometry.attributes.color.array, baseline);
});
