import * as THREE from 'three/webgpu';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';

// The panorama centre maps to +x in three.js equirectangular UVs, so a +90 deg yaw turns it to north (-z) (checked by Sol with a software probe).
// Check by eye when the panorama lands: the Ngong Hills must sit to the south-west. ?panoyaw=<deg> overrides.
const NORTH_YAW = (() => { const q = new URLSearchParams(location.search).get('panoyaw'); return q == null ? Math.PI / 2 : (+q * Math.PI) / 180; })();

function listedEnvironmentFile(manifest, small) {
  const wanted = small ? manifest.environment?.file_2048 : manifest.environment?.file;
  const entry = manifest.files?.find((file) => file.file === wanted && file.file.startsWith('app/public/env/'));
  return entry?.file?.replace(/^app\/public\//, '');
}

/** Load the exported HDR panorama and apply it to the scene, or return null when it is unavailable. */
export async function loadEnvironment({ renderer, scene, manifest, base = './', preferSmall = false, environmentIntensity = 1 }) {
  const small = preferSmall || (typeof window !== 'undefined' && window.innerWidth < 768);
  const path = listedEnvironmentFile(manifest, small);
  if (!path) {
    console.warn('Environment panorama is missing from manifest.files.');
    return null;
  }

  const url = `${base.endsWith('/') ? base : `${base}/`}${path}`;
  try {
    const texture = await new HDRLoader().loadAsync(url);
    texture.mapping = THREE.EquirectangularReflectionMapping;
    texture.colorSpace = THREE.LinearSRGBColorSpace;
    scene.background = texture;
    scene.environment = texture;
    scene.backgroundRotation.y = NORTH_YAW;
    scene.environmentRotation.y = NORTH_YAW;
    scene.environmentIntensity = environmentIntensity;
    return {
      texture, rotation: new THREE.Euler(0, NORTH_YAW, 0),
      dispose() {
        if (scene.background === texture) scene.background = null;
        if (scene.environment === texture) scene.environment = null;
        texture.dispose();
      },
    };
  } catch (error) {
    console.warn(`Environment panorama failed to load: ${url}`, error);
    return null;
  }
}

/**
 * Keep the environment mostly specular on lightmapped meshes: their lightmap already holds the sky and bounce
 * diffuse (export contract), so full environment light would count it twice. three.js has no per-material
 * "specular only" switch that survives the WebGPU renderer's material conversion, so scale envMapIntensity by
 * (1 - roughness): rough surfaces, whose environment term is almost all diffuse, get little; glossy ones keep
 * their reflections. Approximation: glossy surfaces still get a little double diffuse.
 */
export function limitEnvToSpecular(root, envTexture) {
  if (!envTexture) return;
  root.traverse((object) => {
    if (!object.isMesh || !object.userData.heroLightmapped) return;
    for (const material of [object.material].flat()) {
      if (!material || !('envMapIntensity' in material)) continue;
      // envMapIntensity only applies when the material has its own envMap; scene.environment alone ignores it.
      material.envMap = envTexture; material.envMapRotation.y = NORTH_YAW;
      material.envMapIntensity = Math.max(0, 1 - (material.roughness ?? 1)); material.needsUpdate = true;
    }
  });
}

/** Sample the northern panorama horizon and return its average as a linear color for fog. */
export function horizonFogColor(texture) {
  const image = texture?.image;
  const data = image?.data;
  const width = image?.width;
  const height = image?.height;
  if (!data || !width || !height) return new THREE.Color(0xe7dfd1);

  const channels = data.length / (width * height);
  if (!Number.isInteger(channels) || channels < 3) return new THREE.Color(0xe7dfd1);
  // HDRLoader returns half floats (Uint16Array) by default: decode them.
  const val = data instanceof Uint16Array ? (i) => THREE.DataUtils.fromHalfFloat(data[i]) : (i) => data[i];
  const x0 = Math.floor(width * 0.45), x1 = Math.ceil(width * 0.55);
  const y0 = Math.floor(height * 0.48), y1 = Math.ceil(height * 0.52);
  const sum = [0, 0, 0];
  let count = 0;
  for (let y = y0; y < y1; y++) {
    for (let x = x0; x < x1; x++) {
      const i = (y * width + x) * channels;
      sum[0] += val(i); sum[1] += val(i + 1); sum[2] += val(i + 2);
      count++;
    }
  }
  return new THREE.Color().setRGB(sum[0] / count, sum[1] / count, sum[2] / count, THREE.LinearSRGBColorSpace);
}
