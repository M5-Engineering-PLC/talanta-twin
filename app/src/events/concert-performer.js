import * as THREE from 'three/webgpu';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { release } from './draw.js';

export async function loadConcertPerformer(performer) {
  return loadConcertActors('./concert/performer/model.glb', [performer], 'concert-lead-performer');
}

export async function loadConcertForeground(placements) {
  const sources = [
    ['./concert/crowd/male.glb', 'concert-crowd-male'],
    ['./concert/performer/model.glb', 'concert-crowd-female'],
  ];
  const results = await Promise.allSettled(sources.map(([url, name], modelIndex) =>
    loadConcertActors(url, placements.filter((_, index) => index % sources.length === modelIndex), name, true)));
  const models = results.filter(result => result.status === 'fulfilled').map(result => result.value);
  const failed = results.find(result => result.status === 'rejected');
  if (failed) {
    for (const model of models) model.dispose();
    throw failed.reason;
  }

  const actor = new THREE.Group();
  actor.name = 'concert-foreground-crowd';
  actor.add(...models.map(model => model.actor));
  return {
    actor,
    draw(state) { for (const model of models) model.draw(state); },
    dispose() {
      actor.removeFromParent();
      for (const model of models) model.dispose();
    },
  };
}

async function loadConcertActors(url, placements, name, withWristbands = false) {
  const { scene, animations } = await new GLTFLoader().loadAsync(url);
  const textures = new Set(), skeletons = new Set(), litMaterials = new Set();
  scene.traverse(object => {
    if (object.isSkinnedMesh) skeletons.add(object.skeleton);
    if (!object.isMesh) return;
    for (const material of [].concat(object.material)) {
      for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
      if (!material.map) continue;
      material.emissive.set(0xffffff);
      material.emissiveMap = material.map;
      material.emissiveIntensity = .28;
      litMaterials.add(material);
    }
  });
  const clip = THREE.AnimationClip.findByName(animations, 'Dance_Loop');
  const actor = new THREE.Group();
  actor.name = name;
  const dancers = [];
  function dispose() {
    for (const { model, mixer } of dancers) {
      mixer.stopAllAction();
      mixer.uncacheRoot(model);
      model.traverse(object => { if (object.isSkinnedMesh) skeletons.add(object.skeleton); });
    }
    release(actor);
    for (const skeleton of skeletons) skeleton.dispose();
    for (const texture of textures) texture.dispose();
  }
  actor.add(scene);
  if (!clip) { dispose(); throw new Error('Performer asset has no dance clip'); }
  scene.position.x = -scene.children[0].position.x;
  for (const [index, { position, facing_deg, phase = 0, scale = 1 }] of placements.entries()) {
    const model = index ? clone(scene) : scene;
    const anchor = new THREE.Group();
    anchor.position.set(...position);
    anchor.rotation.y = THREE.MathUtils.degToRad(facing_deg);
    anchor.scale.setScalar(scale);
    anchor.add(model);
    actor.add(anchor);
    const mixer = new THREE.AnimationMixer(model);
    mixer.clipAction(clip).play();
    dancers.push({ model, mixer, phase });
  }
  let wristbands;
  const wristAnchors = [];
  const inverseActor = new THREE.Matrix4(), bandMatrix = new THREE.Matrix4();
  if (withWristbands && dancers.length) {
    const geometry = new THREE.CylinderGeometry(.044, .044, .034, 10, 1, true);
    wristbands = new THREE.InstancedMesh(geometry, new THREE.MeshBasicMaterial(), dancers.length);
    wristbands.name = 'concert-audience-wristbands';
    wristbands.frustumCulled = false;
    actor.add(wristbands);
    const origin = new THREE.Vector3(), scale = new THREE.Vector3();
    const up = new THREE.Vector3(0, 1, 0);
    actor.updateMatrixWorld(true);
    for (const { model } of dancers) {
      const hand = model.getObjectByName('Bip01_L_Hand');
      const forearm = model.getObjectByName('Bip01_L_Forearm');
      const towardElbow = hand.worldToLocal(forearm.getWorldPosition(origin)).normalize();
      const units = hand.getWorldScale(scale).x;
      const band = new THREE.Object3D();
      band.name = 'concert-audience-wristband';
      band.position.copy(towardElbow).multiplyScalar(.025 / units);
      band.scale.setScalar(1 / units);
      band.quaternion.setFromUnitVectors(up, towardElbow);
      hand.add(band);
      wristAnchors.push(band);
    }
  }
  const beatsPerLoop = Math.max(1, Math.round(clip.duration * 2));
  return {
    actor,
    draw({ beat, pulse, led }) {
      for (const { mixer, phase } of dancers) mixer.setTime((beat + phase) * clip.duration / beatsPerLoop);
      if (wristbands) {
        actor.updateWorldMatrix(true, true);
        inverseActor.copy(actor.matrixWorld).invert();
        wristAnchors.forEach((band, index) => {
          bandMatrix.multiplyMatrices(inverseActor, band.matrixWorld);
          wristbands.setMatrixAt(index, bandMatrix);
        });
        wristbands.instanceMatrix.needsUpdate = true;
        wristbands.material.color.setRGB(...led.color).multiplyScalar(.22 + led.energy * (1.5 + 2.2 * pulse));
      }
      for (const material of litMaterials) material.emissiveIntensity = .28 + pulse * .22;
    },
    dispose,
  };
}
