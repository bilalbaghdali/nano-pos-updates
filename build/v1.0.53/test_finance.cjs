'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

async function newEnvironment(filename) {
 const memory = new Map();
 const init = {
   products:[{id:1,name:'Product',barcode:'1',cost_price:6,pos_price:10,batches:[{id:11,stock:40,cost_price:6,selling_price:10}]}],
   customers:[{id:9,name:'Ali',phone:'0555000000',balance:0,initial_debt:0,credit_limit:300}],
   suppliers:[{id:19,name:'Supply',balance:0}],
   sales:[],purchases:[],supplier_payments:[],supplier_returns:[],
   caisse_sessions:[],caisse_transactions:[],expenses:[],capital:[],
   users:[{id:1,name:'Manager',username:'admin',password:'admin',role:'Admin',permissions:['all']}],
   roles:['Admin'],settings:{currency:'DZD'},revision:1,
 };
 memory.set('lumina-browser-data-v1',JSON.stringify(init));
 const storage = { getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,String(v)),removeItem:k=>memory.delete(k)};
 const window = {NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},nanoLicense:{access:async()=>({allowed:true,reason:'licensed'})},setTimeout,clearTimeout,dispatchEvent:()=>{}};
 const context={window,location:{protocol:'file:',port:'',origin:'file://'},localStorage:storage,sessionStorage:storage,console,Date,Math,Number,JSON,Map,Set,Array,Object,structuredClone,URL,Blob:global.Blob,document:{body:{style:{}}}};
 vm.runInNewContext(fs.readFileSync(filename,'utf8'),context,{filename});
 const invoke=window.__browserElectron.ipcRenderer.invoke;
 return {invoke:(channel,...args)=>invoke(channel,...args),state:()=>JSON.parse(memory.get('lumina-browser-data-v1'))};
}

async function run(file) {
 const {invoke,state}=await newEnvironment(file);
 const items=[{id:1,qty:3,batch_id:11,pos_price:10}];
 assert.equal((await invoke('process-sale',{items,checkout:{customerId:null,total:30,paidAmount:10}})).success,false,'Credit without a customer must fail');
 assert.equal(state().products[0].batches[0].stock,40,'Rejected credit must not touch inventory');
 const saved=await invoke('process-sale',{items,checkout:{customerId:9,total:30,subtotal:30,paidAmount:10,paymentMethod:'cash'}});
 assert.equal(saved.success,true);
 assert.equal(saved.remaining_amount,20);
 assert.equal(state().sales[0].payment_method,'cash');
 assert.equal(state().sales[0].payment_status,'partial');
 assert.equal(state().customers[0].balance,20);
 assert.equal(state().products[0].batches[0].stock,37);
 let stats=await invoke('get-analytics',{});
 assert.equal(stats.totalCustomerDebt,20,'Live customer analytics');
 assert.equal((await invoke('get-customer-credit-summary',9)).debt,20);
 const saleId=saved.saleId;
 assert.equal((await invoke('add-sale-payment',saleId,7)).success,true);
 assert.equal(state().sales[0].remaining_amount,13);
 assert.equal(state().customers[0].balance,13);
 stats=await invoke('get-analytics',{});
 assert.equal(stats.totalCustomerDebt,13);
 assert.equal((await invoke('add-sale-payment',saleId,100)).success,false);
 assert.equal(state().customers[0].balance,13);
 assert.equal((await invoke('add-customer-payment',9,8)).success,true);
 assert.equal(state().sales[0].remaining_amount,5);
 assert.equal(state().customers[0].balance,5);
 assert.equal((await invoke('get-analytics',{})).totalCustomerDebt,5);
 // Purchases adjust supplier debts, invoice payment and supplier-wide settlement.
 const purchase=await invoke('save-purchase',{invoiceData:{supplier_id:19,subtotal:100,total:100,paid_amount:35},items:[{product_id:1,quantity:2,cost_price:50}]});
 assert.equal(purchase.success,true);
 assert.equal(state().suppliers[0].balance,65);
 assert.equal((await invoke('get-analytics',{})).totalSupplierDebt,65);
 assert.equal((await invoke('add-invoice-payment',purchase.id,15)).success,true);
 assert.equal((await invoke('get-analytics',{})).totalSupplierDebt,50);
 assert.equal((await invoke('add-supplier-payment',19,30)).success,true);
 assert.equal((await invoke('get-analytics',{})).totalSupplierDebt,20);
 assert.equal(state().suppliers[0].balance,20);
 assert.equal((await invoke('delete-sale',saleId)).success,true);
 assert.equal((await invoke('get-analytics',{})).totalCustomerDebt,0);
 console.log('PASS',file,'— partial sale, validation, debts, settlements, supplier invoices, analytics');
}
(async()=>{
 for(const file of process.argv.slice(2)) await run(file);
})().catch(e=>{console.error(e);process.exit(1)});