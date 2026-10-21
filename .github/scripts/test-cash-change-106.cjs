'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require('jsdom'),change=require('./nano-cash-plan-106.js');
const money=v=>change.format(v);
assert.equal(change.cents('١٢٣٤,٥٠'),123450);
assert.equal(change.cents('12.345'),null);
assert.equal(change.cents('-1'),null);
assert.deepEqual(change.plan('1480','2000').pieces,[{denomination:500,count:1},{denomination:20,count:1}]);
assert.equal(change.plan('1480','2000').changeCents,52000);
assert.deepEqual(change.plan('1730','2000').pieces,[{denomination:200,count:1},{denomination:50,count:1},{denomination:20,count:1}]);
assert.equal(change.plan('100.01','200.02').centimes,1);
assert.equal(change.plan('100','99').code,'cash_insufficient');
let seed=20261021;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
for(let k=0;k<3000;k++){
 const total=rand()%10000000,given=total+(rand()%300000);
 const result=change.plan(money(total),money(given));
 assert.equal(result.ok,true);
 assert.equal(result.changeCents,given-total);
 const matched=result.pieces.reduce((sum,item)=>sum+item.count*item.denomination*100,0)+result.centimes;
 assert.equal(matched,given-total,'denomination totals must equal exact change');
}
(async()=>{
 const html=fs.readFileSync('index.html','utf8');
 assert.ok(html.includes('src="nano-cash-plan-106.js"')&&html.includes('src="nano-cash-guide-106.js"'));
 assert.ok(!html.includes('src="nano-split-ui-102.js"'));
 const dom=new JSDOM('<!doctype html><html lang="ar"><body>'+
  '<div id="checkoutModal" class="hidden">'+
  '<div id="checkoutTotalUI">1480.00 د.ج</div>'+
  '<select id="checkoutPaymentMethod"><option value="cash">Cash</option><option value="card">Card</option></select>'+
  '<div id="nanoCheckoutChoice104"><input id="checkoutPaidAmount" type="hidden" value="1480.00"></div>'+
  '<button onclick="processSale()">Confirm</button></div></body></html>',{
   url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,d=w.document;
 let calls=0,lastPayload=null;
 w.__browserElectron={ipcRenderer:{invoke:async(name,payload)=>{
  calls++;lastPayload=payload;return {success:true,id:1};
 }}};
 w.eval(fs.readFileSync('nano-cash-plan-106.js','utf8'));
 w.eval(fs.readFileSync('nano-cash-guide-106.js','utf8'));
 const panel=d.getElementById('nanoCashGuide106'),tender=d.getElementById('nanoCashTendered106');
 assert.ok(panel);assert.ok(panel.hidden);
 d.getElementById('checkoutModal').classList.remove('hidden');
 await new Promise(r=>setTimeout(r,5));
 assert.equal(panel.hidden,false);
 tender.value='2000';tender.dispatchEvent(new w.Event('input',{bubbles:true}));
 assert.equal(d.getElementById('nanoCashChange106').textContent,'520.00 د.ج');
 assert.ok(d.getElementById('nanoCashBreakdown106').textContent.includes('500'));
 assert.ok(d.getElementById('nanoCashBreakdown106').textContent.includes('20'));
 const create=()=>w.__browserElectron.ipcRenderer.invoke('process-sale',{items:[{id:3,qty:1,pos_price:1480}],
   checkout:{total:1480,paidAmount:1480,paymentMethod:'cash'}});
 await create();
 assert.equal(calls,1);
 assert.equal(lastPayload.checkout.cashTenderedAmount,'2000.00');
 assert.equal(lastPayload.checkout.paidAmount,1480);
 tender.value='1000';tender.dispatchEvent(new w.Event('input',{bubbles:true}));
 const rejected=await create();assert.equal(rejected.success,false);
 assert.equal(calls,1,'short cash never reaches stock posting');
 const input=d.getElementById('checkoutPaymentMethod');
 input.value='card';input.dispatchEvent(new w.Event('change',{bubbles:true}));
 assert.equal(panel.hidden,true);
 await w.__browserElectron.ipcRenderer.invoke('process-sale',{items:[{id:3,qty:1,pos_price:1480}],
   checkout:{total:1480,paidAmount:1480,paymentMethod:'card',cashTenderedAmount:2000}});
 assert.equal(calls,2);assert.ok(!('cashTenderedAmount' in lastPayload.checkout),'no cash record on card payment');
 input.value='cash';input.dispatchEvent(new w.Event('change',{bubbles:true}));
 d.getElementById('checkoutPaidAmount').value='0';
 d.getElementById('checkoutPaidAmount').dispatchEvent(new w.Event('input',{bubbles:true}));
 assert.equal(panel.hidden,true,'no cash tender on full credit sale');
 await w.__browserElectron.ipcRenderer.invoke('process-sale',{items:[{id:3,qty:1,pos_price:1480}],
   checkout:{total:1480,paidAmount:0,customerId:7,paymentMethod:'cash'}});
 assert.equal(calls,3,'credit still works without cash tender');
 assert.ok(!('cashTenderedAmount' in lastPayload.checkout));
 dom.window.close();
 console.log('PASS: 3000 change/denomination invariants, tender UI, short cash blocked, single method and credit preserved');
})().catch(e=>{console.error(e);process.exitCode=1});
