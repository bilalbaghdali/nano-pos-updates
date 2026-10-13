'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
async function run(path){
 const memory = new Map();
 const initial = {
  products:[],
  customers:[{id:9,name:'Ali',initial_debt:100,balance:40},{id:10,name:'Fatima',balance:0}],
  customer_payments:[{id:60,customer_id:9,amount:8,date:'2026-10-13'}],
  sales:[{id:31,customer_id:9,total:50,paid_amount:20,sale_date:'2026-10-12',payments:[{id:61,amount:5,date:'2026-10-13',source:'direct'},{id:62,amount:8,date:'2026-10-13',source:'customer-payment'}]}, {id:32,customer_id:10,total:70,paid_amount:70,payments:[]}],
  suppliers:[],purchases:[],supplier_payments:[],supplier_returns:[],caisse_sessions:[],caisse_transactions:[],expenses:[],capital:[],users:[],roles:[],settings:{currency:'DZD'},revision:1
 };
 memory.set('lumina-browser-data-v1',JSON.stringify(initial));
 const store={getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,String(v)),removeItem:k=>memory.delete(k)};
 const window={NANO_CONFIG:{distribution:{cleanBusinessDataOnFirstRun:false}},nanoLicense:{access:async()=>({allowed:true})},setTimeout,clearTimeout,dispatchEvent:()=>{}};
 const ctx={window,location:{protocol:'file:',port:'',origin:'file://'},localStorage:store,sessionStorage:store,console,Date,Math,Number,JSON,Map,Set,Array,Object,structuredClone,URL,Blob:global.Blob,document:{body:{style:{}}}};
 vm.runInNewContext(fs.readFileSync(path,'utf8'),ctx,{filename:path});
 const call=(ch,...args)=>window.__browserElectron.ipcRenderer.invoke(ch,...args);
 const details=await call('get-customer-sales',9);
 assert.equal(Array.isArray(details),false,'Desktop detail expects a structured result');
 assert.equal(details.sales.length,1);
 assert.equal(details.sales[0].id,31);
 assert.equal(details.customer.name,'Ali');
 assert.equal(details.payments.length,2,'Do not duplicate customer-wide settlements');
 assert.equal(details.payments.reduce((n,p)=>n+p.amount,0),13);
 assert.equal(details.payments.find(p=>p.id===61)?.invoice_num,31);
 assert.equal(details.payments.find(p=>p.id===60)?.amount,8);
 assert.equal((await call('get-customer-sales',10)).sales.length,1);
 const unknown=await call('get-customer-sales',999);
 assert.equal(unknown.sales.length,0);assert.equal(unknown.payments.length,0);assert.equal(unknown.customer,null);
 const after=JSON.parse(memory.get('lumina-browser-data-v1'));
 assert.deepEqual(after,initial,'Opening customer details MUST NOT modify database');
 console.log('PASS customer detail backend',path);
}
(async()=>{for(const file of process.argv.slice(2))await run(file)})().catch(e=>{console.error(e);process.exitCode=1});