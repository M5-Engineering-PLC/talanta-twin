import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { useImpostor, installTreeImpostors } from '../src/hero/impostors.js';
test('distance switch uses hysteresis',()=>{
 assert.equal(useImpostor(290,300,false),false);
 assert.equal(useImpostor(310,300,false),true);
 assert.equal(useImpostor(290,300,true),true);
 assert.equal(useImpostor(260,300,true),false);
});
function fixture(){
 const root=new THREE.Group(), map=new THREE.Texture();
 for(let k=0;k<2;k++) {
 const lod=new THREE.LOD();lod.name='trees__'+k;
 const near=new THREE.InstancedMesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial(),2);
 const fg=new THREE.PlaneGeometry(2,4); fg.setIndex([0,2,1,2,3,1,0,2,1,2,3,1]);
 const far=new THREE.InstancedMesh(fg,new THREE.MeshBasicMaterial({map,alphaTest:.5}),2);
 for(let i=0;i<2;i++){const m=new THREE.Matrix4().makeTranslation(k*10+i*1000,0,0);near.setMatrixAt(i,m);far.setMatrixAt(i,m);}
 lod.addLevel(near,0);lod.addLevel(far,300);root.add(lod);
 }
 root.updateMatrixWorld(true);return root;
}
test('far trees share a draw call and switch individually',()=>{
 const root=fixture(), camera=new THREE.PerspectiveCamera();camera.position.set(0,10,0);
 const controller=installTreeImpostors(root,camera);controller.update();
 const batch=root.getObjectByName('hero-tree-impostors');
 assert.equal(batch.count,2);
 const lods=root.children.filter(o=>o.isLOD);
 assert.deepEqual(lods.map(l=>l.levels[0].object.count),[1,1]);
 assert.equal(batch.geometry.index.count,6);
 camera.position.set(2000,10,0);controller.update();assert.equal(batch.count,4);
 assert.deepEqual(lods.map(l=>l.levels[0].object.count),[0,0]);
});

test('multi-material near LOD groups keep all primitives and compact colours',()=>{
 const root=fixture();
 for(const lod of root.children){
   const mesh=lod.levels[0].object, group=new THREE.Group();
   mesh.instanceColor=new THREE.InstancedBufferAttribute(new Float32Array([1,0,0,0,1,0]),3);
   const second=mesh.clone(); group.add(mesh,second); lod.add(group);lod.levels[0].object=group;
 }
 const camera=new THREE.PerspectiveCamera();camera.position.set(1000,10,0);
 installTreeImpostors(root,camera).update();
 assert.equal(root.getObjectByName('hero-tree-impostors').count,2);
 for(const lod of root.children.filter(o=>o.isLOD)) {
  assert.equal(lod.levels[0].object.visible,true);
  for(const mesh of lod.levels[0].object.children){
   assert.equal(mesh.count,1);assert.deepEqual([...mesh.instanceColor.array.slice(0,3)],[0,1,0]);
  }
 }
});

test('UV-less textured near trees get finite coordinates without changing the source geometry',()=>{
 const root=fixture(), map=new THREE.Texture();
 const original=[];
 for(const lod of root.children){
  const mesh=lod.levels[0].object;
  mesh.geometry.deleteAttribute('uv'); mesh.material.map=map;original.push(mesh.geometry);
 }
 const camera=new THREE.PerspectiveCamera();camera.position.set(0,10,0);
 installTreeImpostors(root,camera);
 root.children.filter(o=>o.isLOD).forEach((lod,i)=>{
  const mesh=lod.levels[0].object,uv=mesh.geometry.getAttribute('uv');
  assert.ok(uv);assert.equal(uv.count,mesh.geometry.attributes.position.count);
  assert.notEqual(mesh.geometry,original[i]); assert.equal(original[i].getAttribute('uv'),undefined);
  assert.ok([...uv.array].every(v=>Number.isFinite(v)&&v>=0&&v<=1));
 });
 const batch=root.getObjectByName('hero-tree-impostors');
 assert.equal(batch.geometry.attributes.uv.count,batch.geometry.attributes.position.count);
});
