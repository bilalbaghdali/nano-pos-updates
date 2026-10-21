(() => {
  'use strict';
  // v1.0.93: robust installed-version release notes (replaces invalid old script).
  const FALLBACK_VERSION = '1.0.93';
  const OFFLINE = {
    ar: [
      'إصلاح ظهور «مميزات الإصدار الحالي» بعد معالجة خطأ JavaScript.',
      'عرض المميزات دون إنترنت، وتحديثها من سجل الإصدارات الرسمي عند توفر الاتصال.',
      'عرض رقم الإصدار المثبت ولغة البرنامج الصحيحة مع الحفاظ على البيانات والتفعيل.'
    ],
    fr: [
      'Correction de l’affichage des nouveautés de la version installée et de l’erreur JavaScript.',
      'Affichage des nouveautés hors ligne et mise à jour depuis l’historique officiel.',
      'Version et langue synchronisées sans toucher aux données ni à l’activation.'
    ],
    en: [
      'Fixed the current-version features panel and JavaScript syntax error.',
      'Highlights now work offline and refresh from the official release history online.',
      'Installed version and language are synchronized; store data and activation are preserved.'
    ]
  };
  const TITLES = {
    ar: 'مميزات الإصدار الحالي',
    fr: 'Nouveautés de la version actuelle',
    en: 'Current version highlights'
  };
  const MISSING = {
    ar: 'مميزات هذا الإصدار غير متوفرة حاليًا.',
    fr: 'Les nouveautés de cette version sont indisponibles.',
    en: 'Highlights for this version are currently unavailable.'
  };
  const STORE_KEY = 'nano-release-features-';
  let version = '';
  let features = null;

  const parseVersion = value => {
    const match = String(value || '').trim().match(/^v?(\d+\.\d+\.\d+)$/i);
    return match ? match[1] : '';
  };
  const language = () => {
    const value = String(window.currentLanguage || document.documentElement.lang || 'ar').toLowerCase();
    return value.startsWith('fr') ? 'fr' : value.startsWith('en') ? 'en' : 'ar';
  };
  const detected = () => parseVersion(window.nanoNative?.appVersion ||
    window.NANO_APP_VERSION || window.NANO_RUNTIME_VERSION || FALLBACK_VERSION) || FALLBACK_VERSION;
  const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  })[c]);
  const getList = (data, lang) => {
    const list = Array.isArray(data) ? data : data?.[lang] || data?.ar || data?.fr || data?.en;
    return Array.isArray(list) ? list.filter(v => typeof v === 'string' && v.trim()).slice(0, 35) : [];
  };
  function cached(v) {
    try {
      const state = JSON.parse(localStorage.getItem(STORE_KEY + v) || 'null');
      return state?.version === v && state?.features && typeof state.features === 'object'
        ? state.features : null;
    } catch { return null; }
  }
  function useVersion(value) {
    const v = parseVersion(value);
    if (!v || v === version) return;
    version = v;
    features = cached(v) || (v === FALLBACK_VERSION ? OFFLINE : null);
  }
  function render() {
    const el = document.getElementById('currentReleaseFeatures');
    if (!el) return;
    const v = version || detected();
    const lang = language();
    const data = features || (v === FALLBACK_VERSION ? OFFLINE : cached(v));
    const items = getList(data, lang);
    const title = document.getElementById('currentReleaseTitle');
    const number = document.getElementById('currentReleaseVersion');
    if (title) title.textContent = TITLES[lang] + ' — v' + v;
    if (number) number.textContent = 'v' + v;
    el.innerHTML = (items.length ? items : [MISSING[lang]]).map(item =>
      '<div class="flex gap-2 items-start"><span class="text-emerald-500 font-black" aria-hidden="true">✓</span><span>' +
      escapeHtml(item) + '</span></div>'
    ).join('');
    window.NANO_RELEASE_NOTES = {version:v, features:data || {}};
  }
  async function sync() {
    const api = window.nanoNative;
    if (!api) return;
    try {
      if (typeof api.getCurrentAppVersion === 'function') {
        const result = await api.getCurrentAppVersion();
        useVersion(result?.version);
        render();
      }
    } catch (error) { console.warn('[NANO release notes] Version lookup:', error?.message); }
    try {
      if (typeof api.checkForUpdates !== 'function') return;
      const result = await api.checkForUpdates();
      if (!result?.success || !result.manifest) return;
      useVersion(result.currentVersion);
      const current = version || detected();
      const manifest = result.manifest;
      // A newer release must NEVER be displayed as the installed version.
      const official = parseVersion(manifest.version) === current
        ? manifest.features : manifest.releaseHistory?.[current]?.features;
      if (official && typeof official === 'object' &&
          Object.values(official).some(v => Array.isArray(v) && v.length)) {
        features = official;
        try { localStorage.setItem(STORE_KEY + current, JSON.stringify({version:current,features:official})); }
        catch {}
        render();
      }
    } catch (error) { console.warn('[NANO release notes] Manifest lookup:', error?.message); }
  }
  function initialize() {
    useVersion(detected());
    render();
    void sync();
  }
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', initialize, {once:true});
  else initialize();
  window.addEventListener('nano-language-synchronized', render);
  window.addEventListener('nano-release-features-refresh', () => { render(); void sync(); });
})();