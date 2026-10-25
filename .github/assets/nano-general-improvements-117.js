/* NANO POS v1.0.117 — wider search and language button matched to toolbar controls. */
(function (root) {
  'use strict';
  const doc = root.document;
  if (!doc || root.NANO_GENERAL_IMPROVEMENTS_117) return;
  root.NANO_GENERAL_IMPROVEMENTS_117 = true;

  const languages = [
    { code: 'ar', label: 'العربية', short: 'AR' },
    { code: 'fr', label: 'Français', short: 'FR' },
    { code: 'en', label: 'English', short: 'EN' }
  ];
  let menu = null, trigger = null, wrapper = null, supportControl = null;

  const style = doc.createElement('style');
  style.id = 'nanoGeneralImprovements117Style';
  style.textContent = [
    '.nano-language-switch-113{position:relative;display:inline-flex;align-items:center;align-self:center;vertical-align:middle;margin:0 4px;flex:0 0 auto;order:initial;line-height:1;white-space:nowrap}',
    '.nano-language-toolbar-row{align-items:center!important}',
    '.nano-language-switch-113-trigger{appearance:none;box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;gap:7px;height:var(--nano-toolbar-control-height,34px);min-height:var(--nano-toolbar-control-height,34px);padding:0 10px;border:1px solid var(--border-color,#dbe2ea);border-radius:9px;background:var(--card-bg,#fff);color:var(--text-color,#334155);font:inherit;font-size:12px;font-weight:600;line-height:1;cursor:pointer;white-space:nowrap}',
    '.nano-language-switch-113-trigger:hover{background:var(--hover-bg,#f8fafc);border-color:var(--primary-color,#94a3b8)}',
    '.nano-language-switch-113-trigger:focus-visible,.nano-language-switch-113-option:focus-visible{outline:2px solid var(--primary-color,#64748b);outline-offset:2px}',
    '.nano-language-switch-113-globe{width:15px;height:15px;display:block;flex:0 0 auto}',
    '.nano-language-switch-113-caption{font:inherit;max-width:112px;overflow:hidden;text-overflow:ellipsis}',
    '.nano-language-switch-113-code{font:700 10px/1 Arial,sans-serif;letter-spacing:.04em;color:var(--muted-color,#64748b);padding-inline-start:6px;border-inline-start:1px solid var(--border-color,#e2e8f0)}',
    '.nano-language-switch-113-chevron{width:11px;height:11px;display:block;flex:0 0 auto;opacity:.65}',
    '.nano-language-switch-113-menu{position:absolute;top:calc(100% + 5px);inset-inline-end:0;z-index:100005;min-width:168px;padding:5px;background:var(--card-bg,#fff);border:1px solid var(--border-color,#e2e8f0);border-radius:11px;box-shadow:0 10px 28px rgba(15,23,42,.14);display:grid;gap:3px;direction:inherit}',
    '.nano-language-switch-113-option{appearance:none;display:flex;align-items:center;gap:10px;width:100%;min-height:36px;padding:8px 10px;border:0;border-radius:8px;background:transparent;color:var(--text-color,#334155);text-align:start;font:inherit;font-size:13px;cursor:pointer}',
    '.nano-language-switch-113-option:hover{background:var(--hover-bg,#f1f5f9)}',
    '.nano-language-switch-113-option[aria-checked="true"]{background:var(--active-bg,#eff6ff);color:var(--primary-color,#1d4ed8);font-weight:700}',
    '.nano-language-switch-113-check{width:13px;height:13px;opacity:0;color:currentColor;margin-inline-start:auto}',
    '.nano-language-switch-113-option[aria-checked="true"] .nano-language-switch-113-check{opacity:1}',
    '.nano-compact-global-search{box-sizing:border-box!important;height:36px!important;min-height:36px!important;max-width:min(420px,38vw)!important;width:min(420px,38vw)!important;padding-block:6px!important;font-size:13px!important;line-height:1.35!important}',
    '.nano-compact-global-search-wrap{box-sizing:border-box!important;max-width:min(460px,44vw)!important;flex:0 1 420px!important;min-width:180px!important}',
    '@media(max-width:600px){.nano-language-switch-113{margin-inline:3px}.nano-language-switch-113-trigger{gap:5px;padding-inline:7px}.nano-language-switch-113-caption{max-width:70px}.nano-language-switch-113-code{display:none}.nano-language-switch-113-menu{min-width:158px}.nano-compact-global-search{max-width:min(240px,48vw)!important;width:min(240px,48vw)!important;height:32px!important;min-height:32px!important}.nano-compact-global-search-wrap{max-width:52vw!important;flex-basis:240px!important;min-width:110px!important}}',
    '@media(prefers-reduced-motion:reduce){.nano-language-switch-113 *{transition:none!important;animation:none!important}}'
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
    if (menu) menu.querySelectorAll('.nano-language-switch-113-option').forEach(option => option.setAttribute('aria-checked', String(option.dataset.language === lang.code)));
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
    } catch (error) { console.error('[NANO POS] Could not persist interface language:', error); }
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
      const name = doc.createElement('span'); name.textContent = language.label;
      const code = doc.createElement('span'); code.textContent = language.short;
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
  function findSupportControl() {
    const candidates = Array.from(doc.querySelectorAll('button,a,[role="button"],input[type="button"],input[type="submit"]'));
    const matches = candidates.map(el => {
      const label = [el.id, typeof el.className === 'string' ? el.className : '', el.getAttribute('aria-label'), el.getAttribute('title'), el.innerText, el.value].filter(Boolean).join(' ').toLowerCase();
      if (!/(اتصال\s*بالدعم|الاتصال\s*بالدعم|اتصل\s*بالدعم|الدعم\s*الفني|مساعدة|contact\s*support|support\s*contact|help\s*desk|technical\s*support)/i.test(label)) return null;
      const inToolbar = !!el.closest('header,[role="banner"],.topbar,.top-bar,.header,.app-header,.navbar,.toolbar,[class*="toolbar"],[class*="header-actions"]');
      const visible = el.getClientRects().length > 0;
      return { el, score: (visible ? 3 : 0) + (inToolbar ? 5 : 0) };
    }).filter(Boolean).sort((a, b) => b.score - a.score);
    return matches.length ? matches[0].el : null;
  }
  function findTopSearch() {
    const candidates = Array.from(doc.querySelectorAll('input[type="search"],input:not([type]),input[type="text"]'));
    const hits = candidates.map(el => {
      const label = [el.id, typeof el.className === 'string' ? el.className : '', el.getAttribute('placeholder'), el.getAttribute('aria-label'), el.getAttribute('title')].filter(Boolean).join(' ').toLowerCase();
      const isSearch = /(search|global|top-search|header-search|بحث|ابحث|recherche)/i.test(label);
      const inHeader = !!el.closest('header,[role="banner"],.topbar,.top-bar,.header,.app-header,.navbar,.toolbar');
      return { el, score: (isSearch ? 4 : 0) + (inHeader ? 5 : 0) + (el.type === 'search' ? 2 : 0) };
    }).filter(x => x.score >= 6).sort((a,b) => b.score-a.score);
    if (!hits.length) return;
    const input = hits[0].el;
    input.classList.add('nano-compact-global-search');
    const wrap = input.closest('.search-container,.search-box,.global-search,.header-search,.top-search,.search-wrapper') || input.parentElement;
    if (wrap) wrap.classList.add('nano-compact-global-search-wrap');
  }
  function findPairingControl() {
    const candidates = Array.from(doc.querySelectorAll('button,a,[role="button"],input[type="button"],input[type="submit"]'));
    return candidates.find(el => {
      const label = [el.id, typeof el.className === 'string' ? el.className : '', el.getAttribute('aria-label'), el.getAttribute('title'), el.innerText, el.value].filter(Boolean).join(' ').toLowerCase();
      return /(اقتران\s*الهاتف|ربط\s*الهاتف|pair\s*(a\s*)?phone|phone\s*pairing|pairing\s*phone|connect\s*phone)/i.test(label);
    }) || null;
  }
  function directChildUnder(node, ancestor) {
    let current = node;
    while (current && current.parentElement !== ancestor) current = current.parentElement;
    return current && current.parentElement === ancestor ? current : null;
  }
  function insertBesideSupport(node, support) {
    if (!support || !support.parentElement) return false;
    const parent = support.parentElement;
    const display = root.getComputedStyle ? root.getComputedStyle(parent).display : '';
    if (display.includes('flex') || display.includes('grid')) {
      support.insertAdjacentElement('afterend', node);
      return true;
    }
    const ancestors = new Set();
    for (let n = support; n; n = n.parentElement) ancestors.add(n);
    let common = node;
    while (common && !ancestors.has(common)) common = common.parentElement;
    if (common) {
      const child = directChildUnder(support, common);
      if (child) { common.insertBefore(node, child.nextSibling); return true; }
    }
    support.insertAdjacentElement('afterend', node);
    return true;
  }
  function syncButtonMetrics() {
    if (!trigger || !wrapper) return;
    const ref = supportControl || findPairingControl() || doc.getElementById('notificationToggle');
    if (!ref || !ref.isConnected || !root.getComputedStyle) return;
    const cs = root.getComputedStyle(ref);
    const rect = ref.getBoundingClientRect();
    const measured = rect.height || Number.parseFloat(cs.height) || Number.parseFloat(cs.minHeight) || 34;
    const height = Math.round(Math.max(30, Math.min(48, measured)));
    wrapper.style.setProperty('--nano-toolbar-control-height', height + 'px');
    trigger.style.height = height + 'px';
    trigger.style.minHeight = height + 'px';
    trigger.style.fontFamily = cs.fontFamily;
    trigger.style.fontSize = cs.fontSize;
    trigger.style.fontWeight = cs.fontWeight;
    trigger.style.lineHeight = cs.lineHeight === 'normal' ? '1' : cs.lineHeight;
    trigger.style.color = cs.color;
    trigger.style.borderRadius = cs.borderRadius;
    for (const side of ['Top','Right','Bottom','Left']) {
      trigger.style['border'+side+'Width'] = cs['border'+side+'Width'];
      trigger.style['border'+side+'Style'] = cs['border'+side+'Style'];
      trigger.style['border'+side+'Color'] = cs['border'+side+'Color'];
    }
    trigger.style.backgroundColor = (cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent') ? cs.backgroundColor : 'var(--card-bg,#fff)';
    trigger.style.boxShadow = cs.boxShadow === 'none' ? 'none' : cs.boxShadow;
  }
  function init() {
    if (doc.getElementById('nanoLanguageSwitch113')) return;
    if (!doc.getElementById('nanoGeneralImprovements117Style')) doc.head.append(style);
    findTopSearch();

    wrapper = doc.createElement('div');
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

    // Prefer the support control; fall back to the existing notification anchor
    // so the language selector remains accessible if a support button is absent.
    supportControl = findSupportControl();
    const anchor = supportControl || findPairingControl() || doc.getElementById('notificationToggle');
    if (anchor && anchor.parentElement) {
      anchor.insertAdjacentElement('afterend', wrapper);
      const parent = anchor.parentElement;
      const parentStyle = root.getComputedStyle ? root.getComputedStyle(parent) : null;
      if (parentStyle && parentStyle.display.includes('flex') && !/column/.test(parentStyle.flexDirection)) parent.classList.add('nano-language-toolbar-row');
    } else {
      const header = doc.querySelector('header,[role="banner"],.topbar,.top-bar,.header,.app-header,.navbar,.toolbar');
      if (header) header.append(wrapper);
    }
    syncButtonMetrics();
    if (supportControl && typeof root.ResizeObserver === 'function') {
      const metricObserver = new root.ResizeObserver(syncButtonMetrics);
      metricObserver.observe(supportControl);
    }
    doc.addEventListener('visibilitychange', () => { if (!doc.hidden) { syncButtonMetrics(); updateTrigger(); } });
    doc.addEventListener('click', event => { if (menu && wrapper && !wrapper.contains(event.target)) closeMenu(false); });
    doc.addEventListener('keydown', event => { if (event.key === 'Escape' && menu) closeMenu(true); });
    updateTrigger();
    const select = doc.getElementById('settLanguage');
    if (select) select.addEventListener('change', updateTrigger);

    // Avoid a whole-document subtree observer: only react to language/direction changes.
    const observer = new MutationObserver(updateTrigger);
    observer.observe(doc.documentElement, { attributes: true, attributeFilter: ['lang', 'dir'] });
  }
  function safeInit() {
    try { init(); } catch (error) { console.warn('[NANO POS] Toolbar refinement skipped:', error); }
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', safeInit, { once: true });
  else safeInit();
})(typeof window !== 'undefined' ? window : globalThis);
