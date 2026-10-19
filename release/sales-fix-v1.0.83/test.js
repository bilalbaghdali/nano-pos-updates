'use strict';
const assert=require('assert'),fs=require('fs'),{JSDOM}=require('/tmp/testkit/node_modules/jsdom');
const root=process.argv[2];
const db={products:[{id:1,name:'Item',cost_price:15,batches:[{id:11,stock:8}]}],customers:[],users:[{id:1,name:'Admin'}],
sales:[{id:51,created_at:'2026-10-11',sale_date:'2026-10-11',total:100,paid_amount:100,initial_paid_amount:100,remaining_amount:0,payments:[],items:[{id:1,product_id:1,batch_id:11,quantity:2,price:50,cost_price:15}]}]};
async function test(){
const dom=new JSDOM('<html><body></body></html>',{url:'http://localhost:4700',runScripts:'outside-only'});
const w=dom.window;w.structuredClone=global.structuredClone;
w.NANO_CONFIG={distribution:{cleanBusinessDataOnFirstRun:false},login:{username:'admin',password:'test'}};
w.nanoLicense={access:async()=>({allowed:true}),installationId:()=> 'test'};
w.localStorage.setItem('lumina-browser-data-v1',JSON.stringify(db));
w.eval(fs.readFileSync(root+'/browser-bridge.js','utf8'));
const rpc=w.__browserElectron.ipcRenderer.invoke;
const edit=async(qty,price)=>rpc('process-sale',{editSaleId:51,userId:1,items:[{id:1,batch_id:11,qty,pos_price:price}],checkout:{total:qty*price,subtotal:qty*price,paidAmount:qty*price,paymentMethod:'cash'}});
let x=await edit(3,60);assert.equal(x.success,true,JSON.stringify(x));assert.equal(x.id,51);
let state=JSON.parse(w.localStorage.getItem('lumina-browser-data-v1'));
assert.equal(state.sales.length,1);assert.equal(state.products[0].batches[0].stock,7);
assert.equal(state.sales[0].created_at,'2026-10-11');
x=await edit(1,60);assert.equal(x.success,true,JSON.stringify(x));
state=JSON.parse(w.localStorage.getItem('lumina-browser-data-v1'));
assert.equal(state.sales.length,1);assert.equal(state.products[0].batches[0].stock,9);
x=await edit(20,60);assert.equal(x.success,false);
state=JSON.parse(w.localStorage.getItem('lumina-browser-data-v1'));assert.equal(state.products[0].batches[0].stock,9);
const analytics=await rpc('get-product-analytics',1);
assert.equal(analytics.totalSold,1);assert.equal(analytics.totalRevenue,60);
assert.equal(analytics.totalProfit,45);
assert.equal((await rpc('get-sale-edit-audit',{limit:10})).length,2);
dom.window.close();console.log('PASS original sale ID/time, no duplicate, stock, analytics, audit');
}
test().catch(e=>{console.error(e);process.exitCode=1});