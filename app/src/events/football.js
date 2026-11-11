import * as THREE from 'three/webgpu';

// 69 cm circumference, the midpoint of the IFAB Law 2 range.
export const BALL_RADIUS = .69 / (2 * Math.PI);

export function footballGeometry(radius = BALL_RADIUS) {
  const ico = new THREE.IcosahedronGeometry(1, 0);
  const source = ico.getAttribute('position');
  const vertices = [], faces = [];
  const index = point => {
    const known = vertices.findIndex(vertex => vertex.distanceToSquared(point) < 1e-10);
    if (known !== -1) return known;
    vertices.push(point);
    return vertices.length - 1;
  };
  for (let i = 0; i < source.count; i += 3) {
    faces.push([i, i + 1, i + 2].map(j => index(new THREE.Vector3().fromBufferAttribute(source, j))));
  }
  ico.dispose();

  const edges = vertices.map(() => new Set());
  const split = (a, b) => vertices[a].clone().lerp(vertices[b], 1 / 3).normalize();
  const positions = [], normals = [], colors = [];
  function panel(points, tint) {
    const centre = points.reduce((sum, point) => sum.add(point), new THREE.Vector3()).normalize();
    for (let i = 0; i < points.length; i++) {
      const a = points[i], b = points[(i + 1) % points.length];
      const outward = a.clone().sub(centre).cross(b.clone().sub(centre)).dot(centre) > 0;
      for (const point of [centre, outward ? a : b, outward ? b : a]) {
        positions.push(point.x * radius, point.y * radius, point.z * radius);
        normals.push(...point);
        colors.push(tint.r, tint.g, tint.b);
      }
    }
  }
  const light = new THREE.Color('#f5f3e8'), dark = new THREE.Color('#212830');
  for (const [a, b, c] of faces) {
    for (const [x, y] of [[a, b], [b, c], [c, a]]) { edges[x].add(y); edges[y].add(x); }
    panel([split(a, b), split(b, a), split(b, c), split(c, b), split(c, a), split(a, c)], light);
  }
  for (const [a, neighbors] of edges.entries()) {
    const axis = vertices[a];
    const points = [...neighbors].map(b => split(a, b));
    const u = points[0].clone().projectOnPlane(axis).normalize();
    const v = axis.clone().cross(u).normalize();
    const angle = point => Math.atan2(point.dot(v), point.dot(u));
    points.sort((left, right) => angle(left) - angle(right));
    panel(points, dark);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  return geometry;
}
