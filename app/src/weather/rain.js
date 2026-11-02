import * as THREE from 'three/webgpu';
import { attribute, vec3, uniform } from 'three/tsl';

const clamp = x => Math.max(0, Math.min(1, Number.isFinite(x) ? x : 0));
export const RAIN_COUNTS = Object.freeze({ low: 160, medium: 400, high: 900, ultra: 1200 });
export function rainCount(tier) { return RAIN_COUNTS[tier] ?? RAIN_COUNTS.low; }

// Stable hashes and absolute time allow backward seeks without a particle simulation.
export function rainSeed(index) {
  const hash = n => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
  return [hash(index * 3), hash(index * 3 + 1), hash(index * 3 + 2)];
}
export function rainPosition(index, seconds) {
  const [x, y, z] = rainSeed(index), phase = ((y - seconds * .72) % 1 + 1) % 1;
  return [(x - .5) * 44 + (1 - phase) * 2, phase * 32 - 12, (z - .5) * 44];
}

// ENV-03: one instanced line draw, no textures, compute dispatch, shadows, or post pass.
export function installRain({ scene, camera, tier = 'low' }) {
  const maximum = RAIN_COUNTS.ultra, geometry = new THREE.InstancedBufferGeometry();
  const seeds = [];
  for (let i = 0; i < maximum; i++) seeds.push(...rainSeed(i));
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(6), 3));
  geometry.setAttribute('rainSeed', new THREE.InstancedBufferAttribute(new Float32Array(seeds), 3));
  geometry.setAttribute('rainTip', new THREE.Float32BufferAttribute([0, 1], 1));
  geometry.setDrawRange(0, 2); geometry.instanceCount = rainCount(tier);
  const clock = uniform(0), amount = uniform(0), seed = attribute('rainSeed', 'vec3'), tip = attribute('rainTip');
  const phase = seed.y.sub(clock.mul(.72)).fract();
  const material = new THREE.LineBasicNodeMaterial({ color: '#c7d9e8', transparent: true, depthWrite: false, fog: false });
  material.positionNode = vec3(seed.x.sub(.5).mul(44).add(phase.oneMinus().mul(2)).add(tip.mul(.08)),
    phase.mul(32).sub(12).sub(tip.mul(.9)), seed.z.sub(.5).mul(44));
  material.opacityNode = amount.mul(.46);
  const lines = new THREE.LineSegments(geometry, material); lines.name = 'ENV-03-rain'; lines.frustumCulled = false;
  lines.visible = false; lines.renderOrder = 2; scene.add(lines);
  return { group: lines, uniforms: { clock, amount },
    update(seconds, intensity, nextTier = tier) {
      clock.value = seconds; amount.value = clamp(intensity); lines.visible = amount.value > 0;
      geometry.instanceCount = rainCount(nextTier); lines.position.copy(camera.position);
    },
    dispose() { lines.removeFromParent(); geometry.dispose(); material.dispose(); },
  };
}

// All changed material properties are existing renderer uniforms. No material replacement,
// needsUpdate, node graph edit, texture load, or shader rebuild occurs here.
export function installWetLook() {
  const records = new Map();
  function collect(root) {
    root?.traverse(node => {
      if (!node.isMesh) return;
      for (const m of Array.isArray(node.material) ? node.material : [node.material]) {
        if (!m || records.has(m)) continue;
        const name = `${node.name} ${m.name}`;
        const wet = /seat|concourse|pav(e|ing)|terrace|plinth|ground|stand/i.test(name) && Number.isFinite(m.roughness);
        const shield = /shield/i.test(name), lamp = /flood|night_lamp/i.test(name);
        if (!wet && !shield && !lamp) continue;
        records.set(m, { wet, shield, lamp, roughness: m.roughness, env: m.envMapIntensity,
          color: m.color?.clone(), emission: m.emissive?.clone(), intensity: m.emissiveIntensity,
          appliedColor: null, appliedEmission: null, appliedIntensity: null });
      }
    });
  }
  function restore() {
    for (const [m, b] of records) {
      if (b.wet) {
        m.roughness = b.roughness; m.envMapIntensity = b.env;
        if (b.appliedColor && m.color.equals(b.appliedColor)) m.color.copy(b.color);
      }
      if (b.appliedEmission && m.emissive.equals(b.appliedEmission)) m.emissive.copy(b.emission);
      if (m.emissiveIntensity === b.appliedIntensity) m.emissiveIntensity = b.intensity;
    }
  }
  function update(amount, floodLevel = null, shieldGlow = 0) {
    const wet = clamp(amount);
    let lampIndex = 0;
    const lamps = [...records.values()].filter(b => b.lamp).length;
    for (const [m, b] of records) {
      if (b.wet) {
        b.color.copy(m.color); m.color.multiplyScalar(1 - .28 * wet); b.appliedColor = m.color.clone();
        m.roughness = b.roughness * (1 - wet) + .14 * wet;
        m.envMapIntensity = b.env * (1 + 2.5 * wet * (floodLevel ?? 1));
      }
      if ((b.lamp && floodLevel !== null || b.shield && shieldGlow > 0) && m.emissive) {
        b.emission.copy(m.emissive); b.intensity = m.emissiveIntensity;
        const level = b.lamp ? clamp(floodLevel * 1.5 - .5 * lampIndex++ / Math.max(1, lamps - 1)) * 6 : shieldGlow;
        if (b.lamp) m.emissive.set('#fff1d6');
        else if (m.emissive.getHex() === 0) m.emissive.copy(m.color);
        m.emissiveIntensity = b.lamp ? level : b.intensity + level;
        b.appliedEmission = m.emissive.clone(); b.appliedIntensity = m.emissiveIntensity;
      }
    }
  }
  return { collect, restore, update, get materialCount() { return records.size; } };
}
