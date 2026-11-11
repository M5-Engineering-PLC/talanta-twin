import * as THREE from 'three/webgpu';
import { match_cues } from './cues.js';
import { matchState } from './match-state.js';
import { eventRoot, release, figures } from './draw.js';
import { playback } from './playback.js';
export { matchState, match_cues };
export function installMatch({ scene, bearing = 0, pad = 0, getCrowd, onState, prototypePlayers = false }) {
  const root = eventRoot(scene, bearing, pad, 'SPT-01');
  const fallback = prototypePlayers ? new THREE.Group() : root;
  if (prototypePlayers) root.add(fallback);
  const actors = figures(fallback, 23);
  let review, disposed = false;
  const ball = new THREE.Mesh(new THREE.IcosahedronGeometry(.22, 1), new THREE.MeshBasicMaterial({ color: '#ffffff' })); root.add(ball);
  const player = playback({ cues: match_cues, sample: t => matchState(match_cues, t), getCrowd, onState,
    draw(state) {
      if (review) review.draw(state);
      else actors.draw([...state.players, state.referee]);
      ball.position.set(...state.ball.position);
      ball.rotation.set(state.ball.phase, 0, state.ball.phase * .5);
    },
    dispose() { disposed = true; review?.dispose(); release(root); },
  });
  if (prototypePlayers) {
    import('./match-review.js').then(({ loadMatchReview }) => {
      if (!disposed) return loadMatchReview(root);
    }).then(instance => {
      if (!instance) return;
      if (disposed) { instance.dispose(); return; }
      review = instance;
      fallback.visible = false;
      player.redraw();
    }).catch(error => {
      if (!disposed) console.warn('Match review models unavailable:', error);
    });
  }
  return player;
}
