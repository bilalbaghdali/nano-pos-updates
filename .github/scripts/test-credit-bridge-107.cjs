'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const KEY='lumina-browser-data-v1';
const original={
 products:[{id:3,name:'Product',stock:10,cost_price:20,
   batches:[{id:44,product_id:3,stock:10,cost_price:20,selling_price:100}]}],
 customers:[],suppliers:[],sales:[],purchases:[],
 settings:{activation:'KEEP_LICENSE'},backups:[{sha256:'KEEP_BACKUP'}],
 users:[{id:1,name:'Admin',username:'admin',role:'Admin',permissions:['all']}],revision:3};
const store=new Map([[KEY,JSON.stringify(original)],
 ['pos_current_user',JSON.stringify({id:1,username:'admin',role:'Admin'})]]);
let failNext=false,notifications=0;
const localStorage={getItem:k=>store.get(k)||null,setItem(k,v){if(failNext){failNext=false;throw Error('no disk');}store.set(k,String(v));},
 removeItem:k=>store.delete(k)};
const window={NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},
 NANO_PAYMENT_LEDGER_102:require('./nano-payment-ledger-102.js'),
 nanoLicense:{access:async()=>({allowed:true})},
 nanoNative:{pcSyncLocalChanged(){notifications++;}},addEventListener(){},dispatchEvent(){}};
const context={window,localStorage,
 sessionStorage:{getItem:()=>null,setItem(){},removeItem(){}},
 location:{protocol:'file:',port:''},navigator:{},document:{},console,
 JSON,Date,Math,Number,Array,Map,Set,Promise,Intl,URL,structuredClone,
 CustomEvent:class {},setTimeout:()=>0,setInterval:()=>0,clearTimeout:()=>{}};
vm.runInNewContext(fs.readFileSync('browser-bridge.js','utf8'),context,{filename:'browser-bridge.js'});
const call=(channel,...args)=>window.__browserElectron.ipcRenderer.invoke(channel,...args);
const read=()=>JSON.parse(store.get(KEY));
(async()=>{
 const before=read();
 const add=await call('add-customer',{name:'Credit Client',phone:'0770000000',address:'Blida',
   initial_debt:0,credit_limit:0,balance:0});
 assert.equal(add.success,true,JSON.stringify(add));
 const newCustomer=read().customers.find(c=>String(c.id)===String(add.id));
 assert.ok(newCustomer);
 assert.equal(Number(newCustomer.initial_debt),0);
 assert.equal(Number(newCustomer.balance),0);
 assert.equal(read().sales.length,0,'creating customer must not create sale or debt');
 assert.equal(read().products[0].batches[0].stock,10);
 const checkout={items:[{id:3,batch_id:44,qty:2,pos_price:100}],checkout:{
  total:200,subtotal:200,customerId:add.id,paidAmount:0,paymentMethod:'cash',
  nanoCheckoutRequestId:'n105-customer-credit-1071'}};
 const sale=await call('process-sale',checkout);
 assert.equal(sale.success,true,JSON.stringify(sale));
 let state=read();
 assert.equal(state.sales.length,1);
 assert.equal(state.sales[0].customer_id,add.id);
 assert.equal(state.sales[0].paid_amount,0);
 assert.equal(state.sales[0].remaining_amount,200);
 assert.equal(state.customers.find(c=>String(c.id)===String(add.id)).balance,200);
 assert.equal(state.products[0].batches[0].stock,8);
 const duplicate=await call('process-sale',JSON.parse(JSON.stringify(checkout)));
 assert.equal(duplicate.success,true);assert.equal(duplicate.alreadyProcessed,true);
 assert.equal(read().sales.length,1);assert.equal(read().products[0].batches[0].stock,8);
 assert.equal(read().customers[0].balance,200);
 const missing=await call('process-sale',{...checkout,checkout:{
   ...checkout.checkout,customerId:'missing',nanoCheckoutRequestId:'n105-missing-customer107'}});
 assert.equal(missing.success,false);
 assert.equal(read().sales.length,1);
 // The debt settlement remains available after a credit sale.
 const payment=await call('nano-record-settlement-102',{kind:'sale',
   documentId:state.sales[0].id,requestId:'customer-credit-pay-10701',method:'cash',amount:'75'});
 assert.equal(payment.success,true,JSON.stringify(payment));
 state=read();assert.equal(state.sales[0].remaining_amount,125);
 assert.equal(state.customers[0].balance,125);
 assert.equal(state.products[0].batches[0].stock,8);
 const beforeFail=JSON.stringify(state);
 failNext=true;
 const declined=await call('process-sale',{...checkout,checkout:{
  ...checkout.checkout,nanoCheckoutRequestId:'n105-credit-savefail-107'}});
 assert.equal(declined.success,false);
 assert.equal(JSON.stringify(read()),beforeFail);
 assert.deepEqual(read().backups,before.backups);
 assert.deepEqual(read().settings,before.settings);
 assert.ok(notifications>=2);
 console.log('PASS: create client without debt; confirm full credit; idempotent invoice, stock and customer balance; debt settlement; failed save and activation backup safety');
})().catch(e=>{console.error(e);process.exitCode=1});
