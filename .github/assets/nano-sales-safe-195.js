/* NANO POS 1.0.95 — sale-submit mutex and lossless invoice-edit preflight.
   This module does not persist data or mutate stock/accounts. */
(function (root) {
  'use strict';
  if (root.NANO_SALE_SAFE_195) return;
  let pending = false;
  const texts = {
    ar: 'تعذر تعديل الفاتورة: بعض المنتجات أو الدفعات الأصلية لم تعد متاحة. لم تتغير السلة أو الفاتورة.',
    fr: 'Modification impossible : un produit ou un lot de la facture est introuvable. La facture reste intacte.',
    en: 'Cannot edit this invoice: an original product or batch is missing. The invoice remains unchanged.'
  };
  function begin() {
    if (pending) return false;
    pending = true;
    return true;
  }
  function end() { pending = false; }
  function inspectInvoice(items, products, lang) {
    const language = String(lang || root.currentLanguage || root.document?.documentElement?.lang || 'ar').slice(0, 2);
    const error = () => ({ok: false, message: texts[language] || texts.ar});
    if (!Array.isArray(items) || !items.length || !Array.isArray(products)) return error();
    const byId = new Map(products.filter(Boolean).map(product => [String(product.id), product]));
    for (const item of items) {
      if (!item || typeof item !== 'object') return error();
      if (item.product_id == null || item.product_id === '') {
        if (!String(item.custom_product_name || '').trim()) return error();
        continue;
      }
      const product = byId.get(String(item.product_id));
      if (!product) return error();
      if (item.batch_id != null && item.batch_id !== '') {
        if (!Array.isArray(product.batches) ||
            !product.batches.some(batch => String(batch?.id) === String(item.batch_id))) return error();
      }
    }
    return {ok: true};
  }
  const api = Object.freeze({begin, end, inspectInvoice, isPending: () => pending});
  root.NANO_SALE_SAFE_195 = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
