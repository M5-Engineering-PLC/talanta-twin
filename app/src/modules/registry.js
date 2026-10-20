// Module registry. IDs come from PLAN.md section 5. Status: planned | partial | done.
// Every module carries a claim label (AGENTS.md rule 7).
export const MODULES = [
  { id: 'ENV-01', name: 'Time of day', status: 'partial', claim: 'Simulation', note: 'Real sun path at the pitch centre' },
  { id: 'CAM-02', name: 'Free orbit', status: 'done', claim: 'n/a' },
  { id: 'CAM-07', name: 'Focus and tour', status: 'partial', claim: 'n/a', note: 'Proposed: fly-to and highlight per feature' },
  { id: 'AMB-03', name: 'City skyline and Ngong Hills', status: 'partial', claim: 'Measured', note: 'GLO-30 terrain to 20 km' },
  { id: 'HIS-01', name: 'Construction replay', status: 'partial', claim: 'Measured', note: 'Proposed: roof ring from Sentinel-2' },
  { id: 'ENV-07', name: 'Live weather sync', status: 'partial', claim: 'Measured', note: 'Open-Meteo, read-only card' },
  { id: 'PPL-01', name: 'Seated crowd', status: 'planned', claim: 'Visualization' },
  { id: 'SPT-01', name: 'Football match', status: 'planned', claim: 'Visualization' },
  { id: 'ENV-03', name: 'Rain', status: 'planned', claim: 'Simulation' },
];
