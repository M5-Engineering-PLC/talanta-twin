import { crossedReactions } from './state.js';
// Rendering and reaction dispatch share the sampled timeline. No wall-clock timers.
export function playback({ cues, sample, draw, getCrowd = () => null, onState = () => {}, dispose }) {
  let time = 0, previous = -Number.EPSILON, dead = false;
  function render(dispatch = true) {
    const state = sample(time);
    if (dispatch) for (const r of crossedReactions(cues, previous, time)) getCrowd()?.react(r.name, r.params);
    previous = time; draw(state); onState(state); return state;
  }
  render();
  return {
    cues,
    sample,
    update(dt) { if (dead) return; if (!Number.isFinite(dt) || dt < 0) throw new Error('Invalid event delta'); time += dt; return render(); },
    seek(t) { if (!Number.isFinite(t)) throw new Error('Invalid event seek'); time = Math.max(0, t); return render(false); },
    redraw() { if (!dead) return render(false); },
    dispose() { if (dead) return; dead = true; dispose(); },
  };
}
