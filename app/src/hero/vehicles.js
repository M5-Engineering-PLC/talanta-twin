import * as THREE from 'three/webgpu';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// Dimensions are metres. The positive X end is the front of the vehicle.
export const VEHICLE_SPECS = [
  { name: 'probox', weight: .22, length: 4.245, width: 1.690, height: 1.525, wheelbase: 2.550, track: [1.485, 1.465], tyre: [155, 80, 14], roof: [-.40, .12, .29], belt: .59 },
  { name: 'premio', weight: .22, length: 4.595, width: 1.695, height: 1.475, wheelbase: 2.700, track: [1.480, 1.460], tyre: [185, 65, 15], roof: [-.20, .10, .31], belt: .57 },
  { name: 'vitz', weight: .20, length: 3.945, width: 1.695, height: 1.500, wheelbase: 2.510, track: [1.460, 1.445], tyre: [165, 70, 14], roof: [-.30, .09, .30], belt: .58 },
  { name: 'prado', weight: .16, length: 4.840, width: 1.885, height: 1.850, wheelbase: 2.790, track: [1.585, 1.585], tyre: [265, 65, 17], roof: [-.34, .13, .31], belt: .64 },
  { name: 'hilux', weight: .20, length: 5.325, width: 1.855, height: 1.815, wheelbase: 3.085, track: [1.540, 1.550], tyre: [265, 65, 17], roof: [-.08, .16, .30], belt: .64 },
];
export const VEHICLE_PARTS = ['body', 'glass', 'tyre', 'rim', 'headlight', 'taillight', 'frontPlate', 'rearPlate', 'mirror'];

function profile(points, width, taper = .9) {
  const shape = new THREE.Shape();
  points.forEach(([x, y], i) => i ? shape.lineTo(x, y) : shape.moveTo(x, y));
  shape.closePath();
  const geo = new THREE.ExtrudeGeometry(shape, { depth: width, bevelEnabled: false, steps: 1 });
  geo.translate(0, 0, -width / 2);
  const p = geo.getAttribute('position');
  const low = Math.min(...points.map((v) => v[1])), high = Math.max(...points.map((v) => v[1]));
  for (let i = 0; i < p.count; i++) p.setZ(i, p.getZ(i) * (1 - (1 - taper) * (p.getY(i) - low) / (high - low)));
  geo.computeVertexNormals();
  return geo;
}

export function createVehicleGeometry(spec) {
  const { length: L, width: W, height: H, wheelbase: wb } = spec;
  const [tyreWidth, aspect, rimInches] = spec.tyre;
  const radius = (rimInches * 25.4 / 2 + tyreWidth * aspect / 100) / 1000;
  const parts = [], records = [];
  const colors = { body: 0xffffff, glass: 0x263c49, tyre: 0x202224, rim: 0xaab0b4, headlight: 0xffeed0, taillight: 0xd22028, frontPlate: 0xffffff, rearPlate: 0xf2ca31, mirror: 0xffffff };
  function add(kind, geo, details = {}) {
    const clean = geo.index ? geo.toNonIndexed() : geo;
    const count = clean.getAttribute('position').count;
    const color = new THREE.Color(colors[kind]);
    const rgb = new Float32Array(count * 3), paint = new Float32Array(count), light = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      rgb.set([color.r, color.g, color.b], i * 3);
      paint[i] = kind === 'body' || kind === 'mirror' ? 1 : 0;
      light[i] = kind === 'headlight' || kind === 'taillight' ? 1 : 0;
    }
    clean.setAttribute('color', new THREE.BufferAttribute(rgb, 3));
    clean.setAttribute('paintMask', new THREE.BufferAttribute(paint, 1));
    clean.setAttribute('lightMask', new THREE.BufferAttribute(light, 1));
    records.push({ kind, start: parts.reduce((n, p) => n + p.getAttribute('position').count, 0), count: clean.getAttribute('position').count, ...details });
    parts.push(clean);
  }
  function box(kind, x, y, z, sx, sy, sz) {
    const g = new THREE.BoxGeometry(sx, sy, sz); g.translate(x, y, z); add(kind, g);
  }
  const b = H * spec.belt, [rearRoof, frontRoof, frontBase] = spec.roof;
  const base = radius * .40;
  // The bonnet and roof narrow toward their upper edges.
  add('body', profile([[-L/2, base], [L/2, base], [L/2, b*.77], [L*.43, b*.94], [L*frontBase, b], [-L*.46, b], [-L/2, b*.83]], W*.96, .94));
  const rearBase = spec.name === 'premio' ? -.38 : spec.name === 'hilux' ? -.20 : -.47;
  add('body', profile([[L*rearBase, b*.98], [L*rearRoof, H], [L*frontRoof, H], [L*frontBase, b*.98]], W*.88, .88));
  // Separate side windows and windshields sit inside the painted pillars.
  const glass = [[L*(rearBase+.025), b*1.02], [L*(rearRoof+.025), H*.96], [L*(frontRoof-.025), H*.96], [L*(frontBase-.025), b*1.02]];
  add('glass', profile(glass, W*.885, .88));
  for (const z of [-W*.42, W*.42]) {
    box('body', L*(rearRoof+frontRoof)/2, (H+b)/2, z, .055, H-b, .035);
    box('mirror', L*(frontBase-.025), b*1.12, Math.sign(z)*W*.47, .21, .11, W*.06);
  }
  // The steering wheel is on the right side of the cabin.
  const steering = new THREE.TorusGeometry(.12, .018, 5, 10);
  steering.rotateY(Math.PI / 2); steering.translate(L * (frontRoof + .01), b * 1.12, W * .22);
  add('tyre', steering, { role: 'right-hand steering' });
  if (spec.name === 'hilux') {
    box('body', -L*.35, b*.91, 0, L*.28, .08, W*.88);
    box('glass', -L*.35, b*.955, 0, L*.24, .02, W*.72);
  }
  const axles = [-wb/2, wb/2];
  for (const [a, x] of axles.entries()) for (const side of [-1, 1]) {
    const track = spec.track[a === 0 ? 1 : 0], z = side * track / 2;
    const wheel = new THREE.CylinderGeometry(radius, radius, tyreWidth/1000, 12); wheel.rotateX(Math.PI/2); wheel.translate(x, radius, z);
    add('tyre', wheel, { axle: x, side });
    const rim = new THREE.CylinderGeometry(rimInches*.0254/2, rimInches*.0254/2, .012, 12); rim.rotateX(Math.PI/2); rim.translate(x, radius, z + side*(tyreWidth/2000+.004)); add('rim', rim);
  }
  for (const side of [-1, 1]) {
    const z = side*W*.32;
    box('headlight', L/2-.018, b*.75, z, .035, H*.10, W*.25);
    box('taillight', -L/2+.018, b*.76, z, .035, H*(spec.name === 'probox' || spec.name === 'hilux' ? .18 : .10), W*.19);
  }
  box('frontPlate', L/2-.005, b*.39, 0, .02, .11, .38);
  box('rearPlate', -L/2+.005, b*.43, 0, .02, .11, .38);
  const geometry = mergeGeometries(parts, false);
  geometry.clearGroups();
  geometry.userData.parts = records;
  geometry.computeBoundingBox();
  parts.forEach((part) => part.dispose());
  return geometry;
}
