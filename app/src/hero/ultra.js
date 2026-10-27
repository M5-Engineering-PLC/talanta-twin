import * as THREE from 'three/webgpu';
import {
  Fn, pass, mrt, output, normalView, diffuseColor, velocity, metalness, roughness,
  float, vec2, vec4, uniform, sample, packNormalToRGB, unpackRGBToNormal,
  logarithmicDepthToViewZ, viewZToPerspectiveDepth, exponentialHeightFogFactor,
  fog, mix, densityFogFactor, texture3D, convertToTexture, screenUV,
} from 'three/tsl';
import { ssgi } from 'three/addons/tsl/display/SSGINode.js';
import { denoise } from 'three/addons/tsl/display/DenoiseNode.js';
import { ao } from 'three/addons/tsl/display/GTAONode.js';
import { ssr } from 'three/addons/tsl/display/SSRNode.js';
import { traa } from 'three/addons/tsl/display/TRAANode.js';
import { bloom } from 'three/addons/tsl/display/BloomNode.js';
import { gaussianBlur } from 'three/addons/tsl/display/GaussianBlurNode.js';
import { godrays } from 'three/addons/tsl/display/GodraysNode.js';
import { bilateralBlur } from 'three/addons/tsl/display/BilateralBlurNode.js';
import { depthAwareBlend } from 'three/addons/tsl/display/depthAwareBlend.js';
import { lensflare } from 'three/addons/tsl/display/LensflareNode.js';
import { film } from 'three/addons/tsl/display/FilmNode.js';
import { lut3D } from 'three/addons/tsl/display/Lut3DNode.js';
import { sss } from 'three/addons/tsl/display/SSSNode.js';
import { IESLoader } from 'three/addons/loaders/IESLoader.js';
import { fallbackFacadeLines, validFacadeLines, padY } from '../shows/geometry.js';
import { heroDuskParameters } from './dusk.js';
import { heroGrade, heroLookCurve } from './heroLook.js';

// three.js r186 examples (MIT): webgpu_postprocessing_ssgi.html,
// webgpu_postprocessing_ssr.html, webgpu_postprocessing_traa.html,
// webgpu_postprocessing_godrays.html, webgpu_postprocessing_lensflare.html,
// webgpu_custom_fog_scattering.html, webgpu_fog_height.html,
// webgpu_lights_ies_spotlight.html, webgpu_postprocessing_bloom_selective.html.
// https://github.com/mrdoob/three.js/tree/r186/examples
// This module and its imports are reachable only through main.js's ultra import.
// All lighting, geometry positions and cost counts here are software visualizations.

export const DEFAULT_SETTINGS = Object.freeze({
  ssgi: true, denoise: true, traa: true, ao: true, ssr: true,
  fog: true, godrays: false, lights: true, bloom: true,
  flare: false, grain: false, lut: false, sss: false,
});

// Structural cost estimates from the r186 implementations, not device timings.
export const EFFECT_COSTS = Object.freeze({
  ssgi: 'One full-resolution pass, 32 ray samples per pixel at 2 slices and 8 steps.',
  denoise: 'Two 17-tap filters in the composite when SSGI and AO are enabled.',
  traa: 'Full-resolution composite and resolve, color history copy and depth history copy.',
  ao: 'SSGI AO reuses its pass. Separate GTAO uses one half-resolution pass.',
  ssr: 'One half-resolution ray pass and a blur mip chain. Rough pixels exit before tracing.',
  fog: 'Inline height fog, composite texture and two half-resolution scattering blur passes.',
  godrays: 'One half-resolution 24-step pass, bilateral blur and depth-aware composite.',
  lights: 'At most eight shadowless IES lights in the scene pass. No shadow draws.',
  bloom: 'One bright pass, ten blur passes and one composite at half resolution or smaller.',
  flare: 'A separate bloom source and a quarter-resolution flare pass.',
  grain: 'Inline arithmetic. No additional render target.',
  lut: 'One inline 3D texture lookup. The generated 16-cubed RGBA8 table uses 16384 bytes.',
  sss: 'One full-resolution contact pass, limited to a 0.35 m ray length.',
});

/** A present ultra= list replaces the defaults. none/0 disables additions; all enables them. */
export function parseUltraSettings(search = '') {
  const params = new URLSearchParams(search);
  if (!params.has('ultra')) return { ...DEFAULT_SETTINGS };
  const tokens = params.get('ultra').toLowerCase().split(',').map(s => s.trim());
  const result = Object.fromEntries(Object.keys(DEFAULT_SETTINGS).map(key => [key, tokens.includes('all')]));
  for (const token of tokens) {
    const key = token.replace(/^[-+]/, '');
    if (Object.hasOwn(result, key)) result[key] = !token.startsWith('-');
  }
  return result;
}

const warnings = new Set();
function warnOnce(key, message, error) {
  if (warnings.has(key)) return;
  warnings.add(key);
  console.warn(`ultra: ${message}`, ...(error ? [error] : []));
}

/** Conservative WebGL2 policy until these temporal/ray passes pass device testing. */
export function supportedSettings(requested, renderer) {
  const effective = { ...requested };
  if (!renderer.backend?.isWebGPUBackend) {
    const skipped = ['ssgi', 'traa', 'ssr', 'godrays', 'sss'].filter(key => effective[key]);
    for (const key of skipped) effective[key] = false;
    if (skipped.length) warnOnce('webgl', `WebGL2 uses the conservative path; skipped ${skipped.join(', ')}. MSAA and the existing AO remain available.`);
  }
  return effective;
}

export function bakedMaterial(material) {
  // The lightMap check covers the interval before panorama conversion and late ground tiles.
  return material?.userData?.ultraBaked === true || Boolean(material?.lightMap);
}
export function lampMaterial(material, object) {
  return /^night_lamp_warm(?:@|\.|$)/.test(material?.name ?? '') || object?.name === 'SHW-01' || object?.userData?.ultraLamp === true;
}

export function maskIndirect(indirect, baked) {
  return indirect.mul(baked.oneMinus());
}

// The mask is compiled per material, rather than a uniform shared across draw calls.
// RGBA properties pack metalness, roughness, baked mask and lamp selection.
export const bakedMaskNode = Fn(builder => float(bakedMaterial(builder.material) ? 1 : 0));
const propertiesNode = Fn(builder => vec4(
  builder.material.metalness !== undefined ? metalness : float(0),
  builder.material.roughness !== undefined ? roughness : float(1),
  bakedMaskNode(), float(lampMaterial(builder.material, builder.object) ? 1 : 0),
));

/** At most eight shadowless IES lights. Positions use the existing show data only. */
export function createFloodlights(scene, geometry, iesMap) {
  const root = new THREE.Group(); root.name = 'ultra-lights-Visualization'; root.position.y = padY;
  const entries = geometry.floodlights, count = Math.min(8, entries.length);
  const lights = Array.from({ length: count }, (_, i) => {
    const source = entries[Math.floor(i * entries.length / count)];
    const light = new THREE.IESSpotLight(0xfff1db, 0);
    light.position.fromArray(source.pos); light.target.position.fromArray(source.aim);
    light.distance = 250; light.angle = Math.PI / 7; light.penumbra = 0.5;
    light.castShadow = false; light.iesMap = iesMap;
    root.add(light, light.target); return light;
  });
  scene.add(root);
  return {
    root, lights,
    update(minutes) {
      const amount = heroDuskParameters(minutes).dusk;
      for (const light of lights) light.intensity = 180000 * amount;
    },
    dispose() { root.removeFromParent(); for (const light of lights) light.dispose(); },
  };
}

/** Existing lamp heads stay emissive while the ultra rig owns the eight-light budget. */
export function limitSpotlights(scene, root) {
  const saved = [];
  scene.traverse(object => {
    if (object.isSpotLight && object.parent !== root) {
      saved.push([object, object.intensity]); object.intensity = 0;
    }
  });
  return () => { for (const [light, intensity] of saved) light.intensity = intensity; };
}

function disposeResources(resources) {
  const visited = new Set(), extra = [];
  const visit = node => {
    if (!node || visited.has(node)) return;
    visited.add(node);
    if (node.isRTTNode && !resources.includes(node)) extra.push(node);
    if (node.getChildren) for (const child of node.getChildren()) visit(child);
  };
  for (const resource of resources) visit(resource);
  for (const resource of [...extra, ...resources].reverse()) resource.dispose?.();
}

// No binary LUT download. A small generated 3D table adds a mild toe and shoulder
// after heroGrade. The existing grade preset and tone mapping remain the base.
export function createCameraLut(size = 16) {
  const data = new Uint8Array(size ** 3 * 4);
  for (let b = 0; b < size; b++) for (let g = 0; g < size; g++) for (let r = 0; r < size; r++) {
    const offset = (r + g * size + b * size * size) * 4;
    for (const [channel, value] of [r, g, b].entries()) {
      const x = value / (size - 1);
      data[offset + channel] = Math.round(255 * (x + 0.04 * x * (1 - x) * (2 * x - 1)));
    }
    data[offset + 3] = 255;
  }
  const lut = new THREE.Data3DTexture(data, size, size, size);
  lut.format = THREE.RGBAFormat; lut.type = THREE.UnsignedByteType;
  lut.minFilter = lut.magFilter = THREE.LinearFilter; lut.unpackAlignment = 1; lut.needsUpdate = true;
  return lut;
}

/** Return null before allocation when additions are off. main.js then uses its exact high chain. */
export function createUltraPipeline({ settings, renderer, scene, camera, sun, look, measured, manifest,
  warmth, exposure, minutes = () => 630, onFailure = () => {}, onSettings = () => {} }) {
  if (!Object.entries(settings).some(([key, enabled]) => enabled && key !== 'denoise')) return null;
  const active = supportedSettings(settings, renderer);
  if (!Object.entries(active).some(([key, enabled]) => enabled && key !== 'denoise')) return null;
  const resources = [], own = node => { resources.push(node); return node; };
  let disposed = false, failed = false, lighting = null, iesTexture = null;
  const abort = new AbortController();
  try {
    const pipeline = own(new THREE.RenderPipeline(renderer));
    // TRAA replaces scene MSAA without changing the renderer constructor or other tiers.
    const scenePass = own(pass(scene, camera, active.traa ? { samples: 0 } : {}));
    const attachments = { output };
    if (active.ssgi || active.ssr || active.ao) attachments.normal = packNormalToRGB(normalView);
    if (active.ssgi) attachments.diffuse = diffuseColor;
    if (active.traa) attachments.velocity = velocity;
    if (active.ssgi || active.ssr || active.bloom || active.flare) attachments.properties = propertiesNode();
    scenePass.setMRT(mrt(attachments).setClearColor('properties', 0, 0).setClearColor('normal', 0, 0));
    // At most 24 color bytes per pixel, below WebGPU's default 32-byte attachment budget.
    for (const name of ['normal', 'diffuse', 'properties']) if (attachments[name]) scenePass.getTexture(name).type = THREE.UnsignedByteType;
    if (active.traa) scenePass.getTexture('velocity').format = THREE.RGFormat;
    const beauty = scenePass.getTextureNode('output'), depth = scenePass.getTextureNode('depth');
    const normal = attachments.normal ? sample(uv => unpackRGBToNormal(scenePass.getTextureNode('normal').sample(uv))) : null;
    const properties = attachments.properties ? scenePass.getTextureNode('properties') : null;
    let shaded = beauty;
    const effects = {};
    if (active.ssgi) {
      const gi = effects.ssgi = own(ssgi(beauty, depth, normal, camera));
      gi.sliceCount.value = 2; gi.stepCount.value = 8; gi.giIntensity.value = 1;
      gi.aoIntensity.value = 0.65; gi.radius.value = 8;
      // DenoiseNode expects perspective depth, unlike SSGINode's log-depth-aware input.
      const near = uniform(camera.near), far = uniform(camera.far);
      const perspectiveDepth = renderer.logarithmicDepthBuffer ? sample(uv =>
        viewZToPerspectiveDepth(logarithmicDepthToViewZ(depth.sample(uv).r, near, far), near, far)) : depth;
      const indirect = active.denoise ? own(denoise(gi.getGINode(), perspectiveDepth, normal, camera)) : gi.getGINode();
      const ambient = active.ao ? (active.denoise ? own(denoise(gi.getAONode(), perspectiveDepth, normal, camera)).r : gi.getAONode().r) : float(1);
      // Do not add any SSGI indirect light to baked pixels, including floodlight bounce.
      shaded = vec4(beauty.rgb.mul(ambient).add(maskIndirect(scenePass.getTextureNode('diffuse').rgb.mul(indirect.rgb), properties.b)), beauty.a);
    } else if (active.ao && !measured) {
      const ambient = effects.ao = own(ao(depth, normal, camera));
      ambient.resolutionScale = 0.5; ambient.radius.value = 1.2;
      shaded = vec4(shaded.rgb.mul(ambient.getTextureNode().r.mul(0.85).add(0.15)), shaded.a);
    }
    if (active.ssr) {
      // The mirror path uses metalnessNode as reflection weight and discards zero weights
      // before tracing. Include the 0.04 dielectric base reflectance only below the cutoff.
      const weight = properties.g.lessThan(0.35).select(properties.r.max(0.04), 0);
      const reflections = effects.ssr = own(ssr(beauty, depth, normal, { metalnessNode: weight, roughnessNode: properties.g }));
      reflections.resolutionScale = 0.5; reflections.quality.value = 0.5; reflections.intensity.value = 0.2;
      // Mirror/gloss surfaces only. No wetness or material roughness is invented here.
      shaded = vec4(shaded.rgb.add(reflections.rgb.mul(properties.g.lessThan(0.35))), shaded.a);
    }
    if (active.sss && sun?.isDirectionalLight) {
      const contact = effects.sss = own(sss(depth, camera, sun));
      contact.maxDistance.value = 0.35; contact.shadowIntensity.value = 0.25;
      const daylight = uniform(1).onFrameUpdate(() => 1 - heroDuskParameters(minutes()).dusk);
      shaded = vec4(shaded.rgb.mul(mix(float(1), contact, daylight)), shaded.a);
    }
    if (active.godrays) {
      if (sun?.castShadow && renderer.shadowMap.enabled) {
        const rays = effects.godrays = own(godrays(depth, camera, sun));
        rays.resolutionScale = 0.5; rays.raymarchSteps.value = 24; rays.density.value = 0.005;
        const blurred = own(bilateralBlur(rays.getTextureNode()));
        // depthAwareBlend samples its inputs. Materialize the composite before blending.
        const source = own(convertToTexture(shaded));
        const perspectiveDepth = renderer.logarithmicDepthBuffer ? sample(uv => viewZToPerspectiveDepth(
          logarithmicDepthToViewZ(depth.sample(uv).r, uniform(camera.near), uniform(camera.far)), uniform(camera.near), uniform(camera.far))) : depth;
        shaded = depthAwareBlend(source, blurred, perspectiveDepth, camera, { blendColor: sun.color });
      } else {
        active.godrays = false;
        warnOnce('godrays', 'GodraysNode needs a shadowed directional/point light. Baked hero and shadowless IES spotlights skip god rays.');
      }
    }
    let heightFog = null;
    if (active.fog) {
      // Same exponential-height factor as webgpu_fog_height; scene state is restored after each render.
      const fogColor = uniform(new THREE.Color(0xc8ced0)).onFrameUpdate(() => scene.fog?.color ?? new THREE.Color(0xc8ced0));
      heightFog = fog(fogColor, exponentialHeightFogFactor(float(0.000012), float(padY + 75)));
      const scattered = effects.fog = own(gaussianBlur(shaded, vec2(1), 2, { resolutionScale: 0.5 }));
      const viewZ = renderer.logarithmicDepthBuffer ? logarithmicDepthToViewZ(depth.r, uniform(camera.near), uniform(camera.far)) : scenePass.getViewZNode();
      const scatterFactor = densityFogFactor(float(0.00012)).context({ getViewZ: () => viewZ }).mul(0.12);
      shaded = mix(shaded, scattered, scatterFactor);
    }
    const graded = heroGrade(shaded, measured ? { manifest, exposure } : { warmth });
    let composed = graded;
    let lampBloom = null;
    if (active.bloom || active.flare) {
      lampBloom = effects.bloom = own(bloom(beauty.mul(properties.a), active.bloom ? look.bloom.strength : 0, look.bloom.radius, look.bloom.threshold));
      lampBloom.setResolutionScale(0.5);
      if (active.bloom) composed = composed.add(lampBloom);
      if (active.flare) {
        // Flare has its own source so bloom can remain independently off.
        const sunUV = uniform(new THREE.Vector2(-10, -10)), sunVisible = uniform(0);
        const direction = new THREE.Vector3(), projected = new THREE.Vector3(), forward = new THREE.Vector3();
        sunVisible.onFrameUpdate(() => {
          if (!sun) return 0;
          direction.copy(sun.position).sub(sun.target.position).normalize();
          projected.copy(direction).multiplyScalar(camera.far * 0.9).add(camera.position).project(camera);
          sunUV.value.set(projected.x * 0.5 + 0.5, 0.5 - projected.y * 0.5);
          return direction.y > 0 && camera.getWorldDirection(forward).dot(direction) > 0 ? 1 : 0;
        });
        const sunMask = screenUV.distance(sunUV).lessThan(0.018).mul(depth.r.greaterThan(0.999)).mul(sunVisible);
        const source = own(bloom(beauty.mul(properties.a.add(sunMask)), 0.15, look.bloom.radius, look.bloom.threshold));
        source.setResolutionScale(0.5);
        const flare = effects.flare = own(lensflare(source, { ghostSamples: 3, ghostAttenuationFactor: 40 }));
        composed = composed.add(flare.mul(0.08));
      }
    }
    if (active.lut) {
      const lut = own(createCameraLut());
      composed = lut3D(composed, texture3D(lut), 16, float(0.18));
    }
    if (active.grain) composed = film(composed, float(0.012));
    // Resolve last. Keep heroLook.js's measured curve and tone mapping decisions.
    composed = measured ? heroLookCurve(composed, measured, exposure) : composed;
    if (active.traa) composed = effects.traa = own(traa(composed, depth, scenePass.getTextureNode('velocity'), camera));
    pipeline.outputColorTransform = !measured; pipeline.outputNode = composed; pipeline.needsUpdate = true;

    if (active.lights) {
      // Load assets only after ultra selection. No IES profile or geometry enters tier 0.
      const loader = new IESLoader(); loader.type = THREE.UnsignedByteType;
      fetch('./ultra/007cfb11e343e2f42e3b476be4ab684e.ies', { signal: abort.signal }).then(response => {
        if (!response.ok) throw new Error(`IES request failed: ${response.status}`);
        return response.text();
      }).then(text => {
        if (disposed) return;
        iesTexture = loader.parse(text);
        lighting = createFloodlights(scene, fallbackFacadeLines(), iesTexture);
        lighting.update(minutes());
        return fetch('./data/facade_lines.json', { signal: abort.signal }).then(async response => {
          if (!response.ok || disposed) return;
          const geometry = await response.json();
          if (!validFacadeLines(geometry) || disposed) return;
          lighting.dispose(); lighting = createFloodlights(scene, geometry, iesTexture); lighting.update(minutes());
        });
      }).catch(error => { if (!disposed) warnOnce('ies', 'IES or optional show geometry unavailable; existing emissive lamps remain.', error); });
    }

    const stats = { claim: 'software', active, renderCalls: 0, effectCalls: {}, cpuSubmitMs: null, gpuMs: null,
      note: 'CPU submission time is not GPU duration. Compare single-effect URL runs at the same view.' };
    // Counts include dependent passes. Isolate effects with ultra=<name> for comparisons.
    for (const [name, node] of Object.entries(effects)) {
      if (typeof node.updateBefore !== 'function') continue;
      const update = node.updateBefore;
      node.updateBefore = function(frame) {
        const before = frame.renderer.info.render.calls;
        try { return update.call(this, frame); }
        finally { stats.effectCalls[name] = frame.renderer.info.render.calls - before; }
      };
    }
    const api = { settings, active, stats, effects, estimatedCosts: EFFECT_COSTS,
      async sampleGpu() {
        if (!renderer.backend.trackTimestamp) return null;
        stats.gpuMs = await renderer.resolveTimestampsAsync('render');
        return stats.gpuMs;
      },
      apply(patch = {}) {
        for (const key of Object.keys(DEFAULT_SETTINGS)) if (Object.hasOwn(patch, key)) settings[key] = Boolean(patch[key]);
        onSettings();
      },
    };
    globalThis.ultra = api;
    const controller = {
      isUltraPipeline: true, bloomPass: active.bloom ? lampBloom : null, scenePass, effects, stats,
      render() {
        if (disposed) return;
        lighting?.update(minutes());
        const saved = THREE.RendererUtils.saveRendererState(renderer);
        const savedXR = renderer.xr.enabled;
        const restoreLights = active.lights ? limitSpotlights(scene, lighting?.root) : () => {};
        const savedFog = scene.fogNode, savedOverride = scene.overrideMaterial;
        const savedView = camera.view ? { ...camera.view } : null;
        const projection = camera.projectionMatrix.clone(), inverse = camera.projectionMatrixInverse.clone();
        const before = renderer.info.render.calls, started = performance.now();
        try {
          if (heightFog) scene.fogNode = heightFog;
          pipeline.render();
          stats.renderCalls = renderer.info.render.calls - before;
          stats.cpuSubmitMs = performance.now() - started;
        } catch (error) {
          failed = true;
          camera.view = savedView; camera.projectionMatrix.copy(projection); camera.projectionMatrixInverse.copy(inverse);
          warnOnce('render', 'effect pipeline failed; restoring the high path.', error);
        } finally {
          restoreLights(); renderer.xr.enabled = savedXR;
          scene.fogNode = savedFog; scene.overrideMaterial = savedOverride;
          THREE.RendererUtils.restoreRendererState(renderer, saved);
        }
        if (failed) {
          controller.dispose(); onFailure();
          renderer.render(scene, camera);
        }
      },
      dispose() {
        if (disposed) return;
        disposed = true; abort.abort(); lighting?.dispose(); iesTexture?.dispose();
        disposeResources(resources);
        if (globalThis.ultra === api) delete globalThis.ultra;
      },
    };
    return controller;
  } catch (error) {
    abort.abort(); lighting?.dispose(); iesTexture?.dispose(); disposeResources(resources);
    warnOnce('setup', 'effect setup failed; keeping the high path.', error);
    return null;
  }
}
