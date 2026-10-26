import { concert_cues, EVENT_FRAME } from './cues.js';
import { cueAt, reactionsAt, seeded } from './state.js';
export function concertBudget(tier = 'high', width = 1024) {
  const base = { high: { crowd: 2400, heads: 16 }, medium: { crowd: 900, heads: 12 }, low: { crowd: 300, heads: 8 } }[tier] ?? { crowd: 300, heads: 8 };
  return { crowd: width < 768 ? Math.floor(base.crowd / 2) : base.crowd, heads: width < 768 ? 8 : base.heads, lights: 0 };
}
export function concertState(cues = concert_cues, t = 0, budget = concertBudget()) {
  const { time, duration, cue, progress } = cueAt(cues, t);
  const beat = time * cue.params.bpm / 60, pulse = .25 + .75 * Math.exp(-6 * (beat % 1));
  const energy = cue.params.energy * (cue.params.mode === 'outro' ? 1 - progress : 1);
  const lights = Array.from({ length: budget.heads }, (_, i) => ({
    position: [-16 + 32 * i / Math.max(1, budget.heads - 1), 10, 44],
    target: [Math.sin(beat * .45 + i * .7) * 27, 1, 6 + Math.cos(beat * .3 + i) * 25],
    color: cue.params.color.slice(), intensity: energy * pulse,
    phase: (beat + i / budget.heads) % 1,
  }));
  const crowd = Array.from({ length: budget.crowd }, (_, i) => {
    const phase = seeded(i) * Math.PI * 2;
    return { position: [(seeded(i, 89) - .5) * 58, .12 + Math.max(0, Math.sin(beat * Math.PI * 2 + phase)) * energy * .12, -42 + seeded(i, 991) * 76],
      heading: 0, phase: beat * Math.PI * 2 + phase, color: i % 3 === 0 ? '#b92332' : i % 3 === 1 ? '#18733d' : '#d4c9c5' };
  });
  return { module: 'EVT-01', frame: EVENT_FRAME, time, duration, phase: cue.params.mode, beat, pulse,
    stage: { position: [0, .12, 46], size: [36, 1.5, 10], heading: Math.PI },
    truss: { position: [0, 10, 46], width: 36, height: 10, depth: 6 },
    screens: [-1, 0, 1].map(i => ({ position: [i * 13, 6.5, 48], size: [i ? 7 : 12, i ? 5 : 6, .35],
      color: cue.params.color.map((v, k) => v * (i === 0 ? 1 : k === 0 ? .65 : .85)), intensity: .1 + energy * pulse * 2 })),
    crowd, lights, crowdReactions: reactionsAt(cues, time), phones: true };
}
