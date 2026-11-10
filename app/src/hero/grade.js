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
  daylight_artistic: {
    time: '10:30', warmth: 0.015, shadowCool: 0.012,
    whiteBalance: [1.0, 1, 0.995], saturation: 1.04, contrast: 1.03,
    greenery: 0.02, vignette: 0.03, dispersion: 0, grain: 0.006,
    bloom: { threshold: 1.0, strength: 0.04, radius: 0.25 },
    fog: { color: 0xd2d8d6, near: 2200, far: 16000, horizonMix: 0.55 },
  },
  sunset_artistic: {
    time: '18:05', warmth: 0.08, shadowCool: 0.03,
    whiteBalance: [1.03, 1, 0.965], saturation: 1.05, contrast: 1.045,
    greenery: 0.008, vignette: 0.045, dispersion: 0, grain: 0.008,
    bloom: { threshold: 0.85, strength: 0.09, radius: 0.38 },
    fog: { color: 0xc9a98a, near: 1500, far: 11500, horizonMix: 0.75 },
  },
  night: {
    time: '20:00', warmth: 0.02, shadowCool: 0.04,
    whiteBalance: [0.985, 1, 1.03], saturation: 0.92, contrast: 1.06,
    greenery: 0, vignette: 0.06, dispersion: 0, grain: 0.012,
    bloom: { threshold: 0.7, strength: 0.14, radius: 0.45 },
    fog: { color: 0x1d2330, near: 1200, far: 9000, horizonMix: 0.8 },
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
