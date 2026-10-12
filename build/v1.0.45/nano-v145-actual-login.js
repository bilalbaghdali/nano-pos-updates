/* NANO POS 1.0.45: use the existing modern visual for the login form that
   actually authenticates desktop users. Does not change any credential logic. */
(function (root) {
  'use strict';
  function enhance(overlay) {
    if (!overlay || overlay.id !== 'nanoLocalLoginOverlay' ||
        overlay.classList.contains('nano-v145-modern-login')) return;
    const originalForm = overlay.querySelector('#nanoLoginForm');
    const card = overlay.querySelector('.nano-login-card');
    const template = document.querySelector('#loginOverlay .nano-commerce-visual');
    if (!originalForm || !card || !template || !overlay.querySelector('#nanoLoginUsername') ||
        !overlay.querySelector('#nanoLoginPassword')) return;

    // Keep the original form node: browser-ui.js attaches authentication to it.
    const logo = card.querySelector('.nano-login-logo');
    if (logo) {
      const identity = document.createElement('div');
      identity.className = 'nano-v145-identity';
      const icon = document.createElement('img');
      icon.className = 'nano-v145-brand-icon';
      icon.src = 'assets/branding/nano-pos-icon.png';
      icon.alt = 'NANO POS';
      icon.width = 68;
      icon.height = 68;
      const text = document.createElement('div');
      text.className = 'nano-v145-brand-text';
      const wordmark = document.createElement('strong');
      wordmark.textContent = 'NANO POS';
      const sub = document.createElement('small');
      sub.textContent = 'POINT OF SALE • BUSINESS MANAGEMENT';
      text.append(wordmark, sub);
      identity.append(icon, text);
      logo.replaceWith(identity);
    }

    const buttons = document.createElement('div');
    buttons.className = 'nano-v145-languages';
    for (const code of ['ar','fr','en']) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = code.toUpperCase();
      btn.setAttribute('aria-label', 'Language ' + code.toUpperCase());
      btn.addEventListener('click', () => {
        try {
          if (typeof root.setLanguage === 'function') root.setLanguage(code);
          else if (typeof setLanguage === 'function') setLanguage(code);
        } catch (err) { console.warn('[NANO Login] Could not change language', err); }
      });
      buttons.appendChild(btn);
    }
    const submit = originalForm.querySelector('#nanoLoginSubmitBtn');
    if (submit) submit.parentElement.insertBefore(buttons, submit);
    else originalForm.append(buttons);

    const visual = template.cloneNode(true);
    visual.removeAttribute('aria-hidden');
    const side = document.createElement('div');
    side.className = 'nano-commerce-login-side nano-v145-login-side';
    side.appendChild(card);
    const layout = document.createElement('div');
    layout.className = 'nano-commerce-login-layout nano-v145-login-layout';
    layout.append(visual, side);
    overlay.replaceChildren(layout);
    overlay.classList.add('nano-commerce-login', 'nano-v145-modern-login');
  }
  root.NANO_MODERNIZE_AUTH_LOGIN = enhance;
  if (typeof module !== 'undefined' && module.exports) module.exports = { enhance };
})(typeof window !== 'undefined' ? window : globalThis);