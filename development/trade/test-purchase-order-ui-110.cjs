'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require('jsdom');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const dom=new JSDOM('<!doctype html><html lang="ar"><body><div id="purchasesListView"><button onclick="togglePurchaseView(\\'new\\')">فاتورة جديدة</button></div></body></html>',{
  url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const win=dom.window,doc=win.document;
 let orders=[],saveCount=0,receiptCount=0;
 win.__browserElectron={ipcRenderer:{invoke:async(channel,arg)=>{
  if(channel==='get-suppliers')return [{id:7,name:'Test Supplier'}];
  if(channel==='get-purchase-orders')return orders;
  if(channel==='get-products')return {items:[{id:3,name:'Test Product',barcode:'ABC',cost_price:10}],total:1};
  if(channel==='create-purchase-order'){
   assert.equal(arg.supplierId,'7');assert.equal(arg.lines.length,1);
   assert.equal(arg.lines[0].quantity,'1');saveCount++;
   orders=[{id:'PO-SAMPLE-1',status:'pending',supplierName:'Test Supplier',revision:1,
     lines:[{lineId:'L1',productName:'Test Product',quantityMilli:1000,receivedMilli:0}]}];
   return {success:true,id:'PO-SAMPLE-1'};
  }
  if(channel==='confirm-purchase-order-receipt'){
   assert.equal(arg.orderId,'PO-SAMPLE-1');
   assert.equal(arg.lines[0].quantity,'1');
   receiptCount++;
   orders=[{...orders[0],status:'received',revision:2,lines:[{...orders[0].lines[0],receivedMilli:1000}]}];
   return {success:true,purchaseId:'POINV-SAMPLE-1'};
  }
  throw Error('unexpected RPC '+channel);
 }}};
 win.eval(fs.readFileSync('nano-purchase-order-ui.js','utf8'));
 doc.dispatchEvent(new win.Event('DOMContentLoaded',{bubbles:true}));
 const opener=doc.getElementById('nanoPoOpen110');
 assert.ok(opener,'Purchase orders button must be visible');
 opener.click();await sleep(30);
 assert.ok(doc.getElementById('nanoPoDialog110'));
 const supplier=doc.getElementById('nanoPoSupplier110');
 assert.equal(supplier.options.length,2);
 supplier.value='7';
 const search=doc.getElementById('nanoPoSearch110');
 search.value='Test';search.dispatchEvent(new win.Event('input'));
 await sleep(350);
 assert.equal(doc.getElementById('nanoPoProductResults110').querySelectorAll('button').length,1);
 doc.getElementById('nanoPoProductResults110').querySelector('button').click();
 assert.ok(doc.getElementById('nanoPoItems110').textContent.includes('Test Product'));
 doc.getElementById('nanoPoSave110').click();await sleep(25);
 assert.equal(saveCount,1);
 assert.ok(doc.getElementById('nanoPoOrders110').textContent.includes('PO-SAMPLE-1'));
 doc.getElementById('nanoPoOrders110').querySelector('button').click();
 doc.getElementById('nanoPoReceipt110').querySelector('button').click();await sleep(25);
 assert.equal(receiptCount,1);
 assert.ok(doc.getElementById('nanoPoStatus110').textContent.includes('POINV-SAMPLE-1'));
 doc.getElementById('nanoPoDialog110').querySelector('section > div button').click();
 assert.equal(doc.getElementById('nanoPoDialog110'),null);
 console.log('PASS: purchase UI create/search/partial receipt/status linked to existing purchase section');
 dom.window.close();
})().catch(error=>{console.error(error);process.exitCode=1});
