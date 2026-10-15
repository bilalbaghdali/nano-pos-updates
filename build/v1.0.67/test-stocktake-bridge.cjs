'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const bridge=fs.readFileSync(process.argv[2],'utf8');
const guard=fs.readFileSync(process.argv[3],'utf8');
const returns=fs.readFileSync(process.argv[4],'utf8');
const stocktake=fs.readFileSync(process.argv[5],'utf8');
const db={products:[{id:1,name:'Milk',pos_price:40,batches:[{id:8,stock:7}]}],
 customers:[{id:2,name:'Customer',balance:75}],suppliers:[],purchases:[],stocktakes:[],settings:{shop_name:'NANO POS'},
 sales:[{id:300,total:120,paid_amount:45,initial_paid_amount:45,customer_id:2,payment_method:'cash',sale_date:'2026-10-15',
 items:[{product_id:1,batch_id:8,quantity:3,cost_price:22,total:120}]}],
 caisse_sessions:[{id:11,user_id:1,status:'open',opened_at:'2026-10-15T10:00:00',opening_balance:100}],
 caisse_transactions:[],users:[{id:1,name:'Admin',username:'admin',password:'admin',role:'Admin',permissions:['all']}],revision:2};
const map=new Map([['lumina-browser-data-v1',JSON.stringify(db)],['pos_current_user',JSON.stringify({id:1,name:'Admin',role:'Admin'})]]);
const storage={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k)};
const noop=()=>{};
const window={NANO_CONFIG:{login:{username:'admin',password:'admin'}},nanoLicense:{access:async()=>({allowed:true})},dispatchEvent:noop,addEventListener:noop,removeEventListener:noop};
const ctx={window,localStorage:storage,sessionStorage:{getItem:()=>null,setItem:noop,removeItem:noop},
 location:{protocol:'file:',port:''},document:{addEventListener:noop,querySelectorAll:()=>[],querySelector:()=>null,getElementById:()=>null,body:{appendChild:noop}},
 Event:class{},CustomEvent:class{},console,setTimeout,clearTimeout,setInterval:()=>0,clearInterval,structuredClone,URL,Map,Set,Intl,Date,Math,Number,String,Error,JSON,Array};
window.location=ctx.location;window.document=ctx.document;
vm.createContext(ctx);
vm.runInContext(guard,ctx,{timeout:5000});
vm.runInContext(returns,ctx,{timeout:5000});
vm.runInContext(stocktake,ctx,{timeout:5000});
vm.runInContext(bridge,ctx,{timeout:10000});
const call=window.__browserElectron?.ipcRenderer?.invoke;
assert.equal(typeof call,'function');
const get=()=>JSON.parse(storage.getItem('lumina-browser-data-v1'));
(async()=>{
 const draft1={requestId:'draft-approval-001',deviceId:'MOBILE-TEST',rows:[{product_id:1,batch_id:8,book_qty:7,counted_qty:3}]};
 let x=await call('create-stocktake-draft',draft1);
 assert.equal(x.success,true,JSON.stringify(x));
 assert.equal(get().products[0].batches[0].stock,7,'draft must not adjust stock');
 assert.equal(get().stocktake_drafts.length,1);
 x=await call('create-stocktake-draft',draft1);
 assert.equal(x.alreadyProcessed,true);
 x=await call('create-stocktake-draft',{requestId:'draft-approval-002',rows:[{product_id:1,batch_id:8,book_qty:7,counted_qty:5}]});
 assert.equal(x.success,true);
 x=await call('approve-stocktake-draft',{draftId:'draft-approval-001'});
 assert.equal(x.success,true,JSON.stringify(x));
 assert.equal(get().products[0].batches[0].stock,3);
 assert.equal(get().stocktakes.length,1);
 assert.equal(get().stocktakes[0].draft_id,'draft-approval-001');
 x=await call('approve-stocktake-draft',{draftId:'draft-approval-001'});
 assert.equal(x.alreadyApproved,true);
 assert.equal(get().stocktakes.length,1,'repeated approval must not create a second post');
 x=await call('approve-stocktake-draft',{draftId:'draft-approval-002'});
 assert.equal(x.success,false,'stale draft must be refused');
 assert.equal(get().products[0].batches[0].stock,3);
 x=await call('reject-stocktake-draft',{draftId:'draft-approval-002',reason:'stale'});
 assert.equal(x.success,true);
 assert.equal(get().stocktake_drafts.find(d=>d.id==='draft-approval-002').status,'rejected');
 const pending=await call('get-stocktake-drafts',{status:'pending'});
 assert.equal(pending.length,0);
 assert.equal(get().audit_log.filter(x=>x.operation==='approve-stocktake-draft').length,1);
 console.log('PASS true PC/mobile browser stocktake draft, stale validation, primary approval and rejection');
})().catch(e=>{console.error(e);process.exit(1);});
