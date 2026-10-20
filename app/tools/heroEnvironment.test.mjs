import test from 'node:test';
import assert from 'node:assert/strict';
import { choosePanorama } from '../src/hero/environment.js';
const manifest = {environment:{file:'app/public/env/day_2048.hdr',file_2048:'app/public/env/day_2048.hdr',file_exr:'app/public/env/day.exr',resolution:[8192,4096]},files:[{file:'app/public/env/day.exr'},{file:'app/public/env/day_2048.hdr'},{file:'app/public/env/evening.exr'}]};
const desktop = {desktopGPU:true,maxTextureSize:16384,memoryGB:8,phone:false};
test('capable desktop selects EXR then HDR fallback',()=>assert.deepEqual(choosePanorama(manifest,desktop),['env/day.exr','env/day_2048.hdr']));
test('phones, small GPUs and low memory select HDR',()=>{
  for(const hints of [{phone:true},{maxTextureSize:4096},{desktopGPU:false},{memoryGB:4},{preferSmall:true}]) assert.deepEqual(choosePanorama(manifest,{...desktop,...hints}),['env/day_2048.hdr']);
});
test('EXR entries work without file_exr and do not select another preset',()=>{
 const m=structuredClone(manifest); delete m.environment.file_exr;
 assert.deepEqual(choosePanorama(m,desktop),['env/day.exr','env/day_2048.hdr']);
});
