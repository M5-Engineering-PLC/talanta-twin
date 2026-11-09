import { copyFile, mkdir, stat, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { meshopt, prune } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';

const bundle = new URL('../../../assets/web_hero_v3/models_phone/', import.meta.url);
const output = new URL('../../../app/public/perimeter/', import.meta.url);

await Promise.all([MeshoptDecoder.ready, MeshoptEncoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.decoder': MeshoptDecoder,
  'meshopt.encoder': MeshoptEncoder,
});
const site = await io.read(fileURLToPath(new URL('talanta_site_phone.glb', bundle)));
// Keep the apron, forecourt, adjacent approaches and perimeter fence.
const perimeter = /^(?:fc_|fp_|ge_apron_|pi_east_|pk_|boundary_fence$|entrance_canopies$)/;
for (const node of site.getRoot().listNodes()) {
  if (!perimeter.test(node.getName())) node.dispose();
}
await site.transform(prune({ keepAttributes: true }), meshopt({ encoder: MeshoptEncoder, level: 'medium' }));

await mkdir(output, { recursive: true });
const models = {
  hero: { file: 'talanta_hero_phone.glb' },
  site: { file: 'talanta_perimeter.glb' },
};
await copyFile(new URL(models.hero.file, bundle), new URL(models.hero.file, output));
await io.write(fileURLToPath(new URL(models.site.file, output)), site);
for (const model of Object.values(models)) {
  model.bytes = (await stat(new URL(model.file, output))).size;
}
const files = Object.values(models).map(model => ({ file: 'app/public/models/' + model.file, bytes: model.bytes }));
await writeFile(new URL('manifest_phone.json', output), JSON.stringify({ models, files }, null, 2));
console.log(models);
