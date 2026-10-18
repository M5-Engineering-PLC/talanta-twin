import { AgXToneMapping, Fog } from 'three/webgpu';
import { float, screenCoordinate, screenUV, saturation, time, vec2, vec3, vec4 } from 'three/tsl';

export const HERO_LOOK = {
  warmth: 0.025,
  saturation: 1.055,
  contrast: 1.035,
  greenery: 0.035, // Small lift limited to green-dominant surfaces.
  vignette: 0.055, // Maximum smooth corner darkening.
  dispersion: 0.0005, // Small chromatic lens dispersion.
  grain: 0.03, // Fine, centered multiplicative film grain amplitude.
};

// In main.js, import { heroGrade } from './hero/heroLook.js';
// Then change the output line to: pipeline.outputNode = heroGrade(shaded).add(bloomPass);
// RenderPipeline applies tone mapping and color-space conversion after outputNode, so this grade stays linear.

/** Set AgX and the Blender exposure from the export manifest. */
export function applyHeroToneMapping(renderer, manifest) {
  const ev = manifest?.tone_mapping?.blender_exposure_ev;
  if (!Number.isFinite(ev)) {
    console.warn('hero tone mapping unavailable: manifest tone_mapping.blender_exposure_ev is missing');
    return null;
  }
  renderer.toneMapping = AgXToneMapping;
  renderer.toneMappingExposure = 2 ** ev;
  return renderer;
}

/** Build the linear-space TSL color grade for the hero render pipeline. */
export function heroGrade(inputNode, opts = {}) {
  const warmth = opts.warmth ?? HERO_LOOK.warmth;
  const sat = opts.saturation ?? HERO_LOOK.saturation;
  const contrast = opts.contrast ?? HERO_LOOK.contrast;
  const vignette = opts.vignette ?? HERO_LOOK.vignette;
  const dispersion = opts.dispersion ?? HERO_LOOK.dispersion;
  const grainStrength = opts.grain ?? HERO_LOOK.grain;
  const uv = screenUV;
  const edge = uv.sub(0.5).length().mul(Math.SQRT2).smoothstep(0.45, 1.0);
  const color = vec4(inputNode);
  let rgb = saturation(color.rgb, sat).sub(0.18).mul(contrast).add(0.18);
  const highlights = rgb.dot(vec3(0.2126, 0.7152, 0.0722)).smoothstep(0.18, 1.2);
  const green = rgb.g.sub(rgb.r.max(rgb.b)).max(0).mul(opts.greenery ?? HERO_LOOK.greenery);
  rgb = rgb.add(vec3(0, green, 0)).mul(vec3(highlights.mul(warmth).add(1), 1, float(1).sub(highlights.mul(warmth))));

  // Approximate edge color fringing in the color node; the contract gives no source texture for offset sampling.
  const fringe = edge.mul(dispersion);
  rgb = vec3(rgb.r.add(rgb.r.mul(fringe)), rgb.g, rgb.b.sub(rgb.b.mul(fringe)));

  const corner = uv.sub(0.5).length().mul(Math.SQRT2).pow(2).mul(vignette);
  const pixel = screenCoordinate.floor().add(float(opts.time ?? time).mul(37));
  const noise = pixel.dot(vec2(12.9898, 78.233)).sin().mul(43758.5453).fract().sub(0.5).mul(2);
  rgb = rgb.mul(float(1).sub(corner).mul(noise.mul(grainStrength).add(1)));
  return vec4(rgb, color.a);
}

/** Add modest distance haze while keeping the foreground clear. */
export function applyHeroHaze(scene, horizon) {
  scene.fog = new Fog(horizon ?? 0xd9dfd5, 2200, 16000);
  return scene.fog;
}
