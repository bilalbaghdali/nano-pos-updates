'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const file = process.argv[2] || __dirname + '/nano-customer-details-fix.js';
const context = {window:{api:{getCustomerSales: async()=>({})}},console,Number,Array,Object,Error};
vm.runInNewContext(fs.readFileSync(file,'utf8'),context,{filename:file});
const read = (data, customer={id:9,name:'Ali'}) => {
 context.window.api.getCustomerSales = async () => data;
 return context.window.nanoGetCustomerSalesAndDebts(9, customer);
};
(async()=>{
 let result=await read({sales:[],payments:[],customer:{id:9,name:'Ali'}});
 assert.equal(result.sales.length,0);assert.equal(result.payments.length,0);
 result=await read([{id:4,total:'300.5',paid_amount:'100'}]);
 assert.equal(result.sales.length,1);assert.equal(result.sales[0].total,300.5);assert.equal(result.payments.length,0);
 result=await read({data:{sales:[{id:8,total:20,paid_amount:5}],payments:[]}});
 assert.equal(result.sales.length,1);assert.equal(result.customer.id,9);
 result=await read({sales:[{id:1,total:200,paid_amount:25}],payments:[{amount:'10',date:'2026-10-13'}],customer:{id:9}});
 assert.equal(result.payments[0].amount,10);assert.equal(result.sales[0].total-result.sales[0].paid_amount,175);
 result=await read({payments:[],customer:{id:9}});
 assert.equal(result.sales.length,0);
 for(const invalid of [undefined,null,{}, {success:false,message:'connection_failed'}, {sales:'bad',payments:'bad'}]) {
   await assert.rejects(read(invalid), /استجابة|connection_failed/);
 }
 await assert.rejects(read({sales:[{total:'invalid',paid_amount:0}],payments:[]}),/مالية/);
 await assert.rejects(read({sales:[],payments:[{amount:'invalid'}]}),/مالية/);
 console.log('PASS customer details: structured, array, nested, empty, errors, monetary safety');
})().catch(e=>{console.error(e);process.exitCode=1});