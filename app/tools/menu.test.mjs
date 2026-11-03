import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildMenuModel, renderMenu } from '../src/modules/menu.js';
import { MODULES } from '../src/modules/registry.js';

const module = (id, phase, status = 'done', action = 'mode:show') => ({
  id, phase, status, action, name: `Module ${id}`, claim: `Claim for ${id}`,
});
const entries = model => model.flatMap(group => group.entries);

test('groups A, B, C and other in order and preserves registry order within groups', () => {
  const modules = [module('C-1', 'C'), module('X-1'), module('A-1', 'A'), module('B-1', 'B'), module('A-2', 'A'), module('D-1', 'D')];
  const before = JSON.stringify(modules);
  const model = buildMenuModel(modules);
  assert.deepEqual(model.map(group => group.phase), ['A', 'B', 'C', 'other']);
  assert.deepEqual(model.map(group => group.entries.map(entry => entry.id)), [['A-1', 'A-2'], ['B-1'], ['C-1'], ['X-1', 'D-1']]);
  assert.equal(JSON.stringify(modules), before);
});

test('planned entries stay disabled even when an action exists', () => {
  let calls = 0;
  const [entry] = entries(buildMenuModel([module('EVT-02', 'B', 'planned')], { 'mode:show': () => calls++ }));
  assert.equal(entry.disabled, true); assert.equal(entry.label, 'Planned');
  assert.equal(entry.run, null); assert.equal(entry.action, null); assert.equal(calls, 0);
});

test('done and partial entries use only callable known actions without starting them during construction', () => {
  let calls = 0; const run = () => calls++;
  const model = buildMenuModel([module('SHW-01', 'A'), module('EVT-01', 'B', 'partial')], { 'mode:show': run });
  assert.equal(calls, 0);
  for (const entry of entries(model)) { assert.equal(entry.disabled, false); assert.equal(entry.run, run); entry.run(); }
  assert.equal(calls, 2);
  assert.deepEqual(entries(model).map(entry => entry.label), ['Done', 'Partial']);
});

test('SEC- entries never appear, including future phases and actionable modules', () => {
  const model = buildMenuModel([module('SEC-01', 'A'), module('SEC-99', 'D', 'partial'), module('SHW-01', 'A')], { 'mode:show': () => {} });
  assert.deepEqual(entries(model).map(entry => entry.id), ['SHW-01']);
});

test('every public registry entry preserves its complete claim text', () => {
  const model = buildMenuModel(MODULES);
  assert.equal(entries(model).length, MODULES.filter(module => !module.id.startsWith('SEC-')).length);
  for (const entry of entries(model)) assert.equal(entry.claim, MODULES.find(module => module.id === entry.id).claim);
});

test('unknown, inherited, absent and non-callable actions are ignored', () => {
  const actions = Object.assign(Object.create({ inherited() {} }), { invalid: true });
  const modules = ['unknown', 'inherited', 'invalid', undefined, 'toString', '__proto__'].map((action, i) => module(`X-${i}`, 'A', 'done', action));
  modules[3].action = undefined;
  for (const entry of entries(buildMenuModel(modules, actions))) {
    assert.equal(entry.disabled, true); assert.equal(entry.run, null); assert.equal(entry.action, null); assert.equal(entry.label, 'Unavailable');
  }
});

// A small DOM host exercises the renderer without a browser or scene renderer.
function dom() {
  const doc = { activeElement: null, listeners: {},
    createElement(tag) { return node(tag); },
    addEventListener(type, fn) { this.listeners[type] = fn; },
  };
  function node(tag) {
    return { tag, ownerDocument: doc, dataset: {}, children: [], attributes: {}, listeners: {}, hidden: false,
      append(...children) { this.children.push(...children); },
      replaceChildren() { this.children = []; },
      setAttribute(key, value) { this.attributes[key] = value; },
      focus() { doc.activeElement = this; },
      addEventListener(type, fn) { this.listeners[type] = fn; },
      querySelector() { return close; },
    };
  }
  const button = node('button'), panel = node('aside'), list = node('div'), claim = node('p'), close = node('button');
  panel.hidden = true;
  return { doc, button, panel, list, claim, close };
}

test('renderer opens with keyboard focus and Escape and Close restore trigger focus', () => {
  const host = dom(); renderMenu(host, buildMenuModel([]));
  host.button.onclick();
  assert.equal(host.panel.hidden, false); assert.equal(host.button.attributes['aria-expanded'], 'true');
  assert.equal(host.doc.activeElement, host.close);
  let prevented = false;
  host.doc.listeners.keydown({ key: 'Escape', preventDefault() { prevented = true; } });
  assert.equal(prevented, true); assert.equal(host.panel.hidden, true);
  assert.equal(host.button.attributes['aria-expanded'], 'false'); assert.equal(host.doc.activeElement, host.button);
  host.button.onclick(); host.close.onclick();
  assert.equal(host.panel.hidden, true); assert.equal(host.doc.activeElement, host.button);
});

test('renderer shows claims, starts selected actions, and guards disabled entries', () => {
  const host = dom(); let calls = 0;
  renderMenu(host, buildMenuModel([module('SHW-01', 'A'), module('SHW-04', 'B', 'planned')], { 'mode:show': () => calls++ }));
  const row = host.list.children[0].children[1], planned = host.list.children[1].children[1];
  assert.equal(row.tag, 'button'); assert.equal(row.type, 'button'); assert.equal(row.children[2].textContent, 'Claim for SHW-01');
  assert.equal(planned.disabled, true); assert.equal(planned.children[1].textContent, 'Planned');
  planned.onclick(); assert.equal(calls, 0);
  host.button.onclick(); row.onclick();
  assert.equal(calls, 1); assert.equal(host.claim.textContent, 'Claim for SHW-01'); assert.equal(host.claim.hidden, false);
  assert.equal(host.panel.hidden, true); assert.equal(host.doc.activeElement, host.button);
});

test('app wiring routes menu actions through existing controls and excludes SEC claims', () => {
  const source = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  const startIndex = source.indexOf('// Module entries reuse the existing controls');
  const section = source.slice(startIndex, source.indexOf('if (!quality.crowdFraction) site.crowd.visible = false;', startIndex));
  const calls = [], nodes = new Map(); let model, claimEntries, landing = true;
  const modes = ['venue', 'construction', 'matchday', 'weather', 'show', 'concert', 'football'].map(mode => ({
    dataset: { mode }, listeners: [],
    addEventListener(type, fn) { this.listeners.push(fn); },
    click() { calls.push(mode); for (const listener of this.listeners) listener(); },
  }));
  const hero = { click() { calls.push('hero'); } }, tourBtn = { click() { calls.push('tour'); } };
  const document = {
    querySelectorAll() { return modes; }, querySelector() { return hero; },
    body: { classList: { contains() { return landing; } } },
  };
  nodes.set('#landing-toggle', { click() { landing = !landing; } });
  const $ = selector => { if (!nodes.has(selector)) nodes.set(selector, {}); return nodes.get(selector); };
  const render = (host, value) => { model = value; return { showClaim(value) { claimEntries = value; } }; };
  new Function('MODULES', 'buildMenuModel', 'renderMenu', 'document', '$', 'viewStills', 'tourBtn', section)(
    [...MODULES, module('SEC-01', 'A', 'done', 'mode:show')], buildMenuModel, render, document, $, { dismiss() {} }, tourBtn);
  const start = id => entries(model).find(entry => entry.id === id).run();
  start('PPL-01'); assert.equal(calls.at(-1), 'matchday');
  start('SHW-01'); assert.equal(calls.at(-1), 'show');
  assert.ok(claimEntries.every(entry => !entry.id.startsWith('SEC-')));
  assert.ok(claimEntries.some(entry => entry.claim === MODULES.find(module => module.id === 'SHW-01').claim));
  start('SPT-01'); assert.equal(calls.at(-1), 'football');
  start('EVT-01'); assert.equal(calls.at(-1), 'concert');
  start('HIS-01'); assert.equal(calls.at(-1), 'construction');
  start('ENV-07'); assert.equal(calls.at(-1), 'weather'); assert.equal(landing, false);
  start('CAM-01'); assert.equal(calls.at(-1), 'hero');
  start('CAM-07'); assert.equal(calls.at(-1), 'tour');
});
