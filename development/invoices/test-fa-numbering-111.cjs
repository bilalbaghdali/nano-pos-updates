'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const seq=require('./nano-invoice-sequence-111.js');
const yyyy=new Date().getFullYear();
const fmt=n=>'FA-'+yyyy+'-'+String(n).padStart(2,'0');
const empty={sales:[]};
assert.deepEqual(seq.next(empty,yyyy+'-01-05'),{year:yyyy,sequence:1,number:fmt(1)});
seq.commit(empty,seq.next(empty,yyyy+'-02-05'));
assert.equal(empty.invoice_counters.sales[yyyy],1);
assert.equal(seq.next(empty,yyyy+'-03-05').number,fmt(2));
empty.sales.push({invoice_number:fmt(12)});
assert.equal(seq.next(empty,yyyy+'-03-05').number,fmt(13),'existing sales must trump stale counters');
const cleaned={sales:[],invoice_counters:{sales:{[yyyy]:20}}};
assert.equal(seq.next(cleaned,yyyy+'-03-05').number,fmt(21),'deletions cannot reuse a number');
assert.equal(seq.next({sales:[],invoice_counters:{sales:{[yyyy]:20}}},(yyyy+1)+'-01-02').number,
 'FA-'+(yyyy+1)+'-01','next year resets numbering');
assert.equal(seq.next({sales:[{invoice_number:'FAC-'+yyyy+'-5000'}]},yyyy+'-01-05').number,fmt(1),'legacy FAC does not consume new sequence');
assert.throws(()=>seq.commit({sales:[{invoice_number:fmt(1)}]}, {number:fmt(1),sequence:1,year:yyyy}),/duplicate_invoice/);
const db={
 products:[{id:3,name:'Lait',stock:10,cost_price:20,batches:[{id:44,product_id:3,stock:10,cost_price:20,selling_price:100}]}],
 customers:[{id:7,name:'Ahmed',balance:0}],suppliers:[],sales:[],purchases:[],
 settings:{activation:'LICENSE-UNCHANGED'},backups:[{id:'BACKUP-UNCHANGED'}],
 users:[{id:1,name:'Admin',username:'admin',role:'Admin',permissions:['all']}],revision:1};
const KEY='lumina-browser-data-v1',store=new Map([[KEY,JSON.stringify(db)],
 ['pos_current_user',JSON.stringify({id:1,username:'admin',role:'Admin'})]]);
let failWrite=false;
const localStorage={getItem:k=>store.get(k)||null,setItem(k,v){if(failWrite){failWrite=false;throw Error('disk full')}store.set(k,String(v))},removeItem:k=>store.delete(k)};
const window={NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},
 NANO_PAYMENT_LEDGER_102:require('./nano-payment-ledger-102.js'),
 NANO_INVOICE_SEQUENCE_111:seq,
 nanoLicense:{access:async()=>({allowed:true})},
 nanoNative:{pcSyncLocalChanged(){}},addEventListener(){},dispatchEvent(){}};
const context={window,localStorage,sessionStorage:{getItem:()=>null,setItem(){},removeItem(){}},
 location:{protocol:'file:',port:''},navigator:{},document:{},console,JSON,Date,Math,Number,Array,Map,Set,
 Promise,Intl,URL,structuredClone,CustomEvent:class {},setTimeout:()=>0,setInterval:()=>0,clearTimeout:()=>{}};
vm.runInNewContext(fs.readFileSync('browser-bridge.js','utf8'),context,{filename:'browser-bridge.js'});
const call=(ch,...args)=>window.__browserElectron.ipcRenderer.invoke(ch,...args);
const read=()=>JSON.parse(store.get(KEY));
const sale=(op,paid,qty=1,extra={})=>({
 items:[{id:3,batch_id:44,qty,pos_price:100}],
 checkout:{customerId:7,subtotal:100*qty,total:100*qty,
  paidAmount:paid,paymentMethod:'cash',nanoCheckoutRequestId:op,...extra}
});
(async()=>{
 let r=await call('process-sale',sale('n105-invoice-111-00001',40));
 assert.equal(r.success,true,JSON.stringify(r));
 assert.equal(r.invoice_number,fmt(1));
 let state=read();assert.equal(state.sales[0].invoice_number,fmt(1));
 assert.equal(state.invoice_counters.sales[yyyy],1);
 assert.equal(state.customers[0].balance,60);
 assert.equal(state.products[0].batches[0].stock,9);
 r=await call('process-sale',sale('n105-invoice-111-00001',40));
 assert.equal(r.alreadyProcessed,true);
 assert.equal(r.invoice_number,fmt(1));
 assert.equal(read().sales.length,1);
 assert.equal(read().invoice_counters.sales[yyyy],1);
 r=await call('process-sale',sale('n105-invoice-111-00002',100));
 assert.equal(r.success,true,JSON.stringify(r));
 assert.equal(r.invoice_number,fmt(2));
 assert.equal(read().sales[0].invoice_number,fmt(2));
 const before=JSON.stringify(read());
 failWrite=true;
 r=await call('process-sale',sale('n105-invoice-111-retry',100));
 assert.equal(r.success,false);
 assert.equal(JSON.stringify(read()),before,'failed sale must not allocate number or stock');
 assert.equal(read().invoice_counters.sales[yyyy],2);
 r=await call('process-sale',sale('n105-invoice-111-retry',100));
 assert.equal(r.success,true);
 assert.equal(r.invoice_number,fmt(3));
 state=read();
 assert.equal(state.sales.length,3);
 assert.equal(state.invoice_counters.sales[yyyy],3);
 assert.equal(state.products[0].batches[0].stock,7);
 // Amend an existing invoice, which must never allocate a new FA number.
 const original=state.sales.find(s=>s.invoice_number===fmt(2));
 const edit=await call('process-sale',{editSaleId:original.id,
   items:[{id:3,batch_id:44,qty:1,pos_price:100}],
   checkout:{customerId:7,subtotal:100,total:100,paidAmount:100,paymentMethod:'cash'}});
 assert.equal(edit.success,true,JSON.stringify(edit));
 state=read();assert.equal(state.sales.find(s=>s.id===original.id).invoice_number,fmt(2));
 assert.equal(state.invoice_counters.sales[yyyy],3);
 const saleDetails=await call('get-sale-details',original.id);
 if(saleDetails?.sale)assert.equal(saleDetails.sale.invoice_number,fmt(2));
 assert.deepEqual(state.backups,db.backups);
 assert.equal(state.settings.activation,'LICENSE-UNCHANGED');
 // Existing format must be recognized by the print engine, not prefixed with FAC.
 const renderer=fs.readFileSync('renderer.js','utf8');
 assert.ok(renderer.includes('!/^(FA|FAC|AV|FR)-/i'));
 console.log('PASS: sequential annual FA; replay/failed storage/edit stable; unique counter; partial debt and stock preserved');
})().catch(err=>{console.error(err);process.exitCode=1});
