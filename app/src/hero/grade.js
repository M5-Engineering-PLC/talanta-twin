// Select the look here. Times describe the baked-light visual targets, not a rebake.
export const DEFAULT_PRESET = 'morning_golden';

export const GRADE_PRESETS = Object.freeze({
  morning_golden: {
    time: '07:30', warmth: 0.045, shadowCool: 0.018,
    whiteBalance: [1.012, 1, 0.988], saturation: 1.035, contrast: 1.025,
    greenery: 0.015, vignette: 0.035, dispersion: 0, grain: 0.008,
    bloom: { threshold: 0.95, strength: 0.065, radius: 0.3 },
    fog: { color: 0xc8bca9, near: 1800, far: 14000, horizonMix: 0.65 },
  },
  evening_golden: {
    time: '17:30', warmth: 0.065, shadowCool: 0.025,
    whiteBalance: [1.02, 1, 0.975], saturation: 1.025, contrast: 1.04,
    greenery: 0.01, vignette: 0.04, dispersion: 0, grain: 0.008,
    bloom: { threshold: 0.9, strength: 0.075, radius: 0.35 },
    fog: { color: 0xbeb29c, near: 1600, far: 12500, horizonMix: 0.7 },
  },
  neutral: {
    time: null, warmth: 0, shadowCool: 0,
    whiteBalance: [1, 1, 1], saturation: 1, contrast: 1,
    greenery: 0, vignette: 0, dispersion: 0, grain: 0,
    bloom: { threshold: 1, strength: 0, radius: 0 },
    fog: { color: 0xd9dfd5, near: 2200, far: 16000, horizonMix: 0 },
  },
});

export function getGradePreset(name = DEFAULT_PRESET) {
  const preset = GRADE_PRESETS[name];
  if (!preset) throw new RangeError(`Unknown hero grade preset: ${name}`);
  return preset;
}
