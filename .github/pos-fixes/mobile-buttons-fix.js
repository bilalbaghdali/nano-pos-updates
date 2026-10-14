/* NANO POS — Mobile download placement fix. UI-only; no data or sync changes. */
(() => {
  'use strict';
  if (window.__nanoMobileButtonsFixInstalled) return;
  window.__nanoMobileButtonsFixInstalled = true;

  let savedLatest = null;
  let observer = null;
  let scheduled = false;
  const newVersion = /(?:^|\D)(?:1\.3\.7|1\.0\.37)(?!\d)/;
  const oldVersion = /(?:^|\D)(?:1\.3\.6|1\.0\.36)(?!\d)/;
  const mobilePattern = /(mobile|phone|هاتف|التطبيق|application|télécharger|download|تنزيل|تحميل)/i;

  const label = node => String(node?.textContent || '').replace(/\s+/g, ' ').trim();
  const within = (root, selector) => Array.from(root.querySelectorAll(selector));
  const isCandidate = node => node && !node.hasAttribute('data-download-scanner') &&
      !node.hasAttribute('data-download-mobile') && !node.closest('#nanoMobileDownloadActions');
  function findLatest(tab) {
    const preferred = [
      '#mobileApkDownloadButton', '#mobileApkSaveButton', '#nanoMobileDownloadLatest',
      '#downloadLatestMobileApk', '#saveMobileApkButton',
      '[data-download-latest-mobile]', '[data-save-mobile-apk]'
    ];
    for (const selector of preferred) {
      const btn = tab.querySelector(selector);
      if (btn && isCandidate(btn)) return btn;
    }
    const nodes = within(tab, 'a[href], button');
    for (const node of nodes) {
      if (!isCandidate(node)) continue;
      const action = [label(node), node.id, node.getAttribute('title') || '',
        node.getAttribute('href') || ''].join(' ');
      if (/(refresh|copy|نسخ|تحديث|actualiser|recharger)/i.test(action)) continue;
      if (!/(download|save|apk|mobile|تحميل|تنزيل|حفظ|télécharger)/i.test(action)) continue;
      const details = [action, label(node.closest('section') || node.parentElement)].join(' ');
      if (newVersion.test(details) && mobilePattern.test(details)) return node;
    }
    return null;
  }

  function syncButtons() {
    const tab = document.getElementById('settingsTab-mobileapp');
    if (!tab) return;
    const scanner = tab.querySelector('[data-download-scanner]');
    if (!scanner) return;
    const detected = findLatest(tab);
    if (detected) savedLatest = detected;
    const latest = savedLatest;
    if (!latest || latest === scanner || latest.hasAttribute('data-download-mobile')) return;

    const scannerCard = scanner.closest('section');
    if (!scannerCard) return;
    let row = scannerCard.querySelector('#nanoMobileDownloadActions');
    if (!row) {
      row = document.createElement('div');
      row.id = 'nanoMobileDownloadActions';
      row.className = 'flex flex-wrap items-center gap-3';
      row.style.cssText = 'display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-top:10px';
      scanner.parentNode.insertBefore(row, scanner);
      row.appendChild(scanner);
    }
    if (latest.parentElement !== row) row.appendChild(latest);
    latest.style.minHeight = '42px';
    latest.style.display = 'inline-flex';
    latest.style.alignItems = 'center';
    latest.style.justifyContent = 'center';
    latest.style.gap = '8px';
    latest.style.flex = '0 1 auto';
    latest.style.maxWidth = '100%';
    latest.style.borderRadius = '12px';
    latest.setAttribute('data-nano-mobile-kept', '1');
    if (!latest.getAttribute('aria-label')) latest.setAttribute('aria-label', 'تحميل تطبيق الهاتف - أحدث نسخة');

    for (const legacyButton of within(tab, '[data-download-mobile]')) {
      if (legacyButton === latest) continue;
      const card = legacyButton.closest('section');
      if (!card || card === scannerCard || card.contains(latest)) continue;
      const detail = label(card);
      if (oldVersion.test(detail) || !newVersion.test(detail)) card.remove();
    }
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(() => {
      scheduled = false;
      syncButtons();
    });
  }
  function begin() {
    const tab = document.getElementById('settingsTab-mobileapp');
    if (!tab) return;
    if (observer) observer.disconnect();
    observer = new MutationObserver(schedule);
    observer.observe(tab, { childList: true, subtree: true });
    schedule();
    document.addEventListener('visibilitychange', schedule);
    window.addEventListener('nano-language-synchronized', schedule);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', begin, { once: true });
  else begin();
})();
