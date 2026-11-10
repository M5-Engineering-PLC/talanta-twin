import * as THREE from 'three/webgpu';
import { match_cues } from './cues.js';
import { matchState } from './match-state.js';
import { eventRoot, release, figures } from './draw.js';
import { playback } from './playback.js';
export { matchState, match_cues };
export function installMatch({ scene, bearing = 0, pad = 0, getCrowd, onState }) {
  const root = eventRoot(scene, bearing, pad, 'SPT-01'), actors = figures(root, 23);
  const ball = new THREE.Mesh(new THREE.IcosahedronGeometry(.22, 1), new THREE.MeshBasicMaterial({ color: '#ffffff' })); root.add(ball);
  return playback({ cues: match_cues, sample: t => matchState(match_cues, t), getCrowd, onState,
    draw(state) { actors.draw([...state.players, state.referee]); ball.position.set(...state.ball.position); ball.rotation.set(state.ball.phase, 0, state.ball.phase * .5); },
    dispose: () => release(root) });
}
