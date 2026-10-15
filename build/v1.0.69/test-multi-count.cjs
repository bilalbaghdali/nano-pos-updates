'use strict';
const assert=require('node:assert/strict'),m=require('./nano-multi-count.js');
const stock=require('../v1.0.67/nano-stocktake-approval.js');
const guard=require('../v1.0.65/nano-transaction-guards.js');
globalThis.NANO_TX_GUARD_165=guard;
const original={revision:1,users:[{id:1,role:'Admin',is_active:1,name:'Manager'}, {id:2,role:'Cashier',permissions:['inventory'],is_active:1}],
 products:[{id:4,barcode:'12345',name:'Milk',batches:[{id:7,stock:10}]},{id:6,barcode:'7788',name:'Juice',batches:[{id:8,stock:3}]}],
 stocktake_drafts:[],stocktakes:[],nano_multi_count_sessions:[]};
const a={origin:'mobile',deviceId:'MOBILE-PHONE-A1',deviceName:'Samsung'};
const b={origin:'mobile',deviceId:'MOBILE-PHONE-B1',deviceName:'Oppo'};
let s=m.start(original,{sessionId:'count-session-169-A',title:'الجرد اليومي'},1,10000);
assert.equal(m.active(original),null);
const requestA={sessionId:s.result.session.id,barcode:'12345',operatorName:'أمين',requestId:'claim-A1-12345678'};
const requestB={sessionId:s.result.session.id,barcode:'12345',operatorName:'سارة',requestId:'claim-B1-12345678'};
let claim=m.claim(s.next,requestA,a,12000);
assert.equal(claim.result.status,'claimed');assert.equal(claim.result.rows[0].book_qty,10);
const pending=m.claim(claim.next,requestB,b,12001);
assert.equal(pending.result.status,'busy');assert.equal(pending.result.operator,'أمين');
const record=m.record(claim.next,{sessionId:requestA.sessionId,productId:4,operatorName:'أمين',token:claim.result.token,
  rows:[{batch_id:7,book_qty:10,counted_qty:9}]},a,13000);
assert.equal(record.result.status,'counted');
assert.equal(record.next.products[0].batches[0].stock,10,'count must not modify inventory');
assert.equal(m.claim(record.next,requestB,b,14000).result.status,'counted');
assert.equal(m.claim(record.next,requestB,b,14000).result.operator,'أمين');
assert.equal(m.record(record.next,{sessionId:requestA.sessionId,productId:4,operatorName:'سارة',token:claim.result.token,
 rows:[{batch_id:7,book_qty:10,counted_qty:6}]},b,14001).result.status,'counted');
assert.equal(m.present(m.active(record.next)).session.countedProducts[0].deviceName,'Samsung');
let claimB=m.claim(record.next,{...requestB,barcode:'7788'},b,17000);
assert.equal(claimB.result.status,'claimed');
const expiry=m.claim(claimB.next,{...requestA,barcode:'7788'},a,17000+5*60*1000+1);
assert.equal(expiry.result.status,'claimed','expired lease must be reassignable');
assert.throws(()=>m.record(expiry.next,{sessionId:requestA.sessionId,productId:6,
 operatorName:'سارة',token:claimB.result.token,rows:[{batch_id:8,book_qty:3,counted_qty:1}]},b,17000+5*60*1000+3));
const changed=structuredClone(expiry.next);changed.products[1].batches[0].stock=4;
assert.throws(()=>m.record(changed,{sessionId:requestA.sessionId,productId:6,operatorName:'أمين',
 token:expiry.result.token,rows:[{batch_id:8,book_qty:3,counted_qty:1}]},a,17000+5*60*1000+4));
assert.throws(()=>m.finish(record.next,{sessionId:requestA.sessionId},2,stock,14000),'only primary manager may end');
let outcome=m.finish(record.next,{sessionId:requestA.sessionId},1,stock,14000);
assert.equal(outcome.result.products,1);assert.equal(outcome.next.products[0].batches[0].stock,10);
assert.equal(outcome.next.stocktake_drafts.length,1);assert.equal(outcome.next.stocktake_drafts[0].rows[0].counted_qty,9);
assert.equal(outcome.next.nano_multi_count_sessions[0].status,'closed');
assert.throws(()=>m.claim(outcome.next,requestB,b,14001));
assert.throws(()=>m.claim(record.next,requestB,{origin:'mobile',deviceId:'BAD'},14000));
console.log('PASS: cross-phone claim conflict, named operator, duplicate scan, stale quantities, lease reassignment, trusted device, draft finalization');