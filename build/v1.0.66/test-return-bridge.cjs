'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const bridge=fs.readFileSync(process.argv[2],'utf8');
const guard=fs.readFileSync(process.argv[3],'utf8');
const returns=fs.readFileSync(process.argv[4],'utf8');
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
vm.runInContext(bridge,ctx,{timeout:10000});
const call=window.__browserElectron?.ipcRenderer?.invoke;
assert.equal(typeof call,'function');
const get=()=>JSON.parse(storage.getItem('lumina-browser-data-v1'));
(async()=>{
 const first={requestId:'verified-return-001',saleId:300,userId:1,lines:[{lineIndex:0,quantity:1}]};
 let p=await call('issue-credit-note',first);
 assert.equal(p.success,true,JSON.stringify(p));assert.equal(p.debt_reduction,40);assert.equal(p.refund_amount,0);
 assert.equal(get().sales[0].total,80);assert.equal(get().products[0].batches[0].stock,8);
 assert.equal(get().customers[0].balance,35);
 p=await call('issue-credit-note',first);assert.equal(p.alreadyProcessed,true);
 assert.equal(get().sales_returns.length,1);
 p=await call('issue-credit-note',{requestId:'verified-return-002',saleId:300,userId:1,lines:[{lineIndex:0,quantity:2}]});
 assert.equal(p.success,true,JSON.stringify(p));assert.equal(p.refund_amount,45);assert.equal(p.debt_reduction,35);
 assert.equal(get().sales[0].total,0);assert.equal(get().sales[0].paid_amount,0);assert.equal(get().customers[0].balance,0);
 assert.equal(get().products[0].batches[0].stock,10);assert.equal(get().caisse_transactions[0].type,'refund');
 assert.equal(get().caisse_transactions[0].amount,45);
 p=await call('issue-credit-note',{requestId:'verified-return-003',saleId:300,userId:1,lines:[{lineIndex:0,quantity:1}]});
 assert.equal(p.success,false);
 const statistics=await call('get-analytics',{});
 assert.equal(statistics.sales.returns_count,2);assert.equal(statistics.sales.returns_value,120);
 assert.equal(statistics.cogs,0);
 assert.equal(get().audit_log.filter(x=>x.operation==='sale-return').length,2);
 console.log('PASS posted sale returns, partial credit, cash refunds, stock restore, idempotency and cost analytics');
})().catch(e=>{console.error(e);process.exit(1);});
