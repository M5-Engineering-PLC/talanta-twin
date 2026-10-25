import { getGradePreset } from './grade.js';

/** Reject incomplete curves rather than silently produce a broken frame. */
export function measuredLook(manifest) {
  const look = manifest?.look, curve = look?.curve;
  if (!look) return null;
  if (look.view_transform !== 'AgX' || !curve || !Number.isFinite(curve.ev_min)
      || !Number.isFinite(curve.ev_max) || curve.ev_max <= curve.ev_min
      || curve.samples?.length !== 33 || !curve.samples.every(Number.isFinite)) {
    throw new Error('Invalid manifest look: expected an AgX curve with 33 finite samples');
  }
  return look;
}

export function lookExposure(manifest, view = 'L07') {
  const ev = measuredLook(manifest)?.views?.[view]?.exposure_ev ?? manifest?.tone_mapping?.blender_exposure_ev;
  return Number.isFinite(ev) ? 2 ** ev : 1;
}

export function manifestGrade(manifest) {
  const look = measuredLook(manifest);
  if (!look) return getGradePreset();
  const c = look.compositor ?? {};
  return { ...getGradePreset('neutral'), contrast: c.contrast ?? 1, saturation: c.saturation ?? 1,
    warmth: c.warmth ?? 0, grain: c.grain ?? 0, vignette: c.vignette ?? 0,
    bloom: { threshold: 2, strength: c.glare ?? 0, radius: 0.3 } };
}

/** Grey input is scene-linear 0.18 * 2^EV. Samples are display-encoded values. */
export function sampleLookCurve(linear, curve) {
  const ev = Math.log2(Math.max(linear, Number.MIN_VALUE) / 0.18);
  const position = Math.max(0, Math.min(32, (ev - curve.ev_min) * 32 / (curve.ev_max - curve.ev_min)));
  const lo = Math.min(31, Math.floor(position));
  return curve.samples[lo] + (curve.samples[lo + 1] - curve.samples[lo]) * (position - lo);
}
