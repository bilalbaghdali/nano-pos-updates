'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const run=async()=>{
 const source=fs.readFileSync('index.html','utf8');
 assert.ok(source.includes('src="nano-payment-quality-105.js"'));
 assert.ok(!source.includes('src="nano-split-ui-102.js"'));
 assert.ok(!source.includes('data-i18n="amount_received_label"'));
 const html='<!doctype html><html lang="ar"><body>'+
 '<select id="posCustomerSelect"><option value="">—</option><option value="7">Customer</option></select>'+
 '<div id="checkoutModal" class="hidden">'+
 '<div id="checkoutTotalUI">100.00 د.ج</div>'+
 '<select id="checkoutPaymentMethod"><option value="cash">نقدًا</option><option value="card">بطاقة</option></select>'+
 '<div id="nanoCheckoutChoice104"><input type="hidden" id="checkoutPaidAmount" value="100.00">'+
 '<button onclick="nanoCheckoutPayFull104()">دفع كامل</button>'+
 '<button onclick="checkoutMarkAsDebt()">دين كامل</button></div>'+
 '<button id="confirm" onclick="processSale()">تأكيد الفاتورة</button>'+
 '<button id="print" onclick="processSaleAndPrintReceipt()">طباعة</button>'+
 '</div></body></html>';
 const dom=new JSDOM(html,{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,d=w.document;let invocations=0,finished;
 w.currentLanguage='ar';w.showToast=()=>{};
 w.__browserElectron={ipcRenderer:{invoke:async (channel,payload)=>{
   if(channel==='process-sale'){
     invocations++;assert.match(payload.checkout.nanoCheckoutRequestId,/^n105-/);
     return {success:true,saleId:77};
   }
   return {success:false};
 }}};
 w.eval(fs.readFileSync('nano-checkout-choice-104.js','utf8'));
 w.eval(fs.readFileSync('nano-payment-quality-105.js','utf8'));
 const modal=d.getElementById('checkoutModal');modal.classList.remove('hidden');
 await new Promise(r=>setTimeout(r,4));
 assert.ok(d.getElementById('nanoPaymentSummary105'));
 assert.equal(d.getElementById('nanoPaymentTotal105').textContent,'100.00 د.ج');
 assert.equal(d.getElementById('nanoCheckoutChoice104').querySelectorAll('input[type=number]').length,0);
 const hidden=d.getElementById('checkoutPaidAmount');
 hidden.value='0';hidden.dispatchEvent(new w.Event('input',{bubbles:true}));
 const confirm=d.getElementById('confirm');
 confirm.click();assert.equal(invocations,0,'no credit sale without named customer');
 assert.ok(d.getElementById('nanoPaymentWarning105').textContent.includes('زبون'));
 d.getElementById('posCustomerSelect').value='7';
 const credit={items:[{id:3,qty:1,pos_price:100}],checkout:{
  total:100,paidAmount:0,customerId:7,paymentMethod:'cash'}};
 const out=await w.__browserElectron.ipcRenderer.invoke('process-sale',credit);
 assert.equal(out.success,true);
 assert.equal(invocations,1);
 const repeat=await w.__browserElectron.ipcRenderer.invoke('process-sale',credit);
 assert.equal(repeat.success,false,'no duplicate after committed sale');
 assert.equal(invocations,1);
 modal.classList.add('hidden');await new Promise(r=>setTimeout(r,4));
 modal.classList.remove('hidden');await new Promise(r=>setTimeout(r,4));
 w.nanoCheckoutPayFull104();assert.equal(Number(hidden.value),100);
 const full={items:[{id:3,qty:1,pos_price:100}],checkout:{
  total:100,paidAmount:100,customerId:null,paymentMethod:'card'}};
 const next=await w.__browserElectron.ipcRenderer.invoke('process-sale',full);
 assert.equal(next.success,true);assert.equal(invocations,2);
 assert.ok(d.getElementById('nanoPaymentDetail105').textContent.includes('الدفع'));
 modal.classList.add('hidden');await new Promise(r=>setTimeout(r,4));
 modal.classList.remove('hidden');await new Promise(r=>setTimeout(r,4));
 const partial=await w.__browserElectron.ipcRenderer.invoke('process-sale',{...full,
  checkout:{...full.checkout,paidAmount:25,customerId:7}});
 assert.equal(partial.success,false);
 assert.equal(invocations,2,'partial must be rejected before RPC');
 assert.equal(d.querySelectorAll('#nanoCheckoutChoice104 input[type=number]').length,0);
 dom.window.close();
 console.log('PASS: professional summary, full/credit state, missing customer, repeat click, single-method checkout and no received field');
};
run().catch(e=>{console.error(e);process.exitCode=1});
