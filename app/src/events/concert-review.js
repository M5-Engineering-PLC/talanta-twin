import * as THREE from 'three/webgpu';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { release } from './draw.js';

export async function loadConcertPerformer(root, performer) {
  const { scene, animations } = await new GLTFLoader().loadAsync('./__talanta_concert_review/performer.glb');
  const textures = new Set(), skeletons = new Set();
  scene.traverse(object => {
    if (object.isSkinnedMesh) skeletons.add(object.skeleton);
    const material = object.material;
    if (!material?.map) return;
    for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
    material.emissive.set(0xffffff);
    material.emissiveMap = material.map;
    material.emissiveIntensity = .28;
  });
  const clip = THREE.AnimationClip.findByName(animations, 'Dance_Loop');
  const mixer = new THREE.AnimationMixer(scene);
  const actor = new THREE.Group();
  function dispose() {
    mixer.stopAllAction();
    mixer.uncacheRoot(scene);
    actor.removeFromParent();
    release(scene);
    for (const skeleton of skeletons) skeleton.dispose();
    for (const texture of textures) texture.dispose();
  }
  if (!clip) { dispose(); throw new Error('Performer asset has no dance clip'); }
  scene.position.x = -scene.children[0].position.x;
  actor.name = 'concert-review-performer';
  actor.position.set(...performer.position);
  actor.rotation.y = THREE.MathUtils.degToRad(performer.facing_deg);
  actor.add(scene);
  root.add(actor);
  mixer.clipAction(clip).play();
  const beatsPerLoop = Math.max(1, Math.round(clip.duration * 2));
  return { draw(beat) { mixer.setTime(beat * clip.duration / beatsPerLoop); }, dispose };
}
