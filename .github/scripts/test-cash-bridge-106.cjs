'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const KEY='lumina-browser-data-v1',store=new Map();
const fixture={
  products:[{id:3,name:'Product',stock:10,cost_price:4,batches:[{id:44,stock:10,product_id:3,cost_price:4,selling_price:100}]}],
  customers:[{id:7,name:'Client',balance:0}],suppliers:[],sales:[],purchases:[],
  settings:{shop_name:'Saved shop',activation:'KEEP_LICENSE'},backups:[{stamp:'KEEP_BACKUP'}],
  users:[{id:1,name:'Admin',username:'admin',role:'Admin',permissions:['all']}],revision:5};
store.set(KEY,JSON.stringify(fixture));
store.set('pos_current_user',JSON.stringify({id:1,username:'admin',role:'Admin'}));
let rejectStorage=false,notify=0;
const localStorage={getItem:k=>store.get(k)||null,setItem(k,v){if(rejectStorage){rejectStorage=false;throw Error('disk unavailable');}store.set(k,String(v));},removeItem:k=>store.delete(k)};
const w={NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},
  nanoLicense:{access:async()=>({allowed:true})},
  NANO_PAYMENT_LEDGER_102:require('./nano-payment-ledger-102.js'),
  nanoNative:{pcSyncLocalChanged(){notify++;}},addEventListener(){},dispatchEvent(){}};
const context={window:w,localStorage,sessionStorage:{getItem(){return null},setItem(){},removeItem(){}},
  location:{protocol:'file:',port:''},navigator:{},document:{},console,
  JSON,Date,Math,Number,Array,Map,Set,Promise,Intl,URL,structuredClone,CustomEvent:class {},
  setTimeout:()=>0,setInterval:()=>0,clearTimeout:()=>{}};
vm.runInNewContext(fs.readFileSync('browser-bridge.js','utf8'),context,{filename:'browser-bridge.js'});
const invoke=(name,...args)=>w.__browserElectron.ipcRenderer.invoke(name,...args);
const read=()=>JSON.parse(store.get(KEY));
(async()=>{
 const payload={items:[{id:3,batch_id:44,qty:1,pos_price:100}],checkout:{
  total:100,subtotal:100,paidAmount:100,customerId:null,paymentMethod:'cash',
  cashTenderedAmount:'200.00',nanoCheckoutRequestId:'n105-change-receipt-0106'}};
 const first=await invoke('process-sale',payload);
 assert.equal(first.success,true,JSON.stringify(first));
 let state=read();
 assert.equal(state.sales.length,1);
 assert.equal(state.sales[0].paid_amount,100);
 assert.equal(state.sales[0].cash_change_amount,100);
 assert.equal(state.sales[0].cash_tendered_amount,200);
 assert.equal(state.cash_change_audit.length,1);
 assert.equal(state.cash_change_audit[0].cash_change_due,100);
 assert.equal(state.products[0].batches[0].stock,9);
 assert.equal(state.customers[0].balance,0);
 const retry=await invoke('process-sale',JSON.parse(JSON.stringify(payload)));
 assert.equal(retry.alreadyProcessed,true);
 assert.equal(read().cash_change_audit.length,1,'do not re-log tender on repeat sale');
 assert.equal(read().products[0].batches[0].stock,9);
 const wrong=await invoke('process-sale',{...payload,checkout:{...payload.checkout,
  nanoCheckoutRequestId:'n105-short-cash-0106',cashTenderedAmount:50}});
 assert.equal(wrong.success,false,'backend rejects insufficient tender');
 assert.equal(read().sales.length,1);
 const before=JSON.stringify(read());
 rejectStorage=true;
 const failed=await invoke('process-sale',{...payload,checkout:{...payload.checkout,
  nanoCheckoutRequestId:'n105-cash-rollback-0106',cashTenderedAmount:150}});
 assert.equal(failed.success,false);
 assert.equal(JSON.stringify(read()),before,'no phantom sale or cash audit on failed write');
 const second=await invoke('process-sale',{...payload,checkout:{...payload.checkout,
  nanoCheckoutRequestId:'n105-cash-rollback-0106',cashTenderedAmount:150}});
 assert.equal(second.success,true);
 state=read();
 assert.equal(state.sales.length,2);
 assert.equal(state.sales[0].cash_change_amount,50);
 assert.equal(state.products[0].batches[0].stock,8);
 assert.equal(state.cash_change_audit.length,2);
 assert.equal(state.settings.activation,'KEEP_LICENSE');
 assert.deepEqual(state.backups,fixture.backups);
 assert.ok(notify>0);
 const native=fs.readFileSync('electron-main.cjs','utf8');
 const start=native.indexOf('await startLocalServer();');
 const show=native.indexOf('createWindow();',start);
 const optional=native.indexOf('const startOptionalConnectivity106',show);
 const mobile=native.indexOf('await mobileSyncServer.start()',optional);
 const pc=native.indexOf('await pcSyncService.start()',optional);
 assert.ok(start>0&&show>start&&optional>show&&mobile>optional&&pc>mobile,
   'window must open before optional mobile and PC sync services start');
 assert.ok(native.includes("if(pcSyncService?.info?.().mode==='client')"),'client must synchronize after late startup');
 assert.ok(native.includes("setInterval(() => {"),'hourly automatic backups are preserved');
 assert.ok(native.includes("const automaticBackupTimer"),'hourly backup creation unchanged');
 console.log('PASS: cash change audit and invoice persist once, idempotency, failed-save rollback, unchanged license/backup and nonblocking window order');
})().catch(e=>{console.error(e);process.exitCode=1});
