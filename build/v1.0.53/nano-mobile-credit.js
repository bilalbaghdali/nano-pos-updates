/* NANO POS Mobile credit & customer picker. Runs only in the paired mobile UI.
   All reads and writes use the existing authenticated window.api bridge. */
(() => {
  'use strict';
  if (!window.NANO_MOBILE || window.__nanoMobileCreditInstalled) return;
  window.__nanoMobileCreditInstalled = true;
  const money = value => Math.round(Number(value || 0) * 100) / 100;
  const el = id => document.getElementById(id);
  const notify = (text, type = 'warning') => {
    if (typeof window.showToast === 'function') window.showToast(text, type);
    else console.warn('[NANO Mobile]', text);
  };
  let customers = [], modal = null, mode = 'full', busy = false;
  const isValidId = id => id !== '' && id !== null && id !== undefined;
  const chosenCustomerId = () => String(el('posCustomerSelect')?.value || '');
  const total = () => {
    // The native checkout computes its total from the cart; this field is updated by openCheckoutModal.
    // Use the same source as renderer.checkoutCalcChange; formatted currency strings
    // can contain thousands separators and are not safe to parse as numbers.
    try {
      if (typeof cart !== 'undefined' && Array.isArray(cart)) {
        const sub = cart.reduce((sum, item) => sum + Number(item.selling_price || 0) * Number(item.qty || 0), 0);
        const discount = typeof globalCartDiscount !== 'undefined' ? Number(globalCartDiscount || 0) : 0;
        const tax = typeof currentTVAPercentage !== 'undefined' ? Number(currentTVAPercentage || 0) : 0;
        return money(Math.max(0, sub - discount) * (1 + tax / 100));
      }
    } catch {}
    const raw = String(el('checkoutTotalUI')?.textContent || '0');
    const compact = raw.match(/[\d.,\s]+/)?.[0]?.replace(/\s/g, '') || '0';
    const digits = compact.replace(/,(?=\d{3}(?:[.,]|$))/g, '').replace(/,(?=\d{1,2}$)/, '.');
    return money(Number(digits) || 0);
  };
  const setPaid = value => {
    if (!el('checkoutPaidAmount')) return;
    el('checkoutPaidAmount').value = money(value).toFixed(2);
    el('checkoutPaidAmount').dispatchEvent(new Event('input', { bubbles: true }));
  };
  const selection = (id, name) => {
    if (typeof window.selectPosCustomer === 'function') window.selectPosCustomer(String(id), String(name));
    else {
      if (el('posCustomerSelect')) el('posCustomerSelect').value = String(id);
      if (el('posCustomerSearchInput')) el('posCustomerSearchInput').value = String(name);
    }
  };
  async function fetchCustomers() {
    // Always query the authoritative PC; do not use a cached customer list.
    if (!window.api?.getCustomers) throw new Error('تعذر الوصول إلى بيانات الزبائن من الكمبيوتر.');
    const list = await window.api.getCustomers();
    if (!Array.isArray(list)) throw new Error('لم تصل قائمة الزبائن من الكمبيوتر.');
    customers = list.filter(x => isValidId(x?.id));
    return customers;
  }
  function createCustomerPicker() {
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'nanoCreditCustomerOverlay';
    modal.className = 'nano-credit-customer-overlay';
    modal.hidden = true;
    modal.innerHTML = `<div role="dialog" aria-modal="true" aria-label="اختيار زبون البيع الآجل" class="nano-credit-customer-card">
       <h3>اختيار الزبون من السجلات</h3>
       <p>لبيع الكريدي أو الدفع الجزئي اختر زبونًا موجودًا في قسم الزبائن.</p>
       <label for="nanoCreditSearch">البحث عن الزبون</label>
       <input id="nanoCreditSearch" autocomplete="off" placeholder="الاسم أو الهاتف" />
       <label for="nanoCreditSelect">الزبون</label>
       <select id="nanoCreditSelect"><option value="">جارٍ جلب الزبائن…</option></select>
       <p id="nanoCreditCustomerInfo" class="nano-credit-customer-info"></p>
       <div class="nano-credit-customer-buttons">
         <button type="button" id="nanoCreditContinue">متابعة الدفع الجزئي</button>
         <button type="button" id="nanoCreditClose">إلغاء</button>
       </div>
     </div>`;
    document.body.appendChild(modal);
    const updateInfo = () => {
      const customer = customers.find(x => String(x.id) === el('nanoCreditSelect')?.value);
      if (el('nanoCreditCustomerInfo')) el('nanoCreditCustomerInfo').textContent = customer ?
        `الزبون: ${customer.name || '—'} | الهاتف: ${customer.phone || '—'} | الرصيد: ${money(customer.balance).toFixed(2)} دج` : 'اختر زبونًا للمتابعة.';
    };
    const populate = () => {
      const search = String(el('nanoCreditSearch')?.value || '').toLocaleLowerCase();
      const filtered = customers.filter(c => `${c.name || ''} ${c.phone || ''} ${c.id}`.toLocaleLowerCase().includes(search));
      const select = el('nanoCreditSelect');
      if (!select) return;
      const prior = select.value || chosenCustomerId();
      select.replaceChildren();
      select.appendChild(new Option(filtered.length ? 'اختر الزبون...' : 'لا يوجد زبون مطابق', ''));
      for (const c of filtered) select.appendChild(new Option(`${c.name || '#' + c.id} • ${c.phone || ''}`, String(c.id)));
      if (filtered.some(c => String(c.id) === String(prior))) select.value = String(prior);
      updateInfo();
    };
    el('nanoCreditSearch').addEventListener('input', populate);
    el('nanoCreditSelect').addEventListener('change', updateInfo);
    el('nanoCreditClose').addEventListener('click', () => { modal.hidden = true; });
    el('nanoCreditContinue').addEventListener('click', async () => {
      const customer = customers.find(x => String(x.id) === el('nanoCreditSelect')?.value);
      if (!customer) return notify('اختر زبونًا من قسم الزبائن أولًا.');
      selection(customer.id, customer.name || '');
      modal.hidden = true;
      if (typeof window.handleCheckoutPress !== 'function') return notify('تعذر فتح شاشة الدفع على الهاتف.', 'error');
      await window.handleCheckoutPress();
      // Checkout opens asynchronously after original trial/license checks.
      setTimeout(() => {
        if (el('checkoutModal') && !el('checkoutModal').classList.contains('hidden')) {
          setMode('partial');
          el('checkoutPaidAmount')?.focus();
          el('checkoutPaidAmount')?.select();
        }
      }, 120);
    });
    return modal;
  }
  async function openPicker() {
    const picker = createCustomerPicker();
    picker.hidden = false;
    el('nanoCreditSearch').value = '';
    el('nanoCreditSelect').replaceChildren(new Option('جارٍ جلب الزبائن…', ''));
    try { await fetchCustomers(); }
    catch (error) {
      notify(error?.message || 'تعذر جلب الزبائن من الكمبيوتر.', 'error');
      el('nanoCreditSelect').replaceChildren(new Option('تعذر الاتصال بالكمبيوتر', ''));
      return;
    }
    const select = el('nanoCreditSelect');
    select.replaceChildren(new Option('اختر الزبون...', ''));
    for (const c of customers) select.appendChild(new Option(`${c.name || '#' + c.id} • ${c.phone || ''}`, String(c.id)));
    if (chosenCustomerId() && customers.some(c => String(c.id) === chosenCustomerId())) select.value = chosenCustomerId();
    select.dispatchEvent(new Event('change'));
  }
  function setMode(value) {
    mode = value;
    const amount = total();
    if (value === 'full') setPaid(amount);
    else if (value === 'credit') setPaid(0);
    else {
      // Force cashier to enter the amount actually received.
      const current = Number(el('checkoutPaidAmount')?.value || 0);
      if (!Number.isFinite(current) || current >= amount || current < 0) setPaid(0);
    }
    document.querySelectorAll('[data-nano-credit-mode]').forEach(btn => {
      btn.setAttribute('aria-pressed', String(btn.dataset.nanoCreditMode === mode));
    });
    updateOutstanding();
  }
  function updateOutstanding() {
    const paid = Number(el('checkoutPaidAmount')?.value || 0);
    const due = money(Math.max(0, total() - paid));
    const label = el('nanoCreditRemaining');
    if (label) label.textContent = due.toFixed(2) + ' دج';
    const customer = customers.find(c => String(c.id) === chosenCustomerId());
    const identity = el('nanoCreditCustomerSelected');
    if (identity) identity.textContent = customer ? `الزبون: ${customer.name}` : 'لم يُحدّد زبون';
  }
  function installCheckoutControls() {
    const checkout = el('checkoutModal');
    const method = el('checkoutPaymentMethod');
    if (!checkout || !method || el('nanoCreditCheckoutControls')) return;
    const box = document.createElement('div');
    box.id = 'nanoCreditCheckoutControls';
    box.className = 'nano-credit-checkout-controls';
    box.innerHTML = `<h3>طريقة تسديد المبلغ</h3>
       <div class="nano-credit-modes" role="group" aria-label="اختيار الدفع">
         <button type="button" data-nano-credit-mode="full" aria-pressed="true">تسديد كامل</button>
         <button type="button" data-nano-credit-mode="partial" aria-pressed="false">دفع جزء (كريدي)</button>
         <button type="button" data-nano-credit-mode="credit" aria-pressed="false">كريدي كامل</button>
       </div>
       <div class="nano-credit-customer-row"><span id="nanoCreditCustomerSelected">لم يُحدّد زبون</span><button type="button" id="nanoCreditChooseCustomer">جلب زبون</button></div>
       <p class="nano-credit-due-label">المبلغ المتبقي كدين: <strong id="nanoCreditRemaining">0.00 دج</strong></p>`;
    method.parentElement?.before(box);
    box.querySelectorAll('[data-nano-credit-mode]').forEach(btn => btn.addEventListener('click', () => setMode(btn.dataset.nanoCreditMode)));
    el('nanoCreditChooseCustomer').addEventListener('click', openPicker);
    el('checkoutPaidAmount')?.addEventListener('input', () => { mode = 'partial'; updateOutstanding(); });
    // Keep cash / card / CCP as the *received payment channel*, credit is the outstanding balance.
    checkout.addEventListener('click', () => setTimeout(updateOutstanding, 20));
  }
  function installMobileChoice() {
    const choice = el('nanoMobileCheckoutChoice');
    const before = el('nanoMobilePayHereBtn');
    if (!choice || !before || el('nanoMobileCreditChoiceBtn')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'nanoMobileCreditChoiceBtn';
    btn.className = 'nano-mobile-choice-credit';
    btn.innerHTML = '<span class="material-symbols-outlined">payments</span><span><b>بيع بالكريدي / دفع جزئي</b><small>اختر زبونًا وأدخل المبلغ المدفوع، وسيسجّل الباقي كدين</small></span>';
    before.before(btn);
    btn.addEventListener('click', () => { choice.hidden = true; void openPicker(); });
  }
  function validPayment() {
    const amount = Number(el('checkoutPaidAmount')?.value);
    const amountTotal = total();
    if (!Number.isFinite(amount) || amount < 0 || amount > amountTotal + 0.005) {
      notify('المبلغ المدفوع غير صالح؛ يجب أن يكون من صفر إلى قيمة الفاتورة.', 'error');
      return false;
    }
    const debt = money(amountTotal - amount);
    if (debt > 0.005 && !chosenCustomerId()) {
      notify('الدفع الجزئي يتطلب اختيار زبون مسجل حتى يُحفظ الدين على حسابه.', 'error');
      void openPicker();
      return false;
    }
    return true;
  }
  function wrapSaleEntry() {
    if (typeof window.processSale !== 'function' || window.processSale.__nanoCreditWrapped) return;
    const original = window.processSale;
    const wrapped = function (...args) {
      if (!validPayment() || busy) return;
      busy = true;
      // A 30 second UI lock avoids rapid double-taps. The server must still dedupe operation ids.
      const buttons = el('checkoutModal')?.querySelectorAll('button[onclick^="processSale"]') || [];
      buttons.forEach(x => x.disabled = true);
      return Promise.resolve().then(() => original.apply(this, args)).finally(() => {
        busy = false;
        buttons.forEach(x => x.disabled = false);
      });
    };
    wrapped.__nanoCreditWrapped = true;
    window.processSale = wrapped;
  }
  function installDataEvents() {
    if (window.__nanoCreditDataEventsInstalled) return;
    window.__nanoCreditDataEventsInstalled = true;
    // Mobile bridge calls to the authoritative primary PC. Re-fetch statistics on mutations.
    const ipc = window.__browserElectron?.ipcRenderer;
    if (!ipc?.invoke || ipc.invoke.__nanoCreditEventsWrapped) return;
    const oldInvoke = ipc.invoke;
    const financial = new Set(['process-sale','save-purchase','add-sale-payment','add-customer-payment','add-invoice-payment','add-supplier-payment','delete-sale','delete-purchase','save-supplier-return']);
    ipc.invoke = async function (channel, ...args) {
      const result = await oldInvoke.call(this, channel, ...args);
      if (financial.has(channel) && result?.success !== false && !result?.queued) {
        window.dispatchEvent(new CustomEvent('nano-mobile-financial-changed', { detail: { channel } }));
      }
      return result;
    };
    ipc.invoke.__nanoCreditEventsWrapped = true;
    let timer;
    window.addEventListener('nano-mobile-financial-changed', () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const current = document.body?.dataset?.nanoMobileSection || '';
        if (current === 'analyticsSection' && typeof window.loadAnalytics === 'function') void window.loadAnalytics();
        if (current === 'customersSection' && typeof window.loadCustomers === 'function') void window.loadCustomers();
        if (current === 'suppliersSection' && typeof window.loadSuppliers === 'function') void window.loadSuppliers();
        if (chosenCustomerId()) void fetchCustomers().then(updateOutstanding).catch(() => {});
      }, 180);
    });
  }
  function init() {
    installCheckoutControls();
    wrapSaleEntry();
    installDataEvents();
    installMobileChoice();
    const obs = new MutationObserver(() => {
      if (!el('nanoMobileCreditChoiceBtn')) installMobileChoice();
      if (!el('nanoCreditCheckoutControls')) installCheckoutControls();
    });
    obs.observe(document.body, { childList: true, subtree: true });
    window.addEventListener('nano-mobile-data-changed', () => {
      const current = document.body?.dataset?.nanoMobileSection || '';
      if (current === 'analyticsSection' && typeof window.loadAnalytics === 'function') void window.loadAnalytics();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();