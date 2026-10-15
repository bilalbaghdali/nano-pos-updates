'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const paths=process.argv.slice(2),src=paths.map(p=>fs.readFileSync(p,'utf8'));
const fixed={revision:1,products:[{id:1,barcode:'BAR-MILK',name:'Milk',pos_price:20,batches:[{id:11,stock:10}]},
  {id:2,barcode:'BAR-JUICE',name:'Juice',pos_price:30,batches:[{id:12,stock:5}]}],
 customers:[],suppliers:[],sales:[],purchases:[],stocktakes:[],stocktake_drafts:[],caisse_sessions:[],caisse_transactions:[],
 users:[{id:1,name:'Admin',role:'Admin',username:'admin',password:'admin',permissions:['all']}],settings:{shop_name:'NANO POS'}};
const map=new Map([['lumina-browser-data-v1',JSON.stringify(fixed)],['pos_current_user',JSON.stringify({id:1,role:'Admin',name:'Admin'})]]);
const store={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k)};
const noop=()=>{};
const window={NANO_CONFIG:{login:{username:'admin',password:'admin'}},nanoLicense:{access:async()=>({allowed:true})},
  dispatchEvent:noop,addEventListener:noop,removeEventListener:noop};
const ctx={window,localStorage:store,sessionStorage:{getItem:()=>null,setItem:noop,removeItem:noop},location:{protocol:'file:',port:''},
 document:{addEventListener:noop,querySelectorAll:()=>[],getElementById:()=>null,querySelector:()=>null,body:{appendChild:noop}},
 Event:class{},CustomEvent:class{},console,setTimeout,clearTimeout,setInterval:()=>0,clearInterval,structuredClone,
 URL,Map,Set,Intl,Date,Math,Number,String,Error,JSON,Array};
window.document=ctx.document;window.location=ctx.location;
vm.createContext(ctx);
src.forEach((s,i)=>vm.runInContext(s,ctx,{filename:paths[i],timeout:11000}));
const call=window.__browserElectron?.ipcRenderer?.invoke;
assert.equal(typeof call,'function');
const get=()=>JSON.parse(store.getItem('lumina-browser-data-v1'));
const dev=(deviceId,deviceName)=>({origin:'mobile',deviceId,deviceName});
const A=dev('MOBILE-ANDROID-DEVICE-A','Samsung A');
const B=dev('MOBILE-ANDROID-DEVICE-B','Oppo B');
const sid='inventory-session-169-001';
(async()=>{
 let x=await call('nano-count-start',{sessionId:sid,userId:1,title:'جرد يومي'});
 assert.equal(x.success,true,JSON.stringify(x));
 assert.equal((await call('nano-count-active')).active,true);
 const a={sessionId:sid,barcode:'BAR-MILK',operatorName:'أحمد',requestId:'claim-A1-12345678',__nanoCountOrigin:A};
 const b={sessionId:sid,barcode:'BAR-MILK',operatorName:'ليلى',requestId:'claim-B1-12345678',__nanoCountOrigin:B};
 x=await call('nano-count-claim',a);
 assert.equal(x.status,'claimed',JSON.stringify(x));const token=x.token;
 assert.equal(x.rows[0].book_qty,10);
 x=await call('nano-count-claim',b);assert.equal(x.status,'busy');assert.equal(x.operator,'أحمد');
 x=await call('nano-count-record',{sessionId:sid,productId:1,token,operatorName:'ليلى',
   rows:[{batch_id:11,book_qty:10,counted_qty:8}],__nanoCountOrigin:B});
 assert.equal(x.success,false,'other phone cannot submit locked product');
 x=await call('nano-count-record',{sessionId:sid,productId:1,token,operatorName:'أحمد',
   rows:[{batch_id:11,book_qty:10,counted_qty:8}],__nanoCountOrigin:A});
 assert.equal(x.success,true,JSON.stringify(x));assert.equal(x.status,'counted');
 assert.equal(get().products[0].batches[0].stock,10,'counting does not change inventory');
 x=await call('nano-count-claim',b);assert.equal(x.status,'counted');assert.equal(x.operator,'أحمد');
 x=await call('nano-count-claim',{...b,barcode:'BAR-JUICE'});assert.equal(x.status,'claimed');
 const milk=(await call('nano-count-active')).session.countedProducts.find(x=>x.productId===1);
 assert.equal(milk.operator,'أحمد');
 assert.equal(milk.deviceName,'Samsung A');
 assert.equal(milk.rows[0].counted_qty,8);
 let end=await call('nano-count-finish',{sessionId:sid});
 assert.equal(end.success,false,'active other device lock should prevent finish');
 x=await call('nano-count-release',{sessionId:sid,productId:2,token:x.token,operatorName:'ليلى',__nanoCountOrigin:B});
 assert.equal(x.success,true);
 end=await call('nano-count-finish',{sessionId:sid});
 assert.equal(end.success,true,JSON.stringify(end));
 assert.equal(get().nano_multi_count_sessions[0].status,'closed');
 assert.equal(get().stocktake_drafts.length,1);
 assert.equal(get().stocktake_drafts[0].rows[0].counted_qty,8);
 assert.equal(get().products[0].batches[0].stock,10);
 console.log('PASS true app bridge: 2 device lock, operator, duplicate rescan, stale reserve, pending draft with unchanged inventory');
})().catch(e=>{console.error(e);process.exitCode=1;});
