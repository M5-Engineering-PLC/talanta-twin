// Web hero step 3b: finish the GLBs staged by blender/web_hero/export_web.py and write the manifest.
//
// Run from the repo root:  node blender/web_hero/node/post_glb.mjs [test]
// (npm install once in blender/web_hero/node; versions are pinned in package.json)
//   instancing  proto nodes become EXT_mesh_gpu_instancing nodes (TRANSLATION, ROTATION, SCALE, seats _COLOR_0)
//   lightmaps   each baked material gets its group's maps as KTX2 (Basis ETC1S, mipmapped):
//                 light  -> emissiveTexture with emissiveFactor 0 (the app moves it to material.lightMap)
//                 ao     -> occlusionTexture (stadium and roof groups)
//                 albedo -> baseColorTexture (ground tiles, sport, roads: procedural surfaces)
//   compression dedup, prune, meshopt (EXT_meshopt_compression, 16-bit positions)
// Writes app/public/models/talanta_hero.glb, talanta_site.glb and manifest.json (test: blender/out/web_hero/test/export/final).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { NodeIO } from "@gltf-transform/core";
import { ALL_EXTENSIONS, EXTMeshGPUInstancing, KHRTextureBasisu } from "@gltf-transform/extensions";
import { dedup, prune, meshopt } from "@gltf-transform/functions";
import { MeshoptEncoder, MeshoptDecoder } from "meshoptimizer";
import { encodeToKTX2 } from "ktx2-encoder";
import sharp from "sharp";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const TEST = process.argv.includes("test");
const BASE = path.join(ROOT, "blender/out/web_hero", TEST ? "test" : "");
const STAGE = path.join(BASE, "export");
const DEST = TEST ? path.join(STAGE, "final") : path.join(ROOT, "app/public/models");
const ENV = path.join(ROOT, "app/public/env");
fs.mkdirSync(DEST, { recursive: true });
const stage = JSON.parse(fs.readFileSync(path.join(STAGE, "stage.json"), "utf8"));
const blob = fs.readFileSync(path.join(STAGE, "instances.bin"));
const bake = stage.bake;
const AO_GROUPS = (g) => g.startsWith("stadium_") || g === "roof";
const LOD_D = [0, 300, 1000];

await MeshoptEncoder.ready; await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ "meshopt.encoder": MeshoptEncoder, "meshopt.decoder": MeshoptDecoder });
const imageDecoder = async (buf) => {
  const { data, info } = await sharp(buf).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data: new Uint8Array(data), width: info.width, height: info.height };
};

function primTris(prim) {
  const idx = prim.getIndices(); const n = idx ? idx.getCount() : prim.getAttribute("POSITION").getCount();
  return prim.getMode() === 4 ? n / 3 : 0;
}
const meshTris = (mesh) => mesh.listPrimitives().reduce((a, p) => a + primTris(p), 0);

const texLog = [];
async function ktx(doc, cache, group, kind) {
  const key = `${group}_${kind}`;
  if (cache.has(key)) return cache.get(key);
  const png = fs.readFileSync(path.join(BASE, "maps", `${key}.png`));
  const t0 = Date.now();
  const data = await encodeToKTX2(new Uint8Array(png), {
    isUASTC: false, qualityLevel: 200, compressionLevel: 2, generateMipmap: true,
    isPerceptual: kind !== "ao", imageDecoder,
  });
  const tex = doc.createTexture(key).setImage(data).setMimeType("image/ktx2").setURI(`${key}.ktx2`);
  cache.set(key, tex);
  texLog.push({ map: key, png_bytes: png.length, ktx2_bytes: data.length, seconds: (Date.now() - t0) / 1000 });
  return tex;
}

const result = {};
for (const glb of ["hero", "site"]) {
  const doc = await io.read(path.join(STAGE, `${glb}_stage.glb`));
  const root = doc.getRoot(); const scene = root.getDefaultScene() || root.listScenes()[0];
  const buffer = root.listBuffers()[0];
  // ---------------------------------------------------------------- instancing
  const gpu = doc.createExtension(EXTMeshGPUInstancing).setRequired(false);
  const sets = [];
  for (const e of stage.instances.filter((x) => x.glb === glb)) {
    const acc = {};
    for (const [k, a] of Object.entries(e.attributes)) {
      const arr = new Float32Array(blob.buffer.slice(blob.byteOffset + a.offset, blob.byteOffset + a.offset + a.count * a.components * 4));
      acc[k] = doc.createAccessor(`${e.set}_${k}`).setType(a.components === 4 ? "VEC4" : "VEC3").setArray(arr).setBuffer(buffer);
    }
    for (const l of e.lods) {
      const proto = root.listNodes().find((n) => n.getName() === l.node);
      if (!proto) throw new Error(`proto node ${l.node} missing`);
      const im = gpu.createInstancedMesh();
      for (const [k, a] of Object.entries(acc)) im.setAttribute(k, a);
      const node = doc.createNode(`${e.set}__${e.proto}__LOD${l.lod}`).setMesh(proto.getMesh())
        .setExtension("EXT_mesh_gpu_instancing", im)
        .setExtras({ instanced_set: e.set, lod_group: `${e.set}__${e.proto}`, lod: l.lod, lod_switch_m: e.lods.map((x) => x.switch_m ?? LOD_D[x.lod]),
                     ...(e.max_m ? { lod_max_m: e.max_m } : {}), instances: e.count });
      scene.addChild(node); proto.dispose();
      sets.push({ set: e.set, proto: e.proto, lod: l.lod, instances: e.count, tris_each: l.tris, tris: e.count * l.tris });
    }
  }
  // ---------------------------------------------------------------- lightmaps
  const basisu = doc.createExtension(KHRTextureBasisu).setRequired(true);
  const cache = new Map();
  for (const mat of root.listMaterials()) {
    const ex = mat.getExtras() || {}; const g = ex.talanta_bake_group;
    if (!g) continue;
    const scale = bake.groups[g].light_scale;
    mat.setEmissiveTexture(await ktx(doc, cache, g, "light")).setEmissiveFactor([0, 0, 0]);
    mat.getEmissiveTextureInfo().setTexCoord(0);
    if (AO_GROUPS(g)) { mat.setOcclusionTexture(await ktx(doc, cache, g, "ao")); mat.getOcclusionTextureInfo().setTexCoord(0); }
    if (ex.talanta_albedo_map) { mat.setBaseColorTexture(await ktx(doc, cache, g, "albedo")); mat.getBaseColorTextureInfo().setTexCoord(0); mat.setBaseColorFactor([1, 1, 1, 1]); }
    mat.setExtras({ talanta_bake_group: g, talanta_lightmap: { source: "emissiveTexture", texCoord: 0, intensity: +(scale * Math.PI).toFixed(4), color_space: "sRGB" } });
  }
  // ---------------------------------------------------------------- compression
  await doc.transform(dedup(), prune({ keepAttributes: true, keepLeaves: false }),
    meshopt({ encoder: MeshoptEncoder, level: "medium", quantizePosition: 16 }));
  // ---------------------------------------------------------------- triangle counts per LOD level
  const groups = new Map();
  for (const n of root.listNodes()) {
    const m = n.getMesh(); if (!m) continue;
    const ex = n.getExtras() || {}; const gpuI = n.getExtension("EXT_mesh_gpu_instancing");
    const count = gpuI ? gpuI.listAttributes()[0].getCount() : 1;
    const key = ex.lod_group || n.getName();
    if (!groups.has(key)) groups.set(key, { lods: {}, max: ex.lod_max_m ?? Infinity });
    groups.get(key).lods[ex.lod ?? 0] = meshTris(m) * count;
  }
  const tris = [0, 0, 0];
  for (const { lods, max } of groups.values()) {
    for (let L = 0; L < 3; L++) {
      if (max <= LOD_D[L]) continue;
      const have = Object.keys(lods).map(Number).filter((k) => k <= L);
      if (have.length) tris[L] += lods[Math.max(...have)];
    }
  }
  const file = path.join(DEST, `talanta_${glb}.glb`);
  await io.write(file, doc);
  result[glb] = { file: path.relative(ROOT, file), bytes: fs.statSync(file).size, triangles: { lod0: tris[0], lod1_300m: tris[1], lod2_1km: tris[2] },
                  textures: [...cache.keys()].length, instanced_sets: sets };
  console.log(glb, JSON.stringify({ bytes: result[glb].bytes, triangles: result[glb].triangles }));
}

// ---------------------------------------------------------------- manifest
const envFiles = ["talanta_0735.hdr", "talanta_0735_2048.hdr"].filter((f) => fs.existsSync(path.join(ENV, f)))
  .map((f) => ({ file: `app/public/env/${f}`, bytes: fs.statSync(path.join(ENV, f)).size }));
const pano = fs.existsSync(path.join(BASE, "panorama_log.json")) ? JSON.parse(fs.readFileSync(path.join(BASE, "panorama_log.json"), "utf8")) : null;
const files = [...Object.values(result).map((r) => ({ file: r.file, bytes: r.bytes })), ...envFiles];
const manifest = {
  generated: new Date().toISOString().slice(0, 10),
  source: "blender/out/talanta_site.blend via blender/web_hero (bake_lightmaps.py, render_panorama.py, export_web.py, node/post_glb.mjs)",
  frame: "glTF y-up = app frame: x east, y up, z south, metres, origin at the pitch centre (Blender (x, y, z) -> (x, z, -y))",
  time: { date: bake.date, local: `${bake.time_eat} EAT` },
  sun: { elevation_deg: bake.sun_elevation_deg, azimuth_deg: bake.sun_azimuth_deg, direction_to_sun: bake.sun_dir_app,
         energy_w_m2: bake.sun_energy, color_linear: bake.sun_color.map((c) => +c.toFixed(4)) },
  files, total_bytes: files.reduce((a, f) => a + f.bytes, 0),
  budget: { max_bytes: 60e6, max_lod0_triangles: 1.5e6, lod0_triangles: Object.values(result).reduce((a, r) => a + r.triangles.lod0, 0) },
  models: result,
  lod: { levels_m: LOD_D, rule: "nodes share extras.lod_group; extras.lod is the level and extras.lod_switch_m the start distance of each level; extras.lod_max_m hides the group beyond it. Build a THREE.LOD per lod_group." },
  lightmaps: {
    how: "Baked materials carry extras.talanta_lightmap. Move material.emissiveMap to material.lightMap (texture.channel stays 0, sRGB), set emissive to black and lightMapIntensity = extras.talanta_lightmap.intensity (light_scale x pi, three.js r155+ physically based lights).",
    contains: "Cycles diffuse direct + indirect at 07:35 (sun, sky, bounce) for a white surface; sky occlusion is already inside, so do not add a DirectionalLight, hemisphere light or environment diffuse to lightmapped meshes. Use the environment map for specular only; aoMap (occlusionTexture) occludes it.",
    textures: "KTX2 (Basis ETC1S, mipmaps, KHR_texture_basisu, required): GLTFLoader needs a KTX2Loader.",
    maps: texLog,
  },
  environment: pano ? { ...pano, use: "scene.environment and background; equirectangular, linear Radiance HDR; image centre looks north (-z)." } : "not rendered yet",
  tone_mapping: { blender_view_transform: stage.view.transform, blender_look: stage.view.look, blender_exposure_ev: stage.view.exposure,
                  three: `AgXToneMapping, toneMappingExposure = 2^${stage.view.exposure} = ${(2 ** stage.view.exposure).toFixed(4)}` },
  labels: "Geometry and colours are estimated (design model and detail sheets); see the parameter ledger. Instanced people or crowds are not included in this export.",
};
fs.writeFileSync(path.join(DEST, "manifest.json"), JSON.stringify(manifest, null, 1) + "\n");
console.log(JSON.stringify({ total_bytes: manifest.total_bytes, lod0_triangles: manifest.budget.lod0_triangles }));
