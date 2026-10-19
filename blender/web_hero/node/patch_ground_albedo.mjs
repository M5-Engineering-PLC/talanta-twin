// L3b (PLAN.md section 12): give the ground tiles of an existing site GLB their baked albedo as base colour.
// Run from the repo root after bake_ground_albedo.py:
//   node blender/web_hero/node/patch_ground_albedo.mjs <bundle dir in> <bundle dir out> [bundle name]
// e.g. node blender/web_hero/node/patch_ground_albedo.mjs <web_hero_v1 tree> blender/out/web_hero/web_hero_v2 web_hero_v2
// The v1 export shipped ground_site.jpg (600 px raw imagery) as the ground colour; see export_web.py. Each material
// with extras.talanta_bake_group "ground_NN" gets maps/ground_NN_albedo.png as KTX2 ETC1S (the same settings as
// post_glb.mjs) on its lightmap UV set, opaque. Every other file of the bundle is copied unchanged. The bundle
// manifest is rewritten with the new size and sha256 of the site GLB.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { NodeIO } from "@gltf-transform/core";
import { ALL_EXTENSIONS } from "@gltf-transform/extensions";
import { prune } from "@gltf-transform/functions";
import { MeshoptEncoder, MeshoptDecoder } from "meshoptimizer";
import { encodeToKTX2 } from "ktx2-encoder";
import sharp from "sharp";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const [IN, OUTDIR, NAME = path.basename(process.argv[3] ?? "")] = process.argv.slice(2);
if (!IN || !OUTDIR) { console.error("usage: patch_ground_albedo.mjs <bundle in> <bundle out> [name]"); process.exit(1); }
const MAPS = path.join(ROOT, "blender/out/web_hero/maps");
const SITE = "models/talanta_site.glb";

await MeshoptEncoder.ready; await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ "meshopt.encoder": MeshoptEncoder, "meshopt.decoder": MeshoptDecoder });
const imageDecoder = async (buf) => {
  const { data, info } = await sharp(buf).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data: new Uint8Array(data), width: info.width, height: info.height };
};

const doc = await io.read(path.join(IN, SITE));
const old = new Set();
let n = 0;
for (const mat of doc.getRoot().listMaterials()) {
  const ex = mat.getExtras() ?? {};
  const g = ex.talanta_bake_group;
  if (!g?.startsWith("ground_")) continue;
  const png = path.join(MAPS, `${g}_albedo.png`);
  if (!fs.existsSync(png)) { console.error(`missing ${png}: run bake_ground_albedo.py first`); process.exit(1); }
  const data = await encodeToKTX2(new Uint8Array(fs.readFileSync(png)), { isUASTC: false, qualityLevel: 200, compressionLevel: 2,
    generateMipmap: true, isPerceptual: true, isSetKTX2SRGBTransferFunc: true, imageDecoder });
  const prev = mat.getBaseColorTexture(); if (prev) old.add(prev);
  const tex = doc.createTexture(`${g}_albedo`).setImage(data).setMimeType("image/ktx2").setURI(`${g}_albedo.ktx2`);
  const uv = ex.talanta_lightmap?.texCoord ?? 0;
  mat.setBaseColorTexture(tex).setBaseColorFactor([1, 1, 1, 1]).setAlphaMode("OPAQUE");
  mat.getBaseColorTextureInfo().setTexCoord(uv);
  mat.setExtras({ ...ex, talanta_albedo_map: true, talanta_alpha_mask: false });
  n++;
}
for (const t of old) if (!t.listParents().some((p) => p !== doc.getRoot())) t.dispose();
await doc.transform(prune({ propertyTypes: ["texture", "accessor"] }));
console.log(`patched ${n} ground materials; replaced ${old.size} base colour texture(s)`);

// copy the bundle, then write the patched GLB and a new manifest
fs.cpSync(IN, OUTDIR, { recursive: true });
await io.write(path.join(OUTDIR, SITE), doc);
const mf = path.join(OUTDIR, "manifest.json");
const m = JSON.parse(fs.readFileSync(mf, "utf8"));
const buf = fs.readFileSync(path.join(OUTDIR, SITE));
const entry = m.files.find((f) => f.file === SITE);
entry.bytes = buf.length; entry.sha256 = createHash("sha256").update(buf).digest("hex");
if (m.models?.site) m.models.site.bytes = buf.length;
m.total_bytes = m.files.reduce((a, f) => a + f.bytes, 0);
if (NAME) m.bundle = NAME;
m.generated = new Date().toISOString();
m.patches = [...(m.patches ?? []), { what: "ground tiles: baked albedo as base colour (L3b)", script: "blender/web_hero/node/patch_ground_albedo.mjs", at: m.generated }];
fs.writeFileSync(mf, `${JSON.stringify(m, null, 1)}\n`);
console.log(`wrote ${path.relative(ROOT, OUTDIR)}: site GLB ${buf.length} bytes, total ${m.total_bytes} bytes`);
