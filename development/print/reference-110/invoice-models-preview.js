(function () {
  'use strict';

  if (typeof document === 'undefined' || !window.PrintEngine) return;
  if (window.__nanoInvoiceModelPreviewInstalled) return;
  window.__nanoInvoiceModelPreviewInstalled = true;

  let selectedDesignKey = null;
  let selectedSaleId = null;
  let selectedLanguage = 'ar';
  let renderToken = 0;
  let knownDesigns = [];

  function tr(key, fallback) {
    try {
      if (typeof window.t === 'function') {
        const out = window.t(key);
        if (out && out !== key) return out;
      }
    } catch (_) {}
    const lang = document.documentElement.lang || window.currentLanguage || 'ar';
    const dict = window.translations && window.translations[lang];
    return (dict && dict[key]) || fallback || key;
  }

  function labelFor(item) {
    if (item.custom) return '★ ' + (item.name || item.label || 'نموذج مخصص');
    return tr(item.labelKey, item.key);
  }

  function formatFor(key, custom) {
    if (custom) return 'مخصص';
    if (key === 'thermal' || key === 'thermalModern') return '80 mm';
    if (key === 'a5') return 'A5';
    return 'A4';
  }

  function previewScaleFor(key, custom) {
    if (custom) return 0.72;
    if (key === 'thermal' || key === 'thermalModern') return 0.96;
    if (key === 'a5') return 0.84;
    return 0.70;
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function thumbnailMarkup(item) {
    const key = item.key;
    const thermal = key === 'thermal' || key === 'thermalModern';
    const modernColor = key === 'design4';
    const premium = key === 'designPremium';
    const boxed = key === 'design3';
    const detailed = key === 'design2' || key === 'detailed';

    if (thermal) {
      return `
        <div class="mx-auto h-[88px] w-[45px] rounded-[4px] border border-slate-300 bg-white p-1 shadow-sm overflow-hidden">
          <div class="h-1.5 w-3/4 bg-slate-700 mx-auto mb-1"></div>
          <div class="h-px w-full border-t border-dashed border-slate-400 my-1"></div>
          <div class="h-1 w-2/3 bg-slate-400 mb-1"></div>
          <div class="h-1 w-full bg-slate-200 mb-1"></div>
          <div class="h-5 border border-slate-300 mb-1"></div>
          <div class="space-y-[2px]">
            <div class="h-[2px] bg-slate-300"></div><div class="h-[2px] bg-slate-300"></div>
            <div class="h-[2px] bg-slate-300"></div>
          </div>
          <div class="h-px w-full bg-slate-800 mt-1"></div>
          <div class="h-1.5 w-1/2 bg-slate-700 mt-1 mr-auto"></div>
        </div>`;
    }

    return `
      <div class="mx-auto h-[88px] w-[64px] rounded-[4px] border border-slate-300 bg-white p-1 shadow-sm overflow-hidden">
        <div class="flex gap-[2px] mb-1">
          <div class="h-3 flex-1 ${modernColor ? 'bg-amber-300' : premium ? 'bg-slate-800' : 'bg-slate-200'}"></div>
          <div class="h-3 w-4 ${modernColor ? 'bg-teal-300' : premium ? 'bg-teal-500' : 'bg-slate-300'}"></div>
        </div>
        <div class="h-1.5 w-1/2 ${boxed ? 'border border-slate-400' : 'bg-slate-400'} mb-1"></div>
        <div class="h-1 w-3/4 bg-slate-200 mb-1"></div>
        <div class="h-7 border border-slate-300 mb-1">
          <div class="h-2 ${modernColor ? 'bg-teal-200' : premium ? 'bg-slate-800' : detailed ? 'bg-slate-300' : 'bg-slate-100'} border-b border-slate-300"></div>
          <div class="grid grid-cols-4 gap-px p-[2px]"><i class="h-1 bg-slate-200"></i><i class="h-1 bg-slate-200"></i><i class="h-1 bg-slate-200"></i><i class="h-1 bg-slate-200"></i></div>
        </div>
        <div class="flex justify-between items-start gap-1">
          <div class="space-y-[2px] flex-1"><div class="h-1 bg-slate-200"></div><div class="h-1 bg-slate-200"></div></div>
          <div class="h-4 w-6 ${modernColor ? 'bg-amber-300' : premium ? 'bg-teal-100' : 'border border-slate-300'}"></div>
        </div>
      </div>`;
  }

  function injectPreviewScale(html, key, custom) {
    const zoom = previewScaleFor(key, custom);
    const previewCss = `<style id="nano-invoice-preview-style">
      html { background:#eef2f7 !important; }
      @media screen {
        html { zoom:${zoom}; }
        body { margin-left:auto !important; margin-right:auto !important; }
      }
    </style>`;
    if (/<\/head>/i.test(html)) return html.replace(/<\/head>/i, previewCss + '</head>');
    return previewCss + html;
  }

  function setStatus(text, kind) {
    const status = document.getElementById('ppcInvoicePreviewStatus');
    if (!status) return;
    status.textContent = text || '';
    status.className = 'text-[11px] font-bold ' + (kind === 'error' ? 'text-red-600' : 'text-slate-500');
  }

  function setActionsDisabled(disabled) {
    ['ppcInvoicePreviewPrintBtn', 'ppcInvoicePreviewPdfBtn'].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) btn.disabled = !!disabled;
    });
  }

  function refreshCardSelection() {
    document.querySelectorAll('[data-invoice-preview-design]').forEach(card => {
      const active = card.getAttribute('data-invoice-preview-design') === String(selectedDesignKey);
      card.setAttribute('aria-pressed', active ? 'true' : 'false');
      card.classList.toggle('ring-2', active);
      card.classList.toggle('ring-indigo-500', active);
      card.classList.toggle('border-indigo-400', active);
      card.classList.toggle('bg-indigo-50', active);
      card.classList.toggle('dark:bg-indigo-950/30', active);
    });
  }

  async function renderSelectedPreview() {
    const frame = document.getElementById('ppcInvoicePreviewFrame');
    const title = document.getElementById('ppcInvoicePreviewName');
    const format = document.getElementById('ppcInvoicePreviewFormat');
    if (!frame || !selectedSaleId || !selectedDesignKey) return;

    const item = knownDesigns.find(d => String(d.key) === String(selectedDesignKey));
    if (title) title.textContent = item ? labelFor(item) : String(selectedDesignKey);
    if (format) format.textContent = `${tr('invoice_preview_format', 'المقاس')}: ${formatFor(selectedDesignKey, item && item.custom)}`;

    const token = ++renderToken;
    setActionsDisabled(true);
    setStatus(tr('invoice_preview_loading', 'جاري تجهيز المعاينة…'));
    frame.srcdoc = '<!doctype html><html dir="rtl"><body style="font-family:Arial;padding:30px;text-align:center;color:#64748b">…</body></html>';

    try {
      const html = await window.printInvoice('sale', selectedSaleId, selectedDesignKey, 'html', selectedLanguage);
      if (token !== renderToken) return;
      if (!html || typeof html !== 'string') throw new Error('empty preview');
      frame.srcdoc = injectPreviewScale(html, selectedDesignKey, item && item.custom);
      setStatus('');
      setActionsDisabled(false);
    } catch (error) {
      if (token !== renderToken) return;
      frame.srcdoc = `<!doctype html><html dir="rtl"><body style="font-family:Arial;padding:30px;text-align:center;color:#b91c1c"><strong>${escapeHtml(tr('invoice_preview_error', 'تعذر إنشاء معاينة لهذا النموذج'))}</strong></body></html>`;
      setStatus(tr('invoice_preview_error', 'تعذر إنشاء معاينة لهذا النموذج'), 'error');
      setActionsDisabled(true);
      console.error('Invoice preview failed:', error);
    }
  }

  function selectDesign(key) {
    selectedDesignKey = String(key);
    refreshCardSelection();
    renderSelectedPreview();
  }

  function renderGallery(designs) {
    const gallery = document.getElementById('ppcInvoicePreviewCards');
    if (!gallery) return;
    gallery.innerHTML = '';

    for (const item of designs) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.setAttribute('data-invoice-preview-design', String(item.key));
      btn.setAttribute('aria-pressed', 'false');
      btn.className = 'w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-right transition hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500';
      btn.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="shrink-0">${thumbnailMarkup(item)}</div>
          <div class="min-w-0 flex-1">
            <div class="text-xs font-black text-slate-800 dark:text-slate-100 leading-5">${escapeHtml(labelFor(item))}</div>
            <div class="mt-1 flex items-center gap-1.5 flex-wrap">
              <span class="inline-flex px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[9px] font-black text-slate-500 dark:text-slate-300">${escapeHtml(formatFor(item.key, item.custom))}</span>
              ${item.configured ? '<span class="inline-flex px-2 py-0.5 rounded-full bg-emerald-100 text-[9px] font-black text-emerald-700">افتراضي</span>' : ''}
              ${item.custom ? '<span class="inline-flex px-2 py-0.5 rounded-full bg-amber-100 text-[9px] font-black text-amber-700">مخصص</span>' : ''}
            </div>
          </div>
        </div>`;
      btn.addEventListener('click', () => selectDesign(item.key));
      gallery.appendChild(btn);
    }
  }

  async function setupInvoicePreview(context) {
    const section = document.getElementById('ppcInvoiceSection');
    const browser = document.getElementById('ppcInvoicePreviewBrowser');
    const oldChips = document.getElementById('ppcInvoiceChips');
    if (!section || !browser) return;

    const sale = context || window.posLastSale || null;
    selectedSaleId = sale && sale.id ? sale.id : null;
    if (!selectedSaleId || section.classList.contains('hidden')) {
      browser.classList.add('hidden');
      return;
    }

    browser.classList.remove('hidden');
    if (oldChips) oldChips.style.display = 'none';

    let settings = {};
    try { settings = await window.api.getSettings(); } catch (_) {}
    selectedLanguage = ['ar', 'fr', 'en'].includes(settings.invoice_lang) ? settings.invoice_lang : 'ar';
    const languageSelect = document.getElementById('ppcInvoicePreviewLang');
    if (languageSelect) languageSelect.value = selectedLanguage;

    const builtIn = window.PrintEngine.listInvoiceDesigns(settings).map(item => ({ ...item, custom: false }));
    let custom = [];
    try {
      const all = await window.api.getCustomTemplates();
      custom = (Array.isArray(all) ? all : [])
        .filter(x => Number(x.is_active) !== 0 && x.doc_type === 'invoice')
        .map(x => ({
          key: 'custom:' + x.id,
          name: x.name,
          custom: true,
          configured: settings.invoice_template === 'custom:' + x.id,
        }));
    } catch (_) {}

    knownDesigns = [...builtIn, ...custom];
    renderGallery(knownDesigns);

    const configured = knownDesigns.find(d => d.configured);
    selectedDesignKey = String((configured || knownDesigns[0] || {}).key || 'design1');
    refreshCardSelection();
    await renderSelectedPreview();
  }

  const printBtn = document.getElementById('ppcInvoicePreviewPrintBtn');
  if (printBtn) {
    printBtn.addEventListener('click', async () => {
      if (!selectedSaleId || !selectedDesignKey) return;
      try {
        if (typeof window.closePosPrintCenter === 'function') window.closePosPrintCenter();
        await window.printInvoice('sale', selectedSaleId, selectedDesignKey, 'print', selectedLanguage);
      } catch (error) { console.error(error); }
    });
  }

  const pdfBtn = document.getElementById('ppcInvoicePreviewPdfBtn');
  if (pdfBtn) {
    pdfBtn.addEventListener('click', async () => {
      if (!selectedSaleId || !selectedDesignKey) return;
      try {
        if (typeof window.closePosPrintCenter === 'function') window.closePosPrintCenter();
        await window.printInvoice('sale', selectedSaleId, selectedDesignKey, 'pdf', selectedLanguage);
      } catch (error) { console.error(error); }
    });
  }

  const languageSelect = document.getElementById('ppcInvoicePreviewLang');
  if (languageSelect) {
    languageSelect.addEventListener('change', () => {
      selectedLanguage = languageSelect.value;
      renderSelectedPreview();
    });
  }

  if (typeof window.openPosPrintCenter === 'function') {
    const originalOpenPosPrintCenter = window.openPosPrintCenter;
    const wrappedOpenPosPrintCenter = async function (context) {
      const result = await originalOpenPosPrintCenter.apply(this, arguments);
      try { await setupInvoicePreview(context); } catch (error) { console.error('Invoice preview setup failed:', error); }
      return result;
    };
    window.openPosPrintCenter = wrappedOpenPosPrintCenter;
    try { openPosPrintCenter = wrappedOpenPosPrintCenter; } catch (_) {}
  }

  window.NanoInvoicePreview = {
    setup: setupInvoicePreview,
    select: selectDesign,
    getSelectedDesign: () => selectedDesignKey,
  };
})();
