/* NANO POS v1.0.104 — full payment or full customer credit; no received-amount entry. */
(function(root){
 'use strict';
 const doc=root.document;
 function paidInput(){return doc?.getElementById('checkoutPaidAmount');}
 function readTotal(){
   const el=doc?.getElementById('checkoutTotalUI');
   const raw=String(el?.textContent||'').replace(/[٠-٩]/g,c=>String(c.charCodeAt(0)-1632))
     .replace(/[۰-۹]/g,c=>String(c.charCodeAt(0)-1776)).replace(/,/g,'.');
   const match=raw.match(/\d+(?:\.\d{1,2})?/);
   const number=Number(match?.[0]||0);
   return Number.isFinite(number)&&number>=0?Math.round(number*100)/100:0;
 }
 function paidFull(){
   const input=paidInput();if(!input)return;
   input.value=readTotal().toFixed(2);
   input.dispatchEvent(new Event('input',{bubbles:true}));
   if(typeof root.checkoutCalcChange==='function')root.checkoutCalcChange();
 }
 // Preserve existing business rule: the full-credit button sets paidAmount=0;
 // the backend requires a registered customer for an unpaid checkout.
 root.nanoCheckoutPayFull104=paidFull;
})(typeof window!=='undefined'?window:globalThis);
