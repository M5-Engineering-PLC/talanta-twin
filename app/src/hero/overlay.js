/** Add the selected internal lead render over the stage during Vite development. */
export function initOverlay({ stage, camera, controls }) {
  const id = new URLSearchParams(location.search).get('overlay');
  if (!import.meta.env.DEV || !['06', '07'].includes(id)) return null;

  const file = id === '06' ? '06_lead_ne_to_ngong_hills.jpg' : '07_lead_ssw_to_lavington.jpg';
  const image = document.createElement('img');
  image.alt = `Internal lead render ${id}`;
  image.src = `/@fs${__TALANTA_REPO_ROOT__}/research/concepts/2026-10-17/${file}`;
  Object.assign(image.style, {
    position: 'absolute', inset: '0', width: '100%', height: '100%', objectFit: 'cover',
    opacity: '0.5', pointerEvents: 'none', zIndex: '20',
  });

  const panel = document.createElement('section');
  Object.assign(panel.style, {
    position: 'absolute', zIndex: '22', top: '12px', right: '12px', width: 'min(340px, calc(100% - 24px))',
    boxSizing: 'border-box', padding: '12px', color: '#fff', background: 'rgba(12, 18, 30, .92)',
    border: '1px solid rgba(255,255,255,.24)', borderRadius: '8px', font: '12px/1.4 system-ui, sans-serif',
  });
  const title = document.createElement('div');
  title.textContent = 'Internal reference, not for release';
  title.style.fontWeight = '700';
  title.style.marginBottom = '8px';
  const controlsRow = document.createElement('div');
  Object.assign(controlsRow.style, { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' });
  const opacityLabel = document.createElement('label');
  opacityLabel.textContent = 'Opacity';
  const opacity = document.createElement('input');
  opacity.type = 'range'; opacity.min = '0'; opacity.max = '100'; opacity.value = '50';
  opacity.setAttribute('aria-label', 'Overlay opacity');
  opacity.style.flex = '1';
  opacity.oninput = () => { image.style.opacity = String(Number(opacity.value) / 100); };
  const wipe = document.createElement('button');
  wipe.type = 'button'; wipe.textContent = 'Wipe';
  Object.assign(wipe.style, { color: '#fff', background: '#34445c', border: '1px solid #70809a', borderRadius: '4px', padding: '4px 8px', cursor: 'pointer' });
  controlsRow.append(opacityLabel, opacity, wipe);
  const readout = document.createElement('pre');
  Object.assign(readout.style, { margin: '0 0 8px', whiteSpace: 'pre-wrap', font: '11px/1.45 ui-monospace, monospace' });
  const copy = document.createElement('button');
  copy.type = 'button'; copy.textContent = 'Copy pose';
  Object.assign(copy.style, { color: '#fff', background: '#34445c', border: '1px solid #70809a', borderRadius: '4px', padding: '5px 9px', cursor: 'pointer' });
  panel.append(title, controlsRow, readout, copy);

  const divider = document.createElement('div');
  Object.assign(divider.style, {
    display: 'none', position: 'absolute', zIndex: '21', top: '0', bottom: '0', left: '50%', width: '3px',
    transform: 'translateX(-50%)', background: '#fff', boxShadow: '0 0 5px #000', cursor: 'ew-resize', touchAction: 'none',
  });
  const grip = document.createElement('span');
  grip.textContent = '↔';
  Object.assign(grip.style, { position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', padding: '5px 7px', color: '#111', background: '#fff', borderRadius: '12px', font: '14px system-ui' });
  divider.append(grip);

  let wipeMode = false;
  let wipeAt = 0.5;
  const applyWipe = () => {
    const percent = wipeAt * 100;
    image.style.clipPath = wipeMode ? `inset(0 ${100 - percent}% 0 0)` : 'none';
    divider.style.display = wipeMode ? '' : 'none';
    divider.style.left = `${percent}%`;
  };
  wipe.onclick = () => { wipeMode = !wipeMode; wipe.setAttribute('aria-pressed', String(wipeMode)); applyWipe(); };
  const setWipe = (event) => {
    const rect = stage.getBoundingClientRect();
    wipeAt = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
    applyWipe();
  };
  divider.onpointerdown = (event) => { divider.setPointerCapture(event.pointerId); setWipe(event); };
  divider.onpointermove = (event) => { if (divider.hasPointerCapture(event.pointerId)) setWipe(event); };
  divider.onpointerup = (event) => { if (divider.hasPointerCapture(event.pointerId)) divider.releasePointerCapture(event.pointerId); };

  const pose = () => {
    const position = camera.position;
    const target = controls.target;
    const dx = position.x, dy = position.y, dz = position.z;
    const horizontal = Math.hypot(dx, dz);
    return {
      position: [position.x, position.y, position.z].map((n) => +n.toFixed(3)),
      target: [target.x, target.y, target.z].map((n) => +n.toFixed(3)),
      fov: +camera.fov.toFixed(3),
      heading_deg: +((Math.atan2(dx, -dz) * 180 / Math.PI + 360) % 360).toFixed(2),
      elevation_deg: +(Math.atan2(dy, horizontal) * 180 / Math.PI).toFixed(2),
      distance_m: +Math.hypot(dx, dy, dz).toFixed(3),
    };
  };
  let frame = 0;
  const update = () => {
    const p = pose();
    readout.textContent = `Position: ${p.position.join(', ')}\nTarget: ${p.target.join(', ')}\nFOV: ${p.fov}°\nHeading: ${p.heading_deg}°  Elevation: ${p.elevation_deg}°\nDistance from stadium centre: ${p.distance_m} m`;
    frame = requestAnimationFrame(update);
  };
  copy.onclick = async () => {
    await navigator.clipboard.writeText(JSON.stringify(pose()));
    copy.textContent = 'Copied';
    setTimeout(() => { copy.textContent = 'Copy pose'; }, 1200);
  };

  image.onerror = () => {
    cancelAnimationFrame(frame);
    image.remove(); panel.remove(); divider.remove();
    console.warn(`Internal lead render ${id} is missing or unavailable.`);
  };
  stage.append(image, divider, panel);
  update();
  return () => { cancelAnimationFrame(frame); image.remove(); panel.remove(); divider.remove(); };
}
