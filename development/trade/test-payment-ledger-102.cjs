'use strict';
const assert=require('node:assert/strict'),pay=require('./nano-payment-ledger-102.js');
const error=(fn,code)=>assert.throws(fn,e=>e.code===code,code);
const split=pay.split('100.00',[{method:'cash',amount:'25.55'},{method:'card',amount:'50'}],7);
assert.equal(split.paidAmount,75.55);assert.equal(split.remainingAmount,24.45);
assert.equal(split.paymentMethod,'mixed');assert.equal(split.payments.length,2);
error(()=>pay.split('100',[{method:'cash',amount:100.01}],7),'overpayment');
error(()=>pay.split('100',[{method:'cash',amount:'50'}],null),'credit_needs_customer');
error(()=>pay.split('100',[{method:'cash',amount:'50'},{method:'cash',amount:'20'}],7),'invalid_payment_method');
const sample=()=>({
  revision:2,products:[{id:3,name:'Unchanged',stock:1}],settings:{activation:'UNCHANGED'},
  customers:[{id:7,balance:40}],suppliers:[{id:9,balance:70}],
  sales:[{id:12,customer_id:7,total:100,paid_amount:60,remaining_amount:40,items:[{product_id:3,quantity:2}],payments:[]}],
  purchases:[{id:15,supplier_id:9,total:100,paid_amount:30,payments:[]}],
  backups:[{sha256:'KEEP'}]
});
const before=sample(),pristine=JSON.stringify(before);
const request={kind:'sale',documentId:12,requestId:'sale-receipt-00001',amount:'10.25',method:'cash'};
const first=pay.settle(before,request);
assert.equal(first.result.success,true);assert.equal(first.next.sales[0].remaining_amount,29.75);
assert.equal(first.next.customers[0].balance,29.75);
assert.equal(first.next.sales[0].payments.length,1);
assert.equal(first.next.nano_payment_ledger.length,1);
assert.equal(JSON.stringify(before),pristine,'planning may not mutate caller state');
const retry=pay.settle(first.next,request);
assert.equal(retry.duplicate,true);assert.equal(retry.next,null);
error(()=>pay.settle(first.next,{...request,amount:'10.26'}),'operation_reuse_conflict');
error(()=>pay.settle(first.next,{...request,requestId:'sale-receipt-00002',amount:'50'}),'payment_exceeds_debt');
const purchased=pay.settle(first.next,{kind:'purchase',documentId:15,requestId:'purchase-receipt-0001',amount:70,method:'virement'});
assert.equal(purchased.next.suppliers[0].balance,0);
assert.equal(purchased.next.purchases[0].paid_amount,100);
assert.equal(purchased.next.products[0].stock,1);
assert.deepEqual(purchased.next.backups,before.backups);
assert.deepEqual(purchased.next.settings,before.settings);
assert.equal(purchased.next.nano_payment_ledger.length,2);
const tamper=sample();tamper.customers[0].balance=0;
error(()=>pay.settle(tamper,request),'account_balance_inconsistent');
for(let n=0;n<2000;n++){
  const due=100000+n%1000,amount=n%100+1;
  const s=sample();
  s.sales[0].total=due/100;s.sales[0].paid_amount=(due-amount)/100;
  s.customers[0].balance=amount/100;
  const output=pay.settle(s,{kind:'sale',documentId:12,requestId:'sale-seq-'+String(n).padStart(8,'0'),
    amount:(amount/100).toFixed(2),method:'cash'});
  assert.equal(output.next.sales[0].paid_amount,due/100);
  assert.equal(output.next.sales[0].remaining_amount,0);
  assert.equal(output.next.customers[0].balance,0);
}
console.log('PASS: split payment, credit, persistent idempotency, supplier/customer accounts, 2000 settlement invariants');
