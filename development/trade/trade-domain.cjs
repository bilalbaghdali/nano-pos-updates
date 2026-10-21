'use strict';
// NANO POS purchase & sales domain foundation. Pure planning only: NO database writes.
// All monetary totals are integers of the smallest currency unit (centimes).
// Item quantities are integers in thousandths. No business records are mutated.

const LIMIT = BigInt(Number.MAX_SAFE_INTEGER);
function fail(code){const error=new Error(code);error.code=code;throw error;}
function decimal(input,digits,zero=true){
  if(typeof input!=='string'&&typeof input!=='number')fail('invalid_decimal');
  const raw=String(input).trim();
  const regex=new RegExp('^\\d+(?:\\.\\d{1,'+digits+'})?$');
  if(!regex.test(raw))fail('invalid_decimal');
  const [whole,fraction='']=raw.split('.');
  const result=BigInt(whole)*10n**BigInt(digits)+BigInt(fraction.padEnd(digits,'0')||'0');
  if(result>LIMIT||(!zero&&result===0n))fail('number_out_of_range');
  return result;
}
function money(v){return decimal(v,2);}
function qty(v){return decimal(v,3,false);}
function asSafe(value){if(value<0n||value>LIMIT)fail('number_out_of_range');return Number(value);}
function addValues(arr){return arr.reduce((sum,value)=>sum+value,0n);}
function halfUp(numerator,denominator){if(denominator<=0n)fail('invalid_denominator');return (numerator+denominator/2n)/denominator;}
function ceilDiv(n,d){if(d<=0n)fail('invalid_denominator');return (n+d-1n)/d;}
function uniqueCode(value){const id=String(value??'').trim();if(!id||id.length>128)fail('invalid_line_id');return id;}
function purchaseTotal(lines,{freight='0',otherFees='0',nonrecoverableTax='0'}={}){
  if(!Array.isArray(lines)||!lines.length||lines.length>10000)fail('invalid_purchase_lines');
  const ids=new Set();
  const items=lines.map(line=>{
    if(!line||typeof line!=='object')fail('invalid_purchase_line');
    const lineId=uniqueCode(line.lineId??line.productId);
    if(ids.has(lineId))fail('duplicate_line_id');ids.add(lineId);
    const quantity=qty(line.quantity),unitCost=money(line.unitCost);
    const base=halfUp(quantity*unitCost,1000n);
    return {lineId,quantity,unitCost,base};
  });
  const extra=money(freight)+money(otherFees)+money(nonrecoverableTax);
  asSafe(extra);
  const subtotal=addValues(items.map(i=>i.base));asSafe(subtotal);
  const basis=subtotal>0n?items.map(i=>i.base):items.map(i=>i.quantity);
  const divisor=addValues(basis);if(divisor===0n)fail('zero_allocation_basis');
  const allocation=items.map((it,index)=>{
    const numerator=extra*basis[index];
    return {index,allocated:numerator/divisor,remainder:numerator%divisor};
  });
  let residual=extra-addValues(allocation.map(i=>i.allocated));
  const ranked=allocation.slice().sort((a,b)=>a.remainder===b.remainder?a.index-b.index:(a.remainder>b.remainder?-1:1));
  let next=0;
  while(residual>0n){ranked[next++].allocated+=1n;residual-=1n;}
  const rows=items.map((it,index)=>{
    const landed=it.base+allocation[index].allocated;
    return {lineId:it.lineId,quantityMilli:asSafe(it.quantity),unitCostCents:asSafe(it.unitCost),
      baseCents:asSafe(it.base),allocatedChargesCents:asSafe(allocation[index].allocated),
      landedCents:asSafe(landed),approxUnitLandedCents:asSafe(halfUp(landed*1000n,it.quantity))};
  });
  const total=subtotal+extra;asSafe(total);
  if(addValues(rows.map(x=>BigInt(x.landedCents)))!==total)fail('allocation_not_balanced');
  return {subtotalCents:asSafe(subtotal),extraCents:asSafe(extra),totalCents:asSafe(total),lines:rows};
}
function targetSellPrice(unitLandedCost,marginPercent){
  const cost=money(unitLandedCost),basis=decimal(marginPercent,2);
  if(basis>=10000n)fail('invalid_margin');
  return {sellingPriceCents:asSafe(ceilDiv(cost*10000n,10000n-basis)),marginBasisPoints:asSafe(basis)};
}
function receiptPlan(orderLines,previousReceipts,receipt){
  if(!Array.isArray(orderLines)||!Array.isArray(previousReceipts)||!receipt||!Array.isArray(receipt.lines))fail('invalid_receipt');
  const ordered=new Map();
  for(const line of orderLines){const id=uniqueCode(line.lineId);if(ordered.has(id))fail('duplicate_line_id');ordered.set(id,qty(line.quantity));}
  const used=new Map();
  const oldIds=new Map();
  for(const r of previousReceipts){
    const id=uniqueCode(r.receiptId);if(oldIds.has(id))fail('duplicate_receipt_id');oldIds.set(id,r);
    if(!Array.isArray(r.lines))fail('invalid_previous_receipt');
    for(const l of r.lines){const k=uniqueCode(l.lineId);if(!ordered.has(k))fail('unknown_order_line');used.set(k,(used.get(k)||0n)+qty(l.quantity));}
  }
  const receiptId=String(receipt.receiptId??'').trim();
  if(!/^[A-Za-z0-9_.:-]{12,128}$/.test(receiptId))fail('invalid_receipt_id');
  const signed=JSON.stringify(receipt.lines.map(l=>[uniqueCode(l.lineId),String(qty(l.quantity))]));
  if(oldIds.has(receiptId)){
    const previous=oldIds.get(receiptId);
    const priorSigned=JSON.stringify(previous.lines.map(l=>[uniqueCode(l.lineId),String(qty(l.quantity))]));
    if(signed!==priorSigned)fail('receipt_id_conflict');
    return {duplicate:true,movements:[],complete:false};
  }
  if(!receipt.lines.length)fail('empty_receipt');
  const repeated=new Set(),movements=[];
  for(const line of receipt.lines){
    const k=uniqueCode(line.lineId);if(repeated.has(k))fail('duplicate_line_id');repeated.add(k);
    if(!ordered.has(k))fail('unknown_order_line');
    const amount=qty(line.quantity),old=used.get(k)||0n;
    if(old+amount>ordered.get(k))fail('over_receipt');
    used.set(k,old+amount);movements.push({lineId:k,qtyMilli:asSafe(amount)});
  }
  for(const [k,value] of used){if(value>ordered.get(k))fail('previous_receipt_overflow');}
  return {duplicate:false,movements,complete:[...ordered].every(([k,v])=>(used.get(k)||0n)===v)};
}
function splitPayment(total,paid){
  const due=money(total);
  if(!Array.isArray(paid)||paid.length>50)fail('invalid_payments');
  let credit=0n;
  const amounts=paid.map(p=>{
    const method=String(p?.method??'').trim();
    if(!['cash','card','transfer'].includes(method))fail('invalid_payment_method');
    const amount=money(p.amount);credit+=amount;return {method,amountCents:asSafe(amount)};
  });
  if(credit>due)fail('overpayment_requires_change_handling');
  return {paidCents:asSafe(credit),dueCents:asSafe(due),debtCents:asSafe(due-credit),payments:amounts};
}
function returnPlan(originalLines,previousReturns,requested){
  if(!Array.isArray(originalLines)||!Array.isArray(previousReturns)||!Array.isArray(requested)||!requested.length)fail('invalid_return');
  const originals=new Map(),returned=new Map();
  for(const l of originalLines){const id=uniqueCode(l.lineId);if(originals.has(id))fail('duplicate_line_id');originals.set(id,qty(l.quantity));}
  for(const l of previousReturns){const id=uniqueCode(l.lineId);if(!originals.has(id))fail('unknown_return_line');returned.set(id,(returned.get(id)||0n)+qty(l.quantity));}
  const used=new Set(),movements=[];
  for(const l of requested){
    const id=uniqueCode(l.lineId);if(used.has(id))fail('duplicate_line_id');used.add(id);
    if(!originals.has(id))fail('unknown_return_line');
    const amount=qty(l.quantity);
    if((returned.get(id)||0n)+amount>originals.get(id))fail('return_exceeds_sale');
    movements.push({lineId:id,qtyMilli:asSafe(amount)});
  }
  return {movements};
}
function rankSupplierQuotes(quotes,quantity){
  if(!Array.isArray(quotes)||!quotes.length||quotes.length>1000)fail('invalid_supplier_quotes');
  const ordered=qty(quantity),vendors=new Set();
  return quotes.map(q=>{
    const id=uniqueCode(q.supplierId);if(vendors.has(id))fail('duplicate_supplier_quote');vendors.add(id);
    const unit=money(q.unitCost),freight=money(q.freight||'0');
    const minQty=q.minQuantity==null?0n:qty(q.minQuantity);
    const days=Number(q.leadDays);
    if(!Number.isSafeInteger(days)||days<0||days>3650)fail('invalid_lead_days');
    const eligible=ordered>=minQty;
    return {supplierId:id,eligible,landedTotalCents:asSafe(halfUp(unit*ordered,1000n)+freight),leadDays:days};
  }).sort((a,b)=>Number(b.eligible)-Number(a.eligible)||a.landedTotalCents-b.landedTotalCents||a.leadDays-b.leadDays||a.supplierId.localeCompare(b.supplierId));
}
module.exports={purchaseTotal,targetSellPrice,receiptPlan,splitPayment,returnPlan,rankSupplierQuotes};
