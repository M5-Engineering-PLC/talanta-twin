import * as THREE from 'three/webgpu';
import { rotate, centroid, shapeMesh } from './geom.js';

// Laws of the Game dimensions. The pitch size itself (105 x 68 m) is assumed until W1b
// measures the markings; the pitch zone (115 x 74 m) is the W1b measurement.
export const PITCH = { L: 105, W: 68, zoneL: 115, zoneW: 74, penD: 16.5, penW: 40.32, goalD: 5.5, goalW: 18.32, circle: 9.15, spot: 11, goalMouth: 7.32, goalH: 2.44 };

export function buildPitch(bearing) {
  const g = new THREE.Group(); g.name = 'pitch';
  const ppm = 16;
  const cv = document.createElement('canvas'); cv.width = PITCH.zoneW * ppm; cv.height = PITCH.zoneL * ppm;
  const x = cv.getContext('2d');
  x.fillStyle = '#4f8a3c'; x.fillRect(0, 0, cv.width, cv.height);
  const ox = (PITCH.zoneW - PITCH.W) / 2 * ppm, oz = (PITCH.zoneL - PITCH.L) / 2 * ppm;
  const bands = 18;
  for (let i = 0; i < bands; i++) { x.fillStyle = i % 2 ? '#5a9644' : '#4c8539'; x.fillRect(ox, oz + (i * PITCH.L * ppm) / bands, PITCH.W * ppm, (PITCH.L * ppm) / bands + 1); }
  x.strokeStyle = '#f4f2ea'; x.lineWidth = 0.12 * ppm * 1.6; x.fillStyle = '#f4f2ea';
  const R = (a, b, w, h) => x.strokeRect(ox + a * ppm, oz + b * ppm, w * ppm, h * ppm);
  R(0, 0, PITCH.W, PITCH.L);
  x.beginPath(); x.moveTo(ox, oz + (PITCH.L / 2) * ppm); x.lineTo(ox + PITCH.W * ppm, oz + (PITCH.L / 2) * ppm); x.stroke();
  const cx = ox + (PITCH.W / 2) * ppm;
  x.beginPath(); x.arc(cx, oz + (PITCH.L / 2) * ppm, PITCH.circle * ppm, 0, Math.PI * 2); x.stroke();
  for (const end of [0, 1]) {
    const gy = end ? PITCH.L : 0, dir = end ? -1 : 1;
    R((PITCH.W - PITCH.penW) / 2, end ? PITCH.L - PITCH.penD : 0, PITCH.penW, PITCH.penD);
    R((PITCH.W - PITCH.goalW) / 2, end ? PITCH.L - PITCH.goalD : 0, PITCH.goalW, PITCH.goalD);
    const sy = oz + (gy + dir * PITCH.spot) * ppm;
    x.beginPath(); x.arc(cx, sy, 0.2 * ppm, 0, Math.PI * 2); x.fill();
    const a = Math.acos((PITCH.penD - PITCH.spot) / PITCH.circle);
    x.beginPath(); x.arc(cx, sy, PITCH.circle * ppm, end ? -Math.PI / 2 - a : Math.PI / 2 - a, end ? -Math.PI / 2 + a : Math.PI / 2 + a); x.stroke();
  }
  x.beginPath(); x.arc(cx, oz + (PITCH.L / 2) * ppm, 0.2 * ppm, 0, Math.PI * 2); x.fill();
  for (const [a, b, s0] of [[0, 0, 0], [PITCH.W, 0, Math.PI / 2], [PITCH.W, PITCH.L, Math.PI], [0, PITCH.L, 1.5 * Math.PI]]) {
    x.beginPath(); x.arc(ox + a * ppm, oz + b * ppm, 1 * ppm, s0, s0 + Math.PI / 2); x.stroke();
  }
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const mat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9 });
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(PITCH.zoneW, PITCH.zoneL), mat);
  plane.rotation.x = -Math.PI / 2; plane.position.y = 0.08; plane.receiveShadow = true; plane.name = 'pitch-surface';
  const holder = new THREE.Group(); holder.rotation.y = -(bearing * Math.PI) / 180; holder.add(plane);
  // goals: posts, crossbar and a light net box
  const post = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.4 });
  const net = new THREE.MeshStandardMaterial({ color: '#ffffff', transparent: true, opacity: 0.25, side: THREE.DoubleSide, depthWrite: false });
  for (const s of [-1, 1]) {
    const z = s * PITCH.L / 2, gw = PITCH.goalMouth, gh = PITCH.goalH;
    for (const px of [-gw / 2, gw / 2]) { const m = new THREE.Mesh(new THREE.BoxGeometry(0.12, gh, 0.12), post); m.position.set(px, gh / 2, z); holder.add(m); }
    const bar = new THREE.Mesh(new THREE.BoxGeometry(gw, 0.12, 0.12), post); bar.position.set(0, gh, z); holder.add(bar);
    const box = new THREE.Mesh(new THREE.BoxGeometry(gw, gh, 2), net); box.position.set(0, gh / 2, z + s * 1); holder.add(box);
  }
  g.add(holder);
  return { group: g, material: mat };
}

// Plan-view features of the pitch, in local metres, for focus and highlight.
export function pitchFeatures(bearing) {
  const L = PITCH.L, W = PITCH.W;
  const rect = (x0, z0, x1, z1) => rotate([[x0, z0], [x1, z0], [x1, z1], [x0, z1], [x0, z0]], bearing);
  const circ = [];
  for (let i = 0; i <= 64; i++) { const a = (i / 64) * Math.PI * 2; circ.push([PITCH.circle * Math.cos(a), PITCH.circle * Math.sin(a)]); }
  const penN = rect(-PITCH.penW / 2, -L / 2, PITCH.penW / 2, -L / 2 + PITCH.penD);
  const penS = rect(-PITCH.penW / 2, L / 2 - PITCH.penD, PITCH.penW / 2, L / 2);
  return {
    pitch: rect(-W / 2, -L / 2, W / 2, L / 2),
    centre: rotate(circ, bearing),
    penN, penS,
    goalN: rotate([[-PITCH.goalMouth / 2, -L / 2], [PITCH.goalMouth / 2, -L / 2]], bearing),
    goalS: rotate([[-PITCH.goalMouth / 2, L / 2], [PITCH.goalMouth / 2, L / 2]], bearing),
    penNc: centroid(penN), penSc: centroid(penS),
  };
}

export function buildSport(sport, y) {
  const g = new THREE.Group(); g.name = 'sport';
  const grass = new THREE.MeshStandardMaterial({ color: '#5b8f45', roughness: 0.95, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 });
  const track = new THREE.MeshStandardMaterial({ color: '#b65d43', roughness: 0.9, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 });
  const meshes = [];
  for (const s of sport) {
    const m = shapeMesh(s.ring, y + 0.12, s.kind === 'track' ? track : grass);
    m.receiveShadow = true; m.userData = { kind: s.kind, area: s.area };
    g.add(m); meshes.push(m);
  }
  return { group: g, meshes, materials: [grass, track] };
}
