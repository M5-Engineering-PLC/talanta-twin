/** Put tier 0 on screen before site data or the renderer starts. */
export function showOpeningPoster() {
  const still = document.getElementById('landing-still');
  const splash = document.getElementById('splash');
  const portrait = globalThis.matchMedia?.('(max-aspect-ratio: 3/4)').matches;
  still.src = `${import.meta.env.BASE_URL}landing/cityside_daylight${portrait ? '_portrait' : ''}.jpg`;
  let resolveView, posterFailed = false, scenePainted = false, resolved = false;
  const ready = new Promise((resolve) => { resolveView = resolve; });
  function shown() {
    if (resolved) return;
    resolved = true;
    // Two frames allow the image to paint. The splash then fades for 600 ms.
    requestAnimationFrame(() => requestAnimationFrame(() => {
      splash.classList.add('done');
      setTimeout(resolveView, 650);
    }));
  }
  const display = async () => {
    try { await still.decode(); } catch { /* onerror handles a missing poster. */ }
    if (!still.naturalWidth) return;
    still.hidden = false;
    document.body.classList.add('landing-still');
    document.getElementById('landing-claim').textContent = 'Rendered from the twin model · Visualization: people, vehicles and lighting are illustrative';
    shown();
  };
  still.addEventListener('load', display, { once: true });
  still.addEventListener('error', () => { posterFailed = true; if (scenePainted) shown(); }, { once: true });
  if (still.complete && still.naturalWidth) void display();
  return { ready, scenePainted() { scenePainted = true; if (posterFailed) shown(); } };
}
