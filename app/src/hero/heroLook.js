import { AgXToneMapping, NoToneMapping, Color, Fog } from 'three/webgpu';
import { float, screenCoordinate, screenUV, saturation, time, vec2, vec3, vec4 } from 'three/tsl';

import { getGradePreset } from './grade.js';
import { measuredLook, lookExposure, manifestGrade } from './manifestLook.js';

export const HERO_LOOK = getGradePreset();

/** The measured display curve replaces AgX, so neither AgX nor sRGB runs twice. */
export function applyHeroToneMapping(renderer, manifest, view) {
  renderer.toneMapping = measuredLook(manifest) ? NoToneMapping : AgXToneMapping;
  renderer.toneMappingExposure = lookExposure(manifest, view);
  return renderer;
}

/** Piecewise-linear TSL lookup, with endpoint clamping and no texture download. */
export function heroLookCurve(inputNode, look, exposure) {
  const curve = look.curve;
  const color = vec4(inputNode);
  const position = color.rgb.mul(exposure).max(1e-12).div(0.18).log2()
    .sub(curve.ev_min).mul(32 / (curve.ev_max - curve.ev_min)).clamp(0, 32);
  let rgb = vec3(curve.samples[0]);
  for (let i = 0; i < 32; i++) {
    rgb = rgb.add(position.sub(i).clamp(0, 1).mul(curve.samples[i + 1] - curve.samples[i]));
  }
  return vec4(rgb, color.a);
}

/** Build the linear-space TSL color grade for the hero render pipeline. */
export function heroGrade(inputNode, opts = {}) {
  opts = { ...(opts.manifest ? manifestGrade(opts.manifest) : getGradePreset(opts.preset)), ...opts };
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
  rgb = rgb.add(vec3(0, green, 0));
  if (opts.manifest && measuredLook(opts.manifest)) {
    // Blender warms mid-tones, then returns the brightest roof highlights to neutral.
    const shown = rgb.dot(vec3(0.2126, 0.7152, 0.0722)).mul(opts.exposure ?? 1);
    const weight = shown.sub(0.03).div(0.15).clamp(0, 1).mul(float(1.4).sub(shown).div(0.85).clamp(0, 1));
    const gain = Array.isArray(warmth) ? vec3(...warmth) : vec3(float(warmth).add(1), 1, float(1).sub(warmth));
    rgb = rgb.mul(vec3(1).add(gain.sub(1).mul(weight)));
  } else rgb = rgb.mul(vec3(highlights.mul(warmth).add(1), 1, float(1).sub(highlights.mul(warmth))));

  const shadows = float(1).sub(highlights).mul(opts.shadowCool);
  rgb = rgb.mul(vec3(...opts.whiteBalance)).mul(vec3(float(1).sub(shadows), 1, shadows.add(1)));

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
export function applyHeroHaze(scene, horizon, preset) {
  const fog = getGradePreset(preset).fog;
  const color = horizon != null ? new Color(horizon).lerp(new Color(fog.color), fog.horizonMix) : new Color(fog.color);
  if (scene.fog?.isFog) {
    scene.fog.color.copy(color);
    scene.fog.near = fog.near;
    scene.fog.far = fog.far;
  } else scene.fog = new Fog(color, fog.near, fog.far);
  return scene.fog;
}
