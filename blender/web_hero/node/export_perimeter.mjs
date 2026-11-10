import { copyFile, mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { compactPrimitive, meshopt, prune } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';

const bundle = new URL('../../../assets/web_hero_v3/models_phone/', import.meta.url);
const output = new URL('../../../app/public/perimeter/', import.meta.url);
const boundaryCsv = new URL('../../../gis/measurements/normalized/site_boundary_w1b_2026-10-16.csv', import.meta.url);
const boundary = (await readFile(boundaryCsv, 'utf8')).trim().split(/\r?\n/).slice(1)
  .map(row => row.split(','))
  .filter(row => row[5] === '1')
  .map(row => [Number(row[3]), Number(row[4])]);
if (boundary.length < 3 || boundary.flat().some(value => !Number.isFinite(value))) {
  throw new Error('Invalid W1b site boundary');
}

function insideBoundary(x, z) {
  let inside = false;
  for (let i = 0, j = boundary.length - 1; i < boundary.length; j = i++) {
    const [ax, az] = boundary[i];
    const [bx, bz] = boundary[j];
    if ((az > z) !== (bz > z) && x < ax + (bx - ax) * (z - az) / (bz - az)) inside = !inside;
  }
  return inside;
}

function insideNode(node) {
  const m = node.getWorldMatrix();
  return ([x, y, z]) => insideBoundary(
    m[0] * x + m[4] * y + m[8] * z + m[12],
    m[2] * x + m[6] * y + m[10] * z + m[14],
  );
}

function cropInstances(document, node, instances) {
  const positions = instances.getAttribute('TRANSLATION');
  if (!positions) throw new Error(`Missing instance translations on ${node.getName()}`);
  const inside = insideNode(node);
  const kept = Array.from({ length: positions.getCount() }, (_, i) => i)
    .filter(i => inside(positions.getElement(i, [])));
  if (!kept.length) return node.dispose();
  for (const semantic of instances.listSemantics()) {
    const source = instances.getAttribute(semantic);
    const width = source.getElementSize();
    const data = source.getArray();
    const filtered = new data.constructor(kept.length * width);
    kept.forEach((index, i) => filtered.set(data.subarray(index * width, (index + 1) * width), i * width));
    instances.setAttribute(semantic, document.createAccessor().copy(source).setArray(filtered));
  }
}

function cropTriangles(document, node) {
  const mesh = node.getMesh();
  const inside = insideNode(node);
  for (const primitive of mesh.listPrimitives()) {
    if (primitive.getMode() !== 4) throw new Error(`Expected triangles on ${node.getName()}`);
    const positions = primitive.getAttribute('POSITION');
    const indices = primitive.getIndices()?.getArray();
    const count = indices?.length ?? positions.getCount();
    const kept = [];
    const point = [[], [], []];
    for (let i = 0; i < count; i += 3) {
      const triangle = [indices?.[i] ?? i, indices?.[i + 1] ?? i + 1, indices?.[i + 2] ?? i + 2];
      triangle.forEach((index, corner) => positions.getElement(index, point[corner]));
      const center = point[0].map((value, axis) => (value + point[1][axis] + point[2][axis]) / 3);
      if (inside(center)) kept.push(...triangle);
    }
    if (!kept.length) primitive.dispose();
    else if (kept.length < count) {
      primitive.setIndices(document.createAccessor().setType('SCALAR')
        .setBuffer(positions.getBuffer()).setArray(new Uint32Array(kept)));
      compactPrimitive(primitive);
    }
  }
  if (!mesh.listPrimitives().length) node.dispose();
}

await Promise.all([MeshoptDecoder.ready, MeshoptEncoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.decoder': MeshoptDecoder,
  'meshopt.encoder': MeshoptEncoder,
});
const site = await io.read(fileURLToPath(new URL('talanta_site_phone.glb', bundle)));
// Keep authored venue features whole. Crop shared layers to the measured site.
const venue = /^(?:fc_|fp_|ge_apron_|ge_east_|ge_road_north_east|pi_east_|pk_|sw_|jets__|track_masts__|boundary_fence$|entrance_canopies$)/;
const shared = /^(?:ground_|trees__|buildings$|layout_cars_visualization$|parking_lines$|roads_final$|road_markings_final$)/;
for (const node of site.getRoot().listNodes()) {
  if (venue.test(node.getName())) continue;
  if (!shared.test(node.getName())) node.dispose();
  else {
    const instances = node.getExtension('EXT_mesh_gpu_instancing');
    if (instances) cropInstances(site, node, instances);
    else cropTriangles(site, node);
  }
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
