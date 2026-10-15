'use strict';const assert=require('node:assert/strict'),r=require('./nano-return-plan.js');
const db={products:[{id:1,batches:[{id:'batch1',stock:6}]}],
  sales:[{id:13,total:120,paid_amount:45,customer_id:2,items:[{product_id:1,batch_id:'batch1',quantity:3,total:120}]}],
  sales_returns:[]};
let p=r.plan(db,{requestId:'return-case-001',saleId:13,lines:[{lineIndex:0,quantity:1}]});
assert.equal(p.credit,40);assert.equal(p.refund,0);assert.equal(p.debtReduction,40);assert.equal(p.nextTotal,80);assert.equal(p.nextPaid,45);
db.sales[0].total=80;db.sales[0].original_total=120;
db.sales_returns.push({request_id:'return-case-001',sale_id:13,credit_amount:40,lines:[{line_index:0,quantity:1}]});
assert.equal(r.plan(db,{requestId:'return-case-001',saleId:13,lines:[{lineIndex:0,quantity:1}]}).repeat,true);
p=r.plan(db,{requestId:'return-case-002',saleId:13,lines:[{lineIndex:0,quantity:2}]});
assert.equal(p.credit,80);assert.equal(p.debtReduction,35);assert.equal(p.refund,45);assert.equal(p.nextTotal,0);assert.equal(p.nextPaid,0);
assert.throws(()=>r.plan(db,{requestId:'return-case-003',saleId:13,lines:[{lineIndex:0,quantity:3}]}));
assert.throws(()=>r.plan(db,{requestId:'return-case-004',saleId:13,lines:[{lineIndex:0,quantity:-1}]}));
assert.throws(()=>r.plan({...db,products:[]},{requestId:'return-case-005',saleId:13,lines:[{lineIndex:0,quantity:1}]}));
console.log('PASS: idempotent return plans, credit debt allocation, refunds and stock batch guard');