import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { MODULES } from '../src/modules/registry.js';
import { buildMenu, parseAction, isSecurity, PHASES } from '../src/modules/menu.js';

const items = (groups) => groups.flatMap((g) => g.items);

test('menu groups follow the phase order and keep every non-security module once', () => {
  const groups = buildMenu(MODULES);
  const order = PHASES.map((p) => p.phase);
  assert.deepEqual(groups.map((g) => g.phase), [...groups.map((g) => g.phase)].sort((a, b) => order.indexOf(a) - order.indexOf(b)));
  assert.deepEqual(items(groups).map((i) => i.id).sort(), MODULES.filter((m) => !isSecurity(m.id)).map((m) => m.id).sort());
  for (const g of groups) for (const i of g.items) {
    const m = MODULES.find((x) => x.id === i.id);
    assert.equal(g.phase, m.phase ?? '', i.id);
    assert.equal(i.name, m.name); assert.equal(i.claim, m.claim); assert.equal(i.status, m.status);
  }
});

test('every entry shows a claim label', () => {
  for (const i of items(buildMenu(MODULES))) assert.ok(typeof i.claim === 'string' && i.claim.length, i.id);
});

test('planned entries show "Planned" and cannot be selected, even with an action', () => {
  const groups = buildMenu([{ id: 'X-01', name: 'x', phase: 'B', status: 'planned', claim: 'c', action: 'hero' }]);
  assert.deepEqual(items(groups)[0], { id: 'X-01', name: 'x', claim: 'c', status: 'planned', planned: true, label: 'Planned', action: null, enabled: false });
  for (const i of items(buildMenu(MODULES))) if (i.status === 'planned') { assert.equal(i.label, 'Planned'); assert.equal(i.enabled, false); }
});

test('SEC- modules never appear', () => {
  const groups = buildMenu([...MODULES, { id: 'SEC-01', name: 'Control room', phase: 'A', status: 'done', claim: 'c', action: 'hero' },
    { id: 'sec-02', name: 'Cameras', status: 'partial', claim: 'c' }]);
  assert.ok(!items(groups).some((i) => /^SEC-/i.test(i.id)));
  assert.ok(!MODULES.some((m) => isSecurity(m.id)));
});

test('actions parse to mode, event or hero and reject anything else', () => {
  assert.equal(parseAction(undefined), null);
  assert.deepEqual(parseAction('hero'), { kind: 'hero' });
  assert.deepEqual(parseAction('mode:show'), { kind: 'mode', value: 'show' });
  assert.deepEqual(parseAction('event:concert'), { kind: 'event', value: 'concert' });
  assert.deepEqual(parseAction('event:match'), { kind: 'event', value: 'match' });
  for (const bad of ['mode:gates', 'event:football', 'hero:1', 'run', 'mode:show:x']) assert.throws(() => parseAction(bad), bad);
});

test('registry actions are valid and wired to the expected controls', () => {
  for (const m of MODULES) parseAction(m.action);
  const by = Object.fromEntries(MODULES.map((m) => [m.id, m.action]));
  assert.equal(by['CAM-01'], 'hero');
  assert.equal(by['EVT-01'], 'event:concert');
  assert.equal(by['SPT-01'], 'event:match');
  assert.equal(by['SHW-01'], 'mode:show');
  assert.equal(by['PPL-01'], 'mode:matchday');
  assert.equal(by['HIS-01'], 'mode:construction');
  assert.equal(by['ENV-07'], 'mode:weather');
  // Every data-mode named by an action exists in the full-site app.
  const html = readFileSync(new URL('../full-site.html', import.meta.url), 'utf8');
  for (const m of MODULES) { const a = parseAction(m.action); if (a?.kind === 'mode') assert.match(html, new RegExp(`data-mode="${a.value}"`), m.id); }
});

test('enabled entries are exactly the non-planned ones with an action', () => {
  for (const i of items(buildMenu(MODULES))) assert.equal(i.enabled, !i.planned && Boolean(MODULES.find((m) => m.id === i.id).action), i.id);
});
