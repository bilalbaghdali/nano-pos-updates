'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const engine=require('./nano-purchase-order-engine.js');
const STORAGE_KEY='lumina-browser-data-v1';
const base=()=>({
 products:[{id:3,name:'Test Product',barcode:'111',pos_price:15,stock:10,
   batches:[{id:44,product_id:3,stock:10,cost_price:5,selling_price:15,created_at:'2026-10-01'}]}],
 suppliers:[{id:7,name:'Main Supplier',balance:0}],
 customers:[{id:10,name:'Customer',balance:19}],
 sales:[{id:900,total:19}],purchases:[],users:[{id:1,username:'admin',password:'admin',role:'Admin',permissions:['all']}],
 settings:{shop_name:'Shop',language:'ar'},revision:2,
 licence:'KEEP-ACTIVATION-UNTOUCHED',backups:[{id:'backup1',hash:'keep'}]
});
const clone=obj=>JSON.parse(JSON.stringify(obj));
async function exerciseBridge(){
 let written=0,crashOnNextWrite=false,notifications=0;
 const map=new Map([[STORAGE_KEY,JSON.stringify(base())],
   ['pos_current_user',JSON.stringify({id:1,role:'Admin',username:'admin'})],
   ['nano-pos-clean-business-2026-09-29-v1','done']]);
 const localStorage={
  getItem:k=>map.has(k)?map.get(k):null,
  setItem(k,v){if(crashOnNextWrite){crashOnNextWrite=false;throw Error('simulated_disk_full')}written++;map.set(k,String(v));},
  removeItem:k=>map.delete(k)
 };
 const sessionStorage={getItem:()=>null,setItem(){},removeItem(){}};
 function start(){
  const window={NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},NANO_PURCHASE_ORDER_ENGINE_110:engine,
    nanoLicense:{access:async()=>({allowed:true})},nanoNative:{pcSyncLocalChanged(){notifications++}},
    dispatchEvent(){},addEventListener(){},removeEventListener(){}};
  const context={window,localStorage,sessionStorage,location:{protocol:'file:',port:'',origin:'file://'},
   document:{},console,Date,Math,JSON,Number,Array,Set,Map,structuredClone,CustomEvent:class {constructor(type,arg){this.type=type;this.detail=arg?.detail;}},
   Event:class {},setTimeout:()=>0,clearTimeout:()=>{},setInterval:()=>0,fetch:async()=>{throw Error('unexpected network')},
   navigator:{},URL,Intl};
  vm.runInNewContext(fs.readFileSync('browser-bridge.js','utf8'),context,{filename:'browser-bridge.js'});
  return (channel,...args)=>window.__browserElectron.ipcRenderer.invoke(channel,...args);
 }
 let rpc=start();
 const before=clone(JSON.parse(map.get(STORAGE_KEY)));
 const payload={supplierId:7,operationId:'operation-order-10001',
  lines:[{productId:3,quantity:'5',unitCost:'10.00'}]};
 let result=await rpc('create-purchase-order',payload);
 assert.equal(result.success,true);
 let stored=JSON.parse(map.get(STORAGE_KEY));
 assert.equal(stored.products[0].stock,10,'order must not post stock');
 assert.equal(stored.suppliers[0].balance,0,'order must not add debt');
 assert.equal(stored.purchases.length,0);
 assert.equal(stored.sales[0].total,19);
 assert.equal(stored.customers[0].balance,19);
 assert.equal(stored.licence,before.licence);
 assert.deepEqual(stored.backups,before.backups);
 assert.equal((await rpc('get-purchase-orders')).length,1);
 // Same client retry after restart: no new order, no new writes.
 const writtenAfterOrder=written;
 rpc=start();
 const second=await rpc('create-purchase-order',payload);
 assert.equal(second.duplicate,true);assert.equal(written,writtenAfterOrder);
 assert.equal((await rpc('create-purchase-order',{...payload,lines:[{productId:3,quantity:6,unitCost:10}]})).success,false);
 const receipt={orderId:result.id,receiptId:'receipt-first-00001',operationId:'receipt-first-00001',
  expectedRevision:1,lines:[{lineId:'L1',quantity:'2'}]};
 const first=await rpc('confirm-purchase-order-receipt',receipt);
 assert.equal(first.success,true);
 stored=JSON.parse(map.get(STORAGE_KEY));
 assert.equal(stored.products[0].stock,12);
 assert.equal(stored.suppliers[0].balance,20);
 assert.equal(stored.purchases.length,1);
 assert.equal(stored.purchases[0].total,20);
 assert.equal(stored.purchase_orders[0].status,'partial');
 assert.equal(stored.purchase_orders[0].lines[0].receivedMilli,2000);
 assert.equal(notifications>0,true);
 // Receipt retry after receipt revised order: must return original invoice, no duplicate posting.
 const afterFirst=written;
 rpc=start();
 const dup=await rpc('confirm-purchase-order-receipt',receipt);
 assert.equal(dup.duplicate,true);assert.equal(dup.purchaseId,first.purchaseId);assert.equal(written,afterFirst);
 assert.equal((await rpc('confirm-purchase-order-receipt',
   {...receipt,lines:[{lineId:'L1',quantity:'3'}]})).success,false);
 assert.equal((await rpc('confirm-purchase-order-receipt',
   {orderId:result.id,receiptId:'receipt-over-00001',expectedRevision:2,
    lines:[{lineId:'L1',quantity:'4'}]})).success,false);
 stored=JSON.parse(map.get(STORAGE_KEY));assert.equal(stored.products[0].stock,12);
 // Simulated localStorage failure: neither stock nor supplier balance may change.
 crashOnNextWrite=true;
 const failed=await rpc('confirm-purchase-order-receipt',
  {orderId:result.id,receiptId:'receipt-retry-0002',expectedRevision:2,
   lines:[{lineId:'L1',quantity:'3'}]});
 assert.equal(failed.success,false);assert.equal(failed.error,'purchase_order_write_failed_no_changes');
 stored=JSON.parse(map.get(STORAGE_KEY));
 assert.equal(stored.products[0].stock,12);assert.equal(stored.suppliers[0].balance,20);
 assert.equal(stored.purchase_orders[0].receipts.length,1);
 // Retry that previously failed to persist with the SAME operation ID:
 const complete=await rpc('confirm-purchase-order-receipt',
   {orderId:result.id,receiptId:'receipt-retry-0002',expectedRevision:2,
    lines:[{lineId:'L1',quantity:'3'}]});
 assert.equal(complete.success,true);assert.equal(complete.status,'received');
 stored=JSON.parse(map.get(STORAGE_KEY));
 assert.equal(stored.products[0].stock,15);assert.equal(stored.suppliers[0].balance,50);
 assert.equal(stored.purchases.length,2);
 assert.equal(stored.purchase_orders[0].receipts.length,2);
 assert.equal(stored.licence,before.licence);
 assert.deepEqual(stored.backups,before.backups);
 assert.deepEqual(stored.sales,before.sales);
 assert.deepEqual(stored.customers,before.customers);
 assert.deepEqual(JSON.parse(map.get(STORAGE_KEY)).purchase_orders,stored.purchase_orders);
 // Backup/snapshot round-trip must preserve orders, linked receipt IDs and balances.
 const snapshot=await rpc('__nano-pc-export-snapshot');
 assert.equal(snapshot.purchase_orders[0].receipts.length,2);
 assert.equal(snapshot.suppliers[0].balance,50);
 rpc=start();
 const persisted=await rpc('get-purchase-orders');
 assert.equal(persisted.length,1);assert.equal(persisted[0].status,'received');
 console.log('PASS: order-to-receipt integration, no stock before receipt, debt exactly once, disk failure rollback, persisted snapshot, activation/data intact');
}
function exerciseCore(){
 const db=base();
 assert.equal(engine.planOrder(db,{supplierId:7,operationId:'order-core-unit-0001',
   lines:[{productId:3,quantity:'1.250',unitCost:'8.20'}]}).snapshot.purchase_orders.length,1);
 assert.equal(JSON.stringify(db),JSON.stringify(base()),'pure order planner mutates source');
 assert.throws(()=>engine.planOrder(db,{supplierId:7,operationId:'order-core-unit-0002',lines:[{productId:3,quantity:'-1',unitCost:4}]}));
 assert.throws(()=>engine.planOrder(db,{supplierId:7,operationId:'order-core-unit-0003',lines:[{productId:4,quantity:1,unitCost:4}]}));
 console.log('PASS: input validation, fractional quantities and read-only calculations');
}
(async()=>{exerciseCore();await exerciseBridge();})().catch(e=>{console.error(e);process.exitCode=1});
