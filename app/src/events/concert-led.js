import * as THREE from 'three/webgpu';
import { uniform, uv, vec2, vec3, float, fract, abs, sin, floor, smoothstep, mix, step, length, select, instanceIndex, positionLocal } from 'three/tsl';

// Procedural LED content for EVT-01. No artist names, logos, text, images or likeness: colour, bars and rings only.
export function ledUniforms() {
  return { pattern: uniform(0), beat: uniform(0), pulse: uniform(1), level: uniform(.1), color: uniform(new THREE.Color(.1, .1, .8)) };
}
export function updateLed(u, state) {
  u.pattern.value = state.led.pattern; u.beat.value = state.led.beat; u.pulse.value = state.led.pulse;
  u.level.value = state.screens[0].intensity; u.color.value.setRGB(...state.led.color);
}
// p is the surface coordinate: x across 0..1, y up 0..1. seed shifts the phase of each surface or tile.
export function ledColor(u, p, seed) {
  const beat = u.beat.add(seed), c = u.color, c2 = vec3(c.z, c.x, c.y).mul(.9), x = p.x, y = p.y;
  // 0: slow wash.
  const wash = mix(c, c2, sin(x.mul(3).add(beat.mul(.25))).mul(.5).add(.5)).mul(y.mul(.55).add(.45));
  // 1: rising bars, one column each.
  const column = floor(x.mul(16)), r = fract(sin(column.mul(12.9898)).mul(43758.5453));
  const top = r.mul(.5).add(.35).mul(u.pulse.mul(.5).add(.5)).add(sin(beat.mul(.5).add(r.mul(6.28))).mul(.08));
  const bars = mix(c2, c, y).mul(step(y, top)).mul(step(.12, fract(x.mul(16)))).add(c.mul(.08));
  // 2: ring pulse on the beat, with a flash.
  const ring = smoothstep(.1, 0, abs(length(p.sub(vec2(.5, .5)).mul(vec2(2.2, 1))).sub(fract(beat.mul(.5)).mul(1.4))));
  const flash = c.mul(u.pulse.mul(u.pulse).mul(.6)).add(c2.mul(ring).mul(1.6));
  // 3: colour sweep with side stripes.
  const band = smoothstep(.14, 0, abs(x.sub(fract(beat.mul(.125)))));
  const stripes = step(.5, fract(x.mul(20).sub(beat.mul(.5)))).mul(.35);
  const sweep = wash.mul(.4).add(c2.mul(band).mul(1.5)).add(c.mul(stripes));
  // 4: fade.
  const fade = wash.mul(.35);
  const pat = u.pattern;
  const content = select(pat.lessThan(.5), wash.mul(.6), select(pat.lessThan(1.5), bars, select(pat.lessThan(2.5), flash, select(pat.lessThan(3.5), sweep, fade))));
  // LED pixel grid: dot mask across the surface.
  const dot = smoothstep(.55, .25, length(fract(p.mul(vec2(120, 28))).sub(.5)));
  return content.mul(dot.mul(.65).add(.35)).mul(u.level);
}
export function ledSurfaceMaterial(u, seed = 0, side = THREE.DoubleSide) {
  const material = new THREE.MeshBasicNodeMaterial({ side });
  material.colorNode = ledColor(u, uv(), float(seed)); material.toneMapped = false;
  return material;
}
// Tiles use the model's local xy, normalised to -1..1, and a hashed seed for each instance.
export function ledTileMaterial(u) {
  const material = new THREE.MeshBasicNodeMaterial({ side: THREE.DoubleSide });
  const seed = fract(sin(instanceIndex.toFloat().mul(12.9898)).mul(43758.5453)).mul(4);
  material.colorNode = ledColor(u, positionLocal.xy.mul(.5).add(.5), seed); material.toneMapped = false;
  return material;
}
export function ledBarMaterial(u) {
  const material = new THREE.MeshBasicNodeMaterial();
  const seed = fract(sin(instanceIndex.toFloat().mul(78.233)).mul(43758.5453));
  material.colorNode = u.color.mul(u.pulse.mul(.6).add(.4).mul(seed.mul(.5).add(.75))).mul(u.level.add(.4)); material.toneMapped = false;
  return material;
}
