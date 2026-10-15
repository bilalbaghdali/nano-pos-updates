/* NANO POS 1.0.66 - deterministic reversible sale return plan.
 * No mutations here. Caller must enforce authenticated write permissions and
 * persist the sale, stock and customer changes as one transaction. */
(function(root){'use strict';
const cash=n=>{if(n===null||n===undefined||n==='')throw Error('المبلغ مفقود');
  const v=Number(n);if(!Number.isFinite(v)||v<0||v>1e12)throw Error('مبلغ غير صالح');return Math.round((v+Number.EPSILON)*100)/100;};
const count=n=>{if(n===null||n===undefined||n==='')throw Error('الكمية مفقودة');
  const v=Number(n);if(!Number.isFinite(v)||v<0||v>1e8)throw Error('كمية غير صالحة');return Math.round(v*1000)/1000;};
function plan(db,request){
  if(!request||typeof request!=='object')throw Error('بيانات المرتجع غير صالحة');
  const id=String(request.requestId||'');
  if(!/^[a-zA-Z0-9_:.\-]{12,100}$/.test(id))throw Error('معرف المرتجع غير صالح');
  const existing=(db.sales_returns||[]).find(r=>r.request_id===id);
  if(existing)return {repeat:true,existing};
  const sale=(db.sales||[]).find(x=>String(x.id)===String(request.saleId));
  if(!sale)throw Error('فاتورة البيع الأصلية غير موجودة');
  const lines=sale.items||[];
  if(!Array.isArray(lines)||!lines.length||!Array.isArray(request.lines)||!request.lines.length||request.lines.length>100)throw Error('أسطر المرتجع غير صالحة');
  const original=cash(sale.original_total??sale.total);
  const current=cash(sale.total),paid=cash(sale.paid_amount??0);
  if(paid>current+.005)throw Error('المدفوع أكبر من إجمالي الفاتورة');
  const bases=lines.map(l=>cash(l.total??count(l.quantity??l.qty)*cash(l.selling_price??l.price??0)));
  const fullBase=cash(bases.reduce((s,x)=>s+x,0));
  if(fullBase<=0||original<=0)throw Error('فاتورة بدون قيمة قابلة للاسترجاع');
  const used=new Set(),returns=[];
  for(const q of request.lines){
    const index=Number(q.lineIndex);
    if(!Number.isInteger(index)||index<0||index>=lines.length||used.has(index))throw Error('رقم سطر مرتجع غير صالح أو مكرر');
    used.add(index);
    const item=lines[index],sold=count(item.quantity??item.qty),qty=count(q.quantity);
    const past=count((db.sales_returns||[]).filter(r=>String(r.sale_id)===String(sale.id)).reduce((s,r)=>s+(r.lines||[]).filter(l=>Number(l.line_index)===index).reduce((t,l)=>t+count(l.quantity),0),0));
    if(qty<=0||qty>sold-past+.0001)throw Error('الكمية المرتجعة تتجاوز الكمية المباعة المتبقية');
    const product=(db.products||[]).find(p=>String(p.id)===String(item.product_id??item.id));
    const batch=product?.batches?.find(b=>String(b.id)===String(item.batch_id));
    if(!batch)throw Error('دفعة البيع الأصلية غير متاحة؛ لا يمكن إعادة المخزون تلقائيًا');
    returns.push({line_index:index,quantity:qty,product_id:product.id,batch_id:batch.id,
      raw_credit:original*bases[index]*qty/(sold*fullBase)});
  }
  const credit=cash(Math.min(current,returns.reduce((s,r)=>s+r.raw_credit,0)));
  if(!(credit>0))throw Error('المرتجع دون قيمة');
  const debt=cash(current-paid),debtReduction=cash(Math.min(debt,credit));
  const refund=cash(credit-debtReduction);
  const nextTotal=cash(current-credit),nextPaid=cash(paid-refund);
  if(nextPaid>nextTotal+.005)throw Error('رصيد الفاتورة غير متوازن');
  return {repeat:false,requestId:id,saleId:sale.id,sale,lines:returns,credit,
    refund,debtReduction,nextTotal,nextPaid,originalTotal:original};
}
const API={cash,count,plan};
if(typeof module!=='undefined'&&module.exports)module.exports=API;
root.NANO_RETURN_PLAN_166=API;
})(typeof window!=='undefined'?window:globalThis);