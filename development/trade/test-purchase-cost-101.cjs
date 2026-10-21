'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const model=require('./nano-trade-analytics-101.js');
const vendors=[{id:1,name:'Supplier A'},{id:2,name:'Supplier B'}],today=Date.parse('2026-10-21T08:00:00Z');
const purchases=[
 {supplier_id:1,invoice_date:'2026-10-15',items:[{product_id:10,cost_price:'100.00'}]},
 {supplier_id:2,invoice_date:'2026-10-19',items:[{product_id:10,cost_price:'98.00'}]},
 {supplier_id:1,invoice_date:'2026-09-01',items:[{product_id:10,cost_price:'30.00'}]},
 {supplier_id:99,invoice_date:'2026-10-20',items:[{product_id:10,cost_price:'1.00'}]}];
const quotes=model.quotes(10,vendors,purchases,today);
assert.equal(quotes.length,2);
assert.equal(quotes[0].supplierId,'2');assert.equal(quotes[0].unitCost,98);
assert.equal(quotes[1].supplierId,'1');assert.equal(quotes[1].unitCost,100);
const inputs=[{productId:10,name:'A',supplierId:1,quantity:'2',unitCost:'100.00'},
 {productId:11,name:'B',supplierId:1,quantity:'1',unitCost:'200.00'},
 {productId:12,name:'C',supplierId:2,quantity:'0.500',unitCost:'50.00'}];
const original=JSON.stringify(inputs);
const planned=model.estimate(inputs,{
 '1':{freight:'1.01',other:'2.02',nonrecoverableTax:'0.03'},
 '2':{freight:'0.01',other:'0',nonrecoverableTax:'0'}},'20.00');
assert.equal(JSON.stringify(inputs),original,'model must never mutate inventory or order data');
assert.equal(planned.groups.length,2);
assert.equal(planned.totals.subtotalCents,42500);
assert.equal(planned.totals.chargesCents,307);
assert.equal(planned.totals.totalCents,42807);
for(const g of planned.groups){
 assert.equal(g.lines.reduce((s,x)=>s+x.addedCostsCents,0),g.chargesCents);
 assert.equal(g.lines.reduce((s,x)=>s+x.landedCents,0),g.totalCents);
 for(const l of g.lines)assert.ok(l.targetSellingCents>=l.landedUnitCents);
}
const pair=model.estimate([{productId:'x',supplierId:1,quantity:1,unitCost:0.01},
 {productId:'y',supplierId:1,quantity:1,unitCost:0.01}],{'1':{freight:'0.01'}},'0');
assert.deepEqual(pair.groups[0].lines.map(l=>l.addedCostsCents),[1,0],'deterministic residual cent');
assert.throws(()=>model.estimate(inputs,{},'100'),e=>e.code==='invalid_margin');
assert.throws(()=>model.estimate([{productId:1,supplierId:1,quantity:-2,unitCost:1}]),e=>e.code==='invalid_decimal');
assert.throws(()=>model.estimate([{productId:1,supplierId:1,quantity:1,unitCost:1.999}]),e=>e.code==='invalid_decimal');
let seed=20261021;
const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
for(let test=0;test<2000;test++){
 const lines=Array.from({length:(rand()%30)+1},(_,i)=>({productId:'P'+i,
  supplierId:String((rand()%3)+1),quantity:String((rand()%1000)+1)+'.'+String(rand()%1000).padStart(3,'0'),
  unitCost:String(rand()%3000)+'.'+String(rand()%100).padStart(2,'0')}));
 const charges={'1':{freight:String(rand()%200)+'.01'},'2':{other:String(rand()%200)+'.03'},'3':{freight:'1.01'}};
 const output=model.estimate(lines,charges,'20');
 assert.equal(output.groups.reduce((sum,g)=>sum+g.totalCents,0),output.totals.totalCents);
 assert.equal(output.groups.reduce((sum,g)=>sum+g.chargesCents,0),output.totals.chargesCents);
 for(const group of output.groups)assert.equal(group.lines.reduce((sum,l)=>sum+l.landedCents,0),group.totalCents);
}
const ui=fs.readFileSync('nano-po-shortage-ui-100.js','utf8'),html=fs.readFileSync('index.html','utf8');
assert.ok(ui.includes('function costReport(){'));
assert.ok(ui.includes('win.NANO_TRADE_ANALYTICS_101'));
assert.ok(ui.includes('read-only')||ui.includes('لا تغير المخزون')||ui.includes('للمراجعة فقط'));
assert.ok(html.indexOf('src="nano-trade-analytics-101.js"')<html.indexOf('src="nano-po-shortage-ui-100.js"'));
assert.equal(JSON.parse(fs.readFileSync('package.json','utf8')).version,'1.0.101');
console.log('PASS: supplier history comparisons, accounting-cents allocation, 2000 random checks, read-only UI integration');
