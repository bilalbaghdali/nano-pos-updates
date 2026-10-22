(function () {
  'use strict';

  const P = window.PrintEngine;
  if (!P || P.__nanoModernInvoiceModelsPatched) return;

  const MODERN_A4_SETTING = 'template_modern_a4';
  const MODERN_THERMAL_SETTING = 'template_modern_thermal';
  const MODERN_A4_KEY = 'design4';
  const MODERN_THERMAL_KEY = 'thermalModern';
  const PREMIUM_A4_SETTING = 'template_premium_a4';
  const PREMIUM_A4_KEY = 'designPremium';
  const PREMIUM_A5_RECEIPT_KEY = 'receiptPremiumA5';
  const PREMIUM_THERMAL_RECEIPT_KEY = 'receiptPremiumThermal';

  const original = {
    invoiceUIToSettings: P.invoiceUIToSettings.bind(P),
    settingsToInvoiceUI: P.settingsToInvoiceUI.bind(P),
    resolveInvoiceTemplate: P.resolveInvoiceTemplate.bind(P),
    resolveInvoiceDesign: P.resolveInvoiceDesign.bind(P),
    listInvoiceDesigns: P.listInvoiceDesigns.bind(P),
    resolveReceiptTemplate: P.resolveReceiptTemplate.bind(P),
    listReceiptDesigns: P.listReceiptDesigns.bind(P),
  };

  function langOf(settings) {
    return String((settings && settings.invoice_lang) || 'ar').toLowerCase();
  }

  function modernDesign(key, settings) {
    const lang = langOf(settings);
    if (key === PREMIUM_A4_KEY) {
      const chosen = ['ar', 'fr', 'en'].includes(lang) ? lang : 'ar';
      return {
        tplName: `invoice_template_premium_${chosen}.html`,
        lang: chosen,
        pageSize: null,
        dynamicLang: false,
      };
    }
    if (key === MODERN_A4_KEY) {
      return {
        tplName: 'invoice_template_modern.html',
        lang,
        pageSize: null,
        dynamicLang: true,
      };
    }
    if (key === MODERN_THERMAL_KEY) {
      return {
        tplName: 'invoice_thermal_modern_80.html',
        lang,
        pageSize: null,
        dynamicLang: true,
      };
    }
    return null;
  }

  P.invoiceUIToSettings = function (design, lang) {
    if (design === PREMIUM_A4_KEY) return PREMIUM_A4_SETTING;
    if (design === MODERN_A4_KEY) return MODERN_A4_SETTING;
    if (design === MODERN_THERMAL_KEY) return MODERN_THERMAL_SETTING;
    return original.invoiceUIToSettings(design, lang);
  };

  P.settingsToInvoiceUI = function (templateKey) {
    if (templateKey === PREMIUM_A4_SETTING) return { design: PREMIUM_A4_KEY, lang: 'ar' };
    if (templateKey === MODERN_A4_SETTING) return { design: MODERN_A4_KEY, lang: 'ar' };
    if (templateKey === MODERN_THERMAL_SETTING) return { design: MODERN_THERMAL_KEY, lang: 'ar' };
    return original.settingsToInvoiceUI(templateKey);
  };

  P.resolveInvoiceTemplate = function (settings) {
    const templateKey = settings && settings.invoice_template;
    if (templateKey === PREMIUM_A4_SETTING) {
      return { ...modernDesign(PREMIUM_A4_KEY, settings), design: PREMIUM_A4_KEY };
    }
    if (templateKey === MODERN_A4_SETTING) {
      return { ...modernDesign(MODERN_A4_KEY, settings), design: MODERN_A4_KEY };
    }
    if (templateKey === MODERN_THERMAL_SETTING) {
      return { ...modernDesign(MODERN_THERMAL_KEY, settings), design: MODERN_THERMAL_KEY };
    }
    return original.resolveInvoiceTemplate(settings);
  };

  P.resolveInvoiceDesign = function (design, settings) {
    const explicit = modernDesign(design, settings);
    if (explicit) return explicit;

    if (!design && settings) {
      if (settings.invoice_template === PREMIUM_A4_SETTING) return modernDesign(PREMIUM_A4_KEY, settings);
      if (settings.invoice_template === MODERN_A4_SETTING) return modernDesign(MODERN_A4_KEY, settings);
      if (settings.invoice_template === MODERN_THERMAL_SETTING) return modernDesign(MODERN_THERMAL_KEY, settings);
    }

    return original.resolveInvoiceDesign(design, settings);
  };

  P.listInvoiceDesigns = function (settings) {
    const current = settings && settings.invoice_template;
    const list = original.listInvoiceDesigns(settings).map(item => ({
      ...item,
      configured: (current === MODERN_A4_SETTING || current === MODERN_THERMAL_SETTING || current === PREMIUM_A4_SETTING)
        ? false
        : !!item.configured,
    }));

    list.push(
      {
        key: PREMIUM_A4_KEY,
        labelKey: 'design_premium_a4',
        configured: current === PREMIUM_A4_SETTING,
      },
      {
        key: MODERN_A4_KEY,
        labelKey: 'design_modern_color',
        configured: current === MODERN_A4_SETTING,
      },
      {
        key: MODERN_THERMAL_KEY,
        labelKey: 'design_thermal_modern',
        configured: current === MODERN_THERMAL_SETTING,
      },
    );
    return list;
  };

  function premiumReceipt(design, settings) {
    const lang = ['ar', 'fr', 'en'].includes(String(settings && settings.receipt_lang))
      ? settings.receipt_lang : 'ar';
    const baseName = design === PREMIUM_A5_RECEIPT_KEY
      ? 'receipt_template_premium_a5' : 'receipt_template_premium_thermal';
    return {
      tplName: baseName + (lang === 'ar' ? '' : '_' + lang) + '.html',
      lang, design, baseName,
    };
  }

  P.resolveReceiptTemplate = function (settings) {
    const design = settings && settings.receipt_template;
    if (design === PREMIUM_A5_RECEIPT_KEY || design === PREMIUM_THERMAL_RECEIPT_KEY) {
      return premiumReceipt(design, settings);
    }
    return original.resolveReceiptTemplate(settings);
  };

  P.listReceiptDesigns = function (settings) {
    const current = settings && settings.receipt_template;
    const list = original.listReceiptDesigns(settings);
    list.push(
      { key: PREMIUM_A5_RECEIPT_KEY, labelKey: 'receipt_premium_a5', configured: current === PREMIUM_A5_RECEIPT_KEY },
      { key: PREMIUM_THERMAL_RECEIPT_KEY, labelKey: 'receipt_premium_thermal', configured: current === PREMIUM_THERMAL_RECEIPT_KEY },
    );
    return list;
  };

  const words = {
    ar: {
      design_premium_a4: 'فاتورة احترافية A4',
      receipt_premium_a5: 'وصل بيع احترافي A5',
      receipt_premium_thermal: 'وصل حراري احترافي 58/80 مم',
      design_modern_color: 'عصري ملون A4',
      design_thermal_modern: 'حراري عصري 80 مم',
      invoice_preview_title: 'معاينة النموذج',
      invoice_preview_loading: 'جاري تجهيز المعاينة…',
      invoice_preview_error: 'تعذر إنشاء معاينة لهذا النموذج',
      invoice_preview_print: 'طباعة النموذج المختار',
      invoice_preview_pdf: 'حفظ PDF',
      invoice_preview_format: 'المقاس',
    },
    fr: {
      design_premium_a4: 'Facture professionnelle A4',
      receipt_premium_a5: 'Reçu professionnel A5',
      receipt_premium_thermal: 'Ticket professionnel 58/80 mm',
      design_modern_color: 'Moderne couleur A4',
      design_thermal_modern: 'Thermique moderne 80 mm',
      invoice_preview_title: 'Aperçu du modèle',
      invoice_preview_loading: 'Préparation de l’aperçu…',
      invoice_preview_error: 'Impossible de générer l’aperçu',
      invoice_preview_print: 'Imprimer ce modèle',
      invoice_preview_pdf: 'Enregistrer PDF',
      invoice_preview_format: 'Format',
    },
    en: {
      design_premium_a4: 'Professional Invoice A4',
      receipt_premium_a5: 'Professional Receipt A5',
      receipt_premium_thermal: 'Professional Thermal Receipt 58/80 mm',
      design_modern_color: 'Modern Color A4',
      design_thermal_modern: 'Modern Thermal 80 mm',
      invoice_preview_title: 'Template preview',
      invoice_preview_loading: 'Preparing preview…',
      invoice_preview_error: 'Could not generate this preview',
      invoice_preview_print: 'Print selected template',
      invoice_preview_pdf: 'Save PDF',
      invoice_preview_format: 'Format',
    },
  };

  if (window.translations) {
    for (const [lang, entries] of Object.entries(words)) {
      window.translations[lang] = window.translations[lang] || {};
      Object.assign(window.translations[lang], entries);
    }
  }

  P.MODERN_INVOICE_MODELS = Object.freeze({
    MODERN_A4_SETTING,
    MODERN_THERMAL_SETTING,
    MODERN_A4_KEY,
    MODERN_THERMAL_KEY,
    PREMIUM_A4_SETTING,
    PREMIUM_A4_KEY,
    PREMIUM_A5_RECEIPT_KEY,
    PREMIUM_THERMAL_RECEIPT_KEY,
  });
  P.__nanoModernInvoiceModelsPatched = true;
})();
