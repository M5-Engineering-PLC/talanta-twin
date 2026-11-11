import test from 'node:test';
import assert from 'node:assert/strict';
import { matchState } from '../src/events/match-state.js';

const distance = (a,b) => Math.hypot(a[0]-b[0], a[2]-b[2]);
test('the attack has controlled dribbles and passes arriving at their receiver', () => {
  for(let t=30;t<59.2;t+=.1){
    const s=matchState(undefined,t), ball=s.ball;
    if(ball.action==='carry') assert.ok(distance(ball.position,s.players[ball.owner].position)<1.05, `owner at ${t}`);
  }
  for(const [time,id] of [[37,9],[45,10],[53,9]]) {
    const s=matchState(undefined,time); assert.equal(s.ball.owner,id);
    assert.ok(distance(s.ball.position,s.players[id].position)<1.05, `arrival ${time}`);
  }
});
test('shot, score, referee and goal reaction share the same timeline', () => {
  const before=matchState(undefined,59.21), goal=matchState(undefined,60);
  assert.equal(before.ball.action,'shot'); assert.deepEqual(before.score,[0,0]);
  assert.deepEqual(goal.score,[1,0]); assert.equal(goal.crowdReactions[0].name,'goal');
  assert.ok(goal.ball.position[2]<-52.5); assert.ok(goal.referee.position[2]<-30);
  for(const t of [30,35,37,43,45,51,53,59.2,60]) {
    const a=matchState(undefined,t-1e-5),b=matchState(undefined,t+1e-5);
    assert.ok(distance(a.ball.position,b.ball.position)<.03,`ball jump at ${t}`);
    for(const id of [7,9,10]) assert.ok(distance(a.players[id].position,b.players[id].position)<.03,`player ${id} jump at ${t}`);
  }
});

