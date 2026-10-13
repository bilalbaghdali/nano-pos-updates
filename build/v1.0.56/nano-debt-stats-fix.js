/* NANO POS v1.0.56 - Read-only debt reconciliation for desktop and paired mobile.
 * Read current account balances and invoice due amounts from the authenticated API.
 * Never alter ledger records, infer payments or write to the database.
 */
(() => {
  'use strict';
  if (window.NANODebtStatsFix) return;
  const number = value => {
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
  };
  const round = value => Math.round(number(value) * 100) / 100;
  const key = value => value === undefined || value === null ? '' : String(value);
  const array = payload => {
    if (Array.isArray(payload)) return payload;
    if (!payload || typeof payload !== 'object' || payload.success === false) return null;
    for (const k of ['rows','items','customers','suppliers','purchases','sales','debts','data']) {
      if (Array.isArray(payload[k])) return payload[k];
    }
    if (payload.data && typeof payload.data === 'object') return array(payload.data);
    return null;
  };
  const call = async (api, method) => {
    if (typeof api?.[method] !== 'function') return null;
    try { return array(await api[method]()); }
    catch (err) { console.warn('[NANO debt stats]', method, err?.message || 'unavailable'); return null; }
  };
  const debtOf = row => Math.max(0,round(row?.debt ?? row?.total_debt ?? row?.balance ?? row?.remaining_balance ?? 0), round(number(row?.initial_debt)-number(row?.initial_debt_paid)));
  const invoiceDue = row => {
    if (row?.remaining_amount != null) return Math.max(0,round(row.remaining_amount));
    if (row?.remaining != null) return Math.max(0,round(row.remaining));
    if (row?.total == null || row?.paid_amount == null) return 0;
    return Math.max(0,round(number(row.total)-number(row.paid_amount)));
  };
  function mergeAccounts(accounts, debtAccounts, invoices, kind) {
    const idKey = kind === 'customer' ? 'customer_id' : 'supplier_id';
    const map = new Map();
    const ensure = id => {
      const k = key(id);
      if (!k) return null;
      if (!map.has(k)) map.set(k, { id, name:'', accountBalance:0, invoicesDue:0, total:0, paid:0, open:0, dueDate:null });
      return map.get(k);
    };
    for (const a of accounts || []) {
      if (!a) continue;
      const e = ensure(a.id ?? a[idKey]);
      if (!e) continue;
      e.name = String(a.name ?? a.customer_name ?? a.supplier_name ?? e.name);
      e.accountBalance = Math.max(e.accountBalance, debtOf(a));
    }
    for (const d of debtAccounts || []) {
      if (!d) continue;
      const e = ensure(d.id ?? d[idKey]);
      if (!e) continue;
      e.name = String(d.name ?? d.customer_name ?? d.supplier_name ?? e.name);
      e.accountBalance = Math.max(e.accountBalance, debtOf(d));
    }
    for (const inv of invoices || []) {
      if (!inv) continue;
      const e = ensure(inv[idKey] ?? inv.customerId ?? inv.supplierId);
      if (!e) continue;
      const due = invoiceDue(inv);
      e.invoicesDue = round(e.invoicesDue + due);
      e.total = round(e.total + number(inv.total));
      e.paid = round(e.paid + number(inv.paid_amount));
      if (due > 0) {
        e.open++;
        const d=inv.due_date;
        if (d && (!e.dueDate || String(d)<e.dueDate)) e.dueDate=String(d);
      }
    }
    const results = [];
    for (const e of map.values()) {
      // Account balance may include initial debt as well as invoice debt.
      // Never add both directly or the same invoice gets counted twice.
      const outstanding = round(Math.max(e.accountBalance, e.invoicesDue));
      if (outstanding <= 0) continue;
      if (kind === 'customer') results.push({customer_id:e.id,name:e.name,debt:outstanding});
      else results.push({supplier_id:e.id,name:e.name,total_purchases:e.total,total_paid:e.paid,debt:outstanding,open_invoices:e.open,due_date:e.dueDate});
    }
    return results;
  }
  async function enrich(data, api) {
    // An unavailable analytics endpoint is an error, not equivalent to zero debt.
    if (!data || typeof data !== 'object' || data.success === false) return data;
    const result = {...data};
    // Fetch the same read-only authoritative data used by Customers / Suppliers.
    const [customersDebt, customers, suppliers] = await Promise.all([
      call(api,'getCustomersDebt'),call(api,'getCustomers'),call(api,'getSuppliers')
    ]);
    let purchases=null, sales=null;
    // Fetch sales/purchases only when needed to recover invoice debt missing from account balances.
    const knownCustomer = [customersDebt,customers].some(a => a?.some(row => debtOf(row)>0));
    const knownSupplier = suppliers?.some(row => debtOf(row)>0);
    const analyticsCustomer = number(result.totalCustomerDebt);
    const analyticsSupplier = number(result.totalSupplierDebt);
    if (!knownCustomer) sales=await call(api,'getSales');
    if (!knownSupplier) purchases=await call(api,'getPurchases');
    const validCustomers = customersDebt!==null || customers!==null || sales!==null;
    const validSuppliers = suppliers!==null || purchases!==null;
    if (validCustomers) {
      const computed=mergeAccounts(customers,customersDebt,sales,'customer');
      // Do not replace an original invoice-based debt figure with an empty response
      // if the upstream account endpoint doesn't contain sufficient ledger data.
      if (computed.length || (customersDebt!==null && customers!==null && sales!==null)) {
        result.customerDebts=computed;
        result.totalCustomerDebt=round(computed.reduce((a,c)=>a+c.debt,0));
      }
    }
    if (validSuppliers) {
      const computed=mergeAccounts(suppliers,null,purchases,'supplier');
      if (computed.length || (suppliers!==null && purchases!==null)) {
        const prior=Array.isArray(result.supplierDebts)?result.supplierDebts:[];
        for (const row of computed) {
          const old=prior.find(x=>key(x?.supplier_id)===key(row.supplier_id));
          if (old && !row.total_purchases && !row.total_paid) {
            row.total_purchases=number(old.total_purchases);
            row.total_paid=number(old.total_paid);
            row.open_invoices=number(old.open_invoices);
            row.due_date=row.due_date || old.due_date || null;
          }
        }
        result.supplierDebts=computed;
        result.totalSupplierDebt=round(computed.reduce((a,s)=>a+s.debt,0));
      }
    }
    result.customerDebts=Array.isArray(result.customerDebts)?result.customerDebts:[];
    result.supplierDebts=Array.isArray(result.supplierDebts)?result.supplierDebts:[];
    result.totalCustomerDebt=round(result.totalCustomerDebt);
    result.totalSupplierDebt=round(result.totalSupplierDebt);
    return result;
  }
  window.NANODebtStatsFix={enrich,mergeAccounts};
})();