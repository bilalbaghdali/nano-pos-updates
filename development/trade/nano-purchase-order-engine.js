/* NANO POS Purchase Orders 1.1.0 — safe, pure order/partial-receipt plans.
   The caller MUST persist the entire returned snapshot as ONE state write;
   this module does not access browser storage, change stock, or touch activation. */
(function(root){
 'use strict';
 function fail(code){let e=new Error(code);e.code=code;throw e;}
 const integer=(n,min,max)=>{if(!Number.isSafeInteger(n)||n<min||n>max)fail('invalid_integer');return n;};
 function cents(v,zero=true){
  const s=String(v??'').trim();
  if(!/^\d+(?:\.\d{1,2})?$/.test(s))fail('invalid_amount');
  const a=s.split('.');const c=Number(a[0])*100+Number((a[1]||'').padEnd(2,'0'));
  if(!Number.isSafeInteger(c)||c<0||(!zero&&c===0))fail('invalid_amount');
  return c;
 }
 function milli(v){
  const s=String(v??'').trim();
  if(!/^\d+(?:\.\d{1,3})?$/.test(s))fail('invalid_quantity');
  const a=s.split('.');const n=Number(a[0])*1000+Number((a[1]||'').padEnd(3,'0'));
  return integer(n,1,100000000000);
 }
 const q=m=>Number((m/1000).toFixed(3));
 const cash=c=>Number((c/100).toFixed(2));
 const opid=v=>{const s=String(v||'');if(!/^[A-Za-z0-9_.:-]{12,128}$/.test(s))fail('invalid_operation_id');return s;};
 const identifier=v=>{const s=String(v??'').trim();if(!s||s.length>128)fail('invalid_identifier');return s;};
 const copy=v=>JSON.parse(JSON.stringify(v));
 const shaInput=v=>JSON.stringify(v);
 function catalog(db,supplierId){
  const supplier=(db.suppliers||[]).find(x=>String(x.id)===String(supplierId));
  if(!supplier)fail('supplier_not_found');return supplier;
 }
 function planOrder(db,body){
  if(!db||typeof db!=='object'||!body||typeof body!=='object')fail('invalid_request');
  const operationId=opid(body.operationId);
  const supplier=catalog(db,body.supplierId);
  if(!Array.isArray(body.lines)||!body.lines.length||body.lines.length>300)fail('invalid_order_lines');
  const lines=[],set=new Set();
  for(let i=0;i<body.lines.length;i++){
   const line=body.lines[i],product=(db.products||[]).find(x=>String(x.id)===String(line?.productId));
   if(!product)fail('product_not_found');
   const productId=identifier(product.id),variantId=line?.variantId??null;
   const key=JSON.stringify([productId,variantId]);
   if(set.has(key))fail('duplicate_product_line');set.add(key);
   const quantityMilli=milli(line.quantity),unitCostCents=cents(line.unitCost);
   lines.push({lineId:'L'+(i+1),productId:product.id,variantId,
    productName:String(product.name||'').slice(0,250),quantityMilli,unitCostCents,receivedMilli:0});
  }
  const fingerprint=shaInput({supplierId:String(supplier.id),lines});
  const existing=(db.purchase_orders||[]).find(o=>o.operationId===operationId);
  if(existing){
   if(existing.fingerprint!==fingerprint)fail('operation_conflict');
   return {duplicate:true,result:{success:true,id:existing.id,duplicate:true},snapshot:null};
  }
  const snapshot=copy(db),now=new Date().toISOString(),id='PO-'+operationId;
  const order={id,operationId,fingerprint,supplierId:supplier.id,supplierName:String(supplier.name||''),
   createdAt:now,updatedAt:now,revision:1,status:'pending',lines,receipts:[]};
  snapshot.purchase_orders=Array.isArray(snapshot.purchase_orders)?snapshot.purchase_orders:[];
  snapshot.purchase_orders.unshift(order);
  snapshot.revision=Number(snapshot.revision||0)+1;
  return {duplicate:false,result:{success:true,id,order:copy(order)},snapshot};
 }
 function planReceipt(db,body){
  if(!body||typeof body!=='object')fail('invalid_request');
  const operationId=opid(body.receiptId||body.operationId),orderId=identifier(body.orderId);
  const order=(db.purchase_orders||[]).find(o=>String(o.id)===orderId);
  if(!order)fail('order_not_found');
  if(!['pending','partial','received'].includes(order.status))fail('invalid_order_status');
  if(body.expectedRevision!=null&&Number(body.expectedRevision)!==Number(order.revision))fail('stale_order_revision');
  if(!Array.isArray(body.lines)||!body.lines.length||body.lines.length>300)fail('invalid_receipt_lines');
  const lines=[],seen=new Set();
  for(const line of body.lines){
   const key=identifier(line?.lineId);
   if(seen.has(key))fail('duplicate_receipt_line');seen.add(key);
   const source=order.lines.find(x=>x.lineId===key);if(!source)fail('unknown_order_line');
   const amountMilli=milli(line.quantity);
   if(source.receivedMilli+amountMilli>source.quantityMilli)fail('over_receipt');
   lines.push({lineId:key,quantityMilli:amountMilli});
  }
  const fingerprint=shaInput(lines);
  const recorded=(order.receipts||[]).find(x=>x.receiptId===operationId);
  if(recorded){
   if(recorded.fingerprint!==fingerprint)fail('receipt_conflict');
   return {duplicate:true,result:{success:true,duplicate:true,receiptId:operationId,purchaseId:recorded.purchaseId},snapshot:null};
  }
  const snapshot=copy(db),target=snapshot.purchase_orders.find(x=>String(x.id)===orderId);
  const supplier=catalog(snapshot,order.supplierId),items=[];
  let subtotalCents=0;
  for(const item of lines){
   const source=target.lines.find(x=>x.lineId===item.lineId);
   const product=snapshot.products.find(x=>String(x.id)===String(source.productId));
   if(!product)fail('product_not_found');
   const amountCents=Math.round(item.quantityMilli*source.unitCostCents/1000);
   if(!Number.isSafeInteger(amountCents)||amountCents<0)fail('invalid_amount');
   subtotalCents+=amountCents;
   if(!Number.isSafeInteger(subtotalCents)||subtotalCents>1e12)fail('amount_overflow');
   items.push({product_id:source.productId,product_name:source.productName,
     quantity:q(item.quantityMilli),cost_price:cash(source.unitCostCents),
     selling_price:Number(product.pos_price||product.selling_price||0),
     variant_id:source.variantId,batch_id:null,total_cost:cash(amountCents)});
   source.receivedMilli+=item.quantityMilli;
  }
  const purchaseId='POINV-'+operationId,now=new Date().toISOString();
  const purchase={id:purchaseId,invoice_number:purchaseId,
   purchase_order_id:orderId,purchase_receipt_id:operationId,
   supplier_id:supplier.id,supplier_name:String(supplier.name||''),
   invoice_date:now.slice(0,10),created_at:now,updated_at:now,
   subtotal:cash(subtotalCents),tax_percentage:0,additional_costs:0,
   total:cash(subtotalCents),paid_amount:0,due_date:null,
   items,items_count:items.length,payments:[]};
  if((snapshot.purchases||[]).some(p=>String(p.id)===purchaseId))fail('duplicate_purchase_id');
  target.receipts.push({receiptId:operationId,fingerprint,purchaseId,at:now,items:lines});
  target.updatedAt=now;target.revision++;
  target.status=target.lines.every(x=>x.receivedMilli===x.quantityMilli)?'received':'partial';
  snapshot.purchases=Array.isArray(snapshot.purchases)?snapshot.purchases:[];
  snapshot.purchases.unshift(purchase);
  snapshot.revision=Number(snapshot.revision||0)+1;
  return {duplicate:false,snapshot,purchase,result:{success:true,receiptId:operationId,purchaseId,status:target.status,order:copy(target)}};
 }
 const api=Object.freeze({planOrder,planReceipt,milli,cents});
 root.NANO_PURCHASE_ORDER_ENGINE_110=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
