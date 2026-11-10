// Module registry. IDs come from PLAN.md section 5; scope, phases and labels from
// engineering/scope_decision_2026-10-25.md. Status: planned | partial | done.
// Every module carries a claim label (AGENTS.md rule 7); the label text is shown on screen with the module.
// Optional action: what the Modules menu (src/modules/menu.js) runs: 'mode:<data-mode>', 'event:concert|match' or 'hero'.
const CROWD = 'Visualization. Illustrative crowd behaviour, not validated safety, capacity or crowd-flow evidence.';
const SHOW = 'Illustrative event concept. Installed equipment and operational feasibility are not confirmed.';
export const MODULES = [
  // Phase A: base
  { id: 'ENV-01', action: 'mode:venue', name: 'Time of day', phase: 'A', status: 'partial', claim: 'Simulation', note: 'Real sun path at the pitch centre; the baked hero switches between four Kaggle GPU light sets (07:30, 10:30, 18:05, 20:00; src/hero/timeOfDay.js) with the nearest set held by hysteresis; times between sets are not interpolated' },
  { id: 'PPL-01', name: 'Seated crowd', phase: 'A', status: 'done', claim: CROWD, note: 'One fan per drawn seat place, loads with Match day', action: 'mode:matchday' },
  { id: 'PPL-02', name: 'Crowd reactions', phase: 'A', status: 'done', claim: CROWD, note: 'Cheer, goal, wave, scarves, phone lights', action: 'mode:matchday' },
  { id: 'SHW-01', name: 'Floodlight show', phase: 'A', status: 'done', claim: SHOW, note: 'Night show mode', action: 'mode:show' },
  { id: 'SHW-02', name: 'Facade and roof light show', phase: 'A', status: 'done', claim: SHOW, note: 'Night show mode', action: 'mode:show' },
  { id: 'SHW-03', name: 'Drone show', phase: 'A', status: 'done', claim: SHOW, note: 'Night show mode; needs a phone version', action: 'mode:show' },
  { id: 'CAM-01', name: 'Cinematic fly-in', phase: 'A', status: 'partial', claim: 'n/a', note: '90-second hero timeline with deterministic seek, input cancellation and reduced-motion holds; GPU appearance and device budgets need review', action: 'hero' },
  { id: 'ENV-02', action: 'mode:weather', name: 'Sunshine and clouds', phase: 'C', status: 'partial', claim: 'Simulation', note: 'Hero milestone: overcast sky and panorama dimming during rain; cloud shadows remain planned' },
  { id: 'CAM-02', name: 'Free orbit', phase: 'A', status: 'done', claim: 'n/a', action: 'mode:venue' },
  { id: 'AMB-02', action: 'mode:venue', name: 'Trees and planting', phase: 'A', status: 'partial', claim: 'Estimated' },
  { id: 'AMB-03', action: 'mode:venue', name: 'City skyline and Ngong Hills', phase: 'A', status: 'partial', claim: 'Measured', note: 'GLO-30 terrain to 20 km' },
  // Built before the scope decision, kept
  { id: 'CAM-07', action: 'tour', name: 'Focus and tour', status: 'partial', claim: 'n/a', note: 'Fly-to and highlight per feature' },
  { id: 'HIS-01', name: 'Construction replay', status: 'partial', claim: 'Measured', note: 'Roof ring from Sentinel-2', action: 'mode:construction' },
  { id: 'ENV-07', name: 'Live weather sync', phase: 'C', status: 'partial', claim: 'Name the provider, the time, the place, and whether the value is observed or a forecast.', note: 'Open-Meteo, read-only card', action: 'mode:weather' },
  // Phase B: headline events
  { id: 'SPT-01', name: 'Football match', phase: 'B', status: 'partial', claim: CROWD, action: 'event:match' },
  { id: 'EVT-01', name: 'Concert', phase: 'B', status: 'partial', claim: SHOW, note: 'End stage with LED backdrop, flown tiles and a standing floor crowd; models from public/concert; not yet checked on a real GPU', action: 'event:concert' },
  { id: 'EVT-02', name: 'National celebration', phase: 'B', status: 'planned', claim: SHOW },
  { id: 'SHW-04', name: 'Fireworks', phase: 'B', status: 'planned', claim: SHOW },
  { id: 'CAM-04', name: 'View from your seat', phase: 'B', status: 'planned', claim: 'Approximate view from the model.' },
  { id: 'PPL-08', name: 'Accessible seating', phase: 'B', status: 'planned', claim: 'Illustrative access preview. Follow approved venue accessibility information.' },
  { id: 'ENV-03', action: 'mode:weather', name: 'Rain', phase: 'C', status: 'partial', claim: 'Simulation', note: 'One instanced line draw with tier-scaled streaks and wet material uniforms; puddles and camera drops remain planned; GPU output needs review' },
];
