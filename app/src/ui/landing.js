const storageKey = 'talanta-interface-mode';
// Backdrop stills rendered in Cycles from the twin model (blender/renders/hero_artistic_04, cameras L06 and L07, approved
// by Munene 2026-10-24), shown while the landing view and time match them, as in the landing mockups (06 Hillside at
// sunset 18:05, 07 Cityside by day 10:30). Phones held upright get a 9:16 crop of the same still.
const STILLS = {
  lead06: { src: 'landing/hillside_sunset.jpg', portrait: 'landing/hillside_sunset_portrait.jpg', minutes: 1085 },
  lead07: { src: 'landing/cityside_daylight.jpg', portrait: 'landing/cityside_daylight_portrait.jpg', minutes: 630 },
};
const portrait = globalThis.matchMedia?.('(max-aspect-ratio: 3/4)');
// The stills show illustrative people, cars and event lighting (hero_artistic_04 README); the claim says so.
const STILL_CLAIM = 'Rendered from the twin model · Visualization: people, vehicles and lighting are illustrative';

export function initLanding({ views, focus, state, stopTour, setTime, setEvent, startTour }) {
  const $ = (id) => document.getElementById(id);
  const view = $('landing-view');
  const time = $('landing-time');
  const event = $('landing-event');
  const toggle = $('landing-toggle');
  const names = { lead06: 'Hillside', lead07: 'Cityside' };
  for (const entry of views) view.add(new Option(names[entry.id] ?? entry.name, entry.id));
  view.value = views.some((v) => v.id === 'lead07') ? 'lead07' : 'overview';
  const still = $('landing-still'), claim = $('landing-claim');
  let touring = false;
  still.onload = () => { still.hidden = false; refreshStill(); };
  still.onerror = () => { still.hidden = true; refreshStill(); };
  portrait?.addEventListener?.('change', () => refreshStill());
  function refreshStill() {
    const s = STILLS[view.value];
    const want = mode === 'landing' && !touring && s && Number(time.value) === s.minutes && event.value === 'venue';
    const file = s && (portrait?.matches ? s.portrait : s.src);
    if (want && !still.src.endsWith(file)) { still.hidden = true; still.src = `${import.meta.env.BASE_URL}${file}`; }
    const on = Boolean(want && !still.hidden && still.complete && still.naturalWidth);
    document.body.classList.toggle('landing-still', on);
    claim.textContent = on ? STILL_CLAIM : 'Visualization';
  }
  function matchStillTime() {
    const s = STILLS[view.value];
    if (mode === 'landing' && s) { time.value = String(s.minutes); setTime(s.minutes); }
  }
  view.onchange = () => { stopTour(); touring = false; focus(view.value); matchStillTime(); refreshStill(); };
  time.onchange = () => { touring = false; setTime(Number(time.value)); refreshStill(); };
  // The weather card lives in the full interface, so Weather opens it there.
  event.onchange = () => { stopTour(); setEvent(event.value); if (event.value === 'weather') apply('full'); refreshStill(); };
  $('landing-tour').onclick = () => { touring = true; refreshStill(); startTour(); };
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
      touring = false;
    }
    refreshStill();
  }
  toggle.onclick = () => apply(mode === 'landing' ? 'full' : 'landing');
  if (mode === 'landing') {
    setTime(STILLS[view.value]?.minutes ?? 450);
    focus(view.value, 1);
  }
  apply(mode);
}
