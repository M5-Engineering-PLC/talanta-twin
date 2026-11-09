import * as THREE from 'three/webgpu';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { loadHero } from './hero/loadHero.js';

const status = document.querySelector('#status');
const full = new URLSearchParams(location.search).has('full');
if (full) document.querySelector('strong').textContent = 'Talanta Twin · Full site comparison';

try {
  const renderer = new THREE.WebGPURenderer({ antialias: true, forceWebGL: true });
  await renderer.init();
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
  scene.add(loaded.group, new THREE.HemisphereLight('#fff8ed', '#6e6355', 1.25));
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1800, 1800), new THREE.MeshBasicMaterial({ color: '#b6b1a3' }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -2;
  scene.add(ground);

  camera.position.set(320, 180, 320);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 15, 0);
  controls.maxPolarAngle = Math.PI / 2;
  controls.minDistance = 35;
  controls.maxDistance = 1300;
  controls.update();
  renderer.render(scene, camera);
  controls.addEventListener('change', () => renderer.render(scene, camera));
  addEventListener('resize', () => renderer.render(scene, camera));
  requestAnimationFrame(() => requestAnimationFrame(() => {
    performance.mark('stadium-interactive');
    status.textContent = 'Drag to orbit · scroll to zoom';
  }));
} catch (error) {
  status.textContent = 'The stadium could not load.';
  console.error(error);
}
