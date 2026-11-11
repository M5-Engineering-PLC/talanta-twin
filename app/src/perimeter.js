import * as THREE from 'three/webgpu';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { loadHero } from './hero/loadHero.js';
import { createModeController } from './perimeterModes.js';

const status = document.querySelector('#status');
const params = new URLSearchParams(location.search);
const full = params.has('full');
const peopleReview = import.meta.env.DEV && params.has('people-review');
const matchReview = import.meta.env.DEV && params.has('match-review');
const pitchSide = matchReview && params.has('pitch-side');
const concertReview = import.meta.env.DEV && params.has('concert-review');
if (full) document.querySelector('strong').textContent = 'Talanta Twin · Full site comparison';

try {
  const renderer = new THREE.WebGPURenderer({ antialias: true, forceWebGL: true });
  await renderer.init();
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  const camera = new THREE.PerspectiveCamera(42, 1, 1, 4000);
  const resize = () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  };
  resize();
  addEventListener('resize', resize);
  document.body.append(renderer.domElement);

  const loaded = await loadHero({ renderer, phone: true, base: full ? './models/' : './perimeter/' });
  if (!loaded) throw new Error('Run export_perimeter.mjs and check the model files.');
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#d4dce1');
  scene.add(loaded.group, new THREE.HemisphereLight('#fff8ed', '#6e6355', .65));

  camera.position.set(410, 280, 440);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 15, 0);
  controls.maxPolarAngle = Math.PI / 2;
  controls.minDistance = 35;
  controls.maxDistance = 1300;
  controls.update();
  renderer.render(scene, camera);
  controls.addEventListener('change', () => renderer.render(scene, camera));
  const claim = document.querySelector('#event-claim');
  const matchScore = document.createElement('p'); matchScore.hidden = true; matchScore.setAttribute('aria-live', 'polite');
  claim.after(matchScore);
  const buttons = [...document.querySelectorAll('[data-mode]')];
  const peopleControls = document.querySelector('#people-controls');
  if (peopleReview) document.querySelector('[data-mode=people]').hidden = false;
  let selected = 'venue', selection = 0;
  const modes = createModeController({ async load(mode) {
    if (mode === 'people') {
      const { installPeopleReview } = await import('./peopleReview.js');
      return installPeopleReview({ scene, hero: loaded.group });
    }
    if (mode === 'drone') {
      const { installShows } = await import('./shows/index.js');
      const show = installShows({ scene, camera, renderer, heroGroup: loaded.group });
      show.setEnabled('SHW-03', true);
      let elapsed = 9; // Begin with the formation airborne and visible.
      show.update(0, elapsed);
      return { update(dt) { elapsed += dt; show.update(dt, elapsed); }, dispose() { show.dispose(); } };
    }
    const [module, data] = await Promise.all([
      mode === 'football' ? import('./events/match.js') : import('./events/concert.js'),
      fetch('./data/manifest.json').then(r => { if (!r.ok) throw new Error(`Venue data: ${r.status}`); return r.json(); }),
    ]);
    const install = mode === 'football' ? module.installMatch : module.installConcert;
    let crowd, reactionHost;
    if (mode === 'football') {
      const [{ installSeatedCrowd }, { matchCrowdSeats, matchReactionHost }] = await Promise.all([import('./people/index.js'), import('./events/match-crowd.js')]);
      crowd = installSeatedCrowd({ scene, camera, renderer, heroGroup: loaded.group,
        quality: { tier: 'low', width: innerWidth, seats: matchCrowdSeats(loaded.group) } });
      try { await crowd.ready; crowd.setPalette('#f2f4ed', '#19824f'); reactionHost = matchReactionHost(crowd, module.match_cues[0].params.goalTime); }
      catch (error) { crowd.dispose(); throw error; }
    }
    try {
      const event = install({ scene, camera, bearing: data.features.pitch_bearing_deg, pad: data.features.site_pad_y,
        tier: innerWidth < 700 ? 'low' : 'medium', width: innerWidth,
        ...(crowd ? { getCrowd: () => reactionHost, onState: frame => {
          if (selected !== 'football') return;
          const teams = matchReview ? ['Harambee Stars', 'Spain'] : ['Home', 'Away'];
          const text = `Illustrative · ${teams[0]} ${frame.score[0]} – ${frame.score[1]} ${teams[1]} · ${frame.phase}`;
          if (matchScore.textContent !== text) matchScore.textContent = text;
          if (pitchSide) {
            const pitch = scene.getObjectByName('SPT-01');
            if (pitch) {
              const [x, , z] = frame.ball.position;
              camera.position.copy(pitch.localToWorld(new THREE.Vector3(x + 14, 8, z + 12)));
              controls.target.copy(pitch.localToWorld(new THREE.Vector3(x, 1, z)));
              controls.update();
            }
          }
        } } : {}),
        ...(mode === 'football' && matchReview ? { prototypePlayers: true } : {}),
        ...(mode === 'concert' && concertReview ? { prototypePerformer: true } : {}) });
      if (!crowd) return event;
      const { attachMatchCrowd } = await import('./events/match-crowd.js');
      const match = attachMatchCrowd(event, crowd);
      if (matchReview) match.seek(30); // Start with the choreographed attack in possession.
      return match;
    } catch (error) { crowd?.dispose(); throw error; }
  } });
  const claims = { venue: '', football: 'Illustrative football and crowd visualization; not validated safety, capacity or crowd-flow evidence.',
    concert: 'Illustrative event concept and crowd visualization; installed equipment and operational feasibility are not confirmed.',
    drone: 'Illustrative show concept; installed equipment and operational feasibility are not confirmed.',
    people: 'Local prototype review: two modeled figures; seating and fit are not validated.' };
  for (const button of buttons) button.addEventListener('click', async () => {
    const mode = button.dataset.mode, version = ++selection; selected = mode;
    for (const b of buttons) b.setAttribute('aria-pressed', String(b === button));
    claim.textContent = claims[mode];
    matchScore.hidden = mode !== 'football';
    if (mode === 'football') matchScore.textContent = 'Loading illustrative match…';
    if (mode === 'football' && matchReview) {
      const notice = document.createElement('a');
      notice.href = './__talanta_match_review/LICENSE.md';
      notice.textContent = 'Rocketbox license';
      claim.append(' Harambee Stars vs. Spain kit study. ', notice);
    }
    if (mode === 'concert' && concertReview) {
      const notice = document.createElement('a');
      notice.href = './__talanta_concert_review/LICENSE.md';
      notice.textContent = 'Rocketbox license';
      claim.append(' ', notice);
    }
    peopleControls.hidden = mode !== 'people';
    if (mode !== 'people') delete window.__peopleReview;
    if (mode !== 'football') delete window.__matchReview;
    controls.minDistance = mode === 'people' || (mode === 'football' && pitchSide) ? 2 : 35;
    if (mode === 'people') { camera.position.set(35, 10, 2.4); controls.target.set(41.5, 9.1, .7); controls.update(); }
    else if (mode === 'football' || mode === 'concert') { camera.position.set(0, 80, 65); controls.target.set(0, 6, 0); controls.update(); }
    else if (mode === 'drone') { camera.position.set(200, 155, -380); controls.target.set(0, 90, -140); controls.update(); }
    else { camera.position.set(410, 280, 440); controls.target.set(0, 15, 0); controls.update(); }
    scene.background.set(mode === 'drone' ? '#182331' : '#d4dce1');
    try { await modes.select(mode); if (version === selection) {
      if (mode === 'people') { window.__peopleReview = modes.active; }
      if (mode === 'football' && matchReview) window.__matchReview = modes.active;
      if (mode === 'concert' && concertReview) {
        modes.active?.seek(18);
        const stage = scene.getObjectByName('EVT-01');
        if (stage) {
          controls.minDistance = 2;
          const wide = params.has('concert-wide');
          camera.position.copy(stage.localToWorld(wide ? new THREE.Vector3(-31, 15, 8) : new THREE.Vector3(-4, 4, 28)));
          controls.target.copy(stage.localToWorld(new THREE.Vector3(0, 2.6, 37)));
          controls.update();
        }
      }
      renderer.render(scene, camera);
    } }
    catch (error) { if (version === selection) { claim.textContent = mode === 'people' ? 'Local character files are unavailable. Export the prototype files and retry.' : 'This mode could not load. Select it to retry.'; console.warn('Mode unavailable:', error); } }
  });
  for (const button of peopleControls.querySelectorAll('[data-pose]')) button.addEventListener('click', () => {
    if (selected === 'people' && modes.active?.setPose) { modes.active.setPose(button.dataset.pose); renderer.render(scene, camera); }
  });
  let previous = performance.now();
  function animate(now) {
    const dt = Math.min(.1, Math.max(0, (now - previous) / 1000)); previous = now;
    if (selected !== 'venue') { modes.update(dt); renderer.render(scene, camera); }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
  addEventListener('resize', () => renderer.render(scene, camera));
  requestAnimationFrame(() => requestAnimationFrame(() => {
    performance.mark('stadium-interactive');
    status.textContent = 'Drag to orbit · scroll to zoom';
  }));
} catch (error) {
  status.textContent = 'The stadium could not load.';
  console.error(error);
}
