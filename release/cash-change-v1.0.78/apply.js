/* Apply NANO POS v1.0.78 cash tender and durable change audit to verified v1.0.77. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Missing ASAR extraction directory');
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
const write=(f,v)=>fs.writeFileSync(path.join(root,f),v,'utf8');
function one(t,oldPart,newPart,label){
 const count=t.split(oldPart).length-1;
 if(count!==1)throw Error('Expected once: '+label+'; found '+count);
 return t.replace(oldPart,newPart);
}
let txt=read('browser-bridge.js');
txt=one(txt,"   sales: [],","   sales: [],\n   cash_change_audit: [],","audit collection initialization");
txt=one(txt,"     const customer = (db.customers || []).find(v => String(v.id) === String(c.customerId));\n     if (remaining > 0 && !customer) return fail('البيع بالدين أو التسديد الجزئي يتطلب اختيار زبون مسجّل.');","     const customer = (db.customers || []).find(v => String(v.id) === String(c.customerId));\n     if (remaining > 0 && !customer) return fail('البيع بالدين أو التسديد الجزئي يتطلب اختيار زبون مسجّل.');\n     // Persist calculated change in cents; this is not evidence of physical handover.\n     let cashRecord = null;\n     if (c.cashTenderedAmount !== undefined && c.cashTenderedAmount !== null) {\n       const tendered = Number(c.cashTenderedAmount);\n       const paidCents = Math.round(paid * 100);\n       const tenderCents = Math.round(tendered * 100);\n       const totalCents = Math.round(total * 100);\n       if ((c.paymentMethod || 'cash') !== 'cash' ||\n           !Number.isFinite(tendered) || tendered < 0 ||\n           !Number.isSafeInteger(tenderCents) || tenderCents > 100000000000 ||\n           Math.abs(tendered * 100 - tenderCents) > 0.001 ||\n           paidCents < 0 || paidCents > totalCents ||\n           tenderCents < paidCents) {\n         return fail('المبلغ النقدي المستلم أو الصرف غير صالح.');\n       }\n       cashRecord = {\n         sale_total: rounded(totalCents/100),\n         cash_tendered_amount: rounded(tenderCents/100),\n         cash_applied_amount: rounded(paidCents/100),\n         cash_change_due: rounded((tenderCents-paidCents)/100),\n       };\n     }","strict validation before stock mutation");
txt=one(txt,"     db.sales.unshift(sale);\n     if (remaining > 0) reviseCustomerBalance(customer.id,remaining);\n     save();","     if (cashRecord) {\n       const audit = {\n         sale_id: id,\n         recorded_at: date,\n         cashier_user_id: data.userId || 1,\n         cashier_name: sale.user_name,\n         caisse_session_id: activeSession?.id || null,\n         customer_id: customer?.id ?? null,\n         ...cashRecord\n       };\n       sale.cash_tendered_amount = audit.cash_tendered_amount;\n       sale.cash_applied_amount = audit.cash_applied_amount;\n       sale.cash_change_amount = audit.cash_change_due;\n       sale.cash_change_record = clone(audit);\n       db.cash_change_audit = Array.isArray(db.cash_change_audit) ? db.cash_change_audit : [];\n       db.cash_change_audit.unshift(audit);\n     }\n     db.sales.unshift(sale);\n     if (remaining > 0) reviseCustomerBalance(customer.id,remaining);\n     save();","atomic sale and independent audit append");
txt=one(txt,"   if (channel === 'get-sale-details') {","   if (channel === 'get-cash-change-audit') {\n     const requested = Number(args[0]?.limit || 300);\n     const limit = Math.max(1, Math.min(1000, Number.isFinite(requested) ? requested : 300));\n     return clone((db.cash_change_audit || []).slice(0,limit));\n   }\n   if (channel === 'get-sale-details') {","audit reader");
txt=one(txt,
  "     save();\n     return { success:true,id,saleId:id,paid_amount:sale.paid_amount,remaining_amount:remaining,customerId:sale.customer_id };",
  "     save();\n     if (cashRecord) {\n       try {\n         const persisted = JSON.parse(localStorage.getItem(KEY) || '{}');\n         if (!(persisted.cash_change_audit || []).some(entry => String(entry.sale_id) === String(id)))\n           return fail('تعذر حفظ سجل الصرف. يرجى التحقق من مساحة التخزين.');\n       } catch { return fail('تعذر التحقق من حفظ سجل الصرف.'); }\n     }\n     return { success:true,id,saleId:id,paid_amount:sale.paid_amount,remaining_amount:remaining,customerId:sale.customer_id };",
  'verify persisted journal before acknowledging the sale');
write('browser-bridge.js',txt);
txt=read('browser-preload.js');
txt=one(txt,"'getSales':_0x3a847b=>_invoke('get-sales',_0x3a847b),","'getSales':_0x3a847b=>_invoke('get-sales',_0x3a847b),'getCashChangeAudit':_0x52a=>_invoke('get-cash-change-audit',_0x52a),","read-only API");
write('browser-preload.js',txt);
txt=read('renderer.js');
const startRegex=/async function executeSalePayload\([^)]*\)\s*\{[\s\S]{0,250}?\btry\s*\{/g;
const matches=[...txt.matchAll(startRegex)];
if(matches.length!==1)throw Error('Cannot identify executeSalePayload entry; found '+matches.length);
const begin=matches[0][0];
const hook="if(window.NANO_CASH_CHANGE_178 && typeof window.NANO_CASH_CHANGE_178.prepare==='function'){" +
 "const checked=window.NANO_CASH_CHANGE_178.prepare(arguments[0]);" +
 "if(!checked.ok){showToast(checked.message,'error');return;}" +
 "}";
txt=txt.replace(begin,begin+hook);
const quick=/return\s+processSaleDirectly\s*\(\s*\)\s*;/g;
const quickMatches=[...txt.matchAll(quick)];
if(quickMatches.length!==1)throw Error('Cannot identify quick sale action; found '+quickMatches.length);
txt=txt.replace(quick,'return openCheckoutModal();');
write('renderer.js',txt);
txt=read('index.html');
txt=one(txt,"</head>","<link rel=\"stylesheet\" href=\"nano-cash-change.css\" />\n</head>","cash change CSS");
txt=one(txt,"</body>","<script defer src=\"nano-cash-change.js\"></script>\n</body>","cash change JS");
write('index.html',txt);
for(const name of ['cash-change.js','cash-change.css'])
 fs.copyFileSync(path.join(__dirname,name),path.join(root,'nano-'+name));
const pkg=JSON.parse(read('package.json'));
if(pkg.version!=='1.0.77')throw Error('Unexpected version: '+pkg.version);
pkg.version='1.0.78';write('package.json',JSON.stringify(pkg,null,2)+'\n');
if(fs.existsSync(path.join(root,'package-lock.json'))){
 const lock=JSON.parse(read('package-lock.json'));lock.version='1.0.78';
 if(lock.packages?.[''])lock.packages[''].version='1.0.78';
 write('package-lock.json',JSON.stringify(lock,null,2)+'\n');
}
console.log('v1.0.78 cash tender and durable change audit installed');
