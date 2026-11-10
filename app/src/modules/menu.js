// Module menu (scope decision 2026-10-25, phase A). Pure logic: no DOM, so app/tools/menu.test.mjs can run it in Node.
// The menu lists app/src/modules/registry.js grouped by phase. Every entry carries its claim label (AGENTS.md rule 7).
// Planned entries are shown but cannot be selected. Security modules (SEC-) never appear in the menu.

export const PHASES = [
  { phase: 'A', title: 'Phase A · Base' },
  { phase: 'B', title: 'Phase B · Headline events' },
  { phase: 'C', title: 'Phase C · The living venue' },
  { phase: '', title: 'Also in this build' },
];

// Actions the app knows how to run. "mode:<m>" presses the matching data-mode button,
// "event:concert|match" starts that event, "hero" runs the Hero sequence.
export const MODES = ['venue', 'construction', 'matchday', 'weather', 'show'];
export const EVENTS = ['concert', 'match'];

/** Parse an optional registry action. Returns null for no action; throws on an unknown one. */
export function parseAction(action) {
  if (action == null) return null;
  if (action === 'hero' || action === 'tour') return { kind: action };
  const [kind, value, ...rest] = String(action).split(':');
  if (!rest.length && kind === 'mode' && MODES.includes(value)) return { kind, value };
  if (!rest.length && kind === 'event' && EVENTS.includes(value)) return { kind, value };
  throw new Error(`Unknown module action "${action}"`);
}

export const isSecurity = (id) => /^SEC-/i.test(String(id));

/** Build the menu groups from the registry. Phases in A, B, C order, then modules with no phase. Empty groups are left out. */
export function buildMenu(modules) {
  const groups = PHASES.map(({ phase, title }) => ({ phase, title, items: [] }));
  for (const m of modules) {
    if (isSecurity(m.id)) continue;
    const group = groups.find((g) => g.phase === (m.phase ?? '')) ?? groups[groups.length - 1];
    const planned = m.status === 'planned';
    const action = planned ? null : parseAction(m.action);
    group.items.push({
      id: m.id, name: m.name, claim: m.claim, status: m.status, planned,
      label: planned ? 'Planned' : m.status === 'partial' ? 'Partial' : 'Ready',
      action, enabled: Boolean(action),
    });
  }
  return groups.filter((g) => g.items.length);
}
