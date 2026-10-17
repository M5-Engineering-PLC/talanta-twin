import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { limitEnvToSpecular } from '../src/hero/environment.js';

const env = new THREE.Texture();
const root = new THREE.Group();
const maps = ['map', 'lightMap', 'aoMap', 'normalMap', 'roughnessMap', 'metalnessMap', 'alphaMap', 'emissiveMap'];

for (const BaseMaterial of [THREE.MeshStandardMaterial, THREE.MeshPhysicalMaterial]) {
  const source = new BaseMaterial({
    color: 0x345678, roughness: 0.94, metalness: 0.23,
    lightMapIntensity: 2.7, aoMapIntensity: 0.63, normalScale: new THREE.Vector2(0.4, -0.7),
    opacity: 0.64, transparent: true, alphaTest: 0.31, vertexColors: true,
    side: THREE.DoubleSide, depthWrite: false, envMapIntensity: 0.82,
    emissive: 0x123456, emissiveIntensity: 0.42,
  });
  source.name = 'baked';
  source.userData.talanta_lightmap = { texCoord: 1, intensity: 2.7 };
  for (const key of maps) {
    source[key] = new THREE.Texture();
    source[key].channel = key === 'lightMap' ? 1 : 0;
  }
  source.lightMap.colorSpace = THREE.SRGBColorSpace;
  if (source.isMeshPhysicalMaterial) {
    source.clearcoat = 0.6;
    source.clearcoatRoughness = 0.27;
    source.clearcoatMap = new THREE.Texture();
    source.transmission = 0.2;
    source.ior = 1.4;
    source.sheen = 0.3;
    source.sheenColor.set(0x567890);
  }
  const untouched = new THREE.MeshStandardMaterial();
  const mesh = new THREE.Mesh(new THREE.BufferGeometry(), [source, untouched]);
  mesh.userData.heroLightmapped = true;
  const shared = new THREE.Mesh(mesh.geometry, source);
  shared.userData.heroLightmapped = true;
  // A non-lightmapped mesh can share the source. Its material must stay unchanged.
  const unmarked = new THREE.Mesh(mesh.geometry, source);
  root.add(mesh, shared, unmarked);
  limitEnvToSpecular(root, env);

  const material = mesh.material[0];
  assert.notEqual(material, source);
  assert.equal(material.isNodeMaterial, true);
  assert.equal(material.isMeshStandardNodeMaterial, true);
  assert.equal(!!material.isMeshPhysicalNodeMaterial, !!source.isMeshPhysicalMaterial);
  assert.equal(shared.material, material);
  assert.equal(mesh.material[1], untouched);
  assert.equal(unmarked.material, source);
  assert.equal(source.envMap, null);
  for (const key of maps) assert.equal(material[key], source[key], key);
  assert.equal(material.lightMap.channel, 1);
  assert.equal(material.lightMap.colorSpace, THREE.SRGBColorSpace);
  for (const key of ['color', 'emissive', 'normalScale', 'userData']) assert.deepEqual(material[key], source[key], key);
  for (const key of ['name', 'roughness', 'metalness', 'lightMapIntensity', 'aoMapIntensity', 'opacity',
    'transparent', 'alphaTest', 'vertexColors', 'side', 'depthWrite', 'envMapIntensity', 'emissiveIntensity']) {
    assert.equal(material[key], source[key], key);
  }
  if (source.isMeshPhysicalMaterial) {
    for (const key of ['clearcoat', 'clearcoatRoughness', 'clearcoatMap', 'transmission', 'ior', 'sheen']) {
      assert.equal(material[key], source[key], key);
    }
    assert.deepEqual(material.sheenColor, source.sheenColor);
  }
  assert.equal(material.envMap, env);
  assert.equal(material.envMapRotation.y, Math.PI / 2);
  const BaseNodeMaterial = source.isMeshPhysicalMaterial ? THREE.MeshPhysicalNodeMaterial : THREE.MeshStandardNodeMaterial;
  const stock = new BaseNodeMaterial();
  const stockModel = stock.setupLightingModel();
  const model = material.setupLightingModel();
  assert.notEqual(model.indirectSpecular, stockModel.indirectSpecular);
  assert.equal(model.indirectDiffuse, stockModel.indirectDiffuse);
  assert.equal(model.ambientOcclusion, stockModel.ambientOcclusion);
  assert.notEqual(material.customProgramCacheKey(), stock.customProgramCacheKey());
  const clone = material.clone();
  assert.notEqual(clone.setupLightingModel().indirectSpecular, stockModel.indirectSpecular);
  limitEnvToSpecular(root, env);
  assert.equal(mesh.material[0], material);
  console.log(`PASS (software): ${source.type} conversion preserves maps, values, AO hook, rotation, sharing, cloning, and repeated calls.`);
}

const untouched = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshStandardMaterial());
root.add(untouched);
limitEnvToSpecular(root, null);
limitEnvToSpecular(root, env);
assert.equal(untouched.material.isNodeMaterial, undefined);
console.log('PASS (software): non-lightmapped materials stay unchanged; no rendering performed.');
