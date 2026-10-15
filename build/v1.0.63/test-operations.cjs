'use strict';
const assert=require('node:assert/strict');
const ops=require('./nano-operations-center.js');
const reorder=require('../v1.0.62/nano-restock-assistant.js');
const x=ops.model([
  {name:'حليب',stock:1,min_stock:5,expiry_date:'2026-10-20'},
  {name:'معجون',stock:8,min_stock:5},
  {name:'عصير',stock:3,min_stock:3,expiry_date:'2026-10-10'}
],reorder,new Date(2026,9,15));
assert.equal(x.low,1);assert.equal(x.expired,1);assert.equal(x.expiring,1);
assert.equal(ops.refs.find(x=>x[0]==='caisseSection')[1],'الصندوق والمناوبات');
assert.equal(ops.normalizeNotifications({}).length,0);
assert.deepEqual(ops.normalizeNotifications([{message:'a'},{title:'b',type:'backup'}]).map(x=>x.title),['a','b']);
assert.equal(ops.safeLabel('x'.repeat(400)).length,220);
console.log('PASS: safe read-only unified alerts, operations links, and stock expiry logic');
