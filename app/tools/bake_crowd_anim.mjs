import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { gzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptSimplifier } from 'three/addons/libs/meshopt_simplifier.module.js';

const source = process.argv[2] ?? '/home/munene/Downloads/talanta_assets_staging/people/quaternius_UAL1/Animation Library[Standard]/Godot/AnimationLibrary_Godot_Standard.glb';
const output = new URL('../public/people/', import.meta.url);
const started = performance.now();
const bytes = await readFile(source);
const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
await MeshoptSimplifier.ready;
const meshes = [];
gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
const mixer = new THREE.AnimationMixer(gltf.scene);
const clips = new Map(gltf.animations.map(c => [c.name, c]));
const slots = ['Sitting_Idle_Loop', 'Sitting_Enter', 'Sitting_Exit', 'Idle_Loop', 'Jump_Start', 'Jump_Loop', 'Jump_Land', 'Dance_Loop', 'Walk_Loop', 'clap', 'cheer', 'wave'];
const framesPerClip = 24;
function pose(name, progress) {
  mixer.stopAllAction();
  const base = name === 'clap' ? 'Sitting_Idle_Loop' : ['cheer', 'wave'].includes(name) ? 'Sitting_Exit' : name;
  const clip = clips.get(base);
  if (!clip) throw new Error(`Missing clip: ${base}`);
  const action = mixer.clipAction(clip).setLoop(THREE.LoopOnce, 1);
  action.clampWhenFinished = true; action.play();
  const smooth = t => { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t); };
  const rise = name === 'wave' ? smooth(progress / .28) * (1 - smooth((progress - .68) / .32)) : smooth(progress / .35);
  mixer.setTime(clip.duration * (['cheer', 'wave'].includes(name) ? rise : progress));
  gltf.scene.updateMatrixWorld(true);
  if (['clap', 'cheer', 'wave'].includes(name)) {
    // World targets become local bone rotations. Child bones retain their lengths.
    const skeleton = meshes[0].skeleton;
    const find = n => skeleton.bones.find(b => b.name === THREE.PropertyBinding.sanitizeNodeName(n));
    function aim(name, childName, target) {
      const bone = find(name), child = find(childName);
      const origin = bone.getWorldPosition(new THREE.Vector3());
      const current = child.getWorldPosition(new THREE.Vector3()).sub(origin).normalize();
      const desired = target.clone().sub(origin).normalize();
      const world = bone.getWorldQuaternion(new THREE.Quaternion());
      world.premultiply(new THREE.Quaternion().setFromUnitVectors(current, desired));
      bone.quaternion.copy(bone.parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(world));
      gltf.scene.updateMatrixWorld(true);
    }
    const chest = find('DEF-spine003') ?? find('DEF-spine.003');
    const c = chest.getWorldPosition(new THREE.Vector3());
    for (const side of ['L', 'R']) {
      const sign = side === 'L' ? 1 : -1;
      const clap = name === 'clap';
      const open = .035 + .12 * (.5 + .5 * Math.cos(progress * Math.PI * 8));
      const height = clap ? .04 : (.48 + .035 * Math.sin(progress * Math.PI * 8)) * rise;
      const elbow = c.clone().add(new THREE.Vector3(sign * .24, clap ? -.05 : height * .48, .18));
      const hand = c.clone().add(new THREE.Vector3(sign * (clap ? open : .25), height, clap ? .39 : .12));
      aim(`DEF-upper_arm.${side}`, `DEF-forearm.${side}`, elbow);
      aim(`DEF-forearm.${side}`, `DEF-hand.${side}`, hand);
    }
  }
  gltf.scene.updateMatrixWorld(true);
  meshes.forEach(m => m.skeleton.update());
}
pose('Idle_Loop', 0);
const bounds = new THREE.Box3();
const v = new THREE.Vector3();
for (const m of meshes) for (let i = 0; i < m.geometry.attributes.position.count; i++) {
  v.fromBufferAttribute(m.geometry.attributes.position, i); m.applyBoneTransform(i, v); m.localToWorld(v); bounds.expandByPoint(v);
}
const scale = 1.75 / (bounds.max.y - bounds.min.y);
const floor = bounds.min.y;
const entries = [], indices = [], positions = [];
for (const m of meshes) {
  const g = m.geometry, offset = entries.length;
  for (let i = 0; i < g.attributes.position.count; i++) {
    const joint = g.attributes.skinIndex, weights = g.attributes.skinWeight;
    let dominant = 0;
    for (let k = 1; k < 4; k++) if (weights.getComponent(i, k) > weights.getComponent(i, dominant)) dominant = k;
    const bone = m.skeleton.bones[joint.getComponent(i, dominant)].name;
    const kind = /head|neck|hand|finger|thumb|f_/.test(bone) ? 1 : /thigh|shin|foot|toe/.test(bone) ? 2 : 0;
    entries.push({ m, i, kind });
    v.fromBufferAttribute(g.attributes.position, i); m.applyBoneTransform(i, v); m.localToWorld(v);
    positions.push(v.x * scale, (v.y - floor) * scale, v.z * scale);
  }
  indices.push(...Array.from(g.index.array, i => i + offset));
}
// Weld coincident seam vertices before reduction. Keep source IDs for baking.
const welded = [], representatives = [], weldMap = new Map(), remap = [];
for (let i = 0; i < entries.length; i++) {
  const p = positions.slice(i * 3, i * 3 + 3);
  const key = p.map(n => Math.round(n * 100000)).join(',');
  if (!weldMap.has(key)) { weldMap.set(key, representatives.length); representatives.push(i); welded.push(...p); }
  remap.push(weldMap.get(key));
}
const sourcePositions = new Float32Array(welded), sourceIndices = new Uint32Array(indices.map(i => remap[i]));
const lods = [];
for (const target of [2100, 80]) {
  const [index, error] = MeshoptSimplifier.simplify(sourceIndices, sourcePositions, 3, target * 3, 1);
  const ids = [...new Set(index)], mapping = new Map(ids.map((id, i) => [id, i]));
  lods.push({ triangles: index.length / 3, error, ids: ids.map(i => representatives[i]), index: Array.from(index, i => mapping.get(i)), kind: ids.map(i => entries[representatives[i]].kind) });
}
if (lods[0].triangles < 1500 || lods[0].triangles > 2500) throw new Error('LOD0 triangle budget exceeded');
// Accessories share the body draw call and animation texture.
const props = new THREE.PlaneGeometry(.64, .065).toNonIndexed();
const phone = new THREE.PlaneGeometry(.045, .075).toNonIndexed();
const propVertices = [...Array.from({ length: props.attributes.position.count }, (_, i) => ({ p: new THREE.Vector3().fromBufferAttribute(props.attributes.position, i), kind: 3 })),
  ...Array.from({ length: phone.attributes.position.count }, (_, i) => ({ p: new THREE.Vector3().fromBufferAttribute(phone.attributes.position, i), kind: 4 }))];
const width = 2 ** Math.ceil(Math.log2(Math.max(...lods.map(l => l.ids.length + propVertices.length))));
const height = framesPerClip * slots.length * lods.length;
const texture = new Uint16Array(width * height * 4);
const manifest = { version: 1, width, height, framesPerClip, format: 'RGBA16F', sourceSha256: createHash('sha256').update(bytes).digest('hex'), clips: [], lods: [] };
for (let slot = 0; slot < slots.length; slot++) {
  const name = slots[slot], base = name === 'clap' ? 'Sitting_Idle_Loop' : ['cheer', 'wave'].includes(name) ? 'Sitting_Exit' : name;
  manifest.clips.push({ name, slot, duration: ['clap', 'cheer', 'wave'].includes(name) ? 2 : clips.get(base).duration, source: base, motion: ['clap', 'cheer', 'wave'].includes(name) ? 'hand-keyed layer' : 'Quaternius clip' });
  for (let frame = 0; frame < framesPerClip; frame++) {
    pose(name, frame / (framesPerClip - 1));
    for (let lod = 0; lod < lods.length; lod++) {
      const data = lods[lod], row = (lod * slots.length + slot) * framesPerClip + frame;
      const baked = [];
      for (const id of data.ids) {
        const e = entries[id];
        v.fromBufferAttribute(e.m.geometry.attributes.position, e.i); e.m.applyBoneTransform(e.i, v); e.m.localToWorld(v);
        baked.push(v.x * scale, (v.y - floor) * scale, v.z * scale);
      }
      const hand = meshes[0].skeleton.bones.find(b => b.name === THREE.PropertyBinding.sanitizeNodeName('DEF-hand.R')).getWorldPosition(new THREE.Vector3());
      for (const prop of propVertices) {
        const p = prop.p.clone();
        if (prop.kind === 3) p.add(new THREE.Vector3(0, name === 'Sitting_Idle_Loop' || name === 'clap' ? 1.3 : 1.95, .08));
        else p.add(new THREE.Vector3(hand.x * scale, (hand.y - floor) * scale, hand.z * scale));
        baked.push(p.x, p.y, p.z);
      }
      for (let i = 0; i < baked.length / 3; i++) {
        for (let k = 0; k < 3; k++) texture[(row * width + i) * 4 + k] = THREE.DataUtils.toHalfFloat(baked[i * 3 + k]);
        texture[(row * width + i) * 4 + 3] = THREE.DataUtils.toHalfFloat(1);
      }
      if (slot === 0 && frame === 0) {
        const start = data.ids.length;
        manifest.lods.push({ triangles: data.triangles + propVertices.length / 3, bodyTriangles: data.triangles, vertices: baked.length / 3,
          position: baked, kind: [...data.kind, ...propVertices.map(p => p.kind)], index: [...data.index, ...propVertices.map((_, i) => start + i)] });
      }
    }
  }
}
await mkdir(output, { recursive: true });
const files = { 'crowd.json': Buffer.from(JSON.stringify(manifest)), 'animation.bin': Buffer.from(texture.buffer) };
let gzipBytes = 0;
for (const [name, data] of Object.entries(files)) { await writeFile(new URL(name, output), data); gzipBytes += gzipSync(data).length; }
const credits = 'Quaternius Universal Animation Library, Standard.\nModel and animation clips: Quaternius. License: CC0 1.0 Universal.\nhttps://quaternius.com/packs/universalanimationlibrary.html\nhttps://creativecommons.org/publicdomain/zero/1.0/\n\nThe bake uses the staged Godot GLB. crowd.json records its SHA-256 hash.\nMeshoptSimplifier from three.js reduces the mesh. Its license is MIT.\nClap, cheer, and wave use hand-keyed bone rotations over Quaternius sitting clips.\nThe other slots use the supplied Quaternius animation clips.\nCMU motion capture data is not used.\n\nCrowds are Visualization. They are not validated safety, capacity, or crowd-flow evidence.\nRendered fan counts do not show venue capacity.\n';
await writeFile(new URL('CREDITS.md', output), credits);
const total = gzipBytes + gzipSync(credits).length;
if (total >= 3_000_000) throw new Error(`Asset budget exceeded: ${total} gzip bytes`);
console.log(`LOD0 ${manifest.lods[0].bodyTriangles} body triangles, ${manifest.lods[0].triangles} with accessories; LOD1 ${manifest.lods[1].bodyTriangles} body triangles, ${manifest.lods[1].triangles} with accessories`);
console.log(`Clips: ${slots.join(', ')}`);
console.log(`Frames: ${framesPerClip} per clip; texture ${width} x ${height} RGBA16F`);
console.log(`Output: ${Object.values(files).reduce((n, b) => n + b.length, Buffer.byteLength(credits))} bytes; ${total} gzip bytes; ${((performance.now() - started) / 1000).toFixed(2)} seconds`);
