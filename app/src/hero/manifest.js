// Both the installed app manifest and the read-only release bundle are supported.
export async function readManifest(response, url) {
  if (!response?.ok) throw new Error(`${url}: manifest request failed (${response?.status ?? 'network'})`);
  const text = await response.text();
  if (response.headers?.get('content-type')?.includes('text/html') || /^\s*</.test(text)) {
    throw new Error(`${url}: expected a JSON manifest, received HTML. Link the bundle with node app/tools/link_bundle.mjs.`);
  }
  let manifest;
  try { manifest = JSON.parse(text); } catch { throw new Error(`${url}: invalid JSON manifest`); }
  if (!manifest || typeof manifest.models !== 'object' || Array.isArray(manifest.models) || !Object.keys(manifest.models ?? {}).length) {
    throw new Error(`${url}: manifest.models is missing or empty`);
  }
  return normalizeManifest(manifest);
}

export function normalizeManifest(manifest) {
  const entries = manifest.files ?? manifest.tier1_files ?? [];
  if (entries.some(e => e.file.startsWith('app/public/'))) return manifest;
  const files = [...entries, ...(manifest.tod_files ?? [])];
  const models = Object.fromEntries(Object.entries(manifest.models).map(([name, model]) => {
    const file = files.find(e => /^(models|models_phone)\//.test(e.file) && e.file.split('/').at(-1) === model.file.split('/').at(-1));
    if (!file) throw new Error(`Manifest model is not listed: ${model.file}`);
    // public/models links to the bundle root. Keep models and models_phone distinct.
    return [name, { ...model, file: `app/public/models/${file.file}`, bytes: file.bytes }];
  }));
  return { ...manifest, models,
    files: files.map(e => ({ ...e, file: `app/public/${e.file}` })),
    ground: files.some(e => e.file === 'ground/tiles.json') ? { index: 'app/public/ground/tiles.json' } : null,
  };
}

// WebGPU rejects block-compressed textures below one 4 x 4 block, and the device is then lost.
export function dropInvalidCompressedMaps(material) {
  const dropped = [];
  for (const slot of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap', 'alphaMap', 'lightMap']) {
    const texture = material?.[slot], image = texture?.image;
    if (!texture?.isCompressedTexture || image?.width % 4 === 0 && image?.height % 4 === 0) continue;
    console.warn(`Dropped ${image?.width}x${image?.height} compressed ${slot} on ${material.name}`);
    material[slot] = null; dropped.push(slot);
  }
  return dropped;
}
