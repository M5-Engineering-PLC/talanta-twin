import test from 'node:test';
import assert from 'node:assert/strict';
import { orderTiles } from '../src/hero/groundTiles.js';
test('coarse tiles load first and nearest centres lead each level', () => {
  const tiles = [{level:0,x0:0,z0:0,size:256,file:'fine'}, {level:1,x0:1000,z0:0,size:512,file:'far'}, {level:1,x0:0,z0:0,size:512,file:'near'}];
  assert.deepEqual(orderTiles(tiles,{x:10,z:10}).map(t=>t.file), ['near','far','fine']);
  assert.deepEqual(orderTiles(tiles,{x:1300,z:10},true).map(t=>t.file), ['far','near']);
  assert.equal(tiles[0].file,'fine');
});
