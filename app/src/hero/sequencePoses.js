// CAM-01. Virtual review viewpoints, never installed camera or security locations.
// The hold at the pitch keeps the goal legible before the final pullback.
export const SEQUENCE_POSES = Object.freeze([
  { time: 0, manifest: 'C16' },
  { time: 14, manifest: 'L06' },
  { time: 24, manifest: 'C06' },
  { time: 36, focus: 'top' },
  { time: 48, focus: 'seating' },
  { time: 62, focus: 'pitch' },
  { time: 78, focus: 'pitch' },
  { time: 90, manifest: 'L07' },
]);

export function resolveSequencePoses(manifest, focus) {
  const array = value => value.toArray ? value.toArray() : [...value];
  return SEQUENCE_POSES.map(key => {
    const source = key.manifest && manifest.cameras.find(c => c.id === key.manifest);
    const target = key.focus && focus.find(f => f.id === key.focus);
    const pose = source || (target?.poseFn ? target.poseFn() : target?.pose);
    if (!pose) throw new Error(`Hero pose unavailable: ${key.manifest || key.focus}`);
    return { time: key.time, position: array(pose.position || pose.pos), target: array(pose.target),
      fov: pose.fov ?? pose.vfov_deg ?? (source ? 2 * Math.atan(manifest.sensor_width_mm / 2 / source.focal_length_mm
        / (manifest.resolution[0] / manifest.resolution[1])) * 180 / Math.PI : 42) };
  });
}
