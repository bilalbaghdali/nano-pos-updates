'use strict';
const assert=require('node:assert/strict');
const model=require('./nano-po-auto-supplier-100.js');
const suppliers=[{id:1,name:'Supplier A'},{id:2,name:'Supplier B'}];
const now=Date.parse('2026-10-21T00:00:00Z');
const purchases=[
 {id:1,supplier_id:1,invoice_date:'2026-09-10',items:[{product_id:10,cost_price:12},{product_id:20,cost_price:3}]},
 {id:2,supplier_id:2,invoice_date:'2026-09-20',items:[{product_id:10,cost_price:8},{product_id:30,cost_price:5}]},
 {id:3,supplier_id:1,invoice_date:'2025-01-12',items:[{product_id:30,cost_price:1}]},
 {id:4,supplier_id:99,invoice_date:'2026-10-05',items:[{product_id:10,cost_price:1}]}
];
const rows=[
 {id:10,name:'Item 10',order:10,stock:2,costPrice:17},
 {id:20,name:'Item 20',order:5,stock:0,supplierId:1,costPrice:7},
 {id:30,name:'Item 30',order:3,stock:0,costPrice:9},
 {id:40,name:'Item 40',order:2,stock:0,costPrice:6},
 {id:50,name:'Item 50',order:4,stock:0,supplierId:99,costPrice:7}
];
const orders=[
 {id:'open',status:'partial',lines:[{productId:10,quantityMilli:6000,receivedMilli:2000}]},
 {id:'cover',status:'pending',lines:[{productId:20,quantityMilli:5000,receivedMilli:0}]},
 {id:'closed',status:'received',lines:[{productId:30,quantityMilli:20000,receivedMilli:20000}]}
];
const before=JSON.stringify([suppliers,purchases,rows,orders]);
const p=model.build(rows,suppliers,purchases,orders,{now});
assert.equal(JSON.stringify([suppliers,purchases,rows,orders]),before,'planning must not mutate any business record');
const find=id=>p.items.find(x=>x.productId===String(id));
assert.equal(find(10).supplierId,'2','choose cheapest recent recorded supplier');
assert.equal(find(10).unitCost,8);
assert.equal(find(10).quantity,6,'subtract previously ordered not-yet-received quantity');
assert.equal(find(20).skip,true,'avoid duplicate outstanding orders');
assert.equal(find(30).supplierId,'2','fresh quote beats historic stale cheap quote');
assert.equal(find(30).quantity,3,'received purchase orders are not pending');
assert.equal(find(40).supplierId,'','unknown supplier must never be invented');
assert.equal(find(40).requiresReview,true);
assert.equal(find(50).supplierId,'','unknown configured supplier must not be used');
assert.equal(p.skipped,1);
const configured=model.build([{id:10,name:'Item 10',order:3,supplierId:1,costPrice:12}],suppliers,purchases,[],{now});
assert.equal(configured.items[0].supplierId,'1','explicit configured supplier wins');
assert.equal(configured.items[0].unitCost,12,'configured supplier historical price is used');
const old=model.build([{id:30,name:'Item 30',order:1}],suppliers,[purchases[2]],[],{now});
assert.equal(old.items[0].supplierId,'1','last known supplier can be suggested but identified as historical');
assert.equal(old.items[0].reason,'last_known_supplier');
const fallback=model.build([{id:77,name:'No history',order:1,supplierId:1,costPrice:5.55}],suppliers,[],[],{now});
assert.equal(fallback.items[0].unitCost,5.55);
assert.equal(model.build([{id:20,order:0}],suppliers,[],[],{now}).items.length,0);
assert.throws(()=>model.build(null,suppliers,[],[],{now}),/invalid_shortage_source/);
console.log('PASS: supplier ranking, stale data, assigned supplier, unassigned fallback, deduplicated open POs, read-only source');
