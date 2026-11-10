import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { installSeatedCrowd, installStandingCrowd } from '../src/people/index.js';

// Software generation only. The canvas does not provide a graphics context.
test('seated and standing animation nodes generate GLSL and WGSL vertex texture reads', async () => {
  for (const standing of [false, true]) for (const quality of ['high', 'low']) {
    const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera();
    const crowd = standing ? installStandingCrowd({ parent: scene, area: { x: 0, z: 0, width: 3, depth: 3 }, count: 4, quality }) :
      installSeatedCrowd({ scene, camera, quality, seats: [{ x: 0, y: 0, z: 0, facing_deg: 0 }] });
    await crowd.ready;
    for (const forceWebGL of [true, false]) {
      const renderer = new THREE.WebGPURenderer({ forceWebGL, canvas: { width: 1, height: 1, style: {}, addEventListener() {}, removeEventListener() {} } });
      renderer.backend.extensions = { has: () => false };
      renderer.backend.capabilities = { getUniformBufferLimit: () => 65536 };
      renderer.hasFeature = () => false;
      const builder = renderer.backend.createNodeBuilder(crowd.group.children[0], renderer);
      builder.camera = camera; builder.scene = scene;
      builder.build();
      assert.match(builder.vertexShader, forceWebGL ? /textureLod\(/ : /textureSampleLevel\(|textureLoad\(/);
      assert.match(builder.vertexShader, /fanOrigin/);
      assert.match(builder.fragmentShader, /fanSkin|nodeVarying/);
      assert.doesNotMatch(builder.vertexShader, /boneMatrices|boneTexture/);
      console.log(`Software shader generation: ${standing ? 'standing' : 'seated'} ${quality} ${forceWebGL ? 'GLSL' : 'WGSL'} ${builder.vertexShader.length} vertex source bytes`);
    }
    crowd.dispose();
  }
});
