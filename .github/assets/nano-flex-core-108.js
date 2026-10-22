/* NANO POS 1.0.108 — decimal-safe single-method checkout plan. */
(function(root){
 'use strict';
 function cents(v){
   const s=String(v??'').trim().replace(/[٠-٩]/g,x=>String(x.charCodeAt(0)-1632))
     .replace(/[۰-۹]/g,x=>String(x.charCodeAt(0)-1776)).replace(/\s/g,'').replace(',','.');
   if(!/^\d+(?:\.\d{1,2})?$/.test(s))return null;
   const [a,b='']=s.split('.');const n=BigInt(a)*100n+BigInt((b+'00').slice(0,2));
   return n>100000000000n?null:Number(n);
 }
 const format=v=>(v/100).toFixed(2);
 function plan(totalValue,tenderValue,method,customerId){
   const total=cents(totalValue),tender=cents(tenderValue);
   if(total===null||tender===null)return {ok:false,error:'invalid_amount'};
   const payment=String(method||'cash');
   if(!['cash','card','cheque','ccp','virement','transfer','other'].includes(payment))
     return {ok:false,error:'invalid_method'};
   if(tender>total&&payment!=='cash')return {ok:false,error:'overpayment_requires_cash'};
   const paid=Math.min(total,tender),debt=total-paid,change=Math.max(0,tender-total);
   if(debt>0&&!String(customerId??'').trim())return {ok:false,error:'customer_required',
     totalCents:total,paidCents:paid,debtCents:debt,changeCents:0};
   return {ok:true,totalCents:total,tenderCents:tender,paidCents:paid,
     debtCents:debt,changeCents:change,method:payment};
 }
 const api=Object.freeze({cents,format,plan});
 root.NANO_FLEX_CORE_108=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
