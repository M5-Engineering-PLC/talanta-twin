import { buildMenu } from '../modules/menu.js';

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

/**
 * Modules panel: a native <dialog> opened by every [data-modules] button. Escape closes it (native cancel, plus a
 * keydown guard for browsers that ignore a repeated Escape). Selecting an entry closes the panel, then runs its action.
 */
export function initModulesMenu({ modules, run }) {
  const groups = buildMenu(modules);
  const dialog = document.createElement('dialog');
  dialog.id = 'modules-panel';
  dialog.setAttribute('aria-labelledby', 'modules-title');
  dialog.innerHTML = `<div class="mm-head"><h2 id="modules-title">Modules</h2>
    <button type="button" class="mm-close" aria-label="Close modules">✕</button></div>
    ${groups.map((g, gi) => `<section aria-labelledby="mm-g${gi}"><h3 id="mm-g${gi}">${esc(g.title)}</h3><ul>${g.items.map((i) => {
      const body = `<span class="mm-row"><span class="mm-name">${esc(i.name)}</span><span class="mm-status mm-${i.planned ? 'planned' : i.status}">${esc(i.label)}</span></span>`
        + `<small class="mm-claim">Claim: ${esc(i.claim)}</small>`;
      if (i.enabled) return `<li><button type="button" class="mm-item" data-module="${esc(i.id)}">${body}</button></li>`;
      if (i.planned) return `<li><button type="button" class="mm-item" disabled aria-disabled="true">${body}</button></li>`;
      return `<li><div class="mm-item mm-static">${body}<small class="mm-note">Part of the scene</small></div></li>`;
    }).join('')}</ul></section>`).join('')}`;
  document.body.append(dialog);

  const byId = new Map(groups.flatMap((g) => g.items).map((i) => [i.id, i]));
  const close = () => { if (dialog.open) dialog.close(); };
  dialog.querySelector('.mm-close').onclick = close;
  dialog.addEventListener('keydown', (e) => { if (e.key === 'Escape') { e.preventDefault(); close(); } });
  // A click on the backdrop (the dialog box itself, outside its content) closes it.
  dialog.addEventListener('click', (e) => {
    if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) close(); }
    const button = e.target.closest('button[data-module]'); if (!button || button.disabled) return;
    const item = byId.get(button.dataset.module); close();
    if (item?.action) run(item.action, item);
  });
  for (const opener of document.querySelectorAll('[data-modules]')) {
    opener.setAttribute('aria-haspopup', 'dialog');
    opener.onclick = () => { if (dialog.open) close(); else dialog.showModal(); };
  }
  return { dialog, open: () => dialog.showModal(), close };
}
