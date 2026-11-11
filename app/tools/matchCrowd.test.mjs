import test from 'node:test';
import assert from 'node:assert/strict';
import { attachMatchCrowd, matchReactionHost } from '../src/events/match-crowd.js';
test('match seek and playback keep crowd clock and goal reaction aligned, then dispose both', () => {
 const calls=[]; const crowd={update:(dt,t)=>calls.push(['clock',dt,t]),react:(n,p)=>calls.push(['react',n,p.duration]),dispose:()=>calls.push(['crowd-dispose'])};
 const event={update:()=>({time:60.2,crowdReactions:[]}),seek:t=>({time:t,crowdReactions:t===61?[{name:'goal',start:60,duration:4,params:{duration:4}}]:[]}),dispose:()=>calls.push(['event-dispose'])};
 const host=attachMatchCrowd(event,crowd);host.seek(61);host.seek(20);host.update(.1);host.dispose();host.dispose();
 assert.deepEqual(calls,[['clock',0,61],['react','goal',3],['clock',0,20],['react','cheer',0],['clock',.1,60.2],['event-dispose'],['crowd-dispose']]);
});

test('goal crossing starts the crowd reaction at the cue rather than the previous frame', () => {
  const calls=[];const crowd={update:(dt,time)=>calls.push(['clock',time]),react:(name)=>calls.push(['reaction',name])};
  const host=matchReactionHost(crowd,60);host.react('goal',{duration:4});
  assert.deepEqual(calls,[['clock',60],['reaction','goal']]);
});

