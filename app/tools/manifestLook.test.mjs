import test from 'node:test';
import assert from 'node:assert/strict';
import { AgXToneMapping, NoToneMapping } from 'three/webgpu';
import { float, vec4 } from 'three/tsl';
import { getGradePreset } from '../src/hero/grade.js';
import { measuredLook, sampleLookCurve, lookExposure, manifestGrade } from '../src/hero/manifestLook.js';
import { applyHeroToneMapping, heroGrade, heroLookCurve } from '../src/hero/heroLook.js';
const curve = { ev_min: -10, ev_max: 6.5, samples: Array.from({ length: 33 }, (_, i) => i / 32) };
const manifest = { tone_mapping: { blender_exposure_ev: -1 }, look: { view_transform: 'AgX', look: 'AgX - High Contrast', curve,
  views: { L06: { exposure_ev: -2, time: '18:05' }, L07: { exposure_ev: -1, time: '10:30' } },
  compositor: { contrast: 1.05, saturation: 1.12, warmth: [1.05, 1, 0.93], grain: 0.03, glare: 0.035, vignette: 0.055 } } };
test('curve interpolates all 33 grey samples, midpoints and clamped ends', () => {
  for (let i = 0; i < 33; i++) {
    const ev = curve.ev_min + i * (curve.ev_max - curve.ev_min) / 32;
    assert.ok(Math.abs(sampleLookCurve(0.18 * 2 ** ev, curve) - curve.samples[i]) < 1e-12);
    if (i < 32) assert.ok(Math.abs(sampleLookCurve(0.18 * 2 ** (ev + 16.5 / 64), curve) - (i + 0.5) / 32) < 1e-12);
  }
  assert.equal(sampleLookCurve(0, curve), 0); assert.equal(sampleLookCurve(1e12, curve), 1);
});
test('manifest replaces AgX and selects exposure independently for L06 and L07', () => {
  const renderer = {};
  applyHeroToneMapping(renderer, manifest, 'L06'); assert.equal(renderer.toneMapping, NoToneMapping); assert.equal(renderer.toneMappingExposure, 0.25);
  assert.equal(lookExposure(manifest, 'L07'), 0.5);
  applyHeroToneMapping(renderer, { tone_mapping: { blender_exposure_ev: -1 } });
  assert.equal(renderer.toneMapping, AgXToneMapping); assert.equal(renderer.toneMappingExposure, 0.5);
  assert.equal(manifestGrade({}), getGradePreset());
});
test('all compositor values replace estimates and the TSL graph accepts measured RGB gain', () => {
  const grade = manifestGrade(manifest);
  for (const key of ['contrast', 'saturation', 'warmth', 'grain', 'vignette']) assert.deepEqual(grade[key], manifest.look.compositor[key]);
  assert.equal(grade.bloom.strength, manifest.look.compositor.glare);
  assert.equal(grade.greenery, 0); assert.equal(grade.shadowCool, 0);
  assert.ok(heroLookCurve(heroGrade(vec4(0.18, 0.18, 0.18, 1), { manifest, exposure: float(0.5) }), manifest.look, float(0.5)).isNode);
});
test('malformed look blocks fail instead of silently applying an invalid curve', () => {
  assert.equal(measuredLook({}), null);
  assert.throws(() => measuredLook({ look: { ...manifest.look, curve: { ...curve, samples: [0, 1] } } }), /33/);
});
