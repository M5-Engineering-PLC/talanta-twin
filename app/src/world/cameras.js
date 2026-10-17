import * as THREE from 'three/webgpu';

// Frozen critic cameras C01-C16 (app/cameras/manifest.json). Render viewpoints for review only,
// not real camera locations. Positions are in the local frame (x east, y up, z south).
export function cameraFromManifest(m, id, aspect = m.resolution[0] / m.resolution[1]) {
  const c = m.cameras.find((k) => k.id === id);
  if (!c) throw new Error(`camera ${id} not in manifest`);
  let cam;
  if (c.projection === 'orthographic') {
    const hw = c.ortho_scale_m / 2, hh = hw / aspect;
    cam = new THREE.OrthographicCamera(-hw, hw, hh, -hh, 0.5, 60000);
  } else {
    // sensor fit horizontal: vertical FOV from the 36 mm sensor width and the aspect ratio
    const vfov = 2 * Math.atan(m.sensor_width_mm / 2 / c.focal_length_mm / aspect) * (180 / Math.PI);
    cam = new THREE.PerspectiveCamera(vfov, aspect, 0.5, 60000);
  }
  cam.name = c.id;
  cam.position.fromArray(c.position);
  cam.up.fromArray(c.up);
  cam.lookAt(new THREE.Vector3().fromArray(c.target));
  cam.updateProjectionMatrix();
  cam.userData = { purpose: c.purpose, sun: c.sun, seed: c.seed, target: c.target };
  return cam;
}
