#!/usr/bin/env python3
"""Patch existing NANO POS browser adapter for monetary consistency.
Anchored replacements deliberately fail closed on unexpected upstream builds.
"""
import sys
from pathlib import Path

def patch(data):
    def change(old,new,label):
        nonlocal data
        if data.count(old)!=1:raise ValueError(f'{label}: expected one anchor, got {data.count(old)}')
        data=data.replace(old,new,1)
    change(" const rounded = n => Math.round(Number(n || 0) * 100) / 100;", """ const rounded = n => Math.round(Number(n || 0) * 100) / 100;
 const invoiceDebt = sale => Math.max(0, rounded(Number(sale?.total || 0) - Number(sale?.paid_amount || 0)));
 const customerInvoiceDebt = id => rounded((db.sales || []).filter(s => String(s.customer_id) === String(id)).reduce((sum,s) => sum + invoiceDebt(s), 0));
 const customerVisibleDebt = customer => rounded(Math.max(0, Number(customer?.balance || 0), customerInvoiceDebt(customer?.id)));
 function reviseCustomerBalance(id, delta) {
   const customer = (db.customers || []).find(c => String(c.id) === String(id));
   if (customer && Number.isFinite(delta)) customer.balance = rounded(Math.max(0, Number(customer.balance || 0) + delta));
 }""",'ledger helpers')
    # Initial cash receipt belongs to the sale session, not later debt settlements.
    # Legacy data without initial_paid_amount remains backward compatible.
    change(".reduce((sum, sale) => sum + Number(sale.paid_amount || sale.total || 0), 0));",
           ".reduce((sum, sale) => sum + Number(sale.initial_paid_amount ?? sale.paid_amount ?? sale.total ?? 0), 0));",
           'cash summary initial receipt')
    # Full replacement of local sale operation retains original output contract.
    sale_start=data.index("   if (channel === 'process-sale') {")
    sale_end=data.index("   if (channel === 'get-sales') {",sale_start)
    sale="""   if (channel === 'process-sale') {
     const data = args[0] || {}, c = data.checkout || {};
     if (!Array.isArray(data.items) || !data.items.length) return fail('السلة فارغة');
     const subtotal = rounded(c.subtotal ?? data.items.reduce((sum, item) => sum + Number(item.qty || 0) * Number(item.pos_price || 0), 0));
     const discount = rounded(c.discount ?? 0);
     const taxPercentage = Number(c.taxPercentage || 0);
     const total = rounded(c.total ?? Math.max(0, subtotal - discount) * (1 + taxPercentage / 100));
     const paid = Number(c.paidAmount ?? total);
     if (![subtotal,discount,taxPercentage,total,paid].every(Number.isFinite) || total < 0 || paid < 0 || paid > total + 0.005) return fail('المبلغ المدفوع أو قيمة الفاتورة غير صالح.');
     const remaining = rounded(Math.max(0,total-paid));
     const customer = (db.customers || []).find(v => String(v.id) === String(c.customerId));
     if (remaining > 0 && !customer) return fail('البيع بالدين أو التسديد الجزئي يتطلب اختيار زبون مسجّل.');
     const quantities = new Map();
     for (const i of data.items) {
       const qty = Number(i.qty), price = Number(i.pos_price);
       if (!(qty > 0) || !Number.isFinite(qty) || !Number.isFinite(price) || price < 0) return fail('تحقق من كميات وأسعار المنتجات.');
       if (i.is_custom) continue;
       const id = i.batch_id;
       quantities.set(id, (quantities.get(id) || 0) + qty);
     }
     for (const [batchId, qty] of quantities) {
       const p = db.products.find(p => (p.batches || []).some(b => String(b.id) === String(batchId)));
       const b = p?.batches.find(b => String(b.id) === String(batchId));
       if (b && qty > Number(b.stock || 0) + 0.000001 && !data.allowNegativeStock) return fail('كمية البيع تتجاوز المخزون المتوفر.');
     }
     // Validate all monetary and stock constraints before touching persistent records.
     for (const [batchId,qty] of quantities) {
       const p = db.products.find(p => (p.batches || []).some(b => String(b.id) === String(batchId)));
       const b = p?.batches.find(b => String(b.id) === String(batchId));
       if (b) { b.stock = rounded(Number(b.stock || 0) - qty); normalize(p); }
     }
     const id=ids(),date=new Date().toISOString();
     const items=data.items.map(i => {
       const p=db.products.find(p => String(p.id)===String(i.id)) || i.product || {};
       return {...clone(i), product_id:i.id,product_name:p.name || i.custom_product_name || '',name:p.name || i.custom_product_name || '',barcode:p.barcode || '',unit:p.unit || '',quantity:Number(i.qty),selling_price:Number(i.pos_price),price:Number(i.pos_price),total:rounded(Number(i.qty)*Number(i.pos_price)),cost_price:Number(p.cost_price || i.custom_cost_price || 0)};
     });
     const activeSession=activeCaisseSession(data.userId || 1);
     const sale={ id,created_at:date,sale_date:date,customer_id:customer?.id ?? null,customer_name:customer?.name || '',user_id:data.userId || 1,user_name:db.users[0]?.name || 'مدير المتجر',caisse_session_id:activeSession?.id || null,subtotal,discount,tax_percentage:taxPercentage,total,paid_amount:rounded(paid),initial_paid_amount:rounded(paid),remaining_amount:remaining,payment_method:paid > 0 ? (c.paymentMethod || 'cash') : 'credit',payment_status:remaining > 0 ? (paid ? 'partial' : 'credit') : 'paid',received_payment_method:c.paymentMethod || 'cash',items_count:items.length,items_qty:items.reduce((s,i)=>s+i.quantity,0),payments:[],items };
     db.sales.unshift(sale);
     if (remaining > 0) reviseCustomerBalance(customer.id,remaining);
     save();
     return { success:true,id,saleId:id,paid_amount:sale.paid_amount,remaining_amount:remaining,customerId:sale.customer_id };
   }
"""
    # Retain the original return/negative-quantity flow rather than changing refund semantics.
    original_sale = data[sale_start:sale_end]
    prefix = "   if (channel === 'process-sale') {"
    assert original_sale.startswith(prefix)
    original_body = original_sale[len(prefix):].rsplit('\n   }',1)[0]
    sale = sale.replace("     const data = args[0] || {}, c = data.checkout || {};", "     if ((args[0]?.items || []).some(i => Number(i.qty) < 0)) {"+original_body+"\n     }\n     const data = args[0] || {}, c = data.checkout || {};", 1)
    data=data[:sale_start]+sale+data[sale_end:]
    change("payments: [], customer: db.customers.find(v => v.id == s.customer_id) || null", "payments: clone(s.payments || []), customer: db.customers.find(v => v.id == s.customer_id) || null",'sale details')
    change("       db.sales = db.sales.filter(v => v.id != id);", "       if (s.customer_id != null) reviseCustomerBalance(s.customer_id, -invoiceDebt(s));\n       db.sales = db.sales.filter(v => v.id != id);",'sale deletion')
    change("""   if (channel === 'add-sale-payment') {
     const s = db.sales.find(v => v.id == args[0]), amount = Number(args[1] || 0);
     if (s) { s.paid_amount = Number(s.paid_amount || 0) + amount; s.remaining_amount = Math.max(0, s.total - s.paid_amount); save(); }
     return { success: true };
   }""", """   if (channel === 'add-sale-payment') {
     const s=(db.sales || []).find(v => String(v.id) === String(args[0]));
     if (!s) return fail('فاتورة البيع غير موجودة');
     const amount=rounded(args[1]);
     const balance=invoiceDebt(s);
     if (!(amount>0) || !Number.isFinite(amount) || amount>balance+0.005) return fail('مبلغ التسديد غير صالح أو يتجاوز الدين المتبقي.');
     s.paid_amount=rounded(Number(s.paid_amount || 0)+amount);
     s.remaining_amount=invoiceDebt(s);
     s.payments=Array.isArray(s.payments)?s.payments:[];
     s.payments.push({ id:ids(),amount,date:args[2] || new Date().toISOString(),note:args[3] || '' });
     if (s.customer_id != null) reviseCustomerBalance(s.customer_id,-amount);
     save();
     return { success:true,paid_amount:s.paid_amount,remaining_amount:s.remaining_amount };
   }""",'sale payment')
    change("""   if (channel === 'add-customer-payment') {
     const c = db.customers.find(v => v.id == args[0]);
     if (c) { c.balance = Math.max(0, Number(c.balance || 0) - Number(args[1] || 0)); save(); }
     return { success: true };
   }
   if (channel === 'get-customers-debt') return db.customers.filter(c => Number(c.balance) > 0);
   if (channel === 'get-customer-credit-summary') return { balance: 0, debt: 0, credit: 0 };""", """   if (channel === 'add-customer-payment') {
     const c=(db.customers || []).find(v => String(v.id)===String(args[0]));
     if (!c) return fail('الزبون غير موجود');
     const amount=rounded(args[1]), available=customerVisibleDebt(c);
     if (!(amount>0) || !Number.isFinite(amount) || amount>available+0.005) return fail('مبلغ التسديد يتجاوز دين الزبون.');
     let unpaid=amount;
     for (const sale of (db.sales || []).filter(s=>String(s.customer_id)===String(c.id)).sort((a,b)=>new Date(a.sale_date||a.created_at)-new Date(b.sale_date||b.created_at))) {
       if (unpaid<=0) break;
       const allocated=rounded(Math.min(unpaid,invoiceDebt(sale)));
       if (allocated<=0) continue;
       sale.paid_amount=rounded(Number(sale.paid_amount||0)+allocated);
       sale.remaining_amount=invoiceDebt(sale);
       sale.payments=Array.isArray(sale.payments)?sale.payments:[];
       sale.payments.push({id:ids(),amount:allocated,date:args[2]||new Date().toISOString(),note:args[3]||'',source:'customer-payment'});
       unpaid=rounded(unpaid-allocated);
     }
     reviseCustomerBalance(c.id,-amount);
     if (unpaid>0 && Number(c.initial_debt)>0) c.initial_debt=rounded(Math.max(0,Number(c.initial_debt)-unpaid));
     db.customer_payments=Array.isArray(db.customer_payments)?db.customer_payments:[];
     const payment={id:ids(),customer_id:c.id,amount,date:args[2]||new Date().toISOString(),note:args[3]||'',unallocated:unpaid};
     db.customer_payments.unshift(payment);
     save();
     return {success:true,payment,remaining_balance:customerVisibleDebt(c)};
   }
   if (channel === 'get-customers-debt') return clone(db.customers.map(c=>({...c,balance:customerVisibleDebt(c)})).filter(c=>c.balance>0));
   if (channel === 'get-customer-credit-summary') {
     const c=(db.customers||[]).find(v=>String(v.id)===String(args[0]));
     const debt=c?customerVisibleDebt(c):0;
     return {balance:debt,debt,credit:0,credit_limit:Number(c?.credit_limit||0),invoice_debt:c?customerInvoiceDebt(c.id):0};
   }""",'customer settlement and credit summary')
    # Critical: supplier debt must go down following supplier-wide payment allocation.
    change("""       remaining = rounded(remaining - allocated);
     }
     save();
     return { success: true, id: payment.id, payment: clone(payment), unallocated: remaining };""","""       remaining = rounded(remaining - allocated);
     }
     changeSupplierDebt(supplier.id,-rounded(amount-remaining));
     save();
     return { success: true, id: payment.id, payment: clone(payment), unallocated: remaining };""",'supplier payment allocation')
    change("""const customerDebts = (db.customers || []).filter(c => Number(c.balance || 0) > 0).map(c => ({ customer_id:c.id, name:c.name||'', debt:Number(c.balance||0) }));""","""const customerDebts = (db.customers || []).map(c => ({ customer_id:c.id, name:c.name||'', debt:customerVisibleDebt(c) })).filter(c=>c.debt>0);""",'customer analytics')
    change("""debt: rounded(Number(supplier.balance ?? (totalPurchases-totalPaid) ?? 0)), open_invoices:""","""debt: rounded(Math.max(0, Number(supplier.balance || 0), allPurchases.reduce((sum,p)=>sum+purchaseDebt(p),0))), open_invoices:""",'supplier analytics')
    return data

if __name__=='__main__':
    for file in sys.argv[1:]:
        path=Path(file)
        data=path.read_text(encoding='utf-8')
        changed=patch(data)
        path.write_text(changed,encoding='utf-8')
        print(path, 'patched',len(changed)-len(data))