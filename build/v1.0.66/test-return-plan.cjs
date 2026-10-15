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
const live={products:[{id:1,batches:[{id:'batch1',stock:2}]}],customers:[{id:2,balance:75}],
  users:[{id:7,name:'Manager',role:'Manager',is_active:1}],caisse_sessions:[{id:88,status:'open',user_id:7}],
  sales:[{id:13,total:120,paid_amount:45,customer_id:2,payment_method:'cash',items:[{product_id:1,batch_id:'batch1',quantity:3,total:120}]}],
  sales_returns:[],caisse_transactions:[],audit_log:[]};
let response=r.post(live,{requestId:'posted-case-001',saleId:13,lines:[{lineIndex:0,quantity:1}]},7);
assert.equal(live.products[0].batches[0].stock,2,'No mutate live db before commit');
assert.equal(response.next.products[0].batches[0].stock,3);
assert.equal(response.next.customers[0].balance,35);
assert.equal(response.next.sales[0].total,80);
assert.equal(response.next.sales_returns.length,1);
assert.equal(response.next.audit_log.length,1);
assert.equal(response.next.caisse_transactions.length,0);
const next=response.next;
response=r.post(next,{requestId:'posted-case-002',saleId:13,lines:[{lineIndex:0,quantity:2}]},7);
assert.equal(response.next.sales[0].total,0);
assert.equal(response.next.sales[0].paid_amount,0);
assert.equal(response.next.customers[0].balance,0);
assert.equal(response.next.caisse_transactions.length,1);
assert.equal(response.next.caisse_transactions[0].amount,45);
assert.equal(response.next.products[0].batches[0].stock,5);
assert.equal(r.post(response.next,{requestId:'posted-case-002',saleId:13,lines:[{lineIndex:0,quantity:2}]},7).result.alreadyProcessed,true);
assert.throws(()=>r.post(live,{requestId:'posted-case-003',saleId:13,lines:[{lineIndex:0,quantity:1}]},33));
console.log('PASS: immutable-copy sale refunds, inventory, partial debt, cash shift and idempotency');