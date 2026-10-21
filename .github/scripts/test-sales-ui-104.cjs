'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require('jsdom');
const html=fs.readFileSync('index.html','utf8');
const fast=fs.readFileSync('nano-fast-pos.js','utf8');
const cash=fs.readFileSync('nano-cash-change.js','utf8');
const ledger=fs.readFileSync('nano-payment-ledger-102.js','utf8');
const bridge=fs.readFileSync('browser-bridge.js','utf8');
assert.equal(JSON.parse(fs.readFileSync('package.json','utf8')).version,'1.0.104');
assert.ok(!html.includes('src="nano-split-ui-102.js"'),'mixed payment widget must not load');
assert.equal((html.match(/id="checkoutPaidAmount"/g)||[]).length,1,'preserve paid input for renderer');
assert.ok(html.includes('type="hidden" id="checkoutPaidAmount"'),'cash received amount must not be user-editable');
assert.ok(!html.includes('data-i18n="amount_received_label"'),'received amount label must be removed');
assert.ok(!fast.includes('setupPayment();'),'legacy split/debt panel must not be added');
assert.ok(cash.includes('no tendered-amount requirement'),'old received-cash widget must not enforce cash tender');
assert.ok(ledger.includes('function settle(db,req)'),'historical settlement logic must remain');
assert.ok(bridge.includes("if (channel === 'process-sale')"),'existing sale must remain');
assert.ok(bridge.includes("if (channel === 'nano-record-settlement-102')"),'payment history/reconciliation must remain');

(async()=>{
 const dom=new JSDOM(html,{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const win=dom.window,doc=win.document;
 const form=doc.getElementById('checkoutModal');
 assert.ok(form);
 assert.equal(form.querySelectorAll('input[type=number]').length,0,
   'checkout must not show a numeric amount received input');
 assert.equal(doc.getElementById('checkoutPaidAmount').type,'hidden');
 assert.equal(form.querySelectorAll('[data-i18n="nano_payment_full"]').length,1);
 assert.equal(form.querySelectorAll('[data-i18n="nano_payment_credit_full"]').length,1);
 let calculations=0;win.checkoutCalcChange=()=>{calculations++;};
 const total=doc.getElementById('checkoutTotalUI');total.textContent='1500.50 د.ج';
 win.eval(fs.readFileSync('nano-checkout-choice-104.js','utf8'));
 win.nanoCheckoutPayFull104();
 assert.equal(Number(doc.getElementById('checkoutPaidAmount').value),1500.5);
 assert.equal(calculations,1);
 assert.ok(!doc.getElementById('nanoCashTendered'),'no additional received amount before initialization');
 win.eval(cash);
 doc.dispatchEvent(new win.Event('DOMContentLoaded',{bubbles:true}));
 assert.ok(!doc.getElementById('nanoCashTendered'),'legacy cash calculator must not reappear');
 assert.ok(!doc.getElementById('nanoCashChangePanel'),'old change calculator must not reappear');
 assert.ok(!doc.getElementById('nanoSplitToggle'),'legacy partial payment must not reappear');
 assert.ok(!doc.getElementById('nanoSplitEnabled102'),'mixed payment must not reappear');
 const prep=win.NANO_CASH_CHANGE_178.prepare({checkout:{total:1500.5,paidAmount:1500.5}});
 assert.equal(prep.ok,true,'cash tender entry no longer required for a regular sale');
 doc.getElementById('checkoutPaidAmount').value='0'; // existing checkoutMarkAsDebt() does this
 assert.equal(Number(doc.getElementById('checkoutPaidAmount').value),0,'full credit still supported');
 win.nanoCheckoutPayFull104();
 assert.equal(Number(doc.getElementById('checkoutPaidAmount').value),1500.5,
   'user can return from full credit to full payment');
 dom.window.close();
 console.log('PASS: checkout has no received-amount field, cash-change UI or split option; full pay/full credit remain available');
})().catch(e=>{console.error(e);process.exitCode=1});
