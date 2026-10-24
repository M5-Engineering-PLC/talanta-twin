import * as THREE from 'three/webgpu';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';

export function orderTiles(tiles, camera, coarseOnly = false) {
  const distance = t => (t.x0 + t.size / 2 - camera.x) ** 2 + (t.z0 + t.size / 2 - camera.z) ** 2;
  return tiles.filter(t => !coarseOnly || t.level === 1)
    .sort((a, b) => b.level - a.level || distance(a) - distance(b));
}

export function tileGeometry(tile, groundAt) {
  const geometry = new THREE.PlaneGeometry(tile.size, tile.size, 16, 16);
  geometry.rotateX(-Math.PI / 2);
  geometry.translate(tile.x0 + tile.size / 2, 0, tile.z0 + tile.size / 2);
  const positions = geometry.attributes.position;
  for (let i = 0; i < positions.count; i++) positions.setY(i, groundAt(positions.getX(i), positions.getZ(i)) + (tile.level === 0 ? 0.06 : 0.03));
  const uv = geometry.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i));
  geometry.computeBoundingSphere();
  return geometry;
}

// The exporter defines x0/z0 as west/north, image top as north, and L0 over L1.
export async function loadGroundTiles({ renderer, manifest, parent, camera, groundAt, coarseOnly = false }) {
  const index = manifest.ground?.index;
  if (!index || !manifest.files?.some(f => f.file === index)) return;
  const url = './' + index.replace(/^app\/public\//, '');
  const loader = new KTX2Loader().setTranscoderPath('./basis/').detectSupport(renderer);
  let loaded = 0;
  try {
    const response = await fetch(url);
    if (!response.ok) return;
    const { tiles } = await response.json();
    const listed = new Set(manifest.files.map(f => f.file));
    const directory = index.slice(0, index.lastIndexOf('/') + 1);
    const remaining = tiles.filter(t => listed.has(directory + t.file));
    while (remaining.length) {
      const tile = orderTiles(remaining, camera.position, coarseOnly)[0];
      if (!tile) break;
      remaining.splice(remaining.indexOf(tile), 1);
      if (![tile.x0, tile.z0, tile.size].every(Number.isFinite) || tile.size <= 0) continue;
      try {
        const texture = await loader.loadAsync('./' + (directory + tile.file).replace(/^app\/public\//, ''));
        texture.colorSpace = THREE.SRGBColorSpace;
        const geometry = tileGeometry(tile, groundAt);
        const material = new THREE.MeshBasicMaterial({ map: texture, polygonOffset: true, polygonOffsetFactor: tile.level === 0 ? -4 : -2, polygonOffsetUnits: -2 });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.name = `hero-ground-${tile.file}`;
        mesh.renderOrder = tile.level === 0 ? 2 : 1;
        parent.add(mesh); loaded++;
      } catch (error) { console.warn('Ground tile unavailable; keeping underlying ground:', tile.file, error); }
    }
  } catch (error) { console.warn('Ground tiles unavailable; keeping underlying ground:', error); }
  finally { loader.dispose(); console.info('hero ground tiles loaded:', loaded); }
}
