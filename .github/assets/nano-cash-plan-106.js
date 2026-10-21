/* NANO POS v1.0.106: integer-cent cash change and practical DZD note/coin counts.
 * Pure calculations; no writes to stock, ledger or local storage.
 */
(function(root){
 'use strict';
 const CURRENCY='DZD';
 const denominations=Object.freeze([2000,1000,500,200,100,50,20,10,5,2,1]);
 function cents(input){
   const raw=String(input??'').trim().replace(/[٠-٩]/g,x=>String(x.charCodeAt(0)-1632))
     .replace(/[۰-۹]/g,x=>String(x.charCodeAt(0)-1776))
     .replace(/\s/g,'').replace(',','.');
   if(!/^\d+(?:\.\d{1,2})?$/.test(raw))return null;
   const [whole,dec='']=raw.split('.');
   const parsed=BigInt(whole)*100n+BigInt(dec.padEnd(2,'0')||'0');
   return parsed>100000000000n?null:Number(parsed);
 }
 function format(value){return (value/100).toFixed(2);}
 function plan(totalInput,tenderInput){
   const total=cents(totalInput),tender=cents(tenderInput);
   if(total===null||tender===null)return {ok:false,code:'invalid_amount'};
   if(tender<total)return {ok:false,code:'cash_insufficient',shortfallCents:total-tender};
   const change=tender-total;
   let whole=Math.floor(change/100);
   const pieces=[];
   for(const amount of denominations){
     const count=Math.floor(whole/amount);
     if(count)pieces.push({denomination:amount,count});
     whole%=amount;
   }
   return {ok:true,currency:CURRENCY,totalCents:total,tenderCents:tender,
     changeCents:change,pieces,centimes:change%100};
 }
 const api=Object.freeze({plan,cents,format,denominations});
 root.NANO_CASH_PLAN_106=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
