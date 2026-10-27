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
  assets = { manifest, texture };
  return assets;
}

export function crowdAssets() { return assets; }

export function loadCrowdAssets() {
  if (assets) return Promise.resolve(assets);
  if (!pending) pending = (async () => {
    if (globalThis.process?.versions?.node) {
      // Node consumers include the existing offline bridge exporter.
      const moduleName = 'node:fs/promises';
      const { readFile } = await import(/* @vite-ignore */ moduleName);
      const directory = new URL(/* @vite-ignore */ '../../public/people/', import.meta.url);
      const [json, bytes] = await Promise.all([readFile(new URL('crowd.json', directory)), readFile(new URL('animation.bin', directory))]);
      return decodeCrowdAssets(JSON.parse(json), bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
    }
    const [manifest, buffer] = await Promise.all([
      fetch('/people/crowd.json').then(r => { if (!r.ok) throw new Error('Crowd geometry is unavailable'); return r.json(); }),
      fetch('/people/animation.bin').then(r => { if (!r.ok) throw new Error('Crowd animation is unavailable'); return r.arrayBuffer(); }),
    ]);
    return decodeCrowdAssets(manifest, buffer);
  })().catch(error => { pending = null; throw error; });
  return pending;
}

export function figureGeometry(lod = 0) {
  if (!assets) throw new Error('Load crowd assets before creating a figure');
  const data = assets.manifest.lods[lod];
  const geometry = new THREE.BufferGeometry();
  geometry.setIndex(data.index);
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(data.position, 3));
  geometry.setAttribute('kind', new THREE.Float32BufferAttribute(data.kind, 1));
  geometry.setAttribute('fanVertex', new THREE.Float32BufferAttribute(data.kind.map((_, i) => i), 1));
  geometry.userData.lod = lod;
  return geometry;
}
