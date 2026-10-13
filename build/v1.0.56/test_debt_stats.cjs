'use strict';
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const filename=process.argv[2]||__dirname+'/nano-debt-stats-fix.js';
const w={};const ctx=vm.createContext({window:w,console,Number,Math,String,Map,Array,Object,Promise});
vm.runInContext(fs.readFileSync(filename,'utf8'),ctx,{filename});
const fix=w.NANODebtStatsFix;
assert(fix&&typeof fix.enrich==='function');
function api(db={}){
 const source={getCustomersDebt:db.debts,getCustomers:db.customers,getSuppliers:db.suppliers,getSales:db.sales,getPurchases:db.purchases};
 return Object.fromEntries(Object.entries(source).map(([k,v])=>[k,async()=>{if(v instanceof Error)throw v;return v;}]))
}
(async()=>{
 let res=await fix.enrich({totalCustomerDebt:0,totalSupplierDebt:0,customerDebts:[],supplierDebts:[]},api({debts:[{id:1,name:'Customer',balance:200}],customers:[{id:1,name:'Customer',balance:200}],suppliers:[{id:5,name:'Supplier',balance:180}]}));
 assert.equal(res.totalCustomerDebt,200);assert.equal(res.totalSupplierDebt,180);
 assert.equal(res.customerDebts.length,1);assert.equal(res.supplierDebts.length,1);
 res=await fix.enrich({totalCustomerDebt:500,totalSupplierDebt:400,customerDebts:[{debt:500}],supplierDebts:[{debt:400}]},api({debts:[],customers:[{id:1,balance:0}],suppliers:[{id:5,balance:0}],sales:[],purchases:[]}));
 assert.equal(res.totalCustomerDebt,0,'Settled customer must update stale analytics');assert.equal(res.totalSupplierDebt,0,'Settled supplier must update stale analytics');
 res=await fix.enrich({totalCustomerDebt:0,totalSupplierDebt:0},api({debts:[],customers:[{id:1,balance:0}],suppliers:[{id:5,balance:0}],sales:[{customer_id:1,total:300,paid_amount:100}],purchases:[{supplier_id:5,total:600,paid_amount:200}]}));
 assert.equal(res.totalCustomerDebt,200,'Open sale must show despite stale account balance');assert.equal(res.totalSupplierDebt,400,'Open purchase must show despite stale account balance');
 assert.equal(res.customerDebts[0].debt,200);assert.equal(res.supplierDebts[0].debt,400);
 res=await fix.enrich({totalCustomerDebt:0,totalSupplierDebt:0},api({debts:[{id:1,balance:200}],customers:[{id:1,balance:200}],suppliers:[{id:5,balance:400}],sales:[{customer_id:1,total:300,paid_amount:100}],purchases:[{supplier_id:5,total:600,paid_amount:200}]}));
 assert.equal(res.totalCustomerDebt,200,'Invoice and ledger should not be added twice');assert.equal(res.totalSupplierDebt,400);
 res=await fix.enrich({totalCustomerDebt:100,totalSupplierDebt:150,customerDebts:[{name:'kept',debt:100}],supplierDebts:[{name:'kept',debt:150}]},api({debts:new Error('offline'),customers:new Error('offline'),suppliers:new Error('offline'),sales:new Error('offline'),purchases:new Error('offline')}));
 assert.equal(res.totalCustomerDebt,100,'Do not clear confirmed stats on network failure');assert.equal(res.totalSupplierDebt,150);
 assert.deepEqual(res.customerDebts.map(x=>x.name),['kept']);
 res=await fix.enrich({totalCustomerDebt:0,totalSupplierDebt:0},api({debts:{data:{customers:[{id:1,balance:95}]}},customers:[],suppliers:{data:{rows:[{id:9,balance:70}]}}}));
 assert.equal(res.totalCustomerDebt,95);assert.equal(res.totalSupplierDebt,70);
 assert.equal(fix.mergeAccounts([{id:1,balance:120}],null,[{customer_id:1,total:30,paid_amount:10}],'customer')[0].debt,120);
 console.log('PASS customer and supplier debts desktop/mobile: missing analytics fields, partial sale/purchase, payment, no double counting, offline and wrapped lists');
})().catch(e=>{console.error(e);process.exitCode=1});