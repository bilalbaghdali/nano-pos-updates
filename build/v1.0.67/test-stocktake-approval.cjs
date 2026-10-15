'use strict';const assert=require('node:assert/strict'),m=require('./nano-stocktake-approval.js');
const g=require('../v1.0.65/nano-transaction-guards.js');
const base={revision:2,products:[{id:1,batches:[{id:9,stock:10}]}],
  users:[{id:1,role:'Admin',name:'Admin'},{id:2,role:'Cashier',permissions:['inventory']}],
  stocktakes:[],stocktake_drafts:[],audit_log:[]};
let x=m.submit(base,{requestId:'stocktake-phone-001',deviceId:'phone',rows:[{product_id:1,batch_id:9,book_qty:10,counted_qty:7}]},2,g);
assert.equal(base.products[0].batches[0].stock,10,'submit cannot change stock');
assert.equal(x.next.stocktake_drafts[0].status,'pending');
assert.equal(m.submit(x.next,{requestId:'stocktake-phone-001',rows:[]},2,g).result.alreadyProcessed,true);
assert.throws(()=>m.approve(x.next,{draftId:'stocktake-phone-001'},2,g));
let approved=m.approve(x.next,{draftId:'stocktake-phone-001'},1,g);
assert.equal(approved.next.products[0].stock,7);
assert.equal(approved.next.stocktakes.length,1);
assert.equal(approved.next.stocktake_drafts[0].status,'approved');
assert.equal(approved.next.audit_log.length,1);
assert.equal(m.approve(approved.next,{draftId:'stocktake-phone-001'},1,g).result.alreadyApproved,true);
const stale=structuredClone(x.next);stale.products[0].batches[0].stock=8;
assert.throws(()=>m.approve(stale,{draftId:'stocktake-phone-001'},1,g),'stale primary stock must block approval');
const rejected=m.reject(x.next,{draftId:'stocktake-phone-001',reason:'Mismatch'},1);
assert.equal(rejected.next.products[0].batches[0].stock,10);
assert.equal(rejected.next.stocktake_drafts[0].status,'rejected');
assert.throws(()=>m.approve(rejected.next,{draftId:'stocktake-phone-001'},1,g));
console.log('PASS: draft preserves stock, approval by manager, collision/stale guard, reject and audit');