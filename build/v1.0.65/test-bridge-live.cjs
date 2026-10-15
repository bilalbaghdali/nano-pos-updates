'use strict';
const fs=require('node:fs');const vm=require('node:vm');const assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8');
const guard=fs.readFileSync(process.argv[3],'utf8');
const fixed={
 products:[{id:1,name:'Product A',pos_price:100,wholesale_price:87,batches:[{id:4,stock:10}]}],
 customers:[],suppliers:[],sales:[],purchases:[],stocktakes:[],settings:{shop_name:'NANO POS'},
 caisse_sessions:[{id:2,user_id:1,status:'open',opened_at:'2026-10-15T09:00:00',opening_balance:100}],
 caisse_transactions:[],users:[{id:1,name:'Admin',username:'admin',password:'admin',role:'Admin',permissions:['all']}],
 revision:2
};
const map=new Map([['lumina-browser-data-v1',JSON.stringify(fixed)]]);
const store={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k)};
const noop=()=>{};
const win={NANO_CONFIG:{login:{username:'admin',password:'admin'}},nanoLicense:{access:async()=>({allowed:true})},
  dispatchEvent:noop,addEventListener:noop,removeEventListener:noop};
const ctx={window:win,localStorage:store,sessionStorage:{getItem:()=>null,setItem:noop,removeItem:noop},
  location:{protocol:'file:',port:''},document:{addEventListener:noop,querySelectorAll:()=>[],querySelector:()=>null,getElementById:()=>null,body:{appendChild:noop}},
  Event:class{constructor(type){this.type=type;}},CustomEvent:class{},console,setTimeout,clearTimeout,
  setInterval:()=>0,clearInterval,structuredClone,URL,Map,Set,Intl,Date,Math,Number,String,Error,JSON,Array};
win.location=ctx.location;win.document=ctx.document;win.localStorage=store;win.sessionStorage=ctx.sessionStorage;
vm.createContext(ctx);
vm.runInContext(guard,ctx,{filename:'nano-transaction-guards.js',timeout:4000});
vm.runInContext(source,ctx,{filename:'browser-bridge.js',timeout:7000});
const call=win.__browserElectron?.ipcRenderer?.invoke;
assert.equal(typeof call,'function','Missing local browser IPC adapter');
(async()=>{
 let x=await call('issue-credit-note',{saleId:1});assert.equal(x.success,false,'unposted credit note must fail closed');
 x=await call('close-caisse-session',{sessionId:2,closingBalance:-5});assert.equal(x.success,false,'negative close must fail');
 x=await call('get-active-session',{});assert.equal(x.active,true,'invalid close must not change session');
 x=await call('close-caisse-session',{sessionId:2,closingBalance:100});assert.equal(x.success,true,'valid close must succeed');
 x=await call('close-caisse-session',{sessionId:2,closingBalance:110});assert.equal(x.success,false,'repeated shift close must fail');
 x=await call('nano-get-financial-action-log');assert.equal(x.filter(v=>v.operation==='close-caisse-session').length,1);
 x=await call('create-stocktake',{rows:[{product_id:1,batch_id:4,book_qty:9,counted_qty:8}]});assert.equal(x.success,false,'stale stocktake must fail');
 x=await call('create-stocktake',{rows:[{product_id:1,batch_id:4,book_qty:10,counted_qty:8},{product_id:1,batch_id:4,book_qty:10,counted_qty:9}]});assert.equal(x.success,false,'duplicate batch must fail');
 x=await call('get-products');assert.equal(x[0].stock,10,'invalid stocktake must not modify stock');
 x=await call('create-stocktake',{rows:[{product_id:1,batch_id:4,book_qty:10,counted_qty:8}]});assert.equal(x.success,true,'valid stocktake must succeed');
 x=await call('get-products');assert.equal(x[0].stock,8);
 x=await call('nano-quote-product-price',{productId:1,tier:'wholesale'});assert.equal(x.price,87);
 x=await call('nano-get-financial-action-log');assert.equal(x.filter(v=>v.operation==='create-stocktake').length,1);
 console.log('PASS real browser bridge shift, unposted credit fail, stocktake, wholesale and local journal');
})().catch(e=>{console.error(e);process.exit(1);});
