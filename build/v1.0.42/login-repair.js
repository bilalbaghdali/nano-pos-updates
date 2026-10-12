/* NANO POS 1.0.42 — preserve native keyboard input in the login form. */
(function installLoginInputRepair() {
  'use strict';
  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  if (window.__nanoLoginInputRepair142) return;
  window.__nanoLoginInputRepair142 = true;
  const IDS = new Set(['loginUsername', 'loginPassword']);
  const visible = () => {
    const screen = document.getElementById('loginOverlay');
    return Boolean(screen && !screen.classList.contains('hidden') &&
      window.getComputedStyle(screen).display !== 'none');
  };
  const repair = () => {
    if (!visible()) return;
    const login = document.getElementById('loginOverlay');
    // Previous lock-session overlay must not intercept an explicitly shown login.
    const lock = document.getElementById('lockOverlay');
    if (lock && !lock.classList.contains('hidden')) {
      lock.classList.add('hidden');
      lock.style.display = 'none';
    }
    // Repair accidental inherited inert state, without bypassing login itself.
    if (login.hasAttribute('inert')) login.removeAttribute('inert');
    const form = document.getElementById('loginForm');
    if (form && form.hasAttribute('inert')) form.removeAttribute('inert');
    if (!IDS.has(document.activeElement?.id)) {
      const username = document.getElementById('loginUsername');
      if (username && !username.disabled) username.focus({preventScroll:true});
    }
  };
  // Block global keyboard shortcuts from stealing printable keys/Backspace while
  // either login field is active, without preventing native text input or form submit.
  window.addEventListener('keydown', event => {
    if (visible() && IDS.has(event.target?.id)) event.stopImmediatePropagation();
  }, true);
  const observe = () => {
    repair();
    const root = document.getElementById('loginOverlay');
    if (!root || typeof MutationObserver !== 'function') return;
    new MutationObserver(() => repair()).observe(root, {attributes:true,attributeFilter:['class','inert']});
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', observe, {once:true});
  else observe();
  window.addEventListener('load', repair, {once:true});
  window.addEventListener('nano-trial-continue', () => setTimeout(repair, 100));
})();