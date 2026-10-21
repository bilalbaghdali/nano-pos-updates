'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require('jsdom');
const tick=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const dom=new JSDOM('<!doctype html><html lang="ar"><body></body></html>',{
  url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,doc=w.document;
 const requests=[];let failFirstSupplierOne=true;
 const purchases=[
  {id:'p1',supplier_id:2,invoice_date:'2026-09-02',items:[{product_id:11,cost_price:12}]},
  {id:'p2',supplier_id:1,invoice_date:'2026-09-03',items:[{product_id:11,cost_price:20}]}];
 w.__browserElectron={ipcRenderer:{invoke:async (channel,payload)=>{
  if(channel==='get-suppliers')return [{id:1,name:'Vendor A'},{id:2,name:'Vendor B'}];
  if(channel==='get-purchases')return purchases;
  if(channel==='get-purchase-orders')return [];
  if(channel==='create-purchase-order'){
   requests.push(JSON.parse(JSON.stringify(payload)));
   if(payload.supplierId==='1'&&failFirstSupplierOne){failFirstSupplierOne=false;throw Error('simulated network disconnect after unknown commit');}
   return {success:true,id:'PO-'+payload.operationId};
  }
  throw Error('unexpected RPC '+channel);
 }}};
 w.eval(fs.readFileSync('nano-po-auto-supplier-100.js','utf8'));
 w.eval(fs.readFileSync('nano-po-shortage-ui-100.js','utf8'));
 const rows=[{id:11,name:'Recently bought',barcode:'111',order:4,costPrice:18},
   {id:22,name:'Assigned vendor',order:2,costPrice:6,supplierId:1}];
 await w.NANO_PO_SHORTAGE_100.open(rows);
 assert.ok(doc.getElementById('nanoPoShortageOverlay100'));
 assert.equal(requests.length,0,'opening review must never post purchase orders');
 const entries=[...doc.querySelectorAll('#nanoPoShortageRows100 > div')];
 assert.equal(entries.length,2);
 assert.equal(entries[0].querySelector('select').value,'2');
 assert.equal(entries[1].querySelector('select').value,'1');
 assert.equal(entries[0].querySelectorAll('input[type=number]')[0].value,'4');
 const save=doc.getElementById('nanoPoShortageSave100');
 save.click();await tick(30);
 assert.equal(requests.length,2);
 assert.equal(new Set(requests.map(x=>x.supplierId)).size,2,'separate purchase order for each vendor');
 assert.ok([...doc.querySelectorAll('#nanoPoShortageRows100 input')].every(x=>x.disabled),'freeze data before first RPC');
 const failed=requests.find(x=>x.supplierId==='1');
 assert.ok(failed,'failing group must exist');
 save.click();await tick(30);
 assert.equal(requests.length,3,'only failed group is retried');
 const retry=requests[2];
 assert.deepEqual(retry,failed,'retry must reuse same operation ID and payload');
 assert.equal(doc.getElementById('nanoPoShortageStatus100').textContent.includes('اكتمل'),true);
 assert.ok(!requests.some(x=>x.supplierId==='99'));
 doc.getElementById('nanoPoShortageOverlay100').querySelector('section > div > button').click();
 assert.equal(doc.getElementById('nanoPoShortageOverlay100'),null);
 console.log('PASS: auto selected suppliers, explicit review before post, separate orders, safe retry, frozen duplicate prevention');
 const html=fs.readFileSync('index.html','utf8'),stock=fs.readFileSync('nano-inventory-shortages.js','utf8');
 assert.ok(stock.includes('nanoShortageCreatePO100'),'low-stock toolbar must provide action');
 assert.ok(stock.includes('root.NANO_PO_SHORTAGE_100?.open'),'low-stock rows must feed purchase plan');
 for(const n of ['nano-po-auto-supplier-100.js','nano-po-shortage-ui-100.js'])assert.ok(html.includes('src="'+n+'"'));
 assert.equal(JSON.parse(fs.readFileSync('package.json','utf8')).version,'1.0.100');
 dom.window.close();
})().catch(e=>{console.error(e);process.exitCode=1});
