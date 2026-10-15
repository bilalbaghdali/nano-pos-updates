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
function post(db,request,actorId,clock=new Date()){
  const p=plan(db,request);
  if(p.repeat)return {next:db,result:{success:true,alreadyProcessed:true,credit_note_id:p.existing.id,refund_amount:p.existing.refund_amount}};
  const actor=(db.users||[]).find(u=>String(u.id)===String(actorId));
  if(!actor||actor.is_active===false||actor.is_active===0||String(actor.is_active)==='0'
     ||!['Admin','Manager'].includes(String(actor.role)))throw Error('لا يملك المستخدم صلاحية اعتماد المرتجع');
  const next=structuredClone(db);
  const sale=next.sales.find(v=>String(v.id)===String(p.saleId));
  let session=null;
  if(p.refund>0){
    if(!['cash','credit'].includes(String(sale.payment_method||'cash').toLowerCase()))throw Error('طريقة الدفع الأصلية تحتاج معالجة استرداد خاصة');
    session=(next.caisse_sessions||[]).find(s=>s.status==='open'&&!s.closed_at&&String(s.user_id)===String(actor.id));
    if(!session)throw Error('افتح مناوبة المستخدم قبل رد أي مبلغ نقدي');
  }
  const before={total:cash(sale.total),paid_amount:cash(sale.paid_amount||0),remaining_amount:cash(Math.max(0,sale.total-sale.paid_amount))};
  sale.original_total=p.originalTotal;
  sale.returned_by_index={...(sale.returned_by_index||{})};
  for(const line of p.lines){
    const item=sale.items[line.line_index];
    const product=(next.products||[]).find(v=>String(v.id)===String(line.product_id));
    const batch=product?.batches?.find(v=>String(v.id)===String(line.batch_id));
    if(!batch)throw Error('تعذر إعادة نفس الدفعة إلى المخزون');
    batch.stock=Math.round((Number(batch.stock||0)+line.quantity)*1000)/1000;
    sale.returned_by_index[line.line_index]=Math.round((Number(sale.returned_by_index[line.line_index]||0)+line.quantity)*1000)/1000;
    if(Array.isArray(product.batches)){
      product.total_stock=product.batches.reduce((n,b)=>n+Number(b.stock||0),0);
      product.stock=product.quantity=product.total_stock;
    }
  }
  sale.total=p.nextTotal;
  sale.paid_amount=p.nextPaid;
  sale.remaining_amount=cash(Math.max(0,p.nextTotal-p.nextPaid));
  sale.payment_status=sale.remaining_amount>0?(p.nextPaid>0?'partial':'credit'):'paid';
  sale.returns_count=Number(sale.returns_count||0)+1;
  if(sale.customer_id!=null&&p.debtReduction>0){
    const customer=(next.customers||[]).find(c=>String(c.id)===String(sale.customer_id));
    if(!customer)throw Error('سجل الزبون غير موجود');
    customer.balance=cash(Math.max(0,Number(customer.balance||0)-p.debtReduction));
  }
  const timestamp=clock.toISOString();
  const record={id:p.requestId,request_id:p.requestId,sale_id:sale.id,created_at:timestamp,
    actor_id:actor.id,actor_name:String(actor.name||actor.username||''),customer_id:sale.customer_id,
    credit_amount:p.credit,debt_reduction:p.debtReduction,refund_amount:p.refund,
    refund_session_id:session?.id??null,note:String(request.note||'').slice(0,500),
    lines:p.lines.map(x=>({line_index:x.line_index,product_id:x.product_id,batch_id:x.batch_id,quantity:x.quantity}))};
  next.sales_returns=Array.isArray(next.sales_returns)?next.sales_returns:[];
  next.sales_returns.push(record);
  if(session){
    next.caisse_transactions=Array.isArray(next.caisse_transactions)?next.caisse_transactions:[];
    next.caisse_transactions.unshift({id:p.requestId+'-refund',session_id:session.id,user_id:actor.id,
      user_name:record.actor_name,type:'refund',amount:p.refund,category:'sale-return',
      description:'مرتجع فاتورة '+String(sale.id),created_at:timestamp,sale_return_id:p.requestId});
  }
  next.audit_log=Array.isArray(next.audit_log)?next.audit_log:[];
  next.audit_log.push({id:p.requestId+'-audit',at:timestamp,operation:'sale-return',record_id:p.requestId,
    user_id:actor.id,before,after:{total:sale.total,paid_amount:sale.paid_amount,remaining_amount:sale.remaining_amount,
    refund:p.refund,debt_reduction:p.debtReduction}});
  return {next,result:{success:true,credit_note_id:p.requestId,refund_amount:p.refund,
    debt_reduction:p.debtReduction,remaining_amount:sale.remaining_amount,return_record:record}};
}
const API={cash,count,plan,post};
if(typeof module!=='undefined'&&module.exports)module.exports=API;
root.NANO_RETURN_PLAN_166=API;
})(typeof window!=='undefined'?window:globalThis);