'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
async function tick(){await new Promise(r=>setTimeout(r,15));}
(async()=>{
 const index=fs.readFileSync('index.html','utf8');
 assert.equal(JSON.parse(fs.readFileSync('package.json','utf8')).version,'1.0.108');
 assert.equal(index.includes('onclick="nanoCheckoutPayFull104()"'),false);
 assert.equal(index.includes('onclick="nanoOpenCreditPicker107()"'),false);
 assert.equal(index.includes('src="nano-cash-guide-106.js"'),false);
 assert.ok(index.includes('id="nanoTenderAmount108"'));
 assert.ok(index.includes('src="nano-flex-payment-108.js"'));
 const minimal='<!doctype html><html lang="ar"><body>'+
 '<div id="checkoutModal" class="hidden">'+
 '<div id="checkoutTotalUI">100.00 د.ج</div>'+
 '<select id="checkoutPaymentMethod"><option value="cash">نقدًا</option><option value="card">بطاقة</option></select>'+
 '<div id="nanoCheckoutChoice104"><input id="nanoTenderAmount108" type="number" min="0" step=".01"><input id="checkoutPaidAmount" type="hidden" value="100">'+
 '<div id="nanoFlexibleSummary108"></div></div>'+
 '<button id="submitSale" onclick="processSale()">تأكيد البيع</button></div>'+
 '<input id="posCustomerSelect" type="hidden" value=""><input id="posCustomerSearchInput" value="">'+
 '</body></html>';
 const dom=new JSDOM(minimal,{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,d=w.document;
 w.currentLanguage='ar';w.showToast=()=>{};w.setTimeout=setTimeout;
 let calls=0,customerRows=[{id:7,name:'Ahmed',phone:'0770000001'}],recorded=null;
 w.api={getCustomers:async()=>customerRows.map(x=>({...x})),addCustomer:async data=>{
  customerRows.push({id:8,...data});return {success:true,id:8};}};
 w.loadCustomersSelect=async()=>{};
 w.selectPosCustomer=(id,name)=>{
  d.getElementById('posCustomerSelect').value=String(id);
  d.getElementById('posCustomerSearchInput').value=name;
 };
 w.checkoutMarkAsDebt=()=>{d.getElementById('checkoutPaidAmount').value='0';};
 w.__browserElectron={ipcRenderer:{invoke:async(name,payload)=>{
  calls++;recorded=payload;return {success:true,saleId:calls};
 }}};
 for(const name of ['nano-cash-plan-106.js','nano-flex-core-108.js',
   'nano-payment-quality-105.js','nano-credit-picker-107.js','nano-flex-payment-108.js']){
   w.eval(fs.readFileSync(name,'utf8'));
 }
 const modal=d.getElementById('checkoutModal');modal.classList.remove('hidden');await tick();
 const tender=d.getElementById('nanoTenderAmount108');
 assert.equal(d.getElementById('checkoutPaidAmount').value,'0');
 assert.equal(d.getElementById('nanoFlexibleSummary108').textContent.includes('أدخل'),true);
 tender.value='40';tender.dispatchEvent(new w.Event('input',{bubbles:true}));await tick();
 assert.equal(d.getElementById('checkoutPaidAmount').value,'40.00');
 assert.match(d.getElementById('nanoFlexibleSummary108').textContent,/60.00/);
 assert.equal(w.NANO_FLEX_108.validateAndMaybeChoose(),false);
 await tick();
 assert.equal(d.getElementById('nanoCreditOverlay107').style.display,'flex');
 assert.equal(calls,0);
 assert.equal(d.getElementById('nanoCreditList107').querySelectorAll('button').length,1);
 d.querySelector('#nanoCreditList107 button').click();await tick();
 assert.equal(d.getElementById('posCustomerSelect').value,'7');
 assert.equal(tender.value,'40');
 assert.equal(d.getElementById('checkoutPaidAmount').value,'40.00');
 assert.equal(w.NANO_FLEX_108.validateAndMaybeChoose(),true);
 const payload={items:[{id:3,qty:1,pos_price:100}],checkout:{
  total:100,paidAmount:40,customerId:7,paymentMethod:'cash'}};
 let result=await w.__browserElectron.ipcRenderer.invoke('process-sale',payload);
 assert.equal(result.success,true);
 assert.equal(recorded.checkout.paidAmount,'40.00');
 assert.equal(recorded.checkout.cashTenderedAmount,'40.00');
 assert.match(recorded.checkout.nanoCheckoutRequestId,/^n105-/);
 assert.equal(calls,1);
 // New modal, cash overpayment displays suggested DZD notes and no debt.
 modal.classList.add('hidden');await tick();modal.classList.remove('hidden');await tick();
 d.getElementById('posCustomerSelect').value='';
 tender.value='150';tender.dispatchEvent(new w.Event('input',{bubbles:true}));await tick();
 assert.equal(d.getElementById('checkoutPaidAmount').value,'100.00');
 assert.match(d.getElementById('nanoFlexibleSummary108').textContent,/50.00/);
 assert.match(d.getElementById('nanoFlexibleSummary108').textContent,/50 د.ج/);
 assert.equal(w.NANO_FLEX_108.validateAndMaybeChoose(),true);
 result=await w.__browserElectron.ipcRenderer.invoke('process-sale',{items:[{id:3,qty:1,pos_price:100}],
  checkout:{total:100,paidAmount:100,customerId:null,paymentMethod:'cash'}});
 assert.equal(result.success,true);
 assert.equal(recorded.checkout.cashTenderedAmount,'150.00');
 assert.equal(recorded.checkout.paidAmount,'100.00');
 assert.equal(calls,2);
 modal.classList.add('hidden');await tick();modal.classList.remove('hidden');await tick();
 d.getElementById('checkoutPaymentMethod').value='card';
 tender.value='150';tender.dispatchEvent(new w.Event('input',{bubbles:true}));await tick();
 assert.equal(w.NANO_FLEX_108.validateAndMaybeChoose(),false);
 assert.equal(calls,2);
 // New customer flow keeps entered partial amount and never posts opening debt.
 tender.value='25';tender.dispatchEvent(new w.Event('input',{bubbles:true}));
 assert.equal(w.NANO_FLEX_108.validateAndMaybeChoose(),false);await tick();
 d.getElementById('nanoCreditNew107').click();
 d.getElementById('nanoCreditName107').value='New client';
 d.getElementById('nanoCreditPhone107').value='0557000000';
 d.getElementById('nanoCreditNewForm107').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 await tick();
 assert.equal(d.getElementById('posCustomerSelect').value,'8');
 assert.equal(d.getElementById('checkoutPaidAmount').value,'25.00');
 result=await w.__browserElectron.ipcRenderer.invoke('process-sale',{items:[{id:3,qty:1,pos_price:100}],
  checkout:{total:100,paidAmount:25,customerId:8,paymentMethod:'card'}});
 assert.equal(result.success,true);assert.equal(calls,3);
 assert.equal(recorded.checkout.paidAmount,'25.00');
 assert.ok(!('cashTenderedAmount' in recorded.checkout));
 dom.window.close();
 console.log('PASS: no old buttons, any amount, customer picker, partial credit, change denominations, credit creation, one method');
})().catch(e=>{console.error(e);process.exitCode=1});
