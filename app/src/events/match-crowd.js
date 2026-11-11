import * as THREE from 'three/webgpu';

// Select a bounded, deterministic subset of the authored instanced seats.
// Coordinates are expressed in hero-local space, where the crowd is attached.
export function matchCrowdSeats(hero, stride = 12) {
  let source;
  hero.traverse(o => { if (o.isInstancedMesh && o.name === 'seats__seat_proto_v2__LOD0') source = o; });
  if (!source) throw new Error('Authored seat instances unavailable');
  hero.updateWorldMatrix(true, false); source.updateWorldMatrix(true, false);
  const relative = new THREE.Matrix4().copy(hero.matrixWorld).invert().multiply(source.matrixWorld);
  const m = new THREE.Matrix4(), seats = [];
  for (let i = 0; i < source.count; i += stride) {
    source.getMatrixAt(i, m); m.premultiply(relative);
    seats.push({ x: m.elements[12], y: m.elements[13], z: m.elements[14],
      facing_deg: Math.atan2(m.elements[8], m.elements[10]) * 180 / Math.PI, tier: 0, row: Math.round(m.elements[13] * 100) });
  }
  return seats;
}

// Keep the visualization clock with the match and release both together.
export function attachMatchCrowd(event, crowd) {
  let dead = false;
  return {
    update(dt) { if (dead) return; const frame = event.update(dt); if (frame) crowd.update(dt, frame.time); return frame; },
    seek(t) {
      if (dead) return;
      const frame = event.seek(t); crowd.update(0, frame.time);
      const reaction = frame.crowdReactions[0];
      if (reaction) crowd.react(reaction.name, { ...reaction.params, duration: Math.max(0, reaction.start + reaction.duration - frame.time) });
      else crowd.react('cheer', { duration: 0 });
      return frame;
    },
    crowdState() { const u = crowd.group?.userData?.animation; return u ? { time: u.time.value, goal: u.goal.value, start: u.start.value, end: u.end.value } : null; },
    dispose() { if (dead) return; dead = true; event.dispose(); crowd.dispose(); },
  };
}

// Playback emits a crossed cue before updating the crowd's clock. Move the
// clock to the goal boundary first so the visual reaction begins exactly there.
export function matchReactionHost(crowd, goalTime) {
  return { react(name, params) {
    if (name === 'goal') crowd.update(0, goalTime);
    crowd.react(name, params);
  } };
}
