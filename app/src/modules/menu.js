// Registry data stays separate from the DOM and the available app actions.
export function buildMenuModel(modules, actions = {}) {
  const groups = ['A', 'B', 'C', 'other'].map(phase => ({ phase, entries: [] }));
  for (const module of modules) {
    if (module.id.startsWith('SEC-')) continue;
    const phase = ['A', 'B', 'C'].includes(module.phase) ? module.phase : 'other';
    const run = ['done', 'partial'].includes(module.status) && Object.hasOwn(actions, module.action)
      && typeof actions[module.action] === 'function' ? actions[module.action] : null;
    groups.find(group => group.phase === phase).entries.push({
      id: module.id, name: module.name, claim: module.claim, status: module.status,
      action: run ? module.action : null, run, disabled: !run,
      label: module.status === 'planned' ? 'Planned' : run ? module.status === 'done' ? 'Done' : 'Partial' : 'Unavailable',
    });
  }
  return groups;
}

export function renderMenu({ button, panel, list, claim }, model) {
  const doc = panel.ownerDocument;
  function close() {
    panel.hidden = true; button.setAttribute('aria-expanded', 'false'); button.focus();
  }
  function showClaim(entries) {
    claim.textContent = [...new Set(entries.map(entry => entry.claim))].join(' ');
    claim.hidden = !claim.textContent;
  }
  list.replaceChildren();
  for (const group of model) {
    if (!group.entries.length) continue;
    const section = doc.createElement('section'), title = doc.createElement('h3');
    title.textContent = group.phase === 'other' ? 'Other modules' : `Phase ${group.phase}`;
    section.append(title);
    for (const entry of group.entries) {
      const row = doc.createElement('button'); row.type = 'button'; row.className = 'module-entry';
      row.dataset.module = entry.id; row.disabled = entry.disabled;
      const name = doc.createElement('span'), status = doc.createElement('span'), label = doc.createElement('small');
      name.textContent = entry.name; status.textContent = entry.label; status.className = 'module-status';
      label.textContent = entry.claim; label.className = 'module-claim';
      row.append(name, status, label);
      row.onclick = () => {
        if (entry.disabled) return;
        close(); showClaim([entry]); entry.run();
      };
      section.append(row);
    }
    list.append(section);
  }
  button.onclick = () => {
    if (!panel.hidden) return close();
    panel.hidden = false; button.setAttribute('aria-expanded', 'true'); panel.querySelector('[data-close]').focus();
  };
  panel.querySelector('[data-close]').onclick = close;
  // Prevent scene shortcuts while the user reads the panel or moves between buttons.
  panel.addEventListener('keydown', event => { if (event.key !== 'Escape') event.stopPropagation(); });
  doc.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) { event.preventDefault(); close(); }
  });
  return { close, showClaim };
}
