import * as THREE from 'three/webgpu';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { loadEnvironment } from './environment.js';

// ENV-01: switch the baked hero between the Kaggle GPU light sets (lightmaps/<HHMM>/tod.json + <group>_light.ktx2).
// AO and albedo never change; only material.lightMap, lightMapIntensity, the panorama and the ground tile colour do.
export const PRESETS = Object.freeze({ '0730': 'morning_golden', '1030': 'daylight_artistic', '1805': 'sunset_artistic', '2000': 'night' });
export const HYSTERESIS_MIN = 25;

const minutesOf = (hhmm) => +hhmm.slice(0, 2) * 60 + +hhmm.slice(2);
const gap = (a, b) => { const d = Math.abs(a - b) % 1440; return Math.min(d, 1440 - d); };

/** Nearest baked time on the 24 h circle. The current time only yields when another is at least `margin` minutes nearer. */
export function nearestTime(times, minutes, current = null, margin = HYSTERESIS_MIN) {
  let best = null;
  for (const t of times) if (best === null || gap(minutesOf(t), minutes) < gap(minutesOf(best), minutes)) best = t;
  if (current && times.includes(current) && best !== current && gap(minutesOf(best), minutes) + margin > gap(minutesOf(current), minutes)) return current;
  return best;
}

/** Check a tod.json (shape written by blender/web_hero/node/post_glb.mjs tod mode). Returns it or throws. */
export function parseTod(tod, hhmm) {
  const fail = (m) => { throw new Error(`tod.json ${hhmm ?? ''}: ${m}`); };
  if (!tod || typeof tod !== 'object') fail('not an object');
  if (hhmm && tod.time !== hhmm) fail(`time is ${tod.time}`);
  if (!PRESETS[tod.time] || tod.preset !== PRESETS[tod.time]) fail(`preset ${tod.preset} does not fit ${tod.time}`);
  if (!tod.groups || !Object.keys(tod.groups).length) fail('groups is missing');
  for (const [name, g] of Object.entries(tod.groups)) {
    if (!g?.file || !(g.intensity > 0)) fail(`group ${name} has no file or intensity`);
  }
  if (!Number.isFinite(tod.ground_tile_gain) || tod.ground_tile_gain < 0) fail('ground_tile_gain is missing');
  return tod;
}

/** Every material under root with a bake group and a lightmap record: [{ material, group, texCoord }]. */
export function collectLightmapped(root) {
  const seen = new Set(), out = [];
  root.traverse((node) => {
    if (!node.isMesh) return;
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      const g = material?.userData?.talanta_bake_group;
      if (!g || !material.userData.talanta_lightmap || seen.has(material)) continue;
      seen.add(material);
      out.push({ material, group: g, texCoord: material.userData.talanta_lightmap.texCoord ?? 0 });
    }
  });
  return out;
}

/** Assign one set to the materials in one go. textures: Map group -> texture; intensities: Map group -> number. Returns the replaced textures. */
export function applyLightmaps(entries, textures, intensities) {
  const replaced = new Set();
  for (const { material, group, texCoord } of entries) {
    const texture = textures.get(group);
    if (!texture) continue;
    if (material.lightMap && material.lightMap !== texture) replaced.add(material.lightMap);
    texture.channel = texCoord; texture.colorSpace = THREE.SRGBColorSpace; texture.flipY = false;
    material.lightMap = texture;
    material.lightMapIntensity = intensities.get(group);
    if (material.userData.heroDaylight) material.userData.heroDaylight.intensity = intensities.get(group);
  }
  return replaced;
}

function groundTileMaterials(root) {
  const out = new Set();
  root.traverse((node) => { if (node.isMesh && /^hero-ground-/.test(node.name) && node.material) out.add(node.material); });
  return out;
}

/** Colour factor of the unlit ground tiles (their light is baked at the base time). Also in the heroLighting baseline if captured. */
export function applyGroundGain(materials, gain) {
  for (const m of materials) {
    m.color?.setScalar(gain);
    if (m.userData?.heroDaylight) m.userData.heroDaylight.color = [gain, gain, gain];
  }
}

const defaultIo = (renderer) => ({
  async json(url) { const r = await fetch(url); if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.json(); },
  async textures(urls) {
    const loader = new KTX2Loader().setTranscoderPath('./basis/').detectSupport(renderer);
    try { return await Promise.all(urls.map((u) => loader.loadAsync(u))); } finally { loader.dispose(); }
  },
  environment: loadEnvironment,
});

/**
 * createTimeOfDay({ group, renderer, scene, base, manifest, phone, onEnvironment, io })
 * base: public root ('./'). manifest: the app manifest; manifest.tod = { base, times, dir } enables it (else times is empty).
 * setTime(hhmm) loads the set, then swaps lightmaps, panorama and ground gain in one synchronous step.
 * A failed load keeps the current set and logs one warning. At most 2 sets (phone) or 4 (desktop) stay cached; the base set
 * (the textures inside the GLB) is never disposed.
 */
export function createTimeOfDay({ group, renderer, scene, base = './', manifest, phone = false, onEnvironment, io = defaultIo(renderer) }) {
  const cfg = manifest?.tod, times = cfg?.times?.length ? [...cfg.times].sort() : [], baseTime = cfg?.base ?? null;
  const dir = `${base}${cfg?.dir ?? (phone ? 'lightmaps_phone' : 'lightmaps')}/`;
  const cap = phone ? 2 : 4;
  const sets = new Map(), pending = new Map(), envs = new Map();
  let current = null, appliedEnv = null, seq = 0, nearestCurrent = null, ground = new Set(), gain = 1, warned = false, tick = 0;
  const warn = (what, error) => { if (!warned) console.warn(`time of day: ${what}`, error); warned = true; };

  // The base set is what the GLB already carries.
  const entries = () => collectLightmapped(group);
  if (baseTime) {
    const textures = new Map(), intensities = new Map();
    for (const e of entries()) if (e.material.lightMap && !textures.has(e.group)) { textures.set(e.group, e.material.lightMap); intensities.set(e.group, e.material.userData.talanta_lightmap.intensity); }
    sets.set(baseTime, { textures, intensities, tod: null, base: true, used: 0 });
  }

  function ensure(hhmm) {
    if (sets.get(hhmm)?.tod) return Promise.resolve(sets.get(hhmm));
    if (!pending.has(hhmm)) {
      pending.set(hhmm, (async () => {
        const have = sets.get(hhmm);
        const tod = parseTod(await io.json(`${dir}${hhmm}/tod.json`), hhmm);
        if (have) { have.tod = tod; return have; }  // base set: textures are already in the GLB
        const names = Object.keys(tod.groups);
        const loaded = await io.textures(names.map((n) => `${dir}${hhmm}/${tod.groups[n].file}`));
        const reference = sets.get(baseTime)?.textures, textures = new Map(), intensities = new Map();
        names.forEach((n, i) => {
          const t = loaded[i], r = reference?.get(n);
          if (r) { t.wrapS = r.wrapS; t.wrapT = r.wrapT; t.magFilter = r.magFilter; t.minFilter = r.minFilter; t.anisotropy = r.anisotropy; }
          textures.set(n, t); intensities.set(n, tod.groups[n].intensity);
        });
        const set = { textures, intensities, tod, base: false, used: 0 };
        sets.set(hhmm, set);
        return set;
      })().finally(() => pending.delete(hhmm)));
    }
    return pending.get(hhmm);
  }

  function evict() {
    while (sets.size > cap) {
      let victim = null;
      for (const [t, s] of sets) if (t !== current && !s.base && (!victim || s.used < sets.get(victim).used)) victim = t;
      if (!victim) break;
      for (const texture of sets.get(victim).textures.values()) texture.dispose();
      sets.delete(victim);
    }
  }

  async function panorama(tod) {
    const p = tod.panorama, ids = p ? [p.hdr, p.exr].filter(Boolean) : [];
    const key = ids.join('|') || 'base';
    if (!envs.has(key)) {
      const m = ids.length
        ? { ...manifest, environment: { ...manifest.environment, file: p.hdr ? `app/public/env/${p.hdr}` : undefined, file_2048: p.hdr ? `app/public/env/${p.hdr}` : undefined, file_exr: p.exr ? `app/public/env/${p.exr}` : undefined },
            files: [...(manifest.files ?? []), ...ids.map((f) => ({ file: `app/public/env/${f}` }))] }
        : manifest;  // no panorama for this time: the base-time panorama
      envs.set(key, io.environment({ renderer, scene: new THREE.Scene(), manifest: m, base }));
    }
    return { key, env: await envs.get(key) };
  }

  async function setTime(hhmm) {
    if (!times.includes(hhmm)) return false;
    const mine = ++seq;
    try {
      const set = await ensure(hhmm);
      const pano = await panorama(set.tod);
      if (mine !== seq) return false;  // a newer time was asked for
      // one synchronous step: lightmaps, ground gain, panorama
      const replaced = applyLightmaps(entries(), set.textures, set.intensities);
      ground = groundTileMaterials(group); gain = set.tod.ground_tile_gain; applyGroundGain(ground, gain);
      if (pano.env && pano.key !== appliedEnv) {
        appliedEnv = pano.key;
        scene.background = scene.environment = pano.env.texture;
        scene.backgroundRotation.copy(pano.env.rotation); scene.environmentRotation.copy(pano.env.rotation);
        onEnvironment?.(pano.env, hhmm);
        for (const [k, p] of envs) if (k !== pano.key) { envs.delete(k); p.then((e) => e?.dispose()); }
      }
      current = hhmm; set.used = ++tick;
      for (const t of replaced) if (![...sets.values()].some((s) => [...s.textures.values()].includes(t))) t.dispose();
      evict();
      return true;
    } catch (error) { warn(`${hhmm} set failed to load; keeping the current set`, error); return false; }
  }

  return {
    times,
    get current() { return current; },
    preset: (hhmm) => PRESETS[hhmm],
    /** The baked time for these minutes, with hysteresis. */
    nearest(minutes) { nearestCurrent = nearestTime(times, minutes, nearestCurrent); return nearestCurrent; },
    setTime,
    /** Load the maps of a time ahead (idle time). On a phone only while the cache has room. */
    async preload(hhmm) {
      if (!times.includes(hhmm) || sets.get(hhmm)?.tod) return false;
      if (phone && sets.size >= cap) return false;
      try { await ensure(hhmm); evict(); return true; } catch (error) { warn(`${hhmm} set failed to preload`, error); return false; }
    },
    /** Re-apply the ground gain after late ground tiles appear. */
    refresh() { ground = groundTileMaterials(group); applyGroundGain(ground, gain); },
    dispose() {
      seq++;
      for (const s of sets.values()) if (!s.base) for (const t of s.textures.values()) t.dispose();
      sets.clear(); for (const p of envs.values()) p.then((e) => e?.dispose()); envs.clear();
    },
  };
}
