/* NANO POS v1.0.67 — authoritative stocktake draft and approval planner.
 * The phone sends count proposals without inventory writes. */
(function(root){'use strict';
const round=n=>Math.round(Number(n)*1000)/1000;
function actor(db,id,approve){
 const u=(db.users||[]).find(x=>String(x.id)===String(id));
 if(!u||u.is_active===false||u.is_active===0||String(u.is_active)==='0')throw Error('حساب المستخدم غير مفعل');
 const perms=(u.permissions||[]).map(x=>String(x).toLowerCase());
 if(approve?(!['Admin','Manager'].includes(u.role)):(!['Admin','Manager'].includes(u.role)&&!perms.includes('inventory')&&!perms.includes('all')))
   throw Error('ليس لديك صلاحية الجرد');
 return u;
}
function checks(db,rows,guard){
 if(!guard||typeof guard.stocktake!=='function')throw Error('تحقق المخزون غير متاح');
 if(!Array.isArray(rows)||rows.length>10000)throw Error('قائمة الجرد غير صالحة');
 return guard.stocktake(db.products,rows);
}
function submit(db,request,userId,guard,now=new Date()){
 if(!request||typeof request!=='object')throw Error('طلب الجرد غير صالح');
 const submitter=actor(db,userId,false);
 const id=String(request.requestId||'');
 if(!/^[a-zA-Z0-9_.:\-]{12,100}$/.test(id))throw Error('معرف الجرد غير صالح');
 const existed=(db.stocktake_drafts||[]).find(x=>x.id===id);
 if(existed)return {next:db,result:{success:true,alreadyProcessed:true,draft:existed}};
 const rows=request.rows;
 const verified=checks(db,rows,guard);
 if(!verified.length)throw Error('لا توجد دفعات للجرد');
 const next=structuredClone(db);
 const draft={id,status:'pending',submitted_at:now.toISOString(),submitted_by:submitter.id,
   submitted_by_name:String(submitter.name||submitter.username||''),source_device:String(request.deviceId||'').slice(0,100),
   scope_type:String(request.scope_type||'all'),note:String(request.note||'').slice(0,500),
   base_revision:Number(db.revision||0),
   rows:verified.map(r=>({product_id:r.productId,batch_id:r.batchId,book_qty:r.current,counted_qty:r.counted}))};
 next.stocktake_drafts=Array.isArray(next.stocktake_drafts)?next.stocktake_drafts:[];
 next.stocktake_drafts.push(draft);
 return {next,result:{success:true,id,draft}};
}
function approve(db,request,userId,guard,now=new Date()){
 const reviewer=actor(db,userId,true),id=String(request?.draftId||'');
 const draft=(db.stocktake_drafts||[]).find(x=>String(x.id)===id);
 if(!draft)throw Error('طلب الجرد غير موجود');
 if(draft.status==='approved')return {next:db,result:{success:true,alreadyApproved:true,id:draft.id,stocktake_id:draft.stocktake_id}};
 if(draft.status!=='pending')throw Error('طلب الجرد غير قابل للاعتماد');
 const verified=checks(db,draft.rows,guard);
 const next=structuredClone(db),d=next.stocktake_drafts.find(x=>x.id===id);
 const byProduct=new Map((next.products||[]).map(p=>[String(p.id),p]));
 let plus=0,minus=0;
 for(const row of verified){
   const p=byProduct.get(String(row.productId));
   const batch=p?.batches?.find(b=>String(b.id)===String(row.batchId));
   if(!batch)throw Error('دفعة غير موجودة أثناء اعتماد الجرد');
   batch.stock=row.counted;
   plus+=Math.max(0,row.difference);
   minus+=Math.max(0,-row.difference);
 }
 for(const p of next.products||[]){
   if(!p.batches)continue;
   p.total_stock=p.batches.reduce((n,b)=>n+Number(b.stock||0),0);
   p.stock=p.quantity=p.total_stock;
 }
 const posted={id:'stocktake-'+id,draft_id:id,status:'posted',
   created_at:d.submitted_at,posted_at:now.toISOString(),
   approved_by:reviewer.id,approved_by_name:String(reviewer.name||reviewer.username||''),
   submitted_by:d.submitted_by,scope_type:d.scope_type,note:d.note,
   rows:verified.map(r=>({product_id:r.productId,batch_id:r.batchId,book_qty:r.current,
      counted_qty:r.counted,difference:r.difference})),
   summary:{rows_count:verified.length,changed_rows:verified.filter(r=>r.difference!==0).length,
      increases:round(plus),decreases:round(minus),net_difference:round(plus-minus)}};
 next.stocktakes=Array.isArray(next.stocktakes)?next.stocktakes:[];
 if(next.stocktakes.some(s=>s.draft_id===id))throw Error('تم تطبيق مسودة الجرد مسبقًا');
 next.stocktakes.unshift(posted);
 d.status='approved';d.approved_at=now.toISOString();d.approved_by=reviewer.id;d.stocktake_id=posted.id;
 next.audit_log=Array.isArray(next.audit_log)?next.audit_log:[];
 next.audit_log.push({id:'audit-'+id,operation:'approve-stocktake-draft',record_id:id,at:now.toISOString(),
   user_id:reviewer.id,before:{status:'pending'},after:{status:'approved',net_difference:posted.summary.net_difference}});
 return {next,result:{success:true,id,stocktake_id:posted.id,summary:posted.summary}};
}
function reject(db,request,userId,now=new Date()){
 const reviewer=actor(db,userId,true),id=String(request?.draftId||'');
 const d=(db.stocktake_drafts||[]).find(x=>x.id===id);
 if(!d)throw Error('طلب الجرد غير موجود');
 if(d.status==='rejected')return {next:db,result:{success:true,alreadyRejected:true}};
 if(d.status!=='pending')throw Error('لا يمكن رفض جرد معتمد');
 const next=structuredClone(db);
 const draft=next.stocktake_drafts.find(x=>x.id===id);
 draft.status='rejected';draft.reviewed_at=now.toISOString();draft.reviewed_by=reviewer.id;
 draft.review_note=String(request.reason||'').slice(0,300);
 next.audit_log=Array.isArray(next.audit_log)?next.audit_log:[];
 next.audit_log.push({id:'audit-reject-'+id,at:now.toISOString(),operation:'reject-stocktake-draft',
   record_id:id,user_id:reviewer.id,before:{status:'pending'},after:{status:'rejected'}});
 return {next,result:{success:true,id,rejected:true}};
}
const api={actor,submit,approve,reject};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.NANO_STOCKTAKE_APPROVAL_167=api;
})(typeof window!=='undefined'?window:globalThis);