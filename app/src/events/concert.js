import * as THREE from 'three/webgpu';
import { concert_cues } from './cues.js';
import { concertBudget, concertState, concertCost, CATWALK, BSTAGE, STAGE } from './concert-state.js';
import { ledUniforms, updateLed, ledSurfaceMaterial, ledTileMaterial, ledBarMaterial } from './concert-led.js';
import { eventRoot, release } from './draw.js';
import { playback } from './playback.js';
import { installStandingCrowd } from '../people/index.js';
export { concertState, concertBudget, concertCost, concert_cues };

// EVT-01. Illustrative event concept. Models: app/public/concert/CREDITS.md. Crowd: visualization, not a safety simulation.
const MODEL_URL = name => `./concert/${name}/model.glb`;

// Scale an object to a target size (x, y, z in metres), turn it by yaw, and rest it on y = base with its centre at x, back at backZ.
function fit(object, { size, yaw = 0, base = 0, x = 0, backZ, centreZ }) {
  object.rotation.set(0, 0, 0); object.scale.set(1, 1, 1); object.position.set(0, 0, 0); object.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(object), have = box.getSize(new THREE.Vector3());
  object.scale.set(size[0] / have.x, size[1] / have.y, size[2] / have.z);
  object.rotation.y = yaw; object.updateMatrixWorld(true);
  const placed = new THREE.Box3().setFromObject(object), c = placed.getCenter(new THREE.Vector3());
  object.position.set(x - c.x, base - placed.min.y, backZ !== undefined ? backZ - placed.max.z : centreZ - c.z);
  return object;
}
// World-space geometry of every mesh in a loaded scene whose material passes the filter.
function collect(object, accept = () => true) {
  object.updateMatrixWorld(true); const list = [];
  object.traverse(o => { if (o.isMesh && accept(o.material)) list.push(o.geometry.clone().applyMatrix4(o.matrixWorld)); });
  return list;
}
function merged(geometries) {
  let total = 0; for (const g of geometries) total += g.attributes.position.count;
  const position = new Float32Array(total * 3), normal = new Float32Array(total * 3), index = []; let offset = 0;
  for (const g of geometries) {
    position.set(g.attributes.position.array, offset * 3); if (g.attributes.normal) normal.set(g.attributes.normal.array, offset * 3);
    const ids = g.index ? g.index.array : Array.from({ length: g.attributes.position.count }, (_, i) => i);
    for (const i of ids) index.push(i + offset); offset += g.attributes.position.count;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(position, 3)); out.setAttribute('normal', new THREE.BufferAttribute(normal, 3)); out.setIndex(index);
  return out;
}
// Centre a geometry group on a shared box and scale it to size, so the tile face and frame stay aligned.
function normalise(groups, size) {
  const box = new THREE.Box3(); for (const g of groups.flat()) { g.computeBoundingBox(); box.union(g.boundingBox); }
  const c = box.getCenter(new THREE.Vector3()), have = box.getSize(new THREE.Vector3());
  const m = new THREE.Matrix4().makeScale(size[0] / have.x, size[1] / have.y, size[2] / have.z).multiply(new THREE.Matrix4().makeTranslation(-c.x, -c.y, -c.z));
  for (const g of groups.flat()) g.applyMatrix4(m);
}

export function installConcert({ scene, bearing = 0, pad = 0, tier = 'high', width = globalThis.innerWidth ?? 1024, getCrowd, onState, loadModels = Boolean(globalThis.document) }) {
  const root = eventRoot(scene, bearing, pad, 'EVT-01');
  let budget = concertBudget(tier, width), currentTier = tier, dead = false, clock = 0, standing = [], performer = null;
  const initial = concertState(concert_cues, 0, budget);
  const led = ledUniforms();
  const dark = new THREE.MeshBasicMaterial({ color: '#1c1d24' }), steel = new THREE.MeshBasicMaterial({ color: '#7e8797' });
  const place = (mesh, [x, y, z]) => { mesh.position.set(x, y, z); root.add(mesh); return mesh; };

  // Procedural stand-ins. They stay if a model fails to load, and are hidden when the models arrive.
  const fallback = new THREE.Group(); fallback.name = 'concert-fallback'; root.add(fallback);
  const deck = new THREE.Mesh(new THREE.BoxGeometry(...initial.stage.size), dark);
  deck.position.set(initial.stage.position[0], initial.stage.position[1] + initial.stage.size[1] / 2, initial.stage.position[2]); fallback.add(deck);
  for (const x of [-30, 30]) for (const z of [41.5, 51]) { const post = new THREE.Mesh(new THREE.BoxGeometry(.5, 17.5, .5), steel); post.position.set(x, 8.8, z); fallback.add(post); }
  for (const z of [41.5, 51]) { const beam = new THREE.Mesh(new THREE.BoxGeometry(60.5, .6, .6), steel); beam.position.set(0, 17.3, z); fallback.add(beam); }
  const bstageBox = new THREE.Mesh(new THREE.BoxGeometry(BSTAGE.halfWidth * 2, CATWALK.top, BSTAGE.depth), dark); bstageBox.position.set(0, CATWALK.top / 2, BSTAGE.centreZ); fallback.add(bstageBox);
  // Catwalk and thrust: one box from the thrust tip to the B-stage.
  place(new THREE.Mesh(new THREE.BoxGeometry(...initial.catwalk.size), dark), initial.catwalk.position).name = 'concert-catwalk';

  // LED surfaces: backdrop and two curved wings.
  const backdropMesh = place(new THREE.Mesh(new THREE.PlaneGeometry(initial.backdrop.size[0], initial.backdrop.size[1], 48, 1), ledSurfaceMaterial(led, 0)), initial.backdrop.position);
  backdropMesh.rotation.y = Math.PI; backdropMesh.name = 'concert-led-backdrop';
  const wingMeshes = initial.wings.map((w, i) => {
    const geometry = new THREE.CylinderGeometry(w.radius, w.radius, w.size[1], 16, 1, true, -w.arc / 2, w.arc).translate(0, 0, -w.radius);
    const mesh = place(new THREE.Mesh(geometry, ledSurfaceMaterial(led, .37 + i * .29)), w.position); mesh.rotation.y = w.yaw; mesh.name = w.id; return mesh;
  });

  // Instanced parts: flown tiles, light bars, speaker line arrays, moving heads, beams. Rebuilt when the budget changes.
  const dummy = new THREE.Object3D(), tint = new THREE.Color(), direction = new THREE.Vector3(), forward = new THREE.Vector3(0, 0, 1);
  let tileFace, tileFrame, bars, speakers, heads, beams;
  const frameMaterial = new THREE.MeshBasicMaterial({ color: '#16171c' }), headMaterial = new THREE.MeshBasicMaterial();
  let tileGeometry = { face: new THREE.PlaneGeometry(2, 2), frame: new THREE.BoxGeometry(2.05, 2.05, .2).translate(0, 0, -.12) };
  let headGeometry = new THREE.SphereGeometry(.3, 6, 4);
  function instance(geometry, material, count, name) {
    const mesh = new THREE.InstancedMesh(geometry, material, count); mesh.name = name; mesh.frustumCulled = false; root.add(mesh); return mesh;
  }
  function drop(mesh) { if (!mesh) return; root.remove(mesh); mesh.dispose(); }
  function buildStatic() {
    for (const mesh of [tileFace, tileFrame, bars, speakers]) drop(mesh);
    const state = concertState(concert_cues, 0, budget);
    tileFace = instance(tileGeometry.face, ledTileMaterial(led), state.flown.length, 'concert-flown-tiles');
    tileFrame = instance(tileGeometry.frame, frameMaterial, state.flown.length, 'concert-flown-frames');
    state.flown.forEach((t, i) => {
      dummy.position.set(...t.position); dummy.rotation.set(0, Math.PI, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix();
      tileFace.setMatrixAt(i, dummy.matrix); tileFrame.setMatrixAt(i, dummy.matrix);
    });
    bars = instance(new THREE.BoxGeometry(1, 1, 1), ledBarMaterial(led), state.bars.length, 'concert-light-bars');
    state.bars.forEach((b, i) => { dummy.position.set(...b.position); dummy.rotation.set(0, 0, 0); dummy.scale.set(...b.size); dummy.updateMatrix(); bars.setMatrixAt(i, dummy.matrix); });
    speakers = instance(new THREE.BoxGeometry(1, 1, 1), dark, state.speakers.length, 'concert-line-arrays');
    state.speakers.forEach((s, i) => { dummy.position.set(...s.position); dummy.rotation.set(s.tilt, s.heading, 0); dummy.scale.set(...s.size); dummy.updateMatrix(); speakers.setMatrixAt(i, dummy.matrix); });
  }
  function buildMoving() {
    drop(heads); drop(beams);
    heads = instance(headGeometry, headMaterial, budget.heads, 'concert-moving-heads');
    beams = instance(new THREE.ConeGeometry(1, 1, 6, 1, true).translate(0, -.5, 0),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: .12, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending }), budget.heads, 'concert-beams');
  }

  // Floor crowd (standing, visualization) and the performer, from the people module.
  const knownLabels = () => new Set(globalThis.document?.querySelectorAll?.('[data-people-visualization]') ?? []);
  function buildFloor() {
    for (const crowd of standing) crowd.dispose(); standing = [];
    const before = knownLabels();
    for (const zone of concertState(concert_cues, 0, budget).floor.zones) {
      if (!zone.count) continue;
      standing.push(installStandingCrowd({ parent: root, area: { polygon: zone.polygon, y: .12, facing_deg: 0 }, count: zone.count,
        quality: { tier: currentTier, width, farDistance: 0 } }));
    }
    performer?.dispose();
    const p = initial.performer;
    performer = installStandingCrowd({ parent: root, area: { x: p.position[0] - .3, z: p.position[2] - .3, width: .6, depth: .6, y: p.position[1], facing_deg: p.facing_deg },
      count: 1, quality: { tier: currentTier, width, farDistance: 100 } });
    performer.group.name = 'concert-performer';
    // The host already shows one Visualization label. Remove the extra ones.
    for (const label of knownLabels()) if (!before.has(label)) label.remove();
  }

  buildStatic(); buildMoving(); buildFloor();

  // Reactions from the cues go to the stands (host crowd), the floor crowd and the performer.
  const everyone = { react(name, params) {
    getCrowd?.()?.react(name, params);
    if (!dead) for (const crowd of [...standing, performer]) crowd?.react(name, params);
  } };
  function tick(dt) {
    if (dead) return;
    const night = getCrowd?.()?.group?.userData?.animation?.night?.value ?? 1;
    for (const crowd of [...standing, performer]) { crowd?.setNight(night > 0); crowd?.update(dt, clock); }
  }

  const player = playback({ cues: concert_cues, sample: t => concertState(concert_cues, t, budget), getCrowd: () => everyone, onState,
    draw(state) {
      updateLed(led, state);
      state.lights.forEach((l, i) => {
        dummy.position.set(...l.position); dummy.scale.setScalar(1); direction.set(...l.target).sub(dummy.position);
        const length = direction.length(); direction.normalize();
        dummy.quaternion.setFromUnitVectors(forward, direction); dummy.updateMatrix(); heads.setMatrixAt(i, dummy.matrix);
        tint.setRGB(.2 + l.color[0] * l.intensity * .8, .2 + l.color[1] * l.intensity * .8, .22 + l.color[2] * l.intensity * .8); heads.setColorAt(i, tint);
        tint.setRGB(...l.color).multiplyScalar(l.intensity * 3); beams.setColorAt(i, tint);
        dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), direction); dummy.scale.set(length * .07, length, length * .07);
        dummy.updateMatrix(); beams.setMatrixAt(i, dummy.matrix);
      });
      heads.instanceMatrix.needsUpdate = beams.instanceMatrix.needsUpdate = true;
      heads.instanceColor.needsUpdate = beams.instanceColor.needsUpdate = true;
    },
    dispose() { dead = true; for (const crowd of [...standing, performer]) crowd?.dispose(); standing = []; performer = null; release(root); },
  });

  // Optimised models load after the first frame. A failure keeps the procedural stand-ins.
  async function loadAll() {
    const [{ GLTFLoader }, { MeshoptDecoder }] = await Promise.all([import('three/addons/loaders/GLTFLoader.js'), import('three/addons/libs/meshopt_decoder.module.js')]);
    const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    const get = name => loader.loadAsync(MODEL_URL(name)).then(g => g.scene);
    const [stage, truss, bstage, tile, light] = await Promise.all(['ipoly3d-concert-stage', 'truss-structure', 'simple-concert-stage', 'led-25-x-4', 'stage-lights'].map(get));
    if (dead) return;
    // Main stage: the model faces +z. Turn it to face north, 60 m wide, back plane at the stage back.
    root.add(fit(stage, { size: [STAGE.width, 17.55, 35.07 * .45], yaw: Math.PI, backZ: STAGE.backZ })).name = 'concert-stage';
    root.add(fit(truss, { size: [initial.truss.width, initial.truss.height, initial.truss.depth], base: initial.truss.position[1], centreZ: initial.truss.position[2] })).name = 'concert-truss';
    root.add(fit(bstage, { size: [BSTAGE.halfWidth * 2, BSTAGE.height, BSTAGE.depth], yaw: Math.PI, centreZ: BSTAGE.centreZ })).name = 'concert-bstage';
    // The truss file has a white factor. Dim it so it reads as painted steel at night.
    truss.traverse(o => { if (o.isMesh) { o.material = o.material.clone(); o.material.color.multiplyScalar(.45); } });
    fallback.visible = false;
    // Tile: face is the FrontColor material, the rest is frame. Light: one fixture, lens along +z.
    const faces = collect(tile, m => m.name === 'FrontColor'), frames = collect(tile, m => m.name !== 'FrontColor');
    normalise([faces, frames], [2, 2, .2]);
    tileGeometry = { face: merged(faces), frame: merged(frames) }; buildStatic();
    const fixture = merged(collect(light)); normalise([[fixture]], [.9, 1.1, .9]);
    headGeometry = fixture; buildMoving(); player.redraw();
  }
  if (loadModels) loadAll().catch(error => console.warn('Concert models unavailable, using stand-ins:', error));

  return { ...player, cost: () => concertCost(budget),
    update(dt) { if (dead) return; clock += dt; const state = player.update(dt); tick(dt); return state; },
    seek(t) { clock = t; return player.seek(t); },
    setTier(next, nextWidth = globalThis.innerWidth ?? width) {
      const nextBudget = concertBudget(next, nextWidth);
      if (nextBudget.crowd === budget.crowd && nextBudget.heads === budget.heads && nextBudget.tiles === budget.tiles) return;
      budget = nextBudget; currentTier = next; width = nextWidth; buildStatic(); buildMoving(); buildFloor(); player.redraw();
    } };
}
