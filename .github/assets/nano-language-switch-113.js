/* NANO POS v1.0.113 — replace the operations/financial shortcut buttons with a global language switch. */
(function (root) {
  'use strict';
  const doc = root.document;
  if (!doc || root.NANO_LANGUAGE_SWITCH_113) return;
  root.NANO_LANGUAGE_SWITCH_113 = true;
  const languages = [
    { code: 'ar', label: 'العربية', short: 'AR' },
    { code: 'fr', label: 'Français', short: 'FR' },
    { code: 'en', label: 'English', short: 'EN' }
  ];
  let menu = null;
  const style = doc.createElement('style');
  style.id = 'nanoLanguageSwitch113Style';
  style.textContent = [
    '.nano-language-switch-113{position:relative;display:inline-flex;align-items:center;margin-inline-start:8px}',
    '.nano-language-switch-113-trigger{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:1px solid #c7d2fe;background:#eef2ff;color:#3730a3;border-radius:11px;padding:8px 12px;min-height:36px;font:700 12px Arial,sans-serif;cursor:pointer;white-space:nowrap;box-shadow:0 1px 2px #0f172a0d}',
    '.nano-language-switch-113-trigger:hover{background:#e0e7ff}',
    '.nano-language-switch-113-menu{position:absolute;top:calc(100% + 7px);inset-inline-end:0;z-index:100005;min-width:150px;padding:6px;background:#fff;border:1px solid #dbe3f0;border-radius:12px;box-shadow:0 12px 30px #0f172a26;display:grid;gap:4px;direction:inherit}',
    '.nano-language-switch-113-option{display:flex;align-items:center;justify-content:space-between;gap:12px;width:100%;border:0;border-radius:8px;background:#fff;color:#1e293b;padding:10px 11px;text-align:start;font:700 12px Arial,sans-serif;cursor:pointer}',
    '.nano-language-switch-113-option:hover,.nano-language-switch-113-option[aria-checked="true"]{background:#eef2ff;color:#3730a3}',
    '.nano-language-switch-113-option:focus-visible,.nano-language-switch-113-trigger:focus-visible{outline:3px solid #2563eb;outline-offset:2px}',
    '@media(max-width:600px){.nano-language-switch-113-trigger{padding:8px 9px}.nano-language-switch-113-caption{display:none}.nano-language-switch-113-menu{position:fixed;top:auto;inset-inline:12px;bottom:12px;min-width:0}}'
  ].join('\n');
  function closeMenu() { if (menu) menu.remove(); menu = null; }
  async function chooseLanguage(code, button) {
    const select = doc.getElementById('settLanguage');
    const setter = root.setLanguage;
    if (!languages.some(x => x.code === code) || typeof setter !== 'function') return;
    closeMenu();
    try {
      if (select) select.value = code;
      await setter(code);
      // Persist through the existing settings path; print language remains independent.
      if (typeof root.saveShopSettings === 'function') await root.saveShopSettings();
      else if (select) select.dispatchEvent(new Event('change', { bubbles: true }));
      button.setAttribute('aria-expanded', 'false');
      button.focus();
    } catch (error) {
      console.error('[NANO POS] Could not persist interface language:', error);
    }
  }
  function openMenu(button) {
    if (menu) { closeMenu(); button.setAttribute('aria-expanded', 'false'); return; }
    menu = doc.createElement('div');
    menu.className = 'nano-language-switch-113-menu';
    menu.setAttribute('role', 'menu');
    menu.setAttribute('aria-label', 'لغة البرنامج / Interface language');
    const active = String(root.currentLanguage || doc.documentElement.lang || 'ar');
    for (const language of languages) {
      const option = doc.createElement('button');
      option.type = 'button';
      option.className = 'nano-language-switch-113-option';
      option.setAttribute('role', 'menuitemradio');
      option.setAttribute('aria-checked', String(active === language.code));
      const name = doc.createElement('span'); name.textContent = language.label;
      const code = doc.createElement('span'); code.textContent = language.short; code.setAttribute('aria-hidden', 'true');
      option.append(name, code);
      option.addEventListener('click', () => chooseLanguage(language.code, button));
      menu.append(option);
    }
    button.parentElement.append(menu);
    button.setAttribute('aria-expanded', 'true');
    menu.querySelector('button')?.focus();
  }
  function init() {
    if (doc.getElementById('nanoLanguageSwitch113')) return;
    const anchor = doc.getElementById('notificationToggle');
    if (!anchor || !anchor.parentElement) return;
    if (!doc.getElementById('nanoLanguageSwitch113Style')) doc.head.append(style);
    const wrapper = doc.createElement('div');
    wrapper.className = 'nano-language-switch-113';
    const button = doc.createElement('button');
    button.id = 'nanoLanguageSwitch113';
    button.type = 'button';
    button.className = 'nano-language-switch-113-trigger';
    button.innerHTML = '<span aria-hidden="true">🌐</span><span class="nano-language-switch-113-caption">لغة البرنامج / Language</span>';
    button.setAttribute('aria-haspopup', 'menu');
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('title', 'تغيير لغة البرنامج / Change interface language');
    button.addEventListener('click', () => openMenu(button));
    wrapper.append(button);
    anchor.insertAdjacentElement('afterend', wrapper);
    doc.addEventListener('click', event => {
      if (menu && !wrapper.contains(event.target)) {
        closeMenu(); button.setAttribute('aria-expanded', 'false');
      }
    });
    doc.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu) {
        closeMenu(); button.setAttribute('aria-expanded', 'false'); button.focus();
      }
    });
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})(typeof window !== 'undefined' ? window : globalThis);
