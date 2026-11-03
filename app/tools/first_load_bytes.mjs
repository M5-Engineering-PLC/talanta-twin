// Software estimate from release manifests. This is not a browser transfer measurement.
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

export function firstLoadBytes(manifest, { phone = false, largePanorama = false } = {}) {
  const files = manifest.files ?? manifest.tier1_files ?? [];
  const path = file => file.replace(/^app\/public\//, '');
  const sum = entries => entries.reduce((n, entry) => n + entry.bytes, 0);
  const models = sum(files.filter(f => path(f.file).startsWith(phone ? 'models_phone/' : 'models/')));
  const ground = sum(files.filter(f => /^ground\//.test(path(f.file)) && (!phone || /\/(tiles\.json|L1_[^/]+\.ktx2)$/.test(path(f.file)))));
  const base = manifest.tod.base;
  const panorama = files.find(f => path(f.file) === `env/talanta_pano_${base}${largePanorama && !phone ? '.exr' : '_2048.hdr'}`)?.bytes ?? 0;
  const lightSet = time => sum((manifest.tod_files ?? []).filter(f => path(f.file).startsWith(`${manifest.tod.dir}/${time}/`)
    && (time !== base || path(f.file).endsWith('/tod.json'))));
  const start = lightSet('1805'), deferred = lightSet('2000');
  return { models, ground, panorama, start, deferred, before: models + ground + panorama + start + deferred,
    after: models + ground + panorama + start };
}

export async function report() {
  console.log('Software estimate: cold hero assets through the first sequence frame; MB = 1,000,000 bytes.');
  console.log('Includes models, listed ground tiles, base panorama and light sets. Excludes code, manifests, decoders, crowd assets and HTTP overhead.');
  console.log('Before: 1805 + 2000 maps requested during preparation. After: only 1805; 2000 and other sets wait for idle.');
  for (const [label, name, options] of [
    ['Desktop (HDR)', 'manifest.json', {}],
    ['Phone (HDR)', 'manifest_phone.json', { phone: true }],
    ['Desktop (capable GPU, EXR)', 'manifest.json', { largePanorama: true }],
  ]) {
    const manifest = JSON.parse(await readFile(new URL(`../../assets/web_hero_v3/${name}`, import.meta.url), 'utf8'));
    const bytes = firstLoadBytes(manifest, options);
    const mb = n => (n / 1_000_000).toFixed(6);
    console.log(`${label}: before ${mb(bytes.before)} MB; after ${mb(bytes.after)} MB; deferred ${mb(bytes.deferred)} MB`);
    console.log(`  models ${mb(bytes.models)} MB; ground ${mb(bytes.ground)} MB; panorama ${mb(bytes.panorama)} MB; start 1805 ${mb(bytes.start)} MB`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await report();
