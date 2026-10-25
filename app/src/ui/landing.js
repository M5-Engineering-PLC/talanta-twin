const storageKey = 'talanta-interface-mode';
// Backdrop stills rendered in Cycles from the twin model (blender/renders/hero_artistic_04, cameras L06 and L07, approved
// by Munene 2026-10-24), shown while the landing view and time match them, as in the landing mockups (06 Hillside at
// sunset 18:05, 07 Cityside by day 10:30). Phones held upright get a 9:16 crop of the same still.
export const STILLS = {
  // Pillow match at 180 x 320: residual mean absolute RGB 0.963/255 (JPEG/resampling).
  lead06: { src: 'landing/hillside_sunset.jpg', portrait: 'landing/hillside_sunset_portrait.jpg', minutes: 1085, crop: { x: 695, y: 0, width: 607, height: 1080, imageAspect: 9 / 16 } },
  // Pillow match at 180 x 320: residual mean absolute RGB 1.045/255 (JPEG/resampling).
  lead07: { src: 'landing/cityside_daylight.jpg', portrait: 'landing/cityside_daylight_portrait.jpg', minutes: 630, crop: { x: 820, y: 0, width: 607, height: 1080, imageAspect: 9 / 16 } },
};
export const portrait = globalThis.matchMedia?.('(max-aspect-ratio: 3/4)');
// The stills show illustrative people, cars and event lighting (hero_artistic_04 README); the claim says so.
const STILL_CLAIM = 'Rendered from the twin model · Visualization: people, vehicles and lighting are illustrative';

export function initLanding({ views, focus, state, stopTour, setTime, setEvent, startTour, stills }) {
  const $ = (id) => document.getElementById(id);
  const view = $('landing-view');
  const time = $('landing-time');
  const event = $('landing-event');
  const toggle = $('landing-toggle');
  const names = { lead06: 'Hillside', lead07: 'Cityside' };
  for (const entry of views) view.add(new Option(names[entry.id] ?? entry.name, entry.id));
  view.value = views.some((v) => v.id === 'lead07') ? 'lead07' : 'overview';
  view.onchange = () => { stopTour(); focus(view.value); };
  time.onchange = () => { stills.dismiss(); setTime(Number(time.value)); };
  // The weather card lives in the full interface, so Weather opens it there.
  event.onchange = () => { stills.dismiss(); stopTour(); setEvent(event.value); if (event.value === 'weather') apply('full'); };
  $('landing-tour').onclick = () => { stills.dismiss(); startTour(); };
  let mode = 'landing';
  try { if (localStorage.getItem(storageKey) === 'full') mode = 'full'; } catch { /* Storage can be disabled. */ }
  if (new URLSearchParams(location.search).get('mode') === 'full') mode = 'full';
  function apply(next) {
    mode = next;
    const landing = mode === 'landing';
    document.body.classList.toggle('landing-mode', landing);
    toggle.textContent = landing ? 'Explore the twin' : 'Back to landing';
    toggle.setAttribute('aria-pressed', String(!landing));
    try { localStorage.setItem(storageKey, mode); } catch { /* Storage can be disabled. */ }
    if (landing) {
      const selected = document.querySelector('#modes button.on');
      event.value = selected?.dataset.mode ?? 'venue';
      // Keep the actual scene time visible when the full timeline uses another minute.
      for (const option of [...time.options]) if (option.dataset.custom) option.remove();
      time.value = String(state.minutes);
      if (!time.value) {
        const minutes = Math.floor(state.minutes);
        const label = `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`;
        const option = new Option(label, String(state.minutes), false, true);
        option.dataset.custom = 'true'; time.add(option);
      }
    }
    stills.dismiss();
  }
  toggle.onclick = () => apply(mode === 'landing' ? 'full' : 'landing');
  apply(mode);
  if (mode === 'landing') focus(view.value, 1);
  return { sync(id, minutes) { view.value = id; time.value = String(minutes); } };
}

/** Own the shared poster image after tier 0. Pending decode never revives a dismissed still. */
export function createViewStills({ onTime, onProjection, onRelease, allowed = () => true }) {
  const image = document.getElementById('landing-still');
  const claim = document.getElementById('landing-claim');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let selected = null, arrived = false, generation = 0, timer;
  function dismiss() {
    // Pointer and touch events can describe the same gesture. Keep the original fade timer.
    if (!selected && !arrived && timer) return;
    generation++; selected = null; arrived = false;
    clearTimeout(timer);
    const visible = document.body.classList.contains('cycles-still') || document.body.classList.contains('landing-still');
    image.style.transitionDuration = reduced.matches ? '0s' : '0.3s';
    document.body.classList.remove('cycles-still', 'landing-still');
    const release = () => {
      document.body.classList.remove('cycles-still-claim');
      timer = null; claim.textContent = 'Visualization'; onRelease();
    };
    if (visible && !reduced.matches) timer = setTimeout(release, 300);
    else release();
  }
  function select(id) {
    dismiss(); clearTimeout(timer); timer = null;
    document.body.classList.remove('cycles-still-claim');
    claim.textContent = 'Visualization'; onRelease();
    selected = STILLS[id] ? id : null;
  }
  async function show() {
    const id = selected, data = STILLS[id], token = ++generation;
    if (!data || !arrived || !allowed()) return;
    const file = portrait?.matches ? data.portrait : data.src;
    image.hidden = false;
    if (!image.src.endsWith(file)) image.src = `${(import.meta.env?.BASE_URL ?? './')}${file}`;
    try { await image.decode(); } catch { return; }
    if (token !== generation || selected !== id || !allowed()) return;
    image.style.transitionDuration = reduced.matches ? '0s' : '0.6s';
    claim.textContent = STILL_CLAIM;
    document.body.classList.add('cycles-still', 'cycles-still-claim');
  }
  portrait?.addEventListener('change', () => {
    if (selected && arrived) { onProjection(selected); void show(); }
  });
  for (const type of ['pointerdown', 'wheel', 'touchstart', 'keydown']) {
    window.addEventListener(type, dismiss, { capture: true, passive: true });
  }
  // The opening poster already uses this image. Release it when the live app takes over.
  dismiss();
  return { dismiss, select, get selected() { return selected; },
    arrive() {
      if (!selected || !allowed()) return;
      arrived = true; onTime(STILLS[selected].minutes, selected); onProjection(selected); void show();
    } };
}
