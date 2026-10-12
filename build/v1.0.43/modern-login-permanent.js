/* NANO POS v1.0.43: retain the existing modern login DOM through late UI initialization.
   Never change credentials, login submission, licensing state, or the hidden state. */
(function preserveModernLogin() {
  'use strict';
  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  if (window.__nanoModernLoginPermanent143) return;
  window.__nanoModernLoginPermanent143 = true;

  function start() {
    const login = document.getElementById('loginOverlay');
    if (!login) return;
    const layout = login.querySelector(':scope > .nano-commerce-login-layout');
    const backdrop = login.querySelector(':scope > .nano-commerce-login-backdrop');
    const form = layout?.querySelector('#loginForm');
    if (!layout || !form || !form.querySelector('#loginUsername') ||
        !form.querySelector('#loginPassword')) return;
    let restoring = false;
    const isVisible = node => node && !node.classList.contains('hidden') &&
      window.getComputedStyle(node).display !== 'none';
    const reconcile = () => {
      if (restoring) return;
      let current = document.getElementById('loginOverlay');
      if (!current || !isVisible(current)) return;
      const rootChanged = current !== login;
      const layoutChanged = !current.contains(layout);
      const needsClass = !current.classList.contains('nano-commerce-login');
      if (!rootChanged && !layoutChanged && !needsClass) return;
      restoring = true;
      try {
        if (rootChanged) {
          // Keep the *original* form and its listeners, not a recreated form.
          current.replaceWith(login);
          login.classList.remove('hidden');
          current = login;
        }
        if (!current.classList.contains('nano-commerce-login'))
          current.classList.add('nano-commerce-login');
        if (!current.contains(layout)) {
          const values = {
            username: form.querySelector('#loginUsername')?.value || '',
            password: form.querySelector('#loginPassword')?.value || ''
          };
          current.replaceChildren();
          if (backdrop) current.appendChild(backdrop);
          current.appendChild(layout);
          const username = form.querySelector('#loginUsername');
          const password = form.querySelector('#loginPassword');
          if (username && username.value !== values.username) username.value = values.username;
          if (password && password.value !== values.password) password.value = values.password;
        }
      } finally { restoring = false; }
    };
    const attrs = {attributes:true,attributeFilter:['class','style'],childList:true};
    new MutationObserver(reconcile).observe(login,attrs);
    // An explicit new/simple overlay with the same ID cannot displace the chosen form.
    if (login.parentNode) new MutationObserver(reconcile).observe(login.parentNode,{childList:true});
    reconcile();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',start,{once:true});
  else start();
})();