// NANO POS: APK is packaged with the desktop application; no Internet download is required.
(function () {
  'use strict';
  if (window.__nanoBundledApkUi) return;
  window.__nanoBundledApkUi = true;
  const VERSION = '1.3.7';
  const FILE = 'NANO-POS-Mobile-v1.3.7.apk';
  const $ = id => document.getElementById(id);
  const LOCAL_PATH = '/nano-mobile.apk';
  const CHECK_PATH = '/api/nano-mobile-apk';

  function makeCard() {
    const section = $('appDownloadSection');
    if (!section || !section.parentElement || $('nanoOfflineApkCard')) return;
    const card = document.createElement('div');
    card.id = 'nanoOfflineApkCard';
    card.setAttribute('dir', 'rtl');
    card.className = 'mt-4 p-5 rounded-2xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-slate-800';
    card.innerHTML = [
      '<div class="flex items-center gap-2 mb-3">',
      '<span class="material-symbols-outlined text-blue-600">android</span>',
      '<strong class="text-sm font-black text-slate-900 dark:text-white">تطبيق NANO POS Mobile مضمّن في البرنامج</strong>',
      '<span id="nanoOfflineVersion" class="text-xs text-blue-700 dark:text-blue-300">v' + VERSION + '</span></div>',
      '<p id="nanoOfflineNotice" role="status" aria-live="polite" class="text-xs text-slate-700 dark:text-slate-200 leading-relaxed mb-3">',
      'نسخة Android محفوظة داخل برنامج الكمبيوتر. يمكنك استخراجها بدون إنترنت أو نقلها إلى الهاتف على نفس الشبكة المحلية.</p>',
      '<button type="button" id="nanoOfflineSave" class="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-black">',
      '<span class="material-symbols-outlined">download</span> تحميل APK من الكمبيوتر</button>',
      '<div class="mt-3 rounded-xl border border-slate-200 dark:border-slate-700 p-3 bg-white/70 dark:bg-slate-900/40">',
      '<p class="text-xs font-bold mb-2">رابط مباشر للهاتف من الشبكة المحلية (بدون إنترنت)</p>',
      '<div id="nanoOfflineLan" class="text-xs break-all select-all" dir="ltr">جاري تحديد عنوان الكمبيوتر...</div>',
      '<button type="button" id="nanoOfflineCopy" class="text-xs font-bold text-blue-700 dark:text-blue-300 underline mt-2">نسخ رابط الهاتف</button>',
      '</div>',
      '<p class="text-[11px] text-amber-700 dark:text-amber-200 mt-3">',
      'تنبيه: يجب تشغيل NANO POS على الكمبيوتر وتوصيل الهاتف بنفس الشبكة أو عبر Tailscale لفتح الرابط المحلي.</p>'
    ].join('');
    section.insertAdjacentElement('afterend', card);
    const saveBtn = $('nanoOfflineSave');
    const copyBtn = $('nanoOfflineCopy');
    const lan = $('nanoOfflineLan');
    const notice = $('nanoOfflineNotice');
    let lanUrl = '';

    async function checkBundled() {
      try {
        let info;
        if (window.nanoNative?.getEmbeddedMobileApkStatus) {
          info = await window.nanoNative.getEmbeddedMobileApkStatus();
        } else if (/^https?:$/.test(location.protocol)) {
          const res = await fetch(CHECK_PATH, {cache: 'no-store'});
          if (!res.ok) throw Error('status_http_' + res.status);
          info = await res.json();
        }
        if (info && info.available === false) throw Error('bundled_apk_unavailable');
        if (info && info.available === true && info.version !== VERSION) throw Error('apk_version_mismatch');
        if (!info && !window.nanoNative?.saveEmbeddedMobileApk) {
          throw Error('no_desktop_apk_service');
        }
        saveBtn.disabled = false;
        saveBtn.classList.remove('opacity-50');
      } catch {
        saveBtn.disabled = true;
        saveBtn.classList.add('opacity-50');
        notice.textContent = 'تعذر العثور على APK داخل هذه النسخة. راجع سلامة تثبيت البرنامج.';
      }
    }

    function networkUrl(endpoint) {
      try {
        const url = new URL(endpoint);
        if (!['http:', 'https:'].includes(url.protocol)) return '';
        if (/^(127\.|localhost$|0\.0\.0\.0$)/i.test(url.hostname)) return '';
        return url.origin + LOCAL_PATH;
      } catch { return ''; }
    }

    async function showLan() {
      let urls = [];
      try {
        if (window.nanoNative?.getMobileSyncInfo) {
          const info = await window.nanoNative.getMobileSyncInfo();
          urls = Array.isArray(info?.endpoints) ? info.endpoints : [];
        } else if (/^https?:$/.test(location.protocol) &&
                   location.hostname !== '127.0.0.1' && location.hostname !== 'localhost') {
          urls = [location.origin];
        }
      } catch { /* The desktop download continues to work even without LAN sync. */ }
      lanUrl = urls.map(networkUrl).find(Boolean) || '';
      lan.textContent = lanUrl || 'رابط الهاتف غير متاح حاليًا. فعّل مزامنة الهاتف وتحقق من عنوان IP للكمبيوتر.';
      copyBtn.disabled = !lanUrl;
      copyBtn.classList.toggle('opacity-50', !lanUrl);
    }

    saveBtn.addEventListener('click', async () => {
      saveBtn.disabled = true;
      try {
        if (window.nanoNative?.saveEmbeddedMobileApk) {
          const result = await window.nanoNative.saveEmbeddedMobileApk();
          if (result?.success) {
            notice.textContent = 'تم حفظ ' + FILE + ' على الكمبيوتر. انقله إلى هاتف Android وثبّته.';
          } else if (!result?.cancelled) {
            notice.textContent = 'تعذر استخراج APK. تأكد من سلامة ملف التطبيق وصلاحية مجلد الحفظ.';
          }
        } else if (/^https?:$/.test(location.protocol)) {
          // Browser-only mode: download the binary served by the local app host.
          const anchor = document.createElement('a');
          anchor.href = LOCAL_PATH;
          anchor.download = FILE;
          document.body.appendChild(anchor);
          anchor.click();
          anchor.remove();
          notice.textContent = 'بدأ تنزيل APK مباشرة من الخادم المحلي للكمبيوتر.';
        } else {
          notice.textContent = 'استخدم إصدار NANO POS للكمبيوتر الذي يتضمن ميزة التنزيل المحلي.';
        }
      } catch {
        notice.textContent = 'تعذر حفظ ملف APK، حاول من جديد.';
      } finally { saveBtn.disabled = false; }
    });
    copyBtn.addEventListener('click', async () => {
      if (!lanUrl) { await showLan(); return; }
      try {
        await navigator.clipboard.writeText(lanUrl);
        notice.textContent = 'تم نسخ رابط الهاتف المحلي؛ افتحه من الهاتف المتصل بنفس الشبكة.';
      } catch {
        notice.textContent = 'انسخ عنوان الرابط الموضح يدويًا.';
      }
    });
    document.querySelector('[data-stab="mobileapp"]')?.addEventListener('click', () => {checkBundled();showLan();});
    checkBundled();
    showLan();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', makeCard, { once: true });
  } else makeCard();

  let queued = false;
  const observer = new MutationObserver(() => {
    if ($('nanoOfflineApkCard') || queued) return;
    queued = true;
    setTimeout(() => { queued = false; makeCard(); }, 100);
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();