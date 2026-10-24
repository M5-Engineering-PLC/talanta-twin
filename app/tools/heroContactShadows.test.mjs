import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { contactShadowBatch } from '../src/hero/contactShadows.js';
test('blob follows a supplied surface matrix and switches off',()=>{
 const blobs=contactShadowBatch(2);blobs.setEnabled(true);
 blobs.set(0,new THREE.Matrix4().makeTranslation(10,5,20),2,4);blobs.finish(1);
 const m=new THREE.Matrix4();blobs.mesh.getMatrixAt(0,m);
 assert.equal(m.elements[12],10);assert.ok(Math.abs(m.elements[13]-5.04)<1e-5);assert.equal(m.elements[14],20);
 assert.equal(blobs.mesh.count,1);assert.equal(blobs.mesh.castShadow,false);
 blobs.setEnabled(false);assert.equal(blobs.mesh.visible,false);
});

test('blob is black with a radial alpha mask and opacity at most 0.35',()=>{
 const {mesh}=contactShadowBatch(1), m=mesh.material;
 assert.equal(m.color.getHex(),0);
 assert.ok(m.opacity>0 && m.opacity<=.35);
 assert.equal(m.transparent,true); assert.equal(m.depthWrite,false);
 assert.equal(m.toneMapped,false); assert.equal(m.fog,false);
 assert.equal(m.blending,THREE.NormalBlending);
 const {data,width,height}=m.map.image;
 const pixel=(x,y,c)=>data[(y*width+x)*4+c];
 const mid=Math.floor(width/2);
 assert.ok(pixel(mid,mid,3)>pixel(mid,Math.floor(height*.25),3));
 assert.ok(pixel(mid,Math.floor(height*.25),3)>pixel(mid,0,3));
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  for(let c=0;c<3;c++)assert.equal(pixel(x,y,c),0);
  assert.ok(pixel(x,y,3)/255*m.opacity<=.35);
  if(x===0||y===0||x===width-1||y===height-1)assert.equal(pixel(x,y,3),0);
 }
});
test('blob shader uses local position rather than a missing UV attribute',()=>{
 const {mesh}=contactShadowBatch(1), names=[];
 assert.ok(mesh.material.isNodeMaterial);
 for(const node of [mesh.material.colorNode,mesh.material.opacityNode]) {
  assert.ok(node);node.traverse(n=>{if(n.isAttributeNode)names.push(n.getAttributeName());});
 }
 assert.ok(!names.some(name=>/^uv\d*$/.test(name)));
});
