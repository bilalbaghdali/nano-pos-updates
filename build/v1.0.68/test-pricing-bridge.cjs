'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const bridge=fs.readFileSync(process.argv[2],'utf8'),guard=fs.readFileSync(process.argv[3],'utf8');
const ret=fs.readFileSync(process.argv[4],'utf8'),stock=fs.readFileSync(process.argv[5],'utf8'),pricing=fs.readFileSync(process.argv[6],'utf8');
const state={revision:3,products:[{id:1,name:'Milk',pos_price:100,wholesale_price:85,wholesale_qty:6,
  batches:[{id:8,stock:20,selling_price:100,wholesale_price:85}]}],
 promotions:[{id:44,product_id:1,discount_type:'percentage',discount_value:10,start_date:'2026-10-01',end_date:'2026-10-30',is_active:1}],
 customers:[{id:2,name:'Customer',balance:0}],suppliers:[],sales:[],purchases:[],stocktakes:[],caisse_transactions:[],
 caisse_sessions:[{id:11,user_id:1,status:'open',opened_at:'2026-10-15',opening_balance:100}],
 users:[{id:1,name:'Admin',username:'admin',password:'admin',role:'Admin',permissions:['all']}],settings:{shop_name:'NANO POS'}};
const map=new Map([['lumina-browser-data-v1',JSON.stringify(state)],['pos_current_user',JSON.stringify({id:1,name:'Admin'})]]);
const store={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k)},noop=()=>{};
const win={NANO_CONFIG:{login:{username:'admin',password:'admin'}},nanoLicense:{access:async()=>({allowed:true})},dispatchEvent:noop,addEventListener:noop};
const ctx={window:win,localStorage:store,sessionStorage:{getItem:()=>null,setItem:noop,removeItem:noop},
 location:{protocol:'file:',port:''},document:{addEventListener:noop,querySelectorAll:()=>[],querySelector:()=>null,getElementById:()=>null,body:{appendChild:noop}},
 Event:class{},CustomEvent:class{},console,setTimeout,clearTimeout,setInterval:()=>0,clearInterval,structuredClone,URL,Map,Set,Intl,Date,Math,Number,String,Error,JSON,Array};
win.document=ctx.document;win.location=ctx.location;vm.createContext(ctx);
for(const src of [guard,ret,stock,pricing,bridge])vm.runInContext(src,ctx,{timeout:8000});
const call=win.__browserElectron?.ipcRenderer?.invoke;assert.equal(typeof call,'function');
const data=()=>JSON.parse(store.getItem('lumina-browser-data-v1'));
(async()=>{
 let r=await call('nano-quote-active-price',{productId:1,quantity:6,tier:'auto'});
 assert.equal(r.success,true);assert.equal(r.quote.price,76.5);
 r=await call('process-sale',{items:[{id:1,batch_id:8,qty:1,pos_price:100}],
   checkout:{customerId:2,subtotal:100,total:100,paidAmount:0,paymentMethod:'credit',applyOffers:true},userId:1});
 assert.equal(r.success,true,JSON.stringify(r));
 assert.equal(data().sales[0].total,90,'promotion must be applied before saving authoritative sale');
 assert.equal(data().customers[0].balance,90);
 assert.equal(data().products[0].batches[0].stock,19);
 r=await call('process-sale',{items:[{id:1,batch_id:8,qty:1,pos_price:100}],
   checkout:{customerId:2,subtotal:100,total:100,paidAmount:100,paymentMethod:'cash'},userId:1});
 assert.equal(r.success,true,JSON.stringify(r));
 assert.equal(data().sales[0].total,100,'legacy sale must remain unchanged by default');
 assert.equal(data().sales.length,2);
 console.log('PASS v168 promotion enforced at invoice posting and legacy pricing untouched for both adapters');
})().catch(e=>{console.error(e);process.exit(1);});
