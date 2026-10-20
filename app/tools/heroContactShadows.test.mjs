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
