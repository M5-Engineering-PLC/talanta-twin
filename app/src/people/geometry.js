import * as THREE from 'three/webgpu';

let assets, pending;

// Decode once. The shader samples positions without a runtime skeleton.
export function decodeCrowdAssets(manifest, buffer) {
  if (manifest.version !== 1 || manifest.format !== 'RGBA16F' || buffer.byteLength !== manifest.width * manifest.height * 8) {
    throw new Error('Crowd animation asset dimensions are invalid');
  }
  const data = new Uint16Array(buffer.slice(0));
  const texture = new THREE.DataTexture(data, manifest.width, manifest.height, THREE.RGBAFormat, THREE.HalfFloatType);
  texture.magFilter = texture.minFilter = THREE.NearestFilter;
  texture.generateMipmaps = false; texture.needsUpdate = true;
  // levels lists the detail levels in the file. The desktop file has [0, 1]. The phone file has [1].
  assets = { manifest, texture, levels: manifest.lodLevels ?? manifest.lods.map((_, i) => i), profile: manifest.profile ?? 'desktop' };
  return assets;
}

// Phone: a phone user agent, a narrow window, or the low quality tier.
export function isPhoneProfile(quality, { userAgent = globalThis.navigator?.userAgent ?? '', width = globalThis.innerWidth } = {}) {
  const tier = typeof quality === 'string' ? quality : quality?.tier;
  return tier === 'low' || /Android|iPhone|iPad|Mobile/i.test(userAgent) || (Number.isFinite(width) && width < 768);
}

export function crowdFiles(phone) {
  return phone ? { json: '/people/crowd_phone.json', bin: '/people/animation_phone.bin' } : { json: '/people/crowd.json', bin: '/people/animation.bin' };
}

// Row block of a detail level inside the loaded animation texture.
export function crowdLevelIndex(lod) {
  const index = assets?.levels.indexOf(lod) ?? -1;
  if (index < 0) throw new Error(`Crowd detail level ${lod} is not in the loaded animation file`);
  return index;
}

export function crowdAssets() { return assets; }

export function loadCrowdAssets(options = {}) {
  if (assets) return Promise.resolve(assets);
  const files = crowdFiles(isPhoneProfile(options.quality, options));
  if (!pending) pending = (async () => {
    if (globalThis.process?.versions?.node) {
      // Node consumers include the existing offline bridge exporter.
      const moduleName = 'node:fs/promises';
      const { readFile } = await import(/* @vite-ignore */ moduleName);
      const directory = new URL(/* @vite-ignore */ '../../public/people/', import.meta.url);
      const [json, bytes] = await Promise.all([readFile(new URL(files.json.slice('/people/'.length), directory)), readFile(new URL(files.bin.slice('/people/'.length), directory))]);
      return decodeCrowdAssets(JSON.parse(json), bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
    }
    const [manifest, buffer] = await Promise.all([
      fetch(files.json).then(r => { if (!r.ok) throw new Error('Crowd geometry is unavailable'); return r.json(); }),
      fetch(files.bin).then(r => { if (!r.ok) throw new Error('Crowd animation is unavailable'); return r.arrayBuffer(); }),
    ]);
    return decodeCrowdAssets(manifest, buffer);
  })().catch(error => { pending = null; throw error; });
  return pending;
}

export function figureGeometry(lod = 0) {
  if (!assets) throw new Error('Load crowd assets before creating a figure');
  const data = assets.manifest.lods[crowdLevelIndex(lod)];
  const geometry = new THREE.BufferGeometry();
  geometry.setIndex(data.index);
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(data.position, 3));
  geometry.setAttribute('kind', new THREE.Float32BufferAttribute(data.kind, 1));
  geometry.setAttribute('fanVertex', new THREE.Float32BufferAttribute(data.kind.map((_, i) => i), 1));
  geometry.userData.lod = lod;
  return geometry;
}
