/* NANO POS v1.0.114 — refined, compact interface-language control. */
(function (root) {
  'use strict';
  const doc = root.document;
  if (!doc || root.NANO_LANGUAGE_SWITCH_114) return;
  root.NANO_LANGUAGE_SWITCH_114 = true;

  const languages = [
    { code: 'ar', label: 'العربية', short: 'AR' },
    { code: 'fr', label: 'Français', short: 'FR' },
    { code: 'en', label: 'English', short: 'EN' }
  ];
  let menu = null;
  let trigger = null;

  const style = doc.createElement('style');
  style.id = 'nanoLanguageSwitch114Style';
  style.textContent = [
    '.nano-language-switch-113{position:relative;display:inline-flex;align-items:center;margin-inline-start:6px;flex:0 0 auto}',
    '.nano-language-switch-113-trigger{appearance:none;display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:36px;padding:0 11px;border:1px solid var(--border-color,#dbe2ea);border-radius:10px;background:var(--card-bg,#fff);color:var(--text-color,#334155);font:inherit;font-size:12px;font-weight:600;line-height:1.2;cursor:pointer;white-space:nowrap;box-shadow:0 1px 2px rgba(15,23,42,.04);transition:background .16s ease,border-color .16s ease,box-shadow .16s ease}',
    '.nano-language-switch-113-trigger:hover{background:var(--hover-bg,#f8fafc);border-color:var(--primary-color,#94a3b8)}',
    '.nano-language-switch-113-trigger[aria-expanded="true"]{border-color:var(--primary-color,#64748b);box-shadow:0 0 0 3px rgba(100,116,139,.12)}',
    '.nano-language-switch-113-trigger:focus-visible,.nano-language-switch-113-option:focus-visible{outline:2px solid var(--primary-color,#64748b);outline-offset:2px}',
    '.nano-language-switch-113-globe{width:16px;height:16px;display:block;flex:0 0 auto;color:currentColor}',
    '.nano-language-switch-113-caption{font:inherit;max-width:100px;overflow:hidden;text-overflow:ellipsis}',
    '.nano-language-switch-113-code{font:700 10px/1 Arial,sans-serif;letter-spacing:.04em;color:var(--muted-color,#64748b);padding-inline-start:7px;border-inline-start:1px solid var(--border-color,#e2e8f0)}',
    '.nano-language-switch-113-chevron{width:12px;height:12px;display:block;flex:0 0 auto;opacity:.65;transition:transform .16s ease}',
    '.nano-language-switch-113-trigger[aria-expanded="true"] .nano-language-switch-113-chevron{transform:rotate(180deg)}',
    '.nano-language-switch-113-menu{position:absolute;top:calc(100% + 6px);inset-inline-end:0;z-index:100005;min-width:176px;padding:5px;background:var(--card-bg,#fff);border:1px solid var(--border-color,#e2e8f0);border-radius:12px;box-shadow:0 10px 28px rgba(15,23,42,.14);display:grid;gap:3px;direction:inherit}',
    '.nano-language-switch-113-option{appearance:none;display:flex;align-items:center;justify-content:space-between;gap:14px;width:100%;min-height:38px;padding:9px 11px;border:0;border-radius:8px;background:transparent;color:var(--text-color,#334155);text-align:start;font:inherit;font-size:13px;font-weight:500;line-height:1.3;cursor:pointer}',
    '.nano-language-switch-113-option:hover{background:var(--hover-bg,#f1f5f9)}',
    '.nano-language-switch-113-option[aria-checked="true"]{background:var(--active-bg,#eff6ff);color:var(--primary-color,#1d4ed8);font-weight:700}',
    '.nano-language-switch-113-check{width:14px;height:14px;opacity:0;color:currentColor}',
    '.nano-language-switch-113-option[aria-checked="true"] .nano-language-switch-113-check{opacity:1}',
    '@media(max-width:600px){.nano-language-switch-113{margin-inline-start:4px}.nano-language-switch-113-trigger{min-height:34px;gap:6px;padding:0 8px;border-radius:9px}.nano-language-switch-113-caption{max-width:66px}.nano-language-switch-113-code{display:none}.nano-language-switch-113-menu{min-width:168px}}',
    '@media(prefers-reduced-motion:reduce){.nano-language-switch-113-trigger,.nano-language-switch-113-chevron{transition:none}}'
  ].join('\n');

  function svg(markup, className) {
    const holder = doc.createElement('span');
    holder.innerHTML = markup;
    const node = holder.firstElementChild;
    if (className) node.setAttribute('class', className);
    node.setAttribute('aria-hidden', 'true');
    return node;
  }
  const globeSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"></path></svg>';
  const chevronSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"></path></svg>';
  const checkSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 4 4L19 6"></path></svg>';

  function currentCode() {
    const code = String(root.currentLanguage || doc.getElementById('settLanguage')?.value || doc.documentElement.lang || 'ar').toLowerCase().slice(0, 2);
    return languages.some(x => x.code === code) ? code : 'ar';
  }
  function updateTrigger() {
    if (!trigger) return;
    const lang = languages.find(x => x.code === currentCode()) || languages[0];
    const caption = trigger.querySelector('.nano-language-switch-113-caption');
    const code = trigger.querySelector('.nano-language-switch-113-code');
    if (caption) caption.textContent = lang.label;
    if (code) code.textContent = lang.short;
    trigger.setAttribute('aria-label', 'لغة البرنامج: ' + lang.label + ' — تغيير اللغة');
    trigger.setAttribute('title', 'لغة البرنامج: ' + lang.label);
    if (menu) menu.querySelectorAll('.nano-language-switch-113-option').forEach(option => {
      const selected = option.dataset.language === lang.code;
      option.setAttribute('aria-checked', String(selected));
    });
  }
  function closeMenu(restoreFocus) {
    if (menu) menu.remove();
    menu = null;
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    if (restoreFocus && trigger) trigger.focus();
  }
  async function chooseLanguage(code) {
    const select = doc.getElementById('settLanguage');
    const setter = root.setLanguage;
    if (!languages.some(x => x.code === code) || typeof setter !== 'function') return;
    closeMenu(false);
    try {
      if (select) select.value = code;
      await setter(code);
      if (typeof root.saveShopSettings === 'function') await root.saveShopSettings();
      else if (select) select.dispatchEvent(new Event('change', { bubbles: true }));
      updateTrigger();
      if (trigger) trigger.focus();
    } catch (error) {
      console.error('[NANO POS] Could not persist interface language:', error);
    }
  }
  function openMenu() {
    if (menu) { closeMenu(false); return; }
    menu = doc.createElement('div');
    menu.className = 'nano-language-switch-113-menu';
    menu.setAttribute('role', 'menu');
    menu.setAttribute('aria-label', 'لغة البرنامج / Interface language');
    const active = currentCode();
    for (const language of languages) {
      const option = doc.createElement('button');
      option.type = 'button';
      option.className = 'nano-language-switch-113-option';
      option.dataset.language = language.code;
      option.setAttribute('role', 'menuitemradio');
      option.setAttribute('aria-checked', String(active === language.code));
      const name = doc.createElement('span');
      name.textContent = language.label;
      const code = doc.createElement('span');
      code.textContent = language.short;
      code.setAttribute('aria-hidden', 'true');
      code.style.cssText = 'font:700 10px Arial,sans-serif;letter-spacing:.04em;opacity:.7;margin-inline-start:auto';
      const check = svg(checkSvg, 'nano-language-switch-113-check');
      option.append(name, code, check);
      option.addEventListener('click', () => chooseLanguage(language.code));
      menu.append(option);
    }
    trigger.parentElement.append(menu);
    trigger.setAttribute('aria-expanded', 'true');
    menu.querySelector('button')?.focus();
  }
  function init() {
    if (doc.getElementById('nanoLanguageSwitch113')) return;
    const anchor = doc.getElementById('notificationToggle');
    if (!anchor || !anchor.parentElement) return;
    if (!doc.getElementById('nanoLanguageSwitch114Style')) doc.head.append(style);
    const wrapper = doc.createElement('div');
    wrapper.className = 'nano-language-switch-113';
    trigger = doc.createElement('button');
    trigger.id = 'nanoLanguageSwitch113';
    trigger.type = 'button';
    trigger.className = 'nano-language-switch-113-trigger';
    trigger.append(
      svg(globeSvg, 'nano-language-switch-113-globe'),
      (() => { const n = doc.createElement('span'); n.className = 'nano-language-switch-113-caption'; return n; })(),
      (() => { const n = doc.createElement('span'); n.className = 'nano-language-switch-113-code'; return n; })(),
      svg(chevronSvg, 'nano-language-switch-113-chevron')
    );
    trigger.setAttribute('aria-haspopup', 'menu');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.addEventListener('click', openMenu);
    wrapper.append(trigger);
    anchor.insertAdjacentElement('afterend', wrapper);
    doc.addEventListener('click', event => {
      if (menu && !wrapper.contains(event.target)) closeMenu(false);
    });
    doc.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu) closeMenu(true);
    });
    updateTrigger();
    // Keep the displayed language in sync if the user changes it in Settings.
    const select = doc.getElementById('settLanguage');
    if (select) select.addEventListener('change', updateTrigger);
    const observer = new MutationObserver(updateTrigger);
    observer.observe(doc.documentElement, { attributes: true, attributeFilter: ['lang', 'dir'] });
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})(typeof window !== 'undefined' ? window : globalThis);
