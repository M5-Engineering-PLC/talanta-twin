// Pure helpers for post_glb.mjs tod mode (ENV-01): no sharp, no encoder, no gltf-transform. Unit tests: app/tools/todBake.test.mjs.
import zlib from "node:zlib";

// hhmm -> preset name of the Kaggle GPU light sets (also the keys of app/src/hero/grade.js GRADE_PRESETS)
export const TOD_PRESETS = Object.freeze({ "0730": "morning_golden", "1030": "daylight_artistic", "1805": "sunset_artistic", "2000": "night" });
export const PHONE_PX = 1024, PHONE_GROUND_PX = 256, MAX_TEXELS = 12582912;

export function checkHHMM(hhmm) {
  if (!/^([01]\d|2[0-3])[0-5]\d$/.test(hhmm || "")) throw new Error(`tod=<HHMM> needs four digits, got "${hhmm}"`);
  if (!TOD_PRESETS[hhmm]) throw new Error(`no preset for ${hhmm}; known: ${Object.keys(TOD_PRESETS).join(" ")}`);
  return hhmm;
}
export const hhmmFromEat = (s) => String(s).replace(/[^0-9:]/g, "").replace(":", "").slice(0, 4).padStart(4, "0"); // "07:30 EAT" -> "0730"

/** [width, height] of a PNG from its IHDR chunk. */
export function pngSize(buf) {
  if (buf.length < 24 || buf.readUInt32BE(0) !== 0x89504e47 || buf.toString("latin1", 12, 16) !== "IHDR") throw new Error("not a PNG");
  return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
}

/** Decode an 8-bit, non-interlaced PNG (gray, RGB, gray+alpha, RGBA) to { width, height, channels, data }. */
export function decodePng(buf) {
  const [width, height] = pngSize(buf);
  const depth = buf[24], type = buf[25];
  if (depth !== 8 || buf[28] !== 0 || ![0, 2, 4, 6].includes(type)) throw new Error(`PNG layout not supported (depth ${depth}, colour type ${type}, interlace ${buf[28]})`);
  const channels = { 0: 1, 2: 3, 4: 2, 6: 4 }[type];
  const idat = [];
  for (let p = 8; p < buf.length;) {
    const len = buf.readUInt32BE(p), name = buf.toString("latin1", p + 4, p + 8);
    if (name === "IDAT") idat.push(buf.subarray(p + 8, p + 8 + len));
    p += 12 + len;
  }
  const raw = zlib.inflateSync(Buffer.concat(idat)), stride = width * channels, out = Buffer.alloc(stride * height);
  for (let y = 0; y < height; y++) {
    const f = raw[y * (stride + 1)], src = y * (stride + 1) + 1, dst = y * stride;
    for (let x = 0; x < stride; x++) {
      const a = x >= channels ? out[dst + x - channels] : 0, b = y ? out[dst - stride + x] : 0, c = x >= channels && y ? out[dst - stride + x - channels] : 0;
      let v = raw[src + x];
      if (f === 1) v += a; else if (f === 2) v += b; else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      else if (f !== 0) throw new Error(`bad PNG filter ${f}`);
      out[dst + x] = v & 255;
    }
  }
  return { width, height, channels, data: out };
}

const srgbToLinear = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
const LUT = Float64Array.from({ length: 256 }, (_, i) => srgbToLinear(i));

/** Sum of linear luminance (Rec.709) over every pixel of an sRGB PNG, times scale, and the pixel count. */
export function pngLuminanceSum(buf, scale = 1) {
  const { width, height, channels, data } = decodePng(buf);
  let sum = 0;
  for (let i = 0; i < data.length; i += channels) {
    sum += channels < 3 ? LUT[data[i]] : 0.2126 * LUT[data[i]] + 0.7152 * LUT[data[i + 1]] + 0.0722 * LUT[data[i + 2]];
  }
  return { sum: sum * scale, count: width * height };
}

/**
 * Mean light of all ground_*_light maps: sum of (linear luminance x light_scale) over all their pixels / pixel count.
 * readMap(group) returns the PNG buffer. Light PNGs hold sRGB(light / light_scale), so the scale restores the physical level.
 */
export function groundLuminance(groups, readMap) {
  let sum = 0, count = 0;
  for (const [name, g] of Object.entries(groups)) {
    if (!name.startsWith("ground_")) continue;
    const r = pngLuminanceSum(readMap(name), g.light_scale);
    sum += r.sum; count += r.count;
  }
  if (!count) throw new Error("no ground_* groups");
  return sum / count;
}

/** The base set a bundle carries: time, the [w, h] of each light map, mean ground light. Stored in manifest.tod_base. */
export function baseInfo(bake, readMap) {
  const groups = {};
  for (const name of Object.keys(bake.groups).sort()) groups[name] = pngSize(readMap(name));
  return { time: hhmmFromEat(bake.time_eat), groups, ground_luminance: +groundLuminance(bake.groups, readMap).toFixed(8) };
}

/** Problems when a tod set differs from the bundle's base set (group list or any map size). Empty array = compatible. */
export function checkAgainstBase(baseGroups, setGroups) {
  const problems = [];
  const a = Object.keys(baseGroups).sort(), b = Object.keys(setGroups).sort();
  for (const g of a) if (!(g in setGroups)) problems.push(`group ${g} is in the bundle but not in the set`);
  for (const g of b) if (!(g in baseGroups)) problems.push(`group ${g} is in the set but not in the bundle`);
  for (const g of a) {
    if (!(g in setGroups)) continue;
    const [bw, bh] = baseGroups[g], [sw, sh] = setGroups[g];
    if (bw !== sw || bh !== sh) problems.push(`map ${g}_light is ${sw}x${sh}, the bundle has ${bw}x${bh}`);
  }
  return problems;
}

export const groundTileGain = (luminance, baseLuminance) => {
  if (!(luminance >= 0) || !(baseLuminance > 0)) throw new Error(`ground luminance ${luminance} / ${baseLuminance} is not usable`);
  return +(luminance / baseLuminance).toFixed(5);
};

/** Pixel size of the encoded map: the 12.58 Mpix cap of the Basis encoder, then (phone) PHONE_PX / PHONE_GROUND_PX. Same rules as post_glb bundle mode. */
export function encodedSize(width, height, group, phone) {
  let w = width, h = height;
  if (w * h > MAX_TEXELS) {
    const s = Math.sqrt(MAX_TEXELS / (w * h));
    w = Math.floor(w * s / 1024) * 1024 || Math.floor(w * s / 4) * 4;
    h = Math.round(height * w / width / 4) * 4;
  }
  if (phone) {
    const px = group.startsWith("ground_") ? PHONE_GROUND_PX : PHONE_PX;
    if (Math.max(w, h) > px) { const m = Math.max(w, h); [w, h] = [Math.round(w * px / m), Math.round(h * px / m)]; }
  }
  return [w, h];
}

/** ktx2-encoder options (without imageDecoder). Same codec rules as bundle mode: desktop light/ao UASTC+RDO+zstd, colour and phone ETC1S. */
export function ktxOptions(kind, phone) {
  const uastc = !phone && kind !== "albedo";
  return uastc
    ? { isUASTC: true, uastcLDRQualityLevel: 2, enableRDO: true, rdoQualityLevel: 1.0, needSupercompression: true, generateMipmap: true,
        isPerceptual: kind !== "ao", isSetKTX2SRGBTransferFunc: kind !== "ao" }
    : { isUASTC: false, qualityLevel: phone ? 255 : 200, compressionLevel: 2, generateMipmap: true, isPerceptual: kind !== "ao",
        isSetKTX2SRGBTransferFunc: kind !== "ao" };
}

/** Panorama names found in <set>/env: { hdr, exr } (basenames) or null. */
export function panoramaNames(names) {
  const hdr = names.find((n) => /_2048\.hdr$/i.test(n)) || names.find((n) => /\.hdr$/i.test(n)) || null;
  const exr = names.find((n) => /\.exr$/i.test(n)) || null;
  return hdr || exr ? { hdr, exr } : null;
}

const GROUP_KEYS = ["file", "bytes", "sha256", "intensity"];
/** Check the shape of a tod.json; returns the document or throws. Mirrors app/src/hero/timeOfDay.js parseTod. */
export function validateTod(tod) {
  const fail = (m) => { throw new Error(`tod.json: ${m}`); };
  if (!tod || typeof tod !== "object") fail("not an object");
  if (!TOD_PRESETS[tod.time]) fail(`time "${tod.time}" is not a known set`);
  if (tod.preset !== TOD_PRESETS[tod.time]) fail(`preset "${tod.preset}" does not match ${tod.time}`);
  if (!tod.groups || typeof tod.groups !== "object" || !Object.keys(tod.groups).length) fail("groups is missing");
  for (const [name, g] of Object.entries(tod.groups)) {
    for (const k of GROUP_KEYS) if (g?.[k] === undefined) fail(`group ${name} has no ${k}`);
    if (!/^[0-9a-f]{64}$/.test(g.sha256)) fail(`group ${name} sha256 is bad`);
    if (!(g.intensity > 0) || !Number.isInteger(g.bytes)) fail(`group ${name} intensity or bytes is bad`);
  }
  if (!(tod.ground_tile_gain >= 0)) fail("ground_tile_gain is missing");
  if (tod.panorama != null && !(tod.panorama.hdr || tod.panorama.exr)) fail("panorama has no file");
  return tod;
}
