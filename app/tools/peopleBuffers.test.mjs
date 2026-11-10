// Software shader/layout generation with the actual three.js backend helpers.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import * as THREE from 'three/webgpu';
import RenderObject from 'three/src/renderers/common/RenderObject.js';
import WebGPUAttributeUtils from 'three/src/renderers/webgpu/utils/WebGPUAttributeUtils.js';
import { decodeCrowdAssets } from '../src/people/geometry.js';
import { installSeatedCrowd } from '../src/people/index.js';

for (const profile of ['desktop', 'phone']) test(`${profile} crowd fits eight vertex buffers and sixteen attributes at every tier`, async () => {
  const suffix = profile === 'phone' ? '_phone' : '';
  const manifest = JSON.parse(await readFile(new URL(`../public/people/crowd${suffix}.json`, import.meta.url)));
  const bytes = await readFile(new URL(`../public/people/animation${suffix}.bin`, import.meta.url));
  decodeCrowdAssets(manifest, bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
  const seats = Array.from({ length: 1600 }, (_, i) => ({ x: i % 40, y: 0, z: Math.floor(i / 40), facing_deg: i % 360 }));
  for (const tier of ['ultra', 'high', 'medium', 'low']) {
    const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera();
    const crowd = installSeatedCrowd({ scene, camera, seats, quality: { tier, width: profile === 'phone' ? 600 : 1440 } });
    await crowd.ready;
    for (const mesh of crowd.group.children) for (const forceWebGL of [false, true]) {
      const renderer = new THREE.WebGPURenderer({ forceWebGL, canvas: { width: 1, height: 1, style: {}, addEventListener() {}, removeEventListener() {} } });
      renderer.backend.extensions = { has: () => false };
      renderer.backend.capabilities = { getUniformBufferLimit: () => 65536 };
      renderer.hasFeature = () => false;
      const builder = renderer.backend.createNodeBuilder(mesh, renderer);
      builder.scene = scene; builder.camera = camera; builder.build();
      const renderObject = { attributes: null, geometry: mesh.geometry, getNodeBuilderState: () => ({ nodeAttributes: builder.getAttributesArray() }) };
      renderObject.getAttributes = () => RenderObject.prototype.getAttributes.call(renderObject);
      const attributes = renderObject.getAttributes();
      assert.ok(attributes.length <= 16, `${attributes.length} shader attributes`);
      if (!forceWebGL) {
        const layouts = new WebGPUAttributeUtils(renderer.backend).createShaderVertexBuffers(renderObject);
        assert.ok(layouts.length <= 8, `${layouts.length} vertex buffers`);
        console.log(`Software ${profile} ${tier} LOD${mesh.userData.lod}: ${layouts.length} vertex buffers, ${attributes.length} attributes, ${mesh.count} fans`);
      }
    }
    // Packed lanes retain the original CPU values exactly, including scale and color.
    for (const mesh of crowd.group.children) {
      const g = mesh.geometry;
      for (let i = 0; i < mesh.count; i++) {
        assert.equal(g.attributes.fanOriginYaw.getX(i), g.attributes.fanOrigin.getX(i));
        assert.equal(g.attributes.fanOriginYaw.getW(i), g.attributes.fanYaw.getX(i));
        assert.equal(g.attributes.fanMotion.getY(i), g.attributes.fanAngle.getX(i));
        assert.equal(g.attributes.fanShirtScale.getW(i), g.attributes.fanScale.getX(i));
        assert.equal(g.attributes.fanSkinScale.getW(i), g.attributes.fanScale.getY(i));
      }
    }
    crowd.dispose();
  }
});
