import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { twoBoneSupport } from '../src/footSupport.js';
test('two-bone support reaches a lowered ankle while retaining both segment lengths', () => {
  const hip=new THREE.Vector3(0,1.1,0), knee=new THREE.Vector3(0,.65,.5), ankle=new THREE.Vector3(0,.25,.35);
  const result=twoBoneSupport(hip,knee,ankle,-.06);
  assert.ok(Math.abs(result.ankle.y-(ankle.y-.06))<1e-8);
  assert.ok(Math.abs(result.knee.distanceTo(hip)-knee.distanceTo(hip))<1e-8);
  assert.ok(Math.abs(result.knee.distanceTo(result.ankle)-ankle.distanceTo(knee))<1e-8);
});



test('when straight-leg reach is short, move the ankle horizontally before sacrificing foot height', () => {
  const hip=new THREE.Vector3(0,1,0), knee=new THREE.Vector3(0,.5,.1), ankle=new THREE.Vector3(0,.1,.2);
  const r=twoBoneSupport(hip,knee,ankle,-.01);
  assert.ok(Math.abs(r.ankle.y-.09)<1e-8);
  assert.ok(r.ankle.z<ankle.z);
  assert.ok(Math.abs(r.knee.distanceTo(hip)-knee.distanceTo(hip))<1e-8);
  assert.ok(Math.abs(r.knee.distanceTo(r.ankle)-ankle.distanceTo(knee))<1e-8);
});

test('unreachable vertical targets clamp without stretching or non-finite values', () => {
  const hip=new THREE.Vector3(0,1,0), knee=new THREE.Vector3(0,.5,.1), ankle=new THREE.Vector3(0,.1,.2);
  const r=twoBoneSupport(hip,knee,ankle,-2);
  assert.equal(r.clamped,true);
  assert.ok([...r.knee.toArray(),...r.ankle.toArray()].every(Number.isFinite));
  assert.ok(Math.abs(r.knee.distanceTo(hip)-knee.distanceTo(hip))<1e-8);
  assert.ok(Math.abs(r.knee.distanceTo(r.ankle)-ankle.distanceTo(knee))<1e-8);
});
