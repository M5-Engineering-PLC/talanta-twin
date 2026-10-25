import * as THREE from 'three/webgpu';
import { vec3 } from 'three/tsl';
import { EXRLoader } from 'three/addons/loaders/EXRLoader.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';

// The panorama centre maps to +x in three.js equirectangular UVs, so a +90 deg yaw turns it to north (-z) (checked by Sol with a software probe).
// Check by eye when the panorama lands: the Ngong Hills must sit to the south-west. ?panoyaw=<deg> overrides.
const NORTH_YAW = (() => { const q = new URLSearchParams(typeof location === 'undefined' ? '' : location.search).get('panoyaw'); return q == null ? Math.PI / 2 : (+q * Math.PI) / 180; })();

function specularEnvironmentMaterial(BaseMaterial) {
  return class extends BaseMaterial {
    copy(source) {
      super.copy(source);
      // NodeMaterial.copy skips Material's inherited alphaTest accessor in three.js 0.186.1.
      this.alphaTest = source.alphaTest;
      return this;
    }

    customProgramCacheKey() {
      return `${super.customProgramCacheKey()}:hero-env-specular`;
    }

    setupLightingModel(builder) {
      const model = super.setupLightingModel(builder);
      const indirectSpecular = model.indirectSpecular;
      model.indirectSpecular = function (builder) {
        const context = builder.context;
        // PhysicalLightingModel.indirectSpecular adds BOTH environment lobes. Discard only its diffuse output.
        // Keep iblIrradiance: specular multiscattering and sheen use it too. Lightmap diffuse and AO stay unchanged.
        builder.context = { ...context, reflectedLight: { ...context.reflectedLight, indirectDiffuse: vec3().toVar() } };
        try {
          indirectSpecular.call(this, builder);
        } finally {
          builder.context = context;
        }
      };
      return model;
    }
  };
}

const SpecularStandardMaterial = specularEnvironmentMaterial(THREE.MeshStandardNodeMaterial);
const SpecularPhysicalMaterial = specularEnvironmentMaterial(THREE.MeshPhysicalNodeMaterial);

export function choosePanorama(manifest, { desktopGPU = false, maxTextureSize = 0, memoryGB = 0, phone = true, preferSmall = false } = {}) {
  const env = manifest.environment ?? {};
  const files = (manifest.files ?? []).map(f => f.file).filter(f => f.startsWith('app/public/env/'));
  const hdr = [env.file_2048, env.file].find(f => files.includes(f) && /\.hdr$/i.test(f));
  const stem = hdr?.replace(/_2048\.hdr$/i, '');
  const exr = [env.file_exr, env.file, ...files.filter(f => f === `${stem}.exr`)].find(f => files.includes(f) && /\.exr$/i.test(f));
  const large = !preferSmall && !phone && desktopGPU && memoryGB >= 8 && maxTextureSize >= (env.resolution?.[0] ?? 8192);
  return [...new Set([large && exr, hdr].filter(Boolean))].map(f => f.replace(/^app\/public\//, ''));
}

export function panoramaDevice(renderer, preferSmall) {
  const backend = renderer.backend;
  const gl = backend?.gl;
  const maxTextureSize = backend?.device?.limits?.maxTextureDimension2D ?? (gl ? gl.getParameter(gl.MAX_TEXTURE_SIZE) : 0);
  let gpu = backend?.adapter?.info?.device ?? backend?.adapter?.info?.description ?? '';
  if (gl) {
    const debug = gl.getExtension('WEBGL_debug_renderer_info');
    if (debug) gpu = gl.getParameter(debug.UNMASKED_RENDERER_WEBGL);
  }
  const nav = globalThis.navigator;
  const phone = /Android|iPhone|iPad|Mobile/i.test(nav?.userAgent ?? '') || (nav?.maxTouchPoints > 1 && /Macintosh/i.test(nav?.userAgent ?? '')) || (globalThis.innerWidth ?? 0) < 768;
  return { phone, preferSmall, maxTextureSize, memoryGB: nav?.deviceMemory ?? 8,
    desktopGPU: Boolean(backend?.isWebGPUBackend || gl) && !/swiftshader|llvmpipe|software/i.test(gpu) };
}

/** Load a capable desktop's EXR or fall back to the small HDR. */
export async function loadEnvironment({ renderer, scene, manifest, base = './', preferSmall = false, environmentIntensity = 1 }) {
  const paths = choosePanorama(manifest, panoramaDevice(renderer, preferSmall));
  for (const path of paths) {
    const url = `${base.endsWith('/') ? base : `${base}/`}${path}`;
    try {
      const loader = /\.exr$/i.test(path) ? new EXRLoader() : new HDRLoader();
      const texture = await loader.loadAsync(url);
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
    }
  }
  console.warn('Environment panorama unavailable; keeping procedural sky.');
  return null;
}

/**
 * Convert lightmapped materials to node materials with specular-only environment lighting on both WebGPURenderer backends.
 * Their lightmaps already hold sky and bounce diffuse light (export contract). Discard the environment diffuse output,
 * but retain the full specular calculation, panorama rotation, and AO. Materials without lightmaps keep full environment lighting.
 */
export function limitEnvToSpecular(root, envTexture) {
  if (!envTexture) return;
  const converted = new Map();
  root.traverse((object) => {
    if (!object.isMesh || !object.userData.heroLightmapped) return;
    const convert = (source) => {
      if (!source?.lightMap || !('envMapIntensity' in source)) return source;
      if (converted.has(source)) return converted.get(source);
      const physical = source.isMeshPhysicalMaterial || source.isMeshPhysicalNodeMaterial;
      const Material = physical ? SpecularPhysicalMaterial : SpecularStandardMaterial;
      const material = source instanceof Material ? source : new Material().copy(source);
      material.envMap = envTexture;
      material.envMapRotation.y = NORTH_YAW;
      material.needsUpdate = true;
      converted.set(source, material);
      return material;
    };
    object.material = Array.isArray(object.material) ? object.material.map(convert) : convert(object.material);
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

/** Select only the installed 17:30 panorama entries for the evening approximation. */
export function panoramaManifest(manifest, period) {
  if (period !== 'evening') return manifest;
  const files = (manifest.files ?? []).map((entry) => entry.file);
  const hdr = files.find((file) => /\/talanta_pano_1730_2048\.hdr$/.test(file));
  const exr = files.find((file) => /\/talanta_pano_1730\.exr$/.test(file));
  return { ...manifest, environment: { ...manifest.environment,
    preset: 'evening_golden', file: hdr, file_2048: hdr, file_exr: exr } };
}
