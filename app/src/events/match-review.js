import * as THREE from 'three/webgpu';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { release } from './draw.js';

const base = './__talanta_match_review/';

function releaseAssets(assets) {
  const textures = new Set();
  for (const { scene } of assets) {
    scene.traverse(object => {
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of materials) {
        for (const value of Object.values(material ?? {})) if (value?.isTexture) textures.add(value);
      }
    });
    release(scene);
  }
  for (const texture of textures) texture.dispose();
}

export async function loadMatchReview(root) {
  const loader = new GLTFLoader();
  const files = ['kenya-white.glb', 'spain-red.glb', 'referee-black.glb'];
  const results = await Promise.allSettled(files.map(file => loader.loadAsync(base + file)));
  const assets = results.filter(result => result.status === 'fulfilled').map(result => result.value);
  const group = new THREE.Group();
  group.name = 'match-review-players';
  const players = [];
  function dispose() {
    group.removeFromParent();
    for (const { mixer, model } of players) {
      mixer.stopAllAction();
      mixer.uncacheRoot(model);
      model.traverse(object => { if (object.isSkinnedMesh) object.skeleton.dispose(); });
    }
    releaseAssets(assets);
  }
  try {
    const failed = results.find(result => result.status === 'rejected');
    if (failed) throw failed.reason;
    const teams = assets.map(({ scene, animations }) => {
      const idle = THREE.AnimationClip.findByName(animations, 'Idle_Loop');
      const sprint = THREE.AnimationClip.findByName(animations, 'Sprint_Loop');
      if (!idle || !sprint) throw new Error('Match kit is missing its movement clips');
      // The baked venue uses a low ambient level. Give the kit maps a small
      // fill term so their colors remain readable beneath the roof.
      scene.traverse(object => {
        if (!object.isMesh || !object.material?.map || !object.material.emissive) return;
        object.material.emissive.set(0xffffff);
        object.material.emissiveMap = object.material.map;
        object.material.emissiveIntensity = .22;
      });
      return { scene, idle, sprint };
    });
    for (let i = 0; i < 23; i++) {
      const { scene, idle, sprint } = teams[i === 22 ? 2 : Number(i >= 11)];
      const model = clone(scene);
      model.position.x = -scene.children[0].position.x;
      const player = new THREE.Group();
      player.name = i === 22 ? 'Referee' : i < 11 ? 'Harambee Stars' : 'Spain';
      player.add(model);
      group.add(player);
      const mixer = new THREE.AnimationMixer(model);
      players.push({ player, model, mixer, idle, sprint });
    }
    root.add(group);
  } catch (error) {
    dispose();
    throw error;
  }

  return {
    draw(state) {
      for (const actor of [...state.players, state.referee]) {
        const entry = players[actor.id];
        const { player, mixer, idle, sprint } = entry;
        player.position.set(...actor.position);
        player.rotation.y = actor.heading;
        const moving = actor.speed > .15;
        const clip = moving ? sprint : idle;
        if (entry.clip !== clip) {
          mixer.stopAllAction();
          mixer.clipAction(clip).play();
          entry.clip = clip;
        }
        mixer.setTime(state.time * (moving ? .75 : 1) + actor.id * .083);
      }
    },
    dispose,
  };
}
