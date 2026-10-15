/* NANO POS v1.0.65 — deterministic financial guards */
(function(root){'use strict';
const amount=x=>{const n=Number(x);if(x==null||x===''||!Number.isFinite(n)||n<0||n>1e12)throw Error('المبلغ غير صالح');return Math.round((n+Number.EPSILON)*100)/100;};
const quantity=x=>{const n=Number(x);if(x==null||x===''||!Number.isFinite(n)||n<0||n>1e9)throw Error('الكمية غير صالحة');return Math.round(n*1000)/1000;};
const close=(session,closing)=>{if(!session||session.status!=='open'||session.closed_at)throw Error('المناوبة مغلقة أو غير موجودة');return amount(closing);};
const stocktake=(products,rows)=>{
 if(!Array.isArray(rows)||!rows.length||rows.length>20000)throw Error('الجرد فارغ أو غير صالح');
 const seen=new Set(),result=[];
 for(const row of rows){
  const p=(products||[]).find(x=>String(x.id)===String(row.product_id));
  const b=p?.batches?.find(x=>String(x.id)===String(row.batch_id));
  if(!b)throw Error('دفعة المخزون غير موجودة');
  const key=String(p.id)+'/'+String(b.id);
  if(seen.has(key))throw Error('دفعة مكررة');seen.add(key);
  const current=quantity(b.stock??0),expected=quantity(row.book_qty),counted=quantity(row.counted_qty);
  if(Math.abs(current-expected)>0.0001)throw Error('المخزون تغير بعد بدء الجرد');
  result.push({productId:p.id,batchId:b.id,current,counted,difference:Math.round((counted-current)*1000)/1000});
 }
 return result;
};
const price=(p,tier='retail')=>{
 if(!p)throw Error('المنتج غير موجود');
 const r=amount(p.pos_price??p.selling_price??p.price??0);
 const w=p.wholesale_price==null?null:amount(p.wholesale_price);
 return tier==='wholesale'&&w>0?w:r;
};
const api={amount,quantity,close,stocktake,price};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.NANO_TX_GUARD_165=api;
})(typeof window!=='undefined'?window:globalThis);