export const night_show = [
  { start: 0, duration: 8, module: 'SHW-01', params: { mode: 'sequence' } },
  { start: 8, duration: 50, module: 'SHW-01', params: { mode: 'on' } },
  { start: 8, duration: 36, module: 'SHW-02', params: { mode: 'flag' } },
  { start: 12, duration: 32, module: 'SHW-03', params: {} },
  { start: 44, duration: 14, module: 'SHW-02', params: { mode: 'chase' } },
  { start: 58, duration: 2, module: 'SHW-02', params: { mode: 'rest' } },
];

export class Timeline {
  constructor(cues = night_show) { this.time = 0; this.playing = false; this.loop = false; this.setCues(cues); }
  setCues(cues) {
    this.cues = cues.map((cue, order) => {
      if (!Number.isFinite(cue.start) || cue.start < 0 || !Number.isFinite(cue.duration) || cue.duration <= 0) throw new Error('Invalid cue time');
      return { ...cue, params: { ...cue.params }, order };
    }).sort((a, b) => a.start - b.start || a.order - b.order);
    this.duration = Math.max(0, ...this.cues.map(c => c.start + c.duration));
    this.seek(0); return this;
  }
  play() { this.playing = true; return this; }
  pause() { this.playing = false; return this; }
  seek(seconds) {
    if (!Number.isFinite(seconds)) throw new Error('Invalid seek time');
    this.time = this.loop && this.duration ? ((seconds % this.duration) + this.duration) % this.duration : Math.max(0, Math.min(seconds, this.duration));
    return this.sample();
  }
  sample(time = this.time) {
    return this.cues.filter(c => time >= c.start && time < c.start + c.duration).map(c => ({ ...c, localTime: time - c.start, progress: (time - c.start) / c.duration }));
  }
  update(dt) {
    if (!Number.isFinite(dt) || dt < 0) throw new Error('Invalid delta time');
    if (this.playing) { this.seek(this.time + dt); if (!this.loop && this.time === this.duration) this.pause(); }
    return this.sample();
  }
}
