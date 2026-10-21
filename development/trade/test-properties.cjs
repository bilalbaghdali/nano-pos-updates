'use strict';
const assert=require('node:assert/strict');
const {purchaseTotal,receiptPlan,splitPayment,targetSellPrice,returnPlan}=require('./trade-domain.cjs');
let seed=9719845;
const next=()=>{seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed;};
const N=(low,high)=>low+(next()%(high-low+1));
for(let iteration=0;iteration<2000;iteration++){
 const rows=Array.from({length:N(1,40)},(_,i)=>({lineId:'line-'+i,quantity:String(N(1,100))+'.'+String(N(0,999)).padStart(3,'0'),unitCost:String(N(0,1000))+'.'+String(N(0,99)).padStart(2,'0')}));
 const extra={freight:String(N(0,1000))+'.'+String(N(0,99)).padStart(2,'0'),otherFees:String(N(0,40)),nonrecoverableTax:'0'};
 const before=JSON.stringify(rows);
 const calc=purchaseTotal(rows,extra);
 assert.equal(calc.lines.reduce((sum,x)=>sum+x.baseCents,0),calc.subtotalCents);
 assert.equal(calc.lines.reduce((sum,x)=>sum+x.allocatedChargesCents,0),calc.extraCents);
 assert.equal(calc.lines.reduce((sum,x)=>sum+x.landedCents,0),calc.totalCents);
 assert.equal(JSON.stringify(rows),before);
 const ordered=N(1,100),previouslyReceived=N(0,ordered),delivery=N(1,Math.max(1,ordered-previouslyReceived));
 const prior=previouslyReceived?[{receiptId:'previous-valid-receipt-0001',lines:[{lineId:'x',quantity:previouslyReceived}]}]:[];
 if(delivery<=ordered-previouslyReceived){
   const r=receiptPlan([{lineId:'x',quantity:ordered}],prior,{receiptId:'current-valid-receipt-0002',lines:[{lineId:'x',quantity:delivery}]});
   assert.equal(r.duplicate,false);assert.equal(r.movements[0].qtyMilli,delivery*1000);
 }
 const due=N(1,100000)/100,cash=N(0,Math.floor(due*100))/100;
 const split=splitPayment(due.toFixed(2),[{method:'cash',amount:cash.toFixed(2)}]);
 assert.equal(split.paidCents+split.debtCents,split.dueCents);
 const margin=targetSellPrice(String(N(0,10000)),String(N(0,9900)/100));
 assert.ok(margin.sellingPriceCents>=0);
 assert.equal(returnPlan([{lineId:'x',quantity:ordered}],[],[{lineId:'x',quantity:1}]).movements.length,1);
}
console.log('PASS: 2,000 deterministic inventory/cost/payments/returns invariant trials');
