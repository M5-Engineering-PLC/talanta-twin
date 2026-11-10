import { SCHEMA, packChannels } from './format.js';
import { MODULES } from '../modules/registry.js';
import { Timeline, night_show } from '../shows/timeline.js';
import { showState, ribAttributes } from '../shows/state.js';
import { fanLayout, occupancyOrder, selectSeats, clampFill } from '../people/model.js';

export function exportModule({ module, data, fps = 24, duration = 60, start = 0, drones = 480, viewer,
  pad = 0, sourceCommit = null, geometrySource = 'fallback', seats, cues = [], fill = 1, width = 1024, night = false }) {
  if (!MODULES.some(m => m.id === module && ['SHW-01', 'SHW-02', 'SHW-03', 'PPL-02'].includes(module))) throw new Error('Unsupported bridge module');
  if (!Number.isFinite(fps) || fps <= 0 || !Number.isFinite(duration) || duration <= 0 || !Number.isFinite(start) || start < 0 || !Number.isInteger(drones) || drones < 1) throw new Error('Invalid export sampling');
  if (viewer && !['x', 'y', 'z'].every(k => Number.isFinite(viewer[k]))) throw new Error('Invalid viewer');
  const frame_count = Math.ceil(fps * duration);
  const header = { schema: SCHEMA, module, claim: MODULES.find(m => m.id === module).claim, fps, duration_s: duration,
    start_s: start, frame_count, coords: `stadium-local metres, x east, y up, z south, origin pitch centre, pad elevation ${pad}`,
    source_commit: sourceCommit, binary: `${module}.bin`, byte_order: 'little-endian', sample_time: 'start_s + frame / fps',
    channel_layout: 'frame, item, component; offset bytes; length float32 scalars', static: {}, channels: [] };
  const entries = [];
  if (module === 'PPL-02') {
    if (!Array.isArray(seats) || !seats.length || seats.some(s => !['x', 'y', 'z', 'facing_deg', 'tier', 'row'].every(k => Number.isFinite(s[k])))) throw new Error('Numeric crowd seats are required');
    const { fans, perimeter } = fanLayout(seats), order = occupancyOrder(seats);
    const selected = selectSeats(seats, fill, width, order);
    header.channel_layout = 'static crowd channels: seat index, component; occupancy_order ranks seat indices; selected_seats lists drawn seat indices; offset bytes; length float32 scalars';
    header.static = { seat_count: seats.length, selected_count: selected.length,
      parent_frame: 'bowl.group local; translate y by pad elevation to stadium-local',
      fill: clampFill(fill), width, perimeter, origin_y_offset: .02,
      shirt_0_srgb: '#b92332', shirt_1_srgb: '#18733d', shirt_2_srgb: '#ded9cc', shirt_3_srgb: '#292934',
      reaction_cues: cues, night: Number(Boolean(night)),
      pose_formula: 'app/src/people/model.js: fanPose. elapsed=max(0,t-start); active=elapsed<duration; travel=elapsed*speed/perimeter*2*pi; delta=acos(clamp(cos(angle-travel),-1,1)); wave=(1-smoothstep(.06,.20,delta))*waveFlag; lift=max(wave,cheer,goal*step(0,fanEnd*end))*active; scarf=scarves*active; phone=phones*night; raised=max(lift,scarf); bob=.012*sin(t*1.7+phase); turn=.035*sin(t*.7+phase).',
      cue_source: cues.length ? 'caller-supplied react() calls' : 'no reactions requested; idle crowd' };
    entries.push(
      { name: 'seat_position', components: 3, values: seats.flatMap(s => [s.x, s.y, s.z]) },
      { name: 'seat_facing_deg', components: 1, values: seats.map(s => s.facing_deg) },
      { name: 'seat_tier', components: 1, values: seats.map(s => s.tier) },
      { name: 'seat_row', components: 1, values: seats.map(s => s.row) },
      { name: 'occupancy_order', components: 1, values: order },
      { name: 'selected_seats', components: 1, values: selected },
      { name: 'fan_phase', components: 1, values: fans.map(f => f.phase) },
      { name: 'fan_wave_angle', components: 1, values: fans.map(f => f.angle) },
      { name: 'fan_end', components: 1, values: fans.map(f => f.end) },
      { name: 'fan_shirt_index', components: 1, values: fans.map(f => f.shirt) },
    );
  } else {
    const timeline = new Timeline(night_show);
    header.timeline = night_show;
    header.static = module === 'SHW-01' ? { floodlights: data.floodlights, spot_intensity_scale: 180000, emissive_scale: 8 } : module === 'SHW-02' ?
      { ribs: data.ribs, fascia: data.fascia, opening: data.opening, rib_attributes: ribAttributes(data), emissive_scale: 5 } :
      { drone_count: drones, facing: viewer ? 'fixed-viewer' : 'none', viewer: viewer ?? null, emissive_scale: 10 };
    header.geometry_source = geometrySource;
    header.parent_frame = 'shows-visualization local; translate y by pad elevation to stadium-local';
    const values = { visible: [], rgb: [], position: [], intensity: [] };
    for (let n = 0; n < frame_count; n++) {
      const t = start + n / fps, state = showState(timeline.sample(t), t, data, { drones }, { viewer })[module];
      values.visible.push(+state.visible);
      if (module === 'SHW-03') {
        // Hidden instances get zero channels rather than stale app buffers.
        values.position.push(...(state.visible ? state.position : new Array(drones * 3).fill(0)));
        values.rgb.push(...(state.visible ? state.rgb : new Array(drones * 3).fill(0)));
      } else {
        values.rgb.push(...state.rgb);
        if (module === 'SHW-01') values.intensity.push(...state.intensity);
      }
    }
    for (const name of ['visible', ...(module === 'SHW-03' ? ['position'] : []), 'rgb', ...(module === 'SHW-01' ? ['intensity'] : [])]) entries.push({ name, components: ['rgb', 'position'].includes(name) ? 3 : 1, values: values[name] });
  }
  const { channels, bytes } = packChannels(entries); header.channels = channels;
  return { header, bytes };
}
