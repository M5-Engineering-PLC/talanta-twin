// Software geometry counts only. No textures, GPU, frustum culling, or timing benchmark.
// Run from app/: node tools/hero_geometry.mjs
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from 'three/webgpu';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { installTreeImpostors, isTreeGroup } from '../src/hero/impostors.js';
import { profileGeometry } from '../src/perf.js';

const app = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
loader.register(parser => {
  const original = parser.getDependency.bind(parser), textures = new Map();
  parser.getDependency = (type, index) => {
    if (type !== 'texture') return original(type, index);
    if (!textures.has(index)) { const t = new THREE.Texture(); t.name = `texture-${index}`; textures.set(index, t); }
    return Promise.resolve(textures.get(index));
  };
  return { name: 'geometry-only-textures' };
});
const start = performance.now();
const root = new THREE.Group(), groups = new Map();
for (const filename of ['talanta_hero.glb','talanta_site.glb']) {
  const bytes = await fs.readFile(path.join(app,'public/models',filename));
  const gltf = await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),'');
  const candidates=[];
  gltf.scene.traverse(n => { if (n.userData.lod_group) candidates.push(n); });
  root.add(gltf.scene);
  for (const n of candidates) {
    const ex=n.userData;
    if (!groups.has(ex.lod_group)) groups.set(ex.lod_group,{levels:[],max:Infinity});
    const group=groups.get(ex.lod_group);
    group.levels.push(n); if(Number.isFinite(ex.lod_max_m)) group.max=Math.min(group.max,ex.lod_max_m);
  }
}
for (const [name, group] of groups) {
 const lod=new THREE.LOD();lod.name=name; root.add(lod);
 group.levels.sort((a,b)=>a.userData.lod-b.userData.lod);
 for(const node of group.levels){
   const ex=node.userData, distances=ex.lod_switch_m;
   node.updateWorldMatrix(true,false);lod.attach(node);
   lod.addLevel(node,ex.lod===0?0:(Array.isArray(distances)?distances[ex.lod]:distances));
 }
 if(Number.isFinite(group.max))lod.addLevel(new THREE.Object3D(),group.max);
}
const camera=new THREE.PerspectiveCamera();camera.position.set(0,200,100000);
root.updateMatrixWorld(true);camera.updateMatrixWorld(true);
root.traverse(n=>{if(n.isLOD)n.update(camera);});
const before=profileGeometry(root);
function treeStats() {
 const result={triangles:0,drawCalls:0};
 for(const n of root.children) if((n.isLOD && isTreeGroup(n.name)) || n.name==='hero-tree-impostors') {
  const stats=profileGeometry(n);result.triangles+=stats.triangles;result.drawCalls+=stats.drawCalls;
 }
 return result;
}
const treesBefore=treeStats();
if (process.argv.includes('--inspect')) root.traverse(n => { if(n.isLOD && isTreeGroup(n.name)) console.log(n.name, n.levels.map(l => ({ type:l.object.type,count:l.object.count,index:l.object.geometry?.index?.count,positions:l.object.geometry?.attributes.position?.count,map:l.object.material?.map?.name,distance:l.distance }))); });
const controller=installTreeImpostors(root,camera);controller.update();
const after=profileGeometry(root),treesAfter=treeStats();
console.log(JSON.stringify({evidence:'software geometry, all-far camera at 100 km; no frustum culling; texture pixels skipped',before,after,treesBefore,treesAfter,geometryParseAndSetupMs:Math.round(performance.now()-start)},null,2));
