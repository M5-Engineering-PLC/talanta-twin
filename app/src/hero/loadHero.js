import * as THREE from 'three/webgpu';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

/** Load the baked stadium hero models and their manifest, off-scene: the caller adds result.group when ready. */
export async function loadHero({ renderer, scene, base = './models/' }) {
  const ktx2 = new KTX2Loader().setTranscoderPath('./basis/').detectSupport(renderer);
  const loader = new GLTFLoader().setKTX2Loader(ktx2).setMeshoptDecoder(MeshoptDecoder);
  try {
    const response = await fetch(`${base}manifest.json`);
    if (!response.ok) throw new Error(`manifest request failed: ${response.status}`);
    const manifest = await response.json();
    if (!manifest.models || typeof manifest.models !== 'object') throw new Error('manifest.models is missing');

    const group = new THREE.Group();
    group.name = 'talanta-hero';
    const lodGroups = new Map();
    let meshCount = 0;
    let triangleCount = 0;
    const modelEntries = Object.values(manifest.models);
    let loadedBytes = 0;

    for (const model of modelEntries) {
      if (!model?.file) throw new Error('manifest model file is missing');
      const file = model.file.split('/').at(-1);
      const gltf = await loader.loadAsync(`${base}${file}`);
      const modelRoot = gltf.scene;
      const standalone = [];

      modelRoot.traverse((node) => {
        if (!node.isMesh) return;
        meshCount++;
        const instances = node.isInstancedMesh ? node.count : 1;
        const index = node.geometry.index;
        triangleCount += (index ? index.count : node.geometry.attributes.position.count) / 3 * instances;
        const materials = Array.isArray(node.material) ? node.material : [node.material];
        for (const material of materials) {
          if (!material) continue;
          const lightmap = material.userData?.talanta_lightmap;
          if (!lightmap) continue;
          if (material.emissiveMap) {
            const texture = material.emissiveMap;
            texture.channel = lightmap.texCoord ?? texture.channel;
            texture.colorSpace = THREE.SRGBColorSpace;
            material.lightMap = texture;
          }
          material.emissive.set(0, 0, 0);
          material.emissiveMap = null;
          material.lightMapIntensity = lightmap.intensity;
          node.userData.heroLightmapped = true;
        }
        if (node.instanceColor) {
          node.instanceColor.needsUpdate = true;
        }
      });

      modelRoot.traverse((node) => {
        const extras = node.userData;
        if (!extras?.lod_group) return;
        const switchValue = extras.lod_switch_m;
        const distance = Array.isArray(switchValue) ? switchValue[extras.lod] : switchValue;
        if (!Number.isFinite(distance)) return;
        if (!lodGroups.has(extras.lod_group)) lodGroups.set(extras.lod_group, { levels: [], max: Infinity });
        const entry = lodGroups.get(extras.lod_group);
        entry.levels.push({ node, distance: extras.lod === 0 ? 0 : distance, level: extras.lod ?? 0 });
        if (Number.isFinite(extras.lod_max_m)) entry.max = Math.min(entry.max, extras.lod_max_m);
      });

      const candidates = new Set();
      for (const { levels } of lodGroups.values()) for (const level of levels) candidates.add(level.node);
      modelRoot.traverse((node) => {
        if (!candidates.has(node)) standalone.push(node);
      });
      for (const node of standalone) {
        if (node.parent === modelRoot) group.add(node);
      }
      loadedBytes += model.bytes ?? 0;
    }

    for (const [name, entry] of lodGroups) {
      const lod = new THREE.LOD();
      lod.name = name;
      entry.levels.sort((a, b) => a.distance - b.distance || a.level - b.level);
      for (const { node, distance } of entry.levels) {
        node.updateWorldMatrix(true, false);
        lod.attach(node);
        lod.addLevel(node, distance);
      }
      if (Number.isFinite(entry.max)) lod.addLevel(new THREE.Object3D(), entry.max);
      group.add(lod);
      lodGroups.set(name, entry);
    }

    const fileSizes = modelEntries.map((model) => ({ file: model.file.split('/').at(-1), bytes: model.bytes ?? 0 }));
    console.info('web hero loaded:', { files: fileSizes, totalBytes: loadedBytes, meshes: meshCount, triangles: Math.round(triangleCount), lodGroups: lodGroups.size });
    ktx2.dispose();
    return { group, manifest };
  } catch (error) {
    console.warn('web hero unavailable; keeping procedural scene:', error);
    ktx2.dispose();
    return null;
  }
}
