/* NANO POS v1.0.55 — customer sales and debts read-only compatibility layer.
 * The desktop details window expects {sales,payments,customer}, while legacy
 * bridges returned a bare sales array. Do not silently treat server errors as
 * an empty ledger, since that would misrepresent a customer's outstanding debt.
 */
(() => {
  'use strict';
  const isObject = x => x !== null && typeof x === 'object' && !Array.isArray(x);
  const numeric = (value, label) => {
    const number = Number(value ?? 0);
    if (!Number.isFinite(number)) throw new Error('قيمة مالية غير صالحة في ' + label + '.');
    return number;
  };
  async function getCustomerDetails(customerId, cachedCustomer) {
    if (!window.api || typeof window.api.getCustomerSales !== 'function') {
      throw new Error('خدمة سجل مبيعات الزبون غير متاحة.');
    }
    const raw = await window.api.getCustomerSales(customerId);
    if (isObject(raw) && raw.success === false) {
      throw new Error(raw.message || raw.error || 'تعذر جلب سجل مبيعات الزبون.');
    }
    const payload = Array.isArray(raw)
      ? { sales: raw, payments: [], customer: cachedCustomer }
      : (isObject(raw?.data) && (Array.isArray(raw.data.sales) || Array.isArray(raw.data.payments)) ? raw.data : raw);
    if (!isObject(payload) || (!Array.isArray(payload.sales) && !Array.isArray(payload.payments))) {
      throw new Error('استجابة سجل مبيعات الزبون غير مكتملة. تحقق من اتصال البرنامج بقاعدة البيانات.');
    }
    const sales = (Array.isArray(payload.sales) ? payload.sales : []).map((sale, index) => {
      if (!isObject(sale)) throw new Error('فاتورة غير صالحة في سجل الزبون: ' + (index + 1));
      return { ...sale, total: numeric(sale.total, 'الفاتورة'), paid_amount: numeric(sale.paid_amount, 'المدفوع') };
    });
    const payments = (Array.isArray(payload.payments) ? payload.payments : []).map((payment, index) => {
      if (!isObject(payment)) throw new Error('تسديد غير صالح في سجل الزبون: ' + (index + 1));
      return { ...payment, amount: numeric(payment.amount, 'التسديد') };
    });
    const customer = isObject(payload.customer) ? payload.customer : cachedCustomer;
    if (!isObject(customer)) throw new Error('بيانات الزبون غير متاحة.');
    return { sales, payments, customer };
  }
  window.nanoGetCustomerSalesAndDebts = getCustomerDetails;
})();