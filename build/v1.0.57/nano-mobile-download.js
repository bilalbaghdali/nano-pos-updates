// NANO POS desktop: public Android download panel for the newest published APK.
(function () {
  'use strict';
  if (window.__nanoOfficialMobileDownloadInitialized) return;
  window.__nanoOfficialMobileDownloadInitialized = true;
  const RELEASE_MANIFEST = 'https://raw.githubusercontent.com/bilalbaghdali/nano-pos-updates/main/mobile-latest.json';
  const APPROVED_URL = /^https:\/\/github\.com\/bilalbaghdali\/nano-pos-updates\/releases\/download\/mobile-v(\d+\.\d+\.\d+)\/NANO-POS-Mobile-v\1\.apk$/i;
  const el = (id) => document.getElementById(id);
  function makeCard() {
    const target = el('appDownloadSection');
    if (!target || !target.parentElement || el('nanoOfficialApkCard')) return;
    const panel = document.createElement('div');
    panel.id = 'nanoOfficialApkCard';
    panel.className = 'mt-4 p-5 rounded-2xl border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20';
    panel.setAttribute('dir', 'rtl');
    panel.innerHTML = [
      '<div class="flex items-center gap-2 mb-3">',
      '<span class="material-symbols-outlined text-amber-600">notification_important</span>',
      '<strong class="text-amber-900 dark:text-amber-100">تنبيه — رابط تطبيق الهاتف</strong>',
      '<span id="nanoApkVersion" class="text-xs text-amber-900 dark:text-amber-100"></span>',
      '</div>',
      '<p id="nanoApkNotice" role="status" aria-live="polite" class="text-xs text-amber-900 dark:text-amber-100 leading-relaxed mb-4">جاري التحقق من الإصدار المتاح...</p>',
      '<a id="nanoApkDownload" role="button" aria-disabled="true" class="flex items-center justify-center gap-2 py-3 px-5 rounded-xl bg-blue-600 text-white font-black cursor-not-allowed opacity-50">',
      '<span class="material-symbols-outlined">download</span><span>تحميل أحدث تطبيق Android (APK)</span>',
      '</a>',
      '<div class="mt-3 flex gap-2 items-start">',
      '<button id="nanoApkCopy" type="button" class="shrink-0 text-xs font-bold text-blue-700 dark:text-blue-300 underline">نسخ الرابط</button>',
      '<span id="nanoApkLink" dir="ltr" class="text-xs break-all select-all text-slate-600 dark:text-slate-300">لم يتم تحميل الرابط</span>',
      '</div>',
      '<button id="nanoApkRefresh" type="button" class="mt-3 text-xs font-bold text-blue-700 dark:text-blue-300 underline">تحديث حالة التطبيق</button>'
    ].join('');
    target.insertAdjacentElement('afterend', panel);
    const download = el('nanoApkDownload');
    const status = el('nanoApkNotice');
    const ver = el('nanoApkVersion');
    const copy = el('nanoApkCopy');
    const link = el('nanoApkLink');
    const refresh = el('nanoApkRefresh');
    let currentUrl = null;
    download.addEventListener('click', (e) => {
      if (!currentUrl) { e.preventDefault(); update(); }
    });
    copy.addEventListener('click', async () => {
      if (!currentUrl) return;
      try { await navigator.clipboard.writeText(currentUrl); status.textContent = 'تم نسخ الرابط. افتحه على هاتفك لتنزيل الملف.'; }
      catch { status.textContent = 'تعذر النسخ تلقائيًا؛ حدّد الرابط المعروض وانسخه يدويًا.'; }
    });
    async function update() {
      refresh.disabled = true;
      currentUrl = null;
      download.removeAttribute('href');
      download.setAttribute('aria-disabled', 'true');
      download.classList.add('opacity-50', 'cursor-not-allowed');
      status.textContent = 'جاري التحقق من آخر نسخة منشورة...';
      link.textContent = 'التحقق من رابط التطبيق...';
      ver.textContent = '';
      try {
        const response = await fetch(RELEASE_MANIFEST + '?t=' + Date.now(), {cache:'no-store'});
        if (!response.ok) throw Error('HTTP ' + response.status);
        const info = await response.json();
        const match = typeof info?.downloadUrl === 'string' && info.downloadUrl.match(APPROVED_URL);
        if (!info || info.product !== 'NANO POS Mobile' || info.channel !== 'stable' || info.published !== true ||
            !/^\d+\.\d+\.\d+$/.test(info.version || '') || !match || match[1] !== info.version) {
          status.textContent = 'تنبيه: لم يُنشر إصدار APK عام صالح للتحميل بعد.';
          link.textContent = 'رابط غير متاح';
          return;
        }
        currentUrl = info.downloadUrl;
        download.href = currentUrl;
        download.target = '_blank';
        download.rel = 'noopener noreferrer';
        download.removeAttribute('aria-disabled');
        download.classList.remove('opacity-50', 'cursor-not-allowed');
        ver.textContent = 'v' + info.version;
        link.textContent = currentUrl;
        status.textContent = 'أحدث إصدار منشور: v' + info.version + '. اضغط أيقونة التحميل للحصول على التطبيق بصيغة APK. احتفظ بنسخة احتياطية قبل استبدال التطبيق المثبت.';
      } catch (error) {
        status.textContent = 'تعذر التحقق من الرابط. تأكد من اتصال الكمبيوتر بالإنترنت ثم أعد المحاولة.';
        link.textContent = 'غير متاح حاليًا';
      } finally { refresh.disabled = false; }
    }
    refresh.addEventListener('click', update);
    document.querySelector('[data-stab="mobileapp"]')?.addEventListener('click', update);
    update();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', makeCard, {once:true});
  else makeCard();
  // Some desktop layouts re-create the settings tab: reattach without duplicating it.
  let pending = false;
  const mo = new MutationObserver(() => {
    if (pending || el('nanoOfficialApkCard')) return;
    pending = true;
    setTimeout(() => { pending = false; makeCard(); }, 80);
  });
  mo.observe(document.documentElement, {childList:true, subtree:true});
})();