'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const sample=()=>({
 products:[{id:3,name:'Item',stock:10,cost_price:4,batches:[{id:44,product_id:3,stock:10,cost_price:4,selling_price:10}]}],
 customers:[{id:7,name:'Buyer',balance:0}],
 suppliers:[{id:9,name:'Vendor',balance:50}],
 sales:[],purchases:[{id:15,supplier_id:9,total:50,paid_amount:0,items:[],payments:[]}],
 users:[{id:1,username:'admin',password:'admin',name:'Admin',role:'Admin',permissions:['all']}],
 settings:{shop_name:'Test Shop',activation:'PRESERVE'},backups:[{sha256:'PRESERVE'}],revision:1
});
(async()=>{
 const KEY='lumina-browser-data-v1',store=new Map([[KEY,JSON.stringify(sample())],
   ['pos_current_user',JSON.stringify({id:1,username:'admin',role:'Admin'})]]);
 let blocked=false,signals=0;
 const localStorage={getItem:k=>store.get(k)||null,setItem(k,v){if(blocked){blocked=false;throw Error('storage unavailable');}store.set(k,String(v));},removeItem:k=>store.delete(k)};
 const win={NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},NANO_PAYMENT_LEDGER_102:require('./nano-payment-ledger-102.js'),
   nanoNative:{pcSyncLocalChanged(){signals++;}},addEventListener(){},dispatchEvent(){}};
 const context={window:win,localStorage,sessionStorage:{getItem:()=>null,setItem(){},removeItem(){}},
   location:{protocol:'file:',port:''},navigator:{},document:{},console,JSON,Date,Math,Number,Array,Map,Set,Promise,Intl,URL,structuredClone,
   CustomEvent:class {},setTimeout:()=>0,setInterval:()=>0,clearTimeout:()=>{}};
 vm.runInNewContext(fs.readFileSync('browser-bridge.js','utf8'),context,{filename:'browser-bridge.js'});
 const call=(channel,...args)=>win.__browserElectron.ipcRenderer.invoke(channel,...args);
 const original=JSON.parse(store.get(KEY));
 const item={id:3,product_id:3,batch_id:44,qty:2,pos_price:10};
 const checkout={customerId:7,total:20,subtotal:20,payments:[{method:'cash',amount:'5'},{method:'card',amount:'10'}]};
 const paid=await call('process-sale',{items:[item],checkout});
 assert.equal(paid.success,true,JSON.stringify(paid));
 let current=JSON.parse(store.get(KEY));
 assert.equal(current.sales.length,1);assert.equal(current.sales[0].paid_amount,15);
 assert.equal(current.sales[0].remaining_amount,5);assert.equal(current.sales[0].payment_method,'mixed');
 assert.equal(current.sales[0].payments.length,2);
 assert.equal(current.customers[0].balance,5);assert.equal(current.products[0].batches[0].stock,8);
 assert.equal(current.settings.activation,original.settings.activation);
 assert.deepEqual(current.backups,original.backups);
 let request={kind:'sale',documentId:current.sales[0].id,requestId:'payment-sale-00001',method:'cash',amount:'5'};
 const paidDebt=await call('nano-record-settlement-102',request);
 assert.equal(paidDebt.success,true);
 current=JSON.parse(store.get(KEY));
 assert.equal(current.sales[0].remaining_amount,0);assert.equal(current.customers[0].balance,0);
 assert.equal(current.nano_payment_ledger.length,1);
 const retry=await call('nano-record-settlement-102',request);
 assert.equal(retry.alreadyProcessed,true);
 assert.equal(JSON.parse(store.get(KEY)).nano_payment_ledger.length,1);
 const conflict=await call('nano-record-settlement-102',{...request,amount:'4'});
 assert.equal(conflict.success,false);
 const purchase=await call('nano-record-settlement-102',{kind:'purchase',documentId:15,
   requestId:'payment-purchase-001',method:'virement',amount:'50'});
 assert.equal(purchase.success,true);
 current=JSON.parse(store.get(KEY));
 assert.equal(current.purchases[0].paid_amount,50);assert.equal(current.suppliers[0].balance,0);
 assert.equal(current.products[0].batches[0].stock,8);
 assert.equal(current.nano_payment_ledger.length,2);
 // Store failure must not update live stock, customer balance, sales or audit.
 blocked=true;
 const failure=await call('process-sale',{items:[{...item,qty:1}],checkout:{
   total:10,subtotal:10,customerId:7,paidAmount:10}});
 assert.equal(failure.success,false);
 current=JSON.parse(store.get(KEY));
 assert.equal(current.sales.length,1);
 assert.equal(current.products[0].batches[0].stock,8);
 assert.equal(current.customers[0].balance,0);
 assert.equal(current.settings.activation,'PRESERVE');
 assert.ok(signals>0);
 console.log('PASS: mixed checkout, credit balance, idempotent sale/supplier settlements, storage failure rollback, unchanged activation/backup');
})().catch(e=>{console.error(e);process.exitCode=1});
