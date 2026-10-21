'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const sample=()=>({products:[{id:3,name:'Item',stock:10,cost_price:4,
 batches:[{id:44,product_id:3,stock:10,cost_price:4,selling_price:10}]}],
 customers:[{id:7,name:'Customer',balance:0}],suppliers:[{id:9,name:'Supplier',balance:25}],
 sales:[],purchases:[{id:15,supplier_id:9,total:25,paid_amount:0,items:[]}],
 users:[{id:1,username:'admin',name:'Admin',role:'Admin',permissions:['all']}],
 settings:{shop_name:'Shop',activation:'KEEP_ACTIVATION'},backups:[{sha:'KEEP_BACKUP'}],revision:1});
const key='lumina-browser-data-v1',store=new Map([[key,JSON.stringify(sample())],['pos_current_user',JSON.stringify({id:1,username:'admin',role:'Admin'})]]);
let failSave=false,notifications=0;
const localStorage={getItem:k=>store.get(k)||null,setItem(k,v){if(failSave){failSave=false;throw Error('storage full');}store.set(k,String(v));},
 removeItem:k=>store.delete(k)};
const window={NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},
 NANO_PAYMENT_LEDGER_102:require('./nano-payment-ledger-102.js'),
 nanoLicense:{access:async()=>({allowed:true})},
 nanoNative:{pcSyncLocalChanged(){notifications++;}},addEventListener(){},dispatchEvent(){}};
const context={window,localStorage,sessionStorage:{getItem:()=>null,setItem(){},removeItem(){}},
 location:{protocol:'file:',port:''},navigator:{},document:{},console,JSON,Date,Math,Number,
 Array,Map,Set,Promise,Intl,URL,structuredClone,CustomEvent:class {},setTimeout:()=>0,
 setInterval:()=>0,clearTimeout:()=>{}};
vm.runInNewContext(fs.readFileSync('browser-bridge.js','utf8'),context,{filename:'browser-bridge.js'});
const call=(channel,...args)=>window.__browserElectron.ipcRenderer.invoke(channel,...args);
const read=()=>JSON.parse(store.get(key));
const product={id:3,product_id:3,batch_id:44,qty:2,pos_price:10};
(async()=>{
 const req={items:[product],checkout:{
  customerId:7,subtotal:20,total:20,paidAmount:20,paymentMethod:'card',
  nanoCheckoutRequestId:'n105-repeat-sale-00001'}};
 let result=await call('process-sale',req);
 assert.equal(result.success,true,JSON.stringify(result));
 const firstId=result.saleId,after=read();
 assert.equal(after.sales.length,1);
 assert.equal(after.sales[0].nano_checkout_operation_id,'n105-repeat-sale-00001');
 assert.equal(after.products[0].batches[0].stock,8);
 assert.equal(after.customers[0].balance,0);
 result=await call('process-sale',JSON.parse(JSON.stringify(req)));
 assert.equal(result.success,true,JSON.stringify(result));
 assert.equal(result.alreadyProcessed,true);
 assert.equal(result.saleId,firstId);
 assert.equal(read().sales.length,1,'retries must not create a second invoice');
 assert.equal(read().products[0].batches[0].stock,8,'retries must not decrement stock twice');
 const conflict=await call('process-sale',{...req,items:[{...product,qty:1}]});
 assert.equal(conflict.success,false);
 assert.equal(read().sales.length,1);
 const mix=await call('process-sale',{items:[product],checkout:{...req.checkout,
  nanoCheckoutRequestId:'n105-mixed-payment-00001',payments:[{method:'cash',amount:10},{method:'card',amount:10}]}});
 assert.equal(mix.success,false,'new checkout must not accept mixed payment');
 const partial=await call('process-sale',{items:[product],checkout:{...req.checkout,
  nanoCheckoutRequestId:'n105-partial-credit-001',paidAmount:10}});
 assert.equal(partial.success,false,'no partial sales');
 const missing=await call('process-sale',{items:[product],checkout:{...req.checkout,
  nanoCheckoutRequestId:'n105-credit-not-linked01',customerId:null,paidAmount:0}});
 assert.equal(missing.success,false,'credit needs registered customer');
 const credit={items:[product],checkout:{...req.checkout,
  nanoCheckoutRequestId:'n105-full-credit-00001',paidAmount:0,paymentMethod:'cash'}};
 result=await call('process-sale',credit);
 assert.equal(result.success,true,JSON.stringify(result));
 assert.equal(read().sales.length,2);
 assert.equal(read().sales[0].remaining_amount,20);
 assert.equal(read().customers[0].balance,20);
 assert.equal(read().products[0].batches[0].stock,6);
 result=await call('process-sale',JSON.parse(JSON.stringify(credit)));
 assert.equal(result.alreadyProcessed,true);
 assert.equal(read().customers[0].balance,20);
 const payResult=await call('nano-record-settlement-102',{kind:'sale',
  documentId:read().sales[0].id,requestId:'settlement-105-0000001',amount:'20',method:'cash'});
 assert.equal(payResult.success,true);
 assert.equal(read().customers[0].balance,0);
 const orig=JSON.stringify(read());
 failSave=true;
 result=await call('process-sale',{items:[product],checkout:{...req.checkout,
  nanoCheckoutRequestId:'n105-failed-storage-0001'}});
 assert.equal(result.success,false);
 assert.equal(JSON.stringify(read()),orig,'failed commit must preserve all stored records');
 result=await call('process-sale',{items:[product],checkout:{...req.checkout,
  nanoCheckoutRequestId:'n105-failed-storage-0001'}});
 assert.equal(result.success,true,'same ID must remain retryable after failed storage commit');
 assert.equal(read().sales.length,3);
 assert.equal(read().products[0].batches[0].stock,4);
 assert.equal(read().settings.activation,'KEEP_ACTIVATION');
 assert.deepEqual(read().backups,[{sha:'KEEP_BACKUP'}]);
 assert.ok(notifications>0,'successful changes notify sync');
 console.log('PASS: single payment/credit; customer validation; repeat sale idempotence; stock and debts; failed storage retry; activation and backups preserved');
})().catch(e=>{console.error(e);process.exitCode=1});
