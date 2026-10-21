/* NANO POS — validated multi-method checkout + idempotent debt settlement.
   Pure state planner. Caller MUST persist next in a single verified atomic commit. */
(function(root){
 'use strict';
 const err=code=>{const e=new Error(code);e.code=code;throw e;};
 const id=v=>String(v??'').trim();
 const asCents=v=>{
  const s=String(v??'').trim();
  if(!/^\d+(?:\.\d{1,2})?$/.test(s))err('invalid_amount');
  const [whole,frac='']=s.split('.');
  const total=BigInt(whole)*100n+BigInt(frac.padEnd(2,'0')||'0');
  if(total>BigInt(Number.MAX_SAFE_INTEGER))err('amount_out_of_range');
  return Number(total);
 };
 const money=n=>Number((n/100).toFixed(2));
 const methods=new Set(['cash','card','cheque','ccp','virement','transfer','other']);
 function split(total,rows,customerId){
  if(!Array.isArray(rows)||!rows.length||rows.length>12)err('invalid_payments');
  const limit=asCents(total);let paid=0;
  const seen=new Set(),payments=[];
  for(const row of rows){
   const method=id(row?.method).toLowerCase();
   if(!methods.has(method)||seen.has(method))err('invalid_payment_method');
   seen.add(method);
   const amount=asCents(row?.amount);
   if(amount<=0)err('invalid_amount');
   paid+=amount;if(!Number.isSafeInteger(paid)||paid>limit)err('overpayment');
   payments.push({method,amount:money(amount)});
  }
  const debt=limit-paid;
  if(debt>0&&!id(customerId))err('credit_needs_customer');
  return {paidCents:paid,debtCents:debt,totalCents:limit,
   paidAmount:money(paid),remainingAmount:money(debt),paymentMethod:payments.length>1?'mixed':payments[0].method,
   payments};
 }
 function settle(db,req){
  if(!db||!req||typeof req!=='object')err('invalid_request');
  const target=req.kind==='sale'?'sales':req.kind==='purchase'?'purchases':null;
  if(!target)err('invalid_document_kind');
  const requestId=id(req.requestId);
  if(!/^[a-zA-Z0-9_.:-]{12,128}$/.test(requestId))err('invalid_operation_id');
  const channel=id(req.method).toLowerCase();
  if(!methods.has(channel))err('invalid_payment_method');
  const amount=asCents(req.amount);
  if(amount<=0)err('invalid_amount');
  const documentId=id(req.documentId);
  const all=(db[target]||[]);const found=all.find(x=>id(x.id)===documentId);
  if(!found)err('document_not_found');
  const records=Array.isArray(db.nano_payment_ledger)?db.nano_payment_ledger:[];
  const existing=records.find(x=>x.requestId===requestId);
  if(existing){
    if(existing.documentId!==documentId||existing.kind!==req.kind||existing.amountCents!==amount||
      existing.method!==channel)err('operation_reuse_conflict');
    return {duplicate:true,next:null,result:{success:true,alreadyProcessed:true,paymentId:existing.paymentId}};
  }
  const total=asCents(found.total??0),paid=asCents(found.paid_amount??0);
  if(paid>total)err('inconsistent_paid_balance');
  if(amount>total-paid)err('payment_exceeds_debt');
  const customerId=id(found.customer_id),supplierId=id(found.supplier_id);
  const accountKey=req.kind==='sale'?'customers':'suppliers',accountId=req.kind==='sale'?customerId:supplierId;
  const account=(db[accountKey]||[]).find(x=>id(x.id)===accountId);
  if(!account)err('account_not_found');
  const existingBalance=asCents(account.balance||'0');
  if(existingBalance<amount)err('account_balance_inconsistent');
  const next=JSON.parse(JSON.stringify(db)),document=next[target].find(x=>id(x.id)===documentId);
  const matched=next[accountKey].find(x=>id(x.id)===accountId);
  const paymentId='NANO-PAY-'+requestId,date=new Date().toISOString();
  document.paid_amount=money(paid+amount);
  document.remaining_amount=money(total-paid-amount);
  if(req.kind==='sale')document.payment_status=total-paid-amount>0?'partial':'paid';
  document.payments=Array.isArray(document.payments)?document.payments:[];
  document.payments.push({id:paymentId,request_id:requestId,method:channel,
    amount:money(amount),date,source:'verified-settlement'});
  matched.balance=money(existingBalance-amount);
  next.nano_payment_ledger=Array.isArray(next.nano_payment_ledger)?next.nano_payment_ledger:[];
  next.nano_payment_ledger.push({requestId,paymentId,documentId,kind:req.kind,amountCents:amount,
    method:channel,created_at:date});
  next.audit_log=Array.isArray(next.audit_log)?next.audit_log:[];
  next.audit_log.push({at:date,operation:'verified_payment',record_id:documentId,
    request_id:requestId,method:channel,amount:money(amount)});
  next.revision=Number(next.revision||0)+1;
  return {duplicate:false,next,result:{success:true,paymentId,paidAmount:document.paid_amount,
    remainingAmount:document.remaining_amount,accountBalance:matched.balance}};
 }
 const api=Object.freeze({split,settle,asCents});
 root.NANO_PAYMENT_LEDGER_102=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
