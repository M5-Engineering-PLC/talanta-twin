// Recover baked maps from the web_hero_v1 GLBs (2026-10-20): the original maps/*.png were lost with a container.
// Decodes every KTX2 texture whose name ends in _light, _ao or _albedo to RGBA PNG with the three.js Basis transcoder.
// Lossy: UASTC + RDO (light, AO) or ETC1S (albedo); suburbs maps were stored at 3072 px instead of 4096.
// Run: node extract_v1_maps.mjs <glb>... <out_dir>
import fs from 'node:fs'; import path from 'node:path'; import vm from 'node:vm';
import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer'; import sharp from 'sharp';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../..');
const LIB = path.join(ROOT, 'app/node_modules/three/examples/jsm/libs/basis');
const ctx = { module: {}, exports: {}, console, WebAssembly, URL, TextDecoder, setTimeout, performance };
vm.createContext(ctx); vm.runInContext(fs.readFileSync(path.join(LIB, 'basis_transcoder.js'), 'utf8') + '\n;this.BASIS = BASIS;', ctx);
const B = await ctx.BASIS({ wasmBinary: fs.readFileSync(path.join(LIB, 'basis_transcoder.wasm')) }); B.initializeBasis();
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const args = process.argv.slice(2); const out = args.pop(); fs.mkdirSync(out, { recursive: true });
const log = [];
for (const f of args) {
  const doc = await io.read(f);
  for (const t of doc.getRoot().listTextures()) {
    const name = t.getName(); if (!/_(light|ao|albedo)$/.test(name)) continue;
    const k = new B.KTX2File(new Uint8Array(t.getImage()));
    const w = k.getWidth(), h = k.getHeight(); if (!k.startTranscoding()) throw new Error('transcode ' + name);
    const fmt = 13; /* cTFRGBA32 */ const dst = new Uint8Array(k.getImageTranscodedSizeInBytes(0, 0, 0, fmt));
    if (!k.transcodeImage(dst, 0, 0, 0, fmt, 0, -1, -1)) throw new Error('transcode ' + name);
    const uastc = k.isUASTC(); k.close(); k.delete();
    const file = path.join(out, name + '.png'); await sharp(Buffer.from(dst), { raw: { width: w, height: h, channels: 4 } }).png().toFile(file);
    log.push({ name, glb: path.basename(f), width: w, height: h, codec: uastc ? 'UASTC' : 'ETC1S', png_bytes: fs.statSync(file).size });
    console.log(name, w, h, uastc ? 'UASTC' : 'ETC1S');
  }
}
fs.writeFileSync(path.join(out, 'extracted_from_v1_glb.json'), JSON.stringify({ note: 'decoded from web_hero_v1 GLB KTX2 textures (lossy); not original bakes', maps: log }, null, 1));
