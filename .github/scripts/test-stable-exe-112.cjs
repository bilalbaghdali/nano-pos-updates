'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const KEY='lumina-browser-data-v1';
const original={
 products:[{id:1,name:'Milk',barcode:'PB-12345',stock:9,batches:[{id:2,stock:9,selling_price:100,cost_price:40}]}],
 customers:[{id:7,name:'Ahmed',balance:0}],suppliers:[],sales:[],purchases:[],
 settings:{shop_name:'NANO POS',activation:'KEEP'},backups:[{id:'KEEP'}],
 users:[{id:1,name:'Admin',username:'admin',role:'Admin',permissions:['all']}],revision:1
};
const records=new Map([[KEY,JSON.stringify(original)],
 ['pos_current_user',JSON.stringify({id:1,username:'admin',role:'Admin'})]]);
let failWrite=false,events=[];
const localStorage={
 getItem:k=>records.get(k)||null,
 setItem(k,v){if(failWrite&&k===KEY){failWrite=false;throw Error('simulated disk/quota failure')}records.set(k,String(v))},
 removeItem:k=>records.delete(k)
};
const w={
 NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},
 NANO_PAYMENT_LEDGER_102:require('./nano-payment-ledger-102.js'),
 NANO_INVOICE_SEQUENCE_111:require('./nano-invoice-sequence-111.js'),
 nanoLicense:{access:async()=>({allowed:true})},
 nanoNative:{pcSyncLocalChanged(){}},
 addEventListener(){},
 dispatchEvent:e=>{events.push(e.type)}
};
const context={window:w,localStorage,
 sessionStorage:{getItem:()=>null,setItem(){},removeItem(){}},location:{protocol:'file:',port:''},
 navigator:{},document:{},console,JSON,Date,Math,Number,Array,Map,Set,Promise,Intl,URL,structuredClone,
 CustomEvent:class {constructor(type){this.type=type}},setTimeout:()=>0,setInterval:()=>0,clearTimeout:()=>{}};
vm.runInNewContext(fs.readFileSync('browser-bridge.js','utf8'),context);
const invoke=(channel,...args)=>w.__browserElectron.ipcRenderer.invoke(channel,...args);
const db=()=>JSON.parse(records.get(KEY));
(async()=>{
 // Positive mutation and normal client interaction
 let result=await invoke('add-customer',{name:'New client',phone:'0551555555',initial_debt:0});
 assert.equal(result.success,true);
 assert.equal(db().customers.length,2);
 const before=JSON.stringify(db());
 const rev=db().revision;
 // Formerly false success from save() swallowed disk/quota errors.
 failWrite=true;
 await assert.rejects(invoke('add-customer',{name:'Unsaved fake client'}),/nano_storage_write_failed_no_changes/);
 assert.equal(JSON.stringify(db()),before,'prior snapshot must not change');
 assert.equal(db().revision,rev,'failed save must not consume revision');
 assert.equal(events.filter(e=>e==='nano-storage-save-failed').length,1);
 await assert.rejects((async()=>{
   failWrite=true;
   return await invoke('update-product',1,{name:'Unsaved product'});
 })(),/nano_storage_write_failed_no_changes/);
 assert.equal(db().products[0].name,'Milk');
 assert.equal(JSON.stringify(db().settings),JSON.stringify({...original.settings}));
 // Existing safe sale implementation must still save complete inventory, balance and FA number.
 const sale={items:[{id:1,batch_id:2,qty:1,pos_price:100}],checkout:{
  subtotal:100,total:100,paidAmount:40,customerId:7,paymentMethod:'cash',
  nanoCheckoutRequestId:'n105-stable-final-112'}};
 result=await invoke('process-sale',sale);
 assert.equal(result.success,true,JSON.stringify(result));
 assert.match(result.invoice_number,/^FA-\d{4}-01$/);
 let saved=db();
 assert.equal(saved.customers.find(x=>x.id===7).balance,60);
 assert.equal(saved.sales[0].paid_amount,40);
 assert.equal(saved.products[0].batches[0].stock,8);
 result=await invoke('process-sale',sale);
 assert.equal(result.alreadyProcessed,true);
 assert.equal(db().sales.length,1);
 // Genuine sale transaction failure must be explicit and atomic as in v111.
 failWrite=true;
 const next={...sale,checkout:{...sale.checkout,nanoCheckoutRequestId:'n105-stable-final-112-next'}};
 result=await invoke('process-sale',next);
 assert.equal(result.success,false);
 assert.equal(db().sales.length,1);
 assert.equal(db().customers.find(x=>x.id===7).balance,60);
 assert.equal(db().products[0].batches[0].stock,8);
 assert.equal(db().invoice_counters.sales[new Date().getFullYear()],1);
 assert.deepEqual(db().backups,original.backups);
 console.log('PASS: failure surfaced and rolled back for product/customer, no phantom success, safe partial-credit sales and stock idempotence');
})().catch(e=>{console.error(e);process.exitCode=1});
