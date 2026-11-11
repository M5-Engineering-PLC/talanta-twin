import * as THREE from 'three/webgpu';

// Two-segment IK in the existing bend plane. Preserve thigh and calf lengths;
// clamp unreachable targets and retain the original knee side.
export function twoBoneSupport(hip, knee, ankle, verticalAdjustment) {
  const upper = knee.distanceTo(hip), lower = ankle.distanceTo(knee);
  if (upper < 1e-8 || lower < 1e-8) throw new Error('Invalid leg lengths');
  const requested = ankle.clone().add(new THREE.Vector3(0, verticalAdjustment, 0));
  // If a nearly straight leg cannot reach the requested point, pull the ankle
  // horizontally toward the hip first, preserving floor height when possible.
  const maxReach = upper + lower - 1e-7;
  const y = requested.y - hip.y;
  const horizontal = new THREE.Vector3(requested.x - hip.x, 0, requested.z - hip.z);
  if (Math.abs(y) < maxReach) {
    const available = Math.sqrt(maxReach * maxReach - y * y);
    if (horizontal.length() > available) {
      horizontal.setLength(available); requested.x = hip.x + horizontal.x; requested.z = hip.z + horizontal.z;
    }
  }
  const toward = requested.clone().sub(hip), distance = toward.length();
  if (distance < 1e-8) throw new Error('Ankle target is at the hip');
  const d = THREE.MathUtils.clamp(distance, Math.abs(upper - lower) + 1e-7, upper + lower - 1e-7);
  const u = toward.multiplyScalar(1 / distance);
  const target = hip.clone().addScaledVector(u, d);
  const along = (upper * upper - lower * lower + d * d) / (2 * d);
  const perpendicular = knee.clone().sub(hip).addScaledVector(u, -knee.clone().sub(hip).dot(u));
  if (perpendicular.lengthSq() < 1e-12) {
    perpendicular.crossVectors(u, Math.abs(u.y) < .9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0));
  }
  perpendicular.normalize().multiplyScalar(Math.sqrt(Math.max(0, upper * upper - along * along)));
  return { knee: hip.clone().addScaledVector(u, along).add(perpendicular), ankle: target, clamped: Math.abs(d - distance) > 1e-8 };
}
