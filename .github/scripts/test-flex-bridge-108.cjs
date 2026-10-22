'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const p=require('./nano-flex-core-108.js');
for(const [total,tender,customer,expected] of [
 ['100','0',4,[0,100,0]],['100','25',4,[25,75,0]],
 ['100','100',null,[100,0,0]],['100','120',null,[100,0,20]],
 ['25.50','30.50',null,[25.50,0,5]]
]){
 const r=p.plan(total,tender,'cash',customer);
 assert.equal(r.ok,true,JSON.stringify(r));
 assert.deepEqual([r.paidCents/100,r.debtCents/100,r.changeCents/100],expected);
}
assert.equal(p.plan('100','25','cash',null).error,'customer_required');
assert.equal(p.plan('100','120','card',4).error,'overpayment_requires_cash');
assert.equal(p.plan('100','20','card',4).paidCents,2000);
assert.equal(p.plan('100','-1','cash',4).ok,false);
assert.equal(p.plan('100','5.003','cash',4).ok,false);
let seed=108;const rand=()=>{seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed;};
for(let i=0;i<3000;i++){
 const t=rand()%10000000,g=rand()%12000000;
 const r=p.plan(p.format(t),p.format(g),'cash',7);
 assert.equal(r.ok,true);
 assert.equal(r.paidCents+r.debtCents,t);
 assert.equal(r.paidCents+r.changeCents,g);
}
console.log('PASS: 3000 monetary invariants, partial debt and cash change');
const store=new Map(),KEY='lumina-browser-data-v1',original={
 products:[{id:3,name:'Product',stock:12,cost_price:2,batches:[{id:44,product_id:3,stock:12,cost_price:2,selling_price:100}]}],
 customers:[{id:7,name:'Client',balance:0}],suppliers:[],sales:[],purchases:[],
 settings:{activation:'LICENSE-KEPT'},backups:[{sha:'BACKUP-KEPT'}],
 users:[{id:1,name:'Admin',username:'admin',role:'Admin',permissions:['all']}],revision:1};
store.set(KEY,JSON.stringify(original));store.set('pos_current_user',JSON.stringify({id:1,username:'admin',role:'Admin'}));
let failWrite=false;
const localStorage={getItem:k=>store.get(k)||null,setItem(k,v){if(failWrite){failWrite=false;throw Error('disk full');}store.set(k,String(v));},removeItem:k=>store.delete(k)};
const w={NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},
  NANO_PAYMENT_LEDGER_102:require('./nano-payment-ledger-102.js'),
  nanoLicense:{access:async()=>({allowed:true})},nanoNative:{pcSyncLocalChanged(){}},
  addEventListener(){},dispatchEvent(){}};
const context={window:w,localStorage,sessionStorage:{getItem:()=>null,setItem(){},removeItem(){}},
 location:{protocol:'file:',port:''},navigator:{},document:{},console,JSON,Date,Math,Number,Array,Map,Set,Promise,Intl,URL,structuredClone,CustomEvent:class {},setTimeout:()=>0,setInterval:()=>0,clearTimeout:()=>{}};
vm.runInNewContext(fs.readFileSync('browser-bridge.js','utf8'),context,{filename:'browser-bridge.js'});
const call=(channel,...args)=>w.__browserElectron.ipcRenderer.invoke(channel,...args);
const read=()=>JSON.parse(store.get(KEY));
function sale(id,paid,tender,customer=7,method='cash'){return {items:[{id:3,batch_id:44,qty:1,pos_price:100}],checkout:{
 subtotal:100,total:100,paidAmount:paid,paymentMethod:method,customerId:customer,
 ...(tender===null?{}:{cashTenderedAmount:tender}),nanoCheckoutRequestId:id}};}
(async()=>{
 let r=await call('process-sale',sale('n105-partial-credit-0108',40,40));
 assert.equal(r.success,true,JSON.stringify(r));
 let d=read();assert.equal(d.sales.length,1);
 assert.equal(d.sales[0].paid_amount,40);
 assert.equal(d.sales[0].remaining_amount,60);
 assert.equal(d.sales[0].payment_status,'partial');
 assert.equal(d.customers[0].balance,60);
 assert.equal(d.products[0].batches[0].stock,11);
 assert.equal(d.sales[0].cash_tendered_amount,40);
 assert.equal(d.sales[0].cash_change_amount,0);
 r=await call('process-sale',sale('n105-partial-credit-0108',40,40));
 assert.equal(r.alreadyProcessed,true);
 assert.equal(read().sales.length,1);assert.equal(read().customers[0].balance,60);
 assert.equal(read().products[0].batches[0].stock,11);
 const noCustomer=await call('process-sale',sale('n105-missing-client-0108',50,50,null));
 assert.equal(noCustomer.success,false);assert.equal(read().sales.length,1);
 const over=await call('process-sale',sale('n105-change-paid-0108',100,150,null));
 assert.equal(over.success,true,JSON.stringify(over));
 d=read();assert.equal(d.sales[0].paid_amount,100);
 assert.equal(d.sales[0].remaining_amount,0);
 assert.equal(d.sales[0].cash_change_amount,50);
 assert.equal(d.cash_change_audit[0].cash_change_due,50);
 assert.equal(d.products[0].batches[0].stock,10);
 const strange=await call('process-sale',sale('n105-inconsistent-tender108',50,100,7));
 assert.equal(strange.success,false,'credit and change cannot be mixed on the same tender');
 const arbitrary=await call('process-sale',sale('n105-more-change-cash108',100,140,null));
 assert.equal(arbitrary.success,true);
 d=read();assert.equal(d.cash_change_audit[0].cash_change_due,40);
 assert.equal(d.products[0].batches[0].stock,9);
 const before=JSON.stringify(d);
 failWrite=true;
 r=await call('process-sale',sale('n105-failed-payment-0108',20,20));
 assert.equal(r.success,false);assert.equal(JSON.stringify(read()),before,'rollback must be atomic');
 r=await call('process-sale',sale('n105-failed-payment-0108',20,20));
 assert.equal(r.success,true);
 assert.equal(read().customers[0].balance,140);
 const invoice=read().sales[0];
 const repay=await call('nano-record-settlement-102',{kind:'sale',documentId:invoice.id,
  requestId:'settle-108-test-0001',method:'cash',amount:30});
 assert.equal(repay.success,true);
 assert.equal(read().customers[0].balance,110);
 assert.deepEqual(read().backups,original.backups);
 assert.equal(read().settings.activation,'LICENSE-KEPT');
 console.log('PASS: backend partial/credit, overpayment/change, duplicate id, stock, rollback and accounting');
})().catch(e=>{console.error(e);process.exitCode=1});
