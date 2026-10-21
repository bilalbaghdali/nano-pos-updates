/* NANO POS v1.0.101 — supplier comparison, exact-cents landed-cost preview.
   Pure, read-only: NEVER posts stock, purchases, supplier debt or selling prices. */
(function(root){
  'use strict';
  const fail=code=>{const e=new Error(code);e.code=code;throw e;};
  const whole=(n,max=9007199254740991n)=>{if(n<0n||n>max)fail('amount_out_of_range');return Number(n);};
  const decimal=(value,digits)=>{
    const s=String(value??'').trim();
    if(!new RegExp('^\\d+(?:\\.\\d{1,'+digits+'})?$').test(s))fail('invalid_decimal');
    const [a,b='']=s.split('.');
    return BigInt(a)*10n**BigInt(digits)+BigInt(b.padEnd(digits,'0')||'0');
  };
  const cash=v=>decimal(v,2),quantity=v=>decimal(v,3);
  const uid=v=>String(v??'').trim();
  const asMoney=c=>Number(c)/100;
  const halfUp=(n,d)=>(n+d/2n)/d;
  const upto=(n,d)=>(n+d-1n)/d;
  function quotes(productId,suppliers,purchases,now=Date.now()){
    if(!Array.isArray(suppliers)||!Array.isArray(purchases))fail('invalid_source');
    const active=new Map(suppliers.filter(x=>x&&x.id!=null).map(s=>[uid(s.id),s]));
    const latest=new Map(),pid=uid(productId);
    for(const purchase of purchases){
      const id=uid(purchase?.supplier_id??purchase?.supplierId);
      if(!active.has(id))continue;
      const date=Date.parse(String(purchase.invoice_date||purchase.created_at||purchase.date||''));
      for(const item of Array.isArray(purchase.items)?purchase.items:[]){
        if(uid(item.product_id??item.productId)!==pid)continue;
        let price;try{price=cash(item.cost_price??item.unit_cost??item.unit_price);}catch{continue;}
        if(price===0n)continue;
        const timestamp=Number.isFinite(date)&&date<=now?date:0;
        const prev=latest.get(id);
        if(!prev||timestamp>prev.timestamp)latest.set(id,{supplierId:id,
          supplierName:String(active.get(id)?.name||active.get(id)?.company_name||id),
          unitCost:asMoney(price),timestamp,ageDays:timestamp?Math.floor((now-timestamp)/86400000):null});
      }
    }
    return [...latest.values()].sort((a,b)=>a.unitCost-b.unitCost||b.timestamp-a.timestamp||a.supplierId.localeCompare(b.supplierId));
  }
  function estimate(entries,feeBySupplier={},marginPercent='20'){
    if(!Array.isArray(entries)||entries.length>500||!feeBySupplier||typeof feeBySupplier!=='object')fail('invalid_entries');
    const margin=decimal(marginPercent,2);
    if(margin>=10000n)fail('invalid_margin');
    const groups=new Map(),ids=new Set();
    for(const item of entries){
      if(!item||item.skip||item.checked===false)continue;
      const pid=uid(item.productId),supplier=uid(item.supplierId);
      if(!pid||!supplier)fail('supplier_not_selected');
      const key=supplier+'|'+pid;if(ids.has(key))fail('duplicate_item');ids.add(key);
      const q=quantity(item.quantity),cost=cash(item.unitCost);
      if(q<=0n||cost<=0n)fail('invalid_item');
      const subtotal=halfUp(q*cost,1000n);
      if(!groups.has(supplier))groups.set(supplier,[]);
      groups.get(supplier).push({productId:pid,name:String(item.name||pid),
        quantityMilli:whole(q),unitCostCents:whole(cost),subtotalCents:whole(subtotal)});
    }
    const result=[];
    for(const [supplierId,items] of groups){
      const fee=feeBySupplier[supplierId]||{};
      const freight=cash(fee.freight??'0'),other=cash(fee.other??'0'),nonrecoverableTax=cash(fee.nonrecoverableTax??'0');
      const charges=freight+other+nonrecoverableTax;
      const subtotal=items.reduce((a,b)=>a+BigInt(b.subtotalCents),0n);
      const basis=subtotal>0n?subtotal:items.reduce((a,b)=>a+BigInt(b.quantityMilli),0n);
      if(basis<=0n)fail('invalid_allocation');
      const allocations=items.map((item,i)=>{
        const weighted=BigInt(item.subtotalCents)||BigInt(item.quantityMilli);
        return {i,amount:charges*weighted/basis,remainder:charges*weighted%basis};
      });
      let leftover=charges-allocations.reduce((sum,a)=>sum+a.amount,0n);
      const ranked=allocations.slice().sort((a,b)=>a.remainder===b.remainder?a.i-b.i:(a.remainder>b.remainder?-1:1));
      for(let i=0;leftover>0n;i++,leftover--)ranked[i].amount++;
      const detail=items.map((i,index)=>{
        const lineTotal=BigInt(i.subtotalCents)+allocations[index].amount;
        const unit=halfUp(lineTotal*1000n,BigInt(i.quantityMilli));
        const minimumSelling=upto(unit*10000n,10000n-margin);
        return {...i,addedCostsCents:whole(allocations[index].amount),landedCents:whole(lineTotal),
          landedUnitCents:whole(unit),targetSellingCents:whole(minimumSelling),
          estimatedMarginBasisPoints:whole(margin)};
      });
      const total=subtotal+charges;
      if(detail.reduce((s,i)=>s+BigInt(i.landedCents),0n)!==total)fail('unbalanced_cost');
      result.push({supplierId,subtotalCents:whole(subtotal),chargesCents:whole(charges),
        totalCents:whole(total),lines:detail});
    }
    return {currencyMinorUnits:2,groups:result,totals:{
      subtotalCents:result.reduce((sum,r)=>sum+r.subtotalCents,0),
      chargesCents:result.reduce((sum,r)=>sum+r.chargesCents,0),
      totalCents:result.reduce((sum,r)=>sum+r.totalCents,0)}};
  }
  const api=Object.freeze({quotes,estimate});
  root.NANO_TRADE_ANALYTICS_101=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
