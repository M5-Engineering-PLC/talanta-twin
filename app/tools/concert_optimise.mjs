// EVT-01 concert assets: copy the staged models into public/concert/<name>/ and optimise them.
// Tools are not app dependencies. Install them outside the repo or use: npm i --no-save @gltf-transform/{core,functions,extensions} meshoptimizer sharp
// Usage: node tools/concert_optimise.mjs [staging directory]
// Output uses meshopt compression (EXT_meshopt_compression) and WebP textures of at most 1024 px.
import { NodeIO } from '@gltf-transform/core';
import { EXTMeshoptCompression, EXTTextureWebP, KHRMeshQuantization } from '@gltf-transform/extensions';
import { dedup, flatten, join, prune, meshopt, textureCompress, weld } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';
import { mkdirSync, copyFileSync, existsSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import { join as path } from 'node:path';

const staging = process.argv[2] ?? path(homedir(), 'Downloads/talanta_assets_staging/concert');
const out = new URL('../public/concert/', import.meta.url).pathname;
// Never read stage-speaker-black (NoAI tag) or the sofi frames (internal layout reference only).
const jobs = [
  { name: 'simple-concert-stage', src: 'sketchfab/simple-concert-stage/scene.gltf', textures: true },
  { name: 'truss-structure', src: 'sketchfab/truss-structure/scene.gltf' },
  { name: 'led-25-x-4', src: 'sketchfab/led-25-x-4/scene.gltf', join: true },
  { name: 'stage-lights', src: 'sketchfab/stage-lights/scene.gltf', join: true },
  { name: 'ipoly3d-concert-stage', src: 'assets/ipoly3d_concert_stage/concert_stage.glb', join: true },
];
await MeshoptEncoder.ready; await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions([EXTMeshoptCompression, EXTTextureWebP, KHRMeshQuantization])
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
for (const job of jobs) {
  const doc = await io.read(path(staging, job.src));
  for (const mesh of doc.getRoot().listMeshes()) for (const prim of mesh.listPrimitives()) {
    for (const semantic of prim.listSemantics()) if (!['POSITION', 'NORMAL', 'TEXCOORD_0'].includes(semantic)) prim.setAttribute(semantic, null);
  }
  const steps = [flatten(), dedup(), weld()];
  if (job.join) steps.push(join());
  steps.push(prune());
  if (job.textures) steps.push(textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [1024, 1024], quality: 80 }));
  steps.push(meshopt({ encoder: MeshoptEncoder, level: 'high' }));
  await doc.transform(...steps);
  mkdirSync(path(out, job.name), { recursive: true });
  const file = path(out, job.name, 'model.glb');
  await io.write(file, doc);
  console.log(job.name, statSync(file).size, 'bytes');
}
