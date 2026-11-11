import test from 'node:test';
import assert from 'node:assert/strict';
import { createModeController } from '../src/perimeterModes.js';

test('loads on selection, disposes old mode and ignores late loads', async () => {
  const disposed=[], pending={}; const loader = mode => new Promise(resolve => { pending[mode]=resolve; });
  const controller=createModeController({load:loader});
  const a=controller.select('football'), b=controller.select('concert');
  pending.football({dispose:()=>disposed.push('football')}); await a;
  pending.concert({dispose:()=>disposed.push('concert'),update:dt=>disposed.push(dt)}); await b;
  controller.update(.2); await controller.select('venue');
  assert.deepEqual(disposed,['football',.2,'concert']);
});

test('unknown modes do not install and errors leave no active instance', async () => {
  const controller=createModeController({load:async()=>{throw new Error('offline')}});
  await assert.rejects(controller.select('bad'), /Unknown/);
  await assert.rejects(controller.select('drone'), /offline/);
  controller.update(.2);
});

test('the local people review can be selected and removed', async () => {
  const calls = []; const c = createModeController({ load: async mode => ({ update: () => {}, dispose: () => calls.push(mode) }) });
  await c.select('people'); await c.select('venue'); assert.deepEqual(calls, ['people']);
});
