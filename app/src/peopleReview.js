import * as THREE from 'three/webgpu';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// Internal opt-in study. These are specific seats in the currently exported stadium GLB.
const SEAT_INDICES = [635, 638];
const FILES = ['Female_Adult_01.glb', 'Male_Adult_01.glb'];
const BASE = './__talanta_people_review/';

function seatSurface(seats, index) {
  if (index >= seats.count) throw new Error('Review seat is missing from this stadium export');
  const instance = new THREE.Matrix4(); seats.getMatrixAt(index, instance);
  const world = new THREE.Matrix4().multiplyMatrices(seats.matrixWorld, instance);
  const origin = new THREE.Vector3().setFromMatrixPosition(world);
  const one = new THREE.Mesh(seats.geometry, seats.material);
  one.matrixAutoUpdate = false; one.matrixWorld.copy(world);
  const ray = new THREE.Raycaster(origin.clone().add(new THREE.Vector3(0, 3, 0)), new THREE.Vector3(0, -1, 0));
  const hit = ray.intersectObject(one, false)[0];
  if (!hit) throw new Error('Could not measure the review seat pan');
  return { index, origin, panY: hit.point.y };
}
function treadHeight(hero, anchor) {
  const meshes = [];
  hero.traverse(o => { if (o.isMesh && !o.isInstancedMesh && /^tier_lower/.test(o.name)) meshes.push(o); });
  const x = anchor.origin.x - .5;
  const ray = new THREE.Raycaster(new THREE.Vector3(x, anchor.origin.y + 1, anchor.origin.z), new THREE.Vector3(0, -1, 0));
  const hit = ray.intersectObjects(meshes, false).find(h => h.point.y < anchor.panY);
  if (!hit) throw new Error('Could not measure the review tread');
  return hit.point.y;
}

export async function installPeopleReview({ scene, hero }) {
  hero.updateMatrixWorld(true);
  let seats;
  hero.traverse(o => { if (o.isInstancedMesh && o.name === 'seats__seat_proto_v2__LOD0') seats = o; });
  if (!seats) throw new Error('Seat instances are unavailable in this stadium');
  const anchors = SEAT_INDICES.map(i => { const a = seatSurface(seats, i); a.treadY = treadHeight(hero, a); return a; });
  const loader = new GLTFLoader();
  const models = await Promise.all(FILES.map(file => loader.loadAsync(BASE + file)));
  const root = new THREE.Group(); root.name = 'local-people-review'; scene.add(root);
  // A neutral review key keeps the unbaked figures legible inside the baked bowl.
  const key = new THREE.DirectionalLight(0xffffff, 3); key.position.set(35, 15, 4); key.target.position.set(41.5, 9, 0); root.add(key, key.target, new THREE.HemisphereLight(0xffffff, 0x888888, 2));
  const figures = models.map((model, i) => {
    const carrier = new THREE.Group(); root.add(carrier); carrier.add(model.scene);
    const mixer = new THREE.AnimationMixer(model.scene);
    const pelvis = model.scene.getObjectByName('Bip01_Pelvis');
    if (!pelvis) throw new Error('Prototype pelvis joint not found');
    return { carrier, model, mixer, pelvis, anchor: anchors[i] };
  });
  let pose = 'sit';
  function setPose(next) {
    if (!['sit', 'stand'].includes(next)) throw new Error(`Unknown pose: ${next}`);
    pose = next;
    for (const f of figures) {
      f.mixer.stopAllAction();
      const clip = f.model.animations.find(a => a.name === (next === 'sit' ? 'Sitting_Idle_Loop' : 'Idle_Loop'));
      if (!clip) throw new Error(`Missing ${next} clip`);
      f.mixer.clipAction(clip).play(); f.mixer.setTime(.5);
      f.carrier.position.set(0, 0, 0); f.carrier.rotation.y = -Math.PI / 2;
      f.carrier.updateMatrixWorld(true);
      const pelvis = f.pelvis.getWorldPosition(new THREE.Vector3());
      f.carrier.position.x += f.anchor.origin.x - pelvis.x - (next === 'stand' ? .5 : 0);
      f.carrier.position.z += f.anchor.origin.z - pelvis.z;
      if (next === 'sit') f.carrier.position.y += f.anchor.panY + .12 - pelvis.y;
      else {
        f.carrier.updateMatrixWorld(true);
        const bottom = new THREE.Box3().setFromObject(f.carrier, true).min.y;
        f.carrier.position.y += f.anchor.treadY - bottom;
      }
      f.carrier.updateMatrixWorld(true);
    }
  }
  function measurements() {
    return figures.map(f => {
      f.carrier.updateMatrixWorld(true);
      const bottom = new THREE.Box3().setFromObject(f.carrier, true).min.y;
      return { seat: f.anchor.index, panY: f.anchor.panY, treadY: f.anchor.treadY,
        lowestVertexY: bottom, lowestVertexOffsetM: bottom - f.anchor.treadY,
        pelvisAbovePanM: f.pelvis.getWorldPosition(new THREE.Vector3()).y - f.anchor.panY };
    });
  }
  setPose(pose);
  return { setPose, measurements, sampleAt(time) { for (const f of figures) f.mixer.setTime(time); }, get pose() { return pose; }, update(dt) { for (const f of figures) f.mixer.update(dt); },
    dispose() {
      root.removeFromParent();
      for (const f of figures) { f.mixer.stopAllAction(); f.model.scene.traverse(o => {
        o.geometry?.dispose(); for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m) {
          for (const value of Object.values(m)) if (value?.isTexture) value.dispose(); m.dispose();
        }
      }); }
    } };
}
