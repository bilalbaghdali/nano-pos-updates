/* NANO POS v1.0.51: visible post-authentication success transition.
 * This module loads before the login handler. Call play() only AFTER loginUser success.
 * Promise resolves after the transition, ensuring the next view does not hide it.
 */
(() => {
  'use strict';
  let node = null;
  let timerHandles = [];
  let frameHandle = null;
  let pendingResolve = null;
  const strings = {
    ar: { checking:'تم التحقق من بيانات الدخول', wait:'جارٍ فتح NANO POS', granted:'تم تسجيل الدخول بنجاح', welcome:'مرحبًا بعودتك', stamp:'تم التحقق' },
    fr: { checking:'Identifiants vérifiés', wait:'Ouverture de NANO POS', granted:'Connexion réussie', welcome:'Bienvenue', stamp:'VÉRIFIÉ' },
    en: { checking:'Credentials verified', wait:'Opening NANO POS', granted:'Access Granted', welcome:'Welcome back', stamp:'VERIFIED' }
  };
  function labels() {
    let value = '';
    try { value = typeof currentLanguage === 'string' ? currentLanguage : ''; } catch (_) {}
    const locale = (value || document.documentElement.lang || 'ar').slice(0,2).toLowerCase();
    return strings[locale] || strings.ar;
  }
  function cleanup() {
    timerHandles.forEach(clearTimeout);
    timerHandles = [];
    if (frameHandle !== null) cancelAnimationFrame(frameHandle);
    frameHandle = null;
    if (node) node.remove();
    node = null;
    if (pendingResolve) { const resolve=pendingResolve; pendingResolve=null; resolve(); }
  }
  function play() {
    cleanup();
    if (!document.body) return Promise.resolve();
    const copy = labels();
    const overlay = document.createElement('div');
    overlay.id = 'nano-auth-success-veil';
    overlay.setAttribute('role','status');
    overlay.setAttribute('aria-live','polite');
    // CSS-protect the overlay from other legacy modal/container styles.
    overlay.style.setProperty('position','fixed','important');
    overlay.style.setProperty('inset','0','important');
    overlay.style.setProperty('z-index','2147483647','important');
    overlay.innerHTML = '<section class="nano-auth-card" data-stage="checking"><h2 class="nano-auth-title"></h2><p class="nano-auth-sub"></p><div class="nano-auth-meter" aria-hidden="true"><svg viewBox="0 0 100 100"><circle class="nano-auth-track" cx="50" cy="50" r="38"/><circle class="nano-auth-progress" cx="50" cy="50" r="38"/></svg><span class="nano-auth-percent">0</span></div><div class="nano-auth-tick" aria-hidden="true">✓</div><span class="nano-auth-stamp"></span></section>';
    const card = overlay.querySelector('.nano-auth-card');
    const title = overlay.querySelector('.nano-auth-title');
    const sub = overlay.querySelector('.nano-auth-sub');
    const ring = overlay.querySelector('.nano-auth-progress');
    const percent = overlay.querySelector('.nano-auth-percent');
    const stamp = overlay.querySelector('.nano-auth-stamp');
    title.textContent = copy.checking; sub.textContent = copy.wait; stamp.textContent = copy.stamp;
    document.body.appendChild(overlay);
    node = overlay;
    const reduced = Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches);
    const duration = reduced ? 90 : 1050;
    const start = performance.now();
    const animation = (now) => {
      if (node !== overlay) return;
      const f = Math.max(0, Math.min(1, (now-start)/duration));
      const easing = 1 - (1-f)**2;
      percent.textContent = String(Math.round(easing*100));
      ring.style.strokeDashoffset = String(239*(1-easing));
      if (f < 1) frameHandle = requestAnimationFrame(animation);
      else frameHandle=null;
    };
    frameHandle=requestAnimationFrame(animation);
    return new Promise(resolve => {
      pendingResolve=resolve;
      timerHandles.push(setTimeout(() => {
        if (node !== overlay) return;
        card.dataset.stage='granted';
        title.textContent=copy.granted;
        sub.textContent=copy.welcome;
      },duration+100));
      timerHandles.push(setTimeout(() => {
        if (node !== overlay) return;
        overlay.classList.add('nano-auth-out');
        timerHandles.push(setTimeout(cleanup,reduced?0:260));
      },duration+1110));
      // Hard stop ensures authentication can never hang due to animation frame failure.
      timerHandles.push(setTimeout(cleanup,3500));
    });
  }
  window.NANOLoginSuccessEffect=Object.freeze({play,clear:cleanup});
  window.addEventListener('beforeunload',cleanup);
})();