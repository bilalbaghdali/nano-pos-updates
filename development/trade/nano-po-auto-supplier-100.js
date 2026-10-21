/* NANO POS 1.0.100: deterministic, read-only supplier selection for existing low-stock list.
   No stock, debt, purchase or activation writes occur here. */
(function(root){
 'use strict';
 const num=value=>{
   if(value===null||value===undefined||String(value).trim()==='')return null;
   const n=Number(value);return Number.isFinite(n)&&n>=0?n:null;
 };
 const code=value=>String(value===null||value===undefined?'':value).trim();
 const money=value=>{const n=num(value);return n===null?null:Math.round((n+Number.EPSILON)*100)/100;};
 const quantity=value=>{const n=num(value);return n===null?null:Math.ceil(Number(n.toFixed(8))*1000)/1000;};
 const date=value=>{const d=Date.parse(String(value||''));return Number.isFinite(d)?d:0;};
 const itemProduct=i=>code(i?.product_id??i?.productId??i?.product?.id);
 const supplierId=p=>code(p?.supplier_id??p?.supplierId);
 function build(rows,suppliers,purchases,orders,opts){
   const options=opts||{},now=Number.isFinite(options.now)?options.now:Date.now();
   if(!Array.isArray(rows)||!Array.isArray(suppliers)||!Array.isArray(purchases)||!Array.isArray(orders))
     throw Error('invalid_shortage_source');
   const live=new Map(suppliers.filter(s=>s&&s.id!=null).map(s=>[code(s.id),s]));
   const outstanding=new Map();
   for(const order of orders){
     if(!order||!['pending','partial'].includes(String(order.status)))continue;
     for(const item of Array.isArray(order.lines)?order.lines:[]){
       const id=code(item.productId??item.product_id);if(!id)continue;
       const requested=num(item.quantityMilli),received=num(item.receivedMilli);
       if(requested===null||received===null)continue;
       const balance=Math.max(0,(requested-received)/1000);
       outstanding.set(id,(outstanding.get(id)||0)+balance);
     }
   }
   const history=new Map();
   for(const purchase of purchases){
     const sid=supplierId(purchase);
     if(!live.has(sid)||!Array.isArray(purchase?.items))continue;
     const created=date(purchase.invoice_date||purchase.purchase_date||purchase.created_at||purchase.date);
     for(const item of purchase.items){
       const pid=itemProduct(item),price=money(item.cost_price??item.unit_cost??item.unit_price);
       if(!pid||price===null||price<=0)continue;
       const key=pid+'|'+sid,prev=history.get(key);
       if(!prev||created>prev.at)history.set(key,{sid,pid,price,at:created});
     }
   }
   const result=[],ids=new Set();
   for(const row of rows){
     if(!row||typeof row!=='object')continue;
     const pid=code(row.id??row.productId);
     if(!pid||ids.has(pid))continue;ids.add(pid);
     const suggested=quantity(row.order),pending=outstanding.get(pid)||0;
     if(suggested===null||suggested<=0)continue;
     const needed=quantity(Math.max(0,suggested-pending));
     if(needed===null||needed<=0){
       result.push({productId:pid,name:String(row.name||pid),barcode:String(row.barcode||''),stock:row.qty,
         suggested,pending:quantity(pending),quantity:0,skip:true,reason:'covered_by_existing_orders'});
       continue;
     }
     const choices=[...history.values()].filter(h=>h.pid===pid);
     const active=choices.filter(h=>h.at>0&&h.at<=now&&now-h.at<=365*86400000);
     const ordered=(active.length?active:choices).sort((a,b)=>
       a.price-b.price||b.at-a.at||a.sid.localeCompare(b.sid));
     const preferred=code(row.supplierId??row.supplier_id);
     const selected=live.has(preferred)?preferred:(ordered[0]?.sid||'');
     const chosen=choices.find(v=>v.sid===selected);
     const price=chosen?.price??money(row.costPrice??row.cost_price);
     result.push({productId:pid,name:String(row.name||pid),barcode:String(row.barcode||''),
       stock:row.qty,suggested,pending:quantity(pending),quantity:needed,skip:false,
       supplierId:selected,supplierName:String(live.get(selected)?.name||live.get(selected)?.company_name||''),
       unitCost:price===null?null:price,
       reason:live.has(preferred)?'configured_supplier':active.length?'recent_lowest_purchase_price':
         choices.length?'last_known_supplier':'needs_supplier',
       requiresReview:!selected||price===null||price<=0});
   }
   return {items:result,ready:result.filter(x=>!x.skip&&x.supplierId&&x.unitCost>0).length,
     needsReview:result.filter(x=>!x.skip&&(!x.supplierId||!(x.unitCost>0))).length,
     skipped:result.filter(x=>x.skip).length};
 }
 const api=Object.freeze({build});
 root.NANO_PO_AUTO_SUPPLIER_100=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
