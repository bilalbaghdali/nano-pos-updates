'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
(async()=>{
 const dom=new JSDOM('<!doctype html><html lang="ar"><body>'+
  '<div id="checkoutModal"><div><select id="checkoutPaymentMethod"><option value="cash">cash</option></select></div>'+
  '<input type="number" id="checkoutPaidAmount" value="0"></div></body></html>',{
   url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const win=dom.window,doc=win.document;
 const intercepted=[];
 win.__browserElectron={ipcRenderer:{invoke:async (name,payload)=>{intercepted.push({name,payload});return {success:true};}}};
 win.eval(fs.readFileSync('nano-payment-ledger-102.js','utf8'));
 win.eval(fs.readFileSync('nano-split-ui-102.js','utf8'));
 doc.dispatchEvent(new win.Event('DOMContentLoaded',{bubbles:true}));
 const toggle=doc.getElementById('nanoSplitEnabled102');assert.ok(toggle);
 toggle.checked=true;toggle.dispatchEvent(new win.Event('change'));
 const inputs=[...doc.querySelectorAll('#nanoSplitFields102 input')];
 assert.equal(inputs.length,6);
 inputs[0].value='5.25';inputs[0].dispatchEvent(new win.Event('input'));
 inputs[1].value='10';inputs[1].dispatchEvent(new win.Event('input'));
 assert.equal(doc.getElementById('checkoutPaidAmount').value,'15.25');
 await win.__browserElectron.ipcRenderer.invoke('process-sale',{items:[{id:1,qty:1,pos_price:20}],
  checkout:{customerId:7,total:20,subtotal:20,paidAmount:20,paymentMethod:'cash'}});
 assert.equal(intercepted.length,1);
 assert.equal(intercepted[0].payload.checkout.paidAmount,15.25);
 assert.equal(intercepted[0].payload.checkout.paymentMethod,'mixed');
 assert.equal(intercepted[0].payload.checkout.payments.length,2);
 assert.equal(intercepted[0].payload.checkout.cashTenderedAmount,null);
 assert.equal(doc.getElementById('checkoutPaymentMethod').disabled,true);
 doc.getElementById('checkoutModal').classList.add('hidden');
 await new Promise(r=>setTimeout(r,10));
 assert.equal(toggle.checked,false);
 assert.equal(doc.getElementById('checkoutPaymentMethod').disabled,false);
 dom.window.close();
 console.log('PASS: mixed checkout UI, exact paid total, RPC payload, modal reset');
})().catch(e=>{console.error(e);process.exitCode=1});
