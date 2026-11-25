import * as THREE from 'three/webgpu';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { loadHero } from './hero/loadHero.js';
import { createModeController } from './perimeterModes.js';

const status = document.querySelector('#status');
const full = new URLSearchParams(location.search).has('full');
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
  const skyLight = new THREE.HemisphereLight('#fff8ed', '#6e6355', .65);
  scene.add(loaded.group, skyLight);

  camera.position.set(410, 280, 440);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 15, 0);
  controls.maxPolarAngle = Math.PI / 2;
  controls.minDistance = 35;
  controls.maxDistance = 1300;
  controls.update();
  renderer.render(scene, camera);
  const claim = document.querySelector('#event-claim');
  const buttons = [...document.querySelectorAll('[data-mode]')];
  const concertCamera = document.querySelector('#concert-camera');
  let concert = null, selected = 'venue', selection = 0;
  // Animated modes submit the next frame themselves, including camera changes.
  function renderVenue() {
    if (selected === 'venue') renderer.render(scene, camera);
  }
  controls.addEventListener('change', renderVenue);
  function applyConcertCamera(pose) {
    camera.position.copy(pose.pos);
    controls.target.copy(pose.target);
    camera.fov = pose.fov;
    camera.updateProjectionMatrix();
    controls.update();
  }
  concertCamera.addEventListener('change', () => {
    if (!concertCamera.value) return;
    const pose = concert?.viewPose(Number(concertCamera.value));
    if (pose) applyConcertCamera(pose);
    concertCamera.value = '';
  });
  const modes = createModeController({ async load(mode) {
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
    return install({ scene, camera, bearing: data.features.pitch_bearing_deg, pad: data.features.site_pad_y,
      tier: innerWidth < 700 ? 'low' : 'medium', width: innerWidth,
      onState: mode === 'concert' ? frame => {
        const text = `Concert · ${frame.phase} · ${Math.floor(frame.time)} / ${frame.duration} s`;
        if (status.textContent !== text) status.textContent = text;
      } : undefined,
    });
  } });
  const claims = { venue: '', football: 'Illustrative football and crowd visualization; not validated safety, capacity or crowd-flow evidence.',
    concert: 'Illustrative event concept and crowd visualization; installed equipment and operational feasibility are not confirmed.',
    drone: 'Illustrative show concept; installed equipment and operational feasibility are not confirmed.' };
  for (const button of buttons) button.addEventListener('click', async () => {
    const mode = button.dataset.mode, version = ++selection; selected = mode;
    concert = null;
    concertCamera.hidden = true;
    status.textContent = mode === 'concert' ? 'Loading concert…' : 'Drag to orbit · scroll to zoom';
    controls.minDistance = mode === 'concert' ? 2 : 35;
    camera.fov = 42;
    camera.updateProjectionMatrix();
    for (const b of buttons) b.setAttribute('aria-pressed', String(b === button));
    claim.textContent = claims[mode];
    if (mode === 'football' || mode === 'concert') { camera.position.set(0, 80, 65); controls.target.set(0, 6, 0); controls.update(); }
    else if (mode === 'drone') { camera.position.set(200, 155, -380); controls.target.set(0, 90, -140); controls.update(); }
    else { camera.position.set(410, 280, 440); controls.target.set(0, 15, 0); controls.update(); }
    const night = mode === 'drone' || mode === 'concert';
    scene.background.set(night ? '#182331' : '#d4dce1');
    skyLight.intensity = mode === 'concert' ? .28 : .65;
    try {
      const event = await modes.select(mode);
      if (version !== selection) return;
      if (mode === 'concert') {
        concert = event;
        concertCamera.replaceChildren(new Option('Concert camera', ''), ...event.viewNames.map((name, index) => new Option(name, index)));
        concertCamera.hidden = false;
        applyConcertCamera(event.viewPose(event.viewNames.indexOf('FOH Soundboard')));
      }
      renderVenue();
    }
    catch (error) { if (version === selection) { claim.textContent = 'This mode could not load. Select it to retry.'; console.warn('Mode unavailable:', error); } }
  });
  let previous = performance.now();
  function animate(now) {
    const elapsed = Math.max(0, (now - previous) / 1000); previous = now;
    if (selected !== 'venue') {
      modes.update(selected === 'concert' ? elapsed : Math.min(.1, elapsed));
      renderer.render(scene, camera);
    }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
  addEventListener('resize', renderVenue);
  requestAnimationFrame(() => requestAnimationFrame(() => {
    performance.mark('stadium-interactive');
    status.textContent = 'Drag to orbit · scroll to zoom';
  }));
} catch (error) {
  status.textContent = 'The stadium could not load.';
  console.error(error);
}
