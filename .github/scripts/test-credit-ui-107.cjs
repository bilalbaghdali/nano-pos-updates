'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
(async()=>{
 const source=fs.readFileSync('index.html','utf8');
 assert.ok(source.includes('onclick="nanoOpenCreditPicker107()"'));
 assert.ok(!source.includes('onclick="checkoutMarkAsDebt()"'));
 assert.ok(source.includes('src="nano-credit-picker-107.js"'));
 assert.ok(!source.includes('src="nano-split-ui-102.js"'));
 assert.equal(JSON.parse(fs.readFileSync('package.json','utf8')).version,'1.0.107');
 const html='<!doctype html><html lang="ar"><body>'+
   '<div id="checkoutModal"><div id="checkoutTotalUI">100.00 د.ج</div>'+
   '<div id="nanoCheckoutChoice104"><input type="hidden" id="checkoutPaidAmount" value="100">'+
   '<button id="creditBtn" onclick="nanoOpenCreditPicker107()">دين كامل</button></div></div>'+
   '<input id="posCustomerSelect" type="hidden" value=""><input id="posCustomerSearchInput" value="">'+
   '</body></html>';
 const dom=new JSDOM(html,{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,d=w.document;
 let customers=[{id:4,name:'Amina',phone:'0550000000'},{id:5,name:'Bilal',phone:'0660000000'}];
 let saved=[],getCalls=0,setDebt=0,details=0;
 w.api={getCustomers:async()=>{getCalls++;return customers.map(x=>({...x}));},
   addCustomer:async input=>{saved.push(JSON.parse(JSON.stringify(input)));let id=10+saved.length;
     customers.push({id,...input});return {success:true,id};}};
 w.loadCustomersSelect=async()=>{};
 w.selectPosCustomer=(id,name)=>{d.getElementById('posCustomerSelect').value=String(id);
   d.getElementById('posCustomerSearchInput').value=String(name);};
 w.checkoutMarkAsDebt=()=>{setDebt++;d.getElementById('checkoutPaidAmount').value='0';};
 w.NANO_PAYMENT_QUALITY_105={render:()=>{details++;}};
 w.eval(fs.readFileSync('nano-credit-picker-107.js','utf8'));
 const open=()=>w.nanoOpenCreditPicker107();
 // Cancelled picker does not change the payment or customer.
 await open();
 assert.equal(d.getElementById('nanoCreditOverlay107').style.display,'flex');
 assert.equal(d.querySelectorAll('#nanoCreditList107 button').length,2);
 d.getElementById('nanoCreditCancel107').click();
 assert.equal(d.getElementById('checkoutPaidAmount').value,'100');
 assert.equal(d.getElementById('posCustomerSelect').value,'');
 assert.equal(setDebt,0);
 // Selecting an existing customer automatically chooses full credit; no invoice written.
 await open();
 const search=d.getElementById('nanoCreditSearch107');
 search.value='0660';search.dispatchEvent(new w.Event('input',{bubbles:true}));
 assert.equal(d.querySelectorAll('#nanoCreditList107 button').length,1);
 d.querySelector('#nanoCreditList107 button').click();
 assert.equal(d.getElementById('posCustomerSelect').value,'5');
 assert.equal(d.getElementById('posCustomerSearchInput').value,'Bilal');
 assert.equal(d.getElementById('checkoutPaidAmount').value,'0');
 assert.equal(setDebt,1);assert.equal(saved.length,0);
 assert.ok(details>0);
 // New customer creation must not pre-populate debt, balance or invoice.
 d.getElementById('checkoutPaidAmount').value='100';
 await open();
 d.getElementById('nanoCreditNew107').click();
 d.getElementById('nanoCreditName107').value='New Customer';
 d.getElementById('nanoCreditPhone107').value='0771000000';
 d.getElementById('nanoCreditAddress107').value='Medea';
 const form=d.getElementById('nanoCreditNewForm107');
 form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 await new Promise(r=>setTimeout(r,30));
 assert.equal(saved.length,1);
 assert.deepEqual(saved[0],{name:'New Customer',phone:'0771000000',address:'Medea',
   initial_debt:0,credit_limit:0,balance:0});
 assert.equal(d.getElementById('posCustomerSelect').value,'11');
 assert.equal(d.getElementById('checkoutPaidAmount').value,'0');
 assert.equal(setDebt,2);
 // Repeated phone can't create customer twice.
 d.getElementById('checkoutPaidAmount').value='100';
 await open();d.getElementById('nanoCreditNew107').click();
 d.getElementById('nanoCreditName107').value='Duplicate Name';
 d.getElementById('nanoCreditPhone107').value='0771000000';
 form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 await new Promise(r=>setTimeout(r,10));
 assert.equal(saved.length,1);
 assert.equal(d.getElementById('checkoutPaidAmount').value,'100');
 assert.match(d.getElementById('nanoCreditStatus107').textContent,/يوجد زبون/);
 assert.ok(getCalls>=3);
 dom.window.close();
 console.log('PASS: credit popup existing/add/cancel/duplicate phone, customer link and initial zero debt; no sale before confirmation');
})().catch(e=>{console.error(e);process.exitCode=1});
