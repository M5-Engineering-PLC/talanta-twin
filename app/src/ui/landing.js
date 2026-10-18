const storageKey = 'talanta-interface-mode';

export function initLanding({ views, focus, state, stopTour, setTime, setEvent, startTour }) {
  const $ = (id) => document.getElementById(id);
  const view = $('landing-view');
  const time = $('landing-time');
  const event = $('landing-event');
  const toggle = $('landing-toggle');
  const names = { lead06: 'Hillside', lead07: 'Cityside' };
  for (const entry of views) view.add(new Option(names[entry.id] ?? entry.name, entry.id));
  view.value = views.some((v) => v.id === 'lead06') ? 'lead06' : 'overview';
  view.onchange = () => { stopTour(); focus(view.value); };
  time.onchange = () => setTime(Number(time.value));
  // The weather card lives in the full interface, so Weather opens it there.
  event.onchange = () => { stopTour(); setEvent(event.value); if (event.value === 'weather') apply('full'); };
  $('landing-tour').onclick = startTour;
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
  }
  toggle.onclick = () => apply(mode === 'landing' ? 'full' : 'landing');
  if (mode === 'landing') {
    setTime(450);
    focus(view.value, 1);
  }
  apply(mode);
}
