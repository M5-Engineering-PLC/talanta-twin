// Repair the painted images of a web_hero bundle in place, without a re-export or a rebake (2026-11-01).
//
// web_hero_v3 (T1) was exported from the 0730_gpu talanta_web_baked.blend, whose file images are unpacked and point at
// the Kaggle extraction folder /tmp/talanta/pack/... The glTF exporter wrote a 1x1 placeholder ("Image") for each
// missing one, and post_glb.mjs dedup then merged the three tree materials that all held the same placeholder:
//   shield_paint@stadium_ornament.001  shield (512x1024)                    -> 1x1 "Image"
//   canopy_tint_1.001                  island_tree_02_leaves_diff_1k (1k)   -> 1x1 "Image"
//   canopy_bark.001                    jacaranda_tree_trunk_diff_1k (1k)    -> merged into canopy_tint_1.001
//   canopy_tint_4.001                  jacaranda_tree_leaves_diff_1k (1k)   -> merged into canopy_tint_1.001
// WebGPU rejects a 1x1 block-compressed texture and loses the device.
//
// This works on the GLB bytes: it swaps the placeholder image data for the real KTX2 (encoded from the repo source with
// the post_glb.mjs ETC1S settings), appends the two lost images, re-creates the two lost materials from the reference
// bundle and points their primitives back at them (matched by mesh name, primitive index and index count). Geometry,
// light maps, AO and every other byte range are copied unchanged. Then it updates the model entries of manifest.json and
// manifest_phone.json (run post_glb.mjs reindex afterwards for the tod lists).
//
//   node blender/web_hero/node/repair_images.mjs bundle=web_hero_v3 ref=web_hero_v2_1 [dry]
import fs from "node:fs";
import crypto from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";
import { encodeToKTX2 } from "ktx2-encoder";
import * as T from "./tod_lib.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const opt = (k) => process.argv.find((a) => a.startsWith(`${k}=`))?.slice(k.length + 1) ?? null;
const BDIR = path.join(ROOT, "assets", opt("bundle") || "web_hero_v3"), RDIR = path.join(ROOT, "assets", opt("ref") || "web_hero_v2_1");
const DRY = process.argv.includes("dry");
const SOURCES = {
  shield: "blender/textures/shield.png",
  island_tree_02_leaves_diff_1k: "blender/assets/foliage/island_tree_02/island_tree_02_leaves_diff_1k.jpg",
  jacaranda_tree_trunk_diff_1k: "blender/assets/foliage/jacaranda_tree/jacaranda_tree_trunk_diff_1k.jpg",
  jacaranda_tree_leaves_diff_1k: "blender/assets/foliage/jacaranda_tree/jacaranda_tree_leaves_diff_1k.jpg",
};
// material -> image it paints with; "lost" materials were merged into "into" by dedup
const FIX = {
  hero: { replace: { "shield_paint@stadium_ornament.001": "shield" }, lost: {} },
  site: { replace: { "canopy_tint_1.001": "island_tree_02_leaves_diff_1k" },
          lost: { "canopy_bark.001": { image: "jacaranda_tree_trunk_diff_1k", into: "canopy_tint_1.001" },
                  "canopy_tint_4.001": { image: "jacaranda_tree_leaves_diff_1k", into: "canopy_tint_1.001" } } },
};
const sha = (b) => crypto.createHash("sha256").update(b).digest("hex");
const al = (n, a) => Math.ceil(n / a) * a;

function readGlb(f) {
  const b = fs.readFileSync(f);
  if (b.readUInt32LE(0) !== 0x46546c67) throw new Error(`${f}: not a GLB`);
  const jl = b.readUInt32LE(12), json = JSON.parse(b.toString("utf8", 20, 20 + jl));
  const bo = 20 + jl, bl = b.readUInt32LE(bo);
  if (b.readUInt32LE(bo + 4) !== 0x004e4942) throw new Error(`${f}: no BIN chunk`);
  return { json, bin: b.subarray(bo + 8, bo + 8 + bl) };
}
function writeGlb(f, json, bin) {
  let js = Buffer.from(JSON.stringify(json), "utf8"); js = Buffer.concat([js, Buffer.alloc(al(js.length, 4) - js.length, 0x20)]);
  const bp = Buffer.concat([bin, Buffer.alloc(al(bin.length, 4) - bin.length)]);
  const h = Buffer.alloc(12); h.writeUInt32LE(0x46546c67, 0); h.writeUInt32LE(2, 4); h.writeUInt32LE(12 + 8 + js.length + 8 + bp.length, 8);
  const c = (len, type) => { const x = Buffer.alloc(8); x.writeUInt32LE(len, 0); x.writeUInt32LE(type, 4); return x; };
  fs.writeFileSync(f, Buffer.concat([h, c(js.length, 0x4e4f534a), js, c(bp.length, 0x004e4942), bp]));
}
// every bufferView range in buffer 0 (the BIN chunk): plain views and EXT_meshopt_compression views (their data is in
// the extension; the view's own buffer is the empty fallback buffer)
function ranges(json) {
  const out = [];
  json.bufferViews.forEach((v, i) => {
    const m = v.extensions?.EXT_meshopt_compression;
    if (m && m.buffer === 0) out.push({ i, obj: m });
    else if (!m && v.buffer === 0) out.push({ i, obj: v });
  });
  return out;
}
// replace the bytes of bufferView vi with data; later ranges move by a multiple of 16 so their alignment is kept
function spliceView(json, bin, vi, data) {
  const rs = ranges(json), r = rs.find((x) => x.i === vi), o = r.obj.byteOffset || 0, L = r.obj.byteLength;
  const next = Math.min(bin.length, ...rs.map((x) => x.obj.byteOffset || 0).filter((x) => x >= o + L));
  const gap = next - o, delta = data.length > gap ? al(data.length - gap, 16) : 0;
  const out = Buffer.concat([bin.subarray(0, o), data, Buffer.alloc(gap + delta - data.length), bin.subarray(next)]);
  for (const x of rs) if ((x.obj.byteOffset || 0) >= next && x.i !== vi) x.obj.byteOffset = (x.obj.byteOffset || 0) + delta;
  r.obj.byteLength = data.length;
  return out;
}
function appendView(json, bin, data) {
  const o = al(bin.length, 16), out = Buffer.concat([bin, Buffer.alloc(o - bin.length), data]);
  json.bufferViews.push({ buffer: 0, byteOffset: o, byteLength: data.length });
  return { bin: out, view: json.bufferViews.length - 1 };
}
const imageOf = (json, ti) => { const t = json.textures[ti]; return t.extensions?.KHR_texture_basisu?.source ?? t.source; };
const matIndex = (json, name) => { const i = json.materials.findIndex((m) => m.name === name); if (i < 0) throw new Error(`material ${name} not found`); return i; };

const imageDecoder = async (buf) => { const { data, info } = await sharp(buf).ensureAlpha().raw().toBuffer({ resolveWithObject: true }); return { data: new Uint8Array(data), width: info.width, height: info.height }; };
const enc = {};
for (const [name, src] of Object.entries(SOURCES)) {   // post_glb.mjs "other colour images": ETC1S q200, level 2, mipmaps, sRGB
  const t0 = Date.now(), buf = fs.readFileSync(path.join(ROOT, src)), meta = await sharp(buf).metadata();
  const data = Buffer.from(await encodeToKTX2(new Uint8Array(buf), { isUASTC: false, qualityLevel: 200, compressionLevel: 2, generateMipmap: true,
    isPerceptual: true, isSetKTX2SRGBTransferFunc: true, imageDecoder }));
  T.checkImageSizes([{ name, size: T.ktx2Size(data) }], src);
  enc[name] = { data, src, size: T.ktx2Size(data), log: { map: name, png_bytes: buf.length, ktx2_bytes: data.length, seconds: (Date.now() - t0) / 1000, codec: "ETC1S" }, source_px: [meta.width, meta.height] };
}

const report = {};
for (const [glb, phone] of [["hero", false], ["site", false], ["hero", true], ["site", true]]) {
  const rel = phone ? `models_phone/talanta_${glb}_phone.glb` : `models/talanta_${glb}.glb`;
  const f = path.join(BDIR, rel), { json } = readGlb(f); let { bin } = readGlb(f);
  const ref = readGlb(path.join(RDIR, rel)).json;
  const fix = FIX[glb];
  if (json.buffers[0].uri !== undefined) throw new Error(`${rel}: buffer 0 is not the BIN chunk`);
  // 1. the placeholder image of each "replace" material gets the real data and name
  for (const [mname, iname] of Object.entries(fix.replace)) {
    const m = json.materials[matIndex(json, mname)], ii = imageOf(json, m.pbrMetallicRoughness.baseColorTexture.index), img = json.images[ii];
    const sz = T.ktx2Size(Buffer.from(bin.subarray(json.bufferViews[img.bufferView].byteOffset || 0, (json.bufferViews[img.bufferView].byteOffset || 0) + json.bufferViews[img.bufferView].byteLength)));
    if (img.name !== "Image" || sz[0] !== 1 || sz[1] !== 1) throw new Error(`${rel}: ${mname} image is ${img.name} ${sz.join("x")}, not the 1x1 placeholder`);
    const users = json.textures.map((t, k) => (imageOf(json, k) === ii ? k : -1)).filter((k) => k >= 0);
    const mats = json.materials.filter((x) => users.includes(x.pbrMetallicRoughness?.baseColorTexture?.index) || users.includes(x.emissiveTexture?.index) || users.includes(x.occlusionTexture?.index)).map((x) => x.name);
    if (mats.length !== 1) throw new Error(`${rel}: the placeholder is used by ${mats.join(", ")}`);
    bin = spliceView(json, bin, img.bufferView, enc[iname].data); img.name = iname;
  }
  // 2. the lost materials: copy each from the reference bundle with a new texture and image, then give back their primitives
  const sampler = json.textures[json.materials[matIndex(json, Object.keys(fix.replace)[0])].pbrMetallicRoughness.baseColorTexture.index].sampler;
  const lostIdx = {};
  for (const [mname, { image, into }] of Object.entries(fix.lost)) {
    if (json.materials.some((m) => m.name === mname)) throw new Error(`${rel}: ${mname} is already there`);
    const a = appendView(json, bin, enc[image].data); bin = a.bin;
    json.images.push({ name: image, mimeType: "image/ktx2", bufferView: a.view });
    json.textures.push({ sampler, extensions: { KHR_texture_basisu: { source: json.images.length - 1 } } });
    const m = structuredClone(ref.materials[matIndex(ref, mname)]); m.pbrMetallicRoughness.baseColorTexture = { ...m.pbrMetallicRoughness.baseColorTexture, index: json.textures.length - 1 };
    const intoM = json.materials[matIndex(json, into)], refInto = ref.materials[matIndex(ref, into)];
    const strip = (x) => JSON.stringify({ ...x, name: 0, pbrMetallicRoughness: { ...x.pbrMetallicRoughness, baseColorTexture: 0 } });
    if (strip(m) !== strip(refInto) || strip(intoM) !== strip(refInto)) throw new Error(`${rel}: ${mname} differs from ${into} beyond its texture; not a dedup merge`);
    json.materials.push(m); lostIdx[mname] = json.materials.length - 1;
  }
  if (Object.keys(fix.lost).length) {
    const refMesh = new Map(ref.meshes.map((m) => [m.name, m])), moved = {};
    for (const me of json.meshes) me.primitives.forEach((p, k) => {
      const rp = refMesh.get(me.name)?.primitives[k], rn = rp && ref.materials[rp.material]?.name;
      if (!(rn in lostIdx)) return;
      if (json.materials[p.material].name !== fix.lost[rn].into) throw new Error(`${rel}: ${me.name}[${k}] is ${json.materials[p.material].name}, expected ${fix.lost[rn].into}`);
      if (json.accessors[p.indices].count !== ref.accessors[rp.indices].count) throw new Error(`${rel}: ${me.name}[${k}] index count differs from the reference`);
      p.material = lostIdx[rn]; moved[rn] = (moved[rn] || 0) + 1;
    });
    for (const n of Object.keys(lostIdx)) if (!moved[n]) throw new Error(`${rel}: no primitive found for ${n}`);
    report[`${rel} primitives`] = moved;
  }
  json.buffers[0].byteLength = bin.length;
  // 3. every embedded image a multiple of 4
  const imgs = json.images.map((im) => { const v = json.bufferViews[im.bufferView]; return { name: im.name, size: T.ktx2Size(Buffer.from(bin.subarray(v.byteOffset || 0, (v.byteOffset || 0) + v.byteLength))) }; });
  T.checkImageSizes(imgs, rel);
  report[rel] = Object.values({ ...fix.replace, ...Object.fromEntries(Object.entries(fix.lost).map(([k, v]) => [k, v.image])) }).map((n) => `${n} ${imgs.find((x) => x.name === n).size.join("x")}`);
  if (!DRY) writeGlb(f, json, bin);
}

// manifests: model files, totals, texture log (the two "Image" entries become the real ones, the lost two are added)
if (!DRY) {
  for (const [mf, phone] of [["manifest.json", false], ["manifest_phone.json", true]]) {
    const mp = path.join(BDIR, mf), man = JSON.parse(fs.readFileSync(mp, "utf8")), list = phone ? man.tier1_files : man.files;
    for (const glb of ["hero", "site"]) {
      const rel = phone ? `models_phone/talanta_${glb}_phone.glb` : `models/talanta_${glb}.glb`, buf = fs.readFileSync(path.join(BDIR, rel));
      const e = list.find((x) => x.file === rel); if (!e) throw new Error(`${mf}: no entry for ${rel}`);
      e.bytes = buf.length; e.sha256 = sha(buf); man.models[glb].bytes = buf.length;
    }
    const ph = man.textures.map((t, i) => (t.map === "Image" ? i : -1)).filter((i) => i >= 0);
    if (ph.length !== 2) throw new Error(`${mf}: expected two "Image" texture entries, found ${ph.length}`);
    man.textures[ph[0]] = enc.shield.log; man.textures[ph[1]] = enc.island_tree_02_leaves_diff_1k.log;
    man.textures.push(enc.jacaranda_tree_trunk_diff_1k.log, enc.jacaranda_tree_leaves_diff_1k.log);
    if (phone) { man.tier1_bytes = list.reduce((a, f) => a + f.bytes, 0); man.within_budget = man.tier1_bytes <= man.budget_bytes; }
    else { man.total_bytes = list.reduce((a, f) => a + f.bytes, 0); man.within_budget = man.total_bytes < man.budget_bytes; }
    man.repaired = { date: "2026-11-01", by: "blender/web_hero/node/repair_images.mjs", images: Object.fromEntries(Object.entries(enc).map(([k, v]) => [k, { source: v.src, size: v.size, ktx2_bytes: v.data.length, sha256: sha(v.data) }])) };
    fs.writeFileSync(mp, JSON.stringify(man, null, 1) + "\n");
    report[mf] = phone ? { tier1_bytes: man.tier1_bytes, within_budget: man.within_budget } : { total_bytes: man.total_bytes, within_budget: man.within_budget };
  }
}
console.log(JSON.stringify(report, null, 1));
