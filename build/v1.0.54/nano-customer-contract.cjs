'use strict';
/** The PC remains authoritative. Never present a stale or fabricated customer list. */
function extractCustomerRows(value) {
  if (Array.isArray(value)) return value;
  if (!value || typeof value !== 'object') return null;
  for (const key of ['customers', 'rows', 'items', 'result', 'data']) {
    const part = value[key];
    if (Array.isArray(part)) return part;
    if (part && typeof part === 'object') {
      if (Array.isArray(part.customers)) return part.customers;
      if (Array.isArray(part.rows)) return part.rows;
      if (Array.isArray(part.items)) return part.items;
    }
  }
  if (value.snapshot && value.snapshot !== value) return extractCustomerRows(value.snapshot);
  return null;
}

async function resolveCustomerRows(dispatchRpc, args = [], context = {}) {
  let originalError;
  try {
    const direct = await dispatchRpc('get-customers', args, context);
    const rows = extractCustomerRows(direct);
    if (rows !== null) return rows;
    originalError = new Error('invalid_customers_response');
  } catch (error) { originalError = error; }
  // The fallback is server-side ONLY, after paired-device permission was checked.
  // Never export a full snapshot over the network: only the customer array leaves this server.
  try {
    const snapshot = await dispatchRpc('__nano-pc-export-snapshot', [], context);
    const rows = extractCustomerRows(snapshot);
    if (rows !== null) return rows;
  } catch (error) {
    // Do not send internal stack traces or snapshot data to the client.
  }
  const error = new Error('تعذر قراءة قائمة الزبائن من الكمبيوتر الرئيسي. تحقق من تشغيل البرنامج وقسم الزبائن ثم أعد المحاولة.');
  error.code = 'CUSTOMER_LIST_UNAVAILABLE';
  error.statusCode = 503;
  error.cause = originalError;
  throw error;
}
module.exports = { extractCustomerRows, resolveCustomerRows };