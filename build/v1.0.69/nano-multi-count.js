/* NANO POS v1.0.69 — primary-authoritative collaborative count sessions.
 * Deterministic state transitions: no writes until validated result is committed by caller.
 * Phones must be identified by the paired-device server, never by client-supplied IDs. */
(function(root){'use strict';
const copy=x=>structuredClone(x);
const num=x=>{if(x==null||x==='')throw Error('الكمية مطلوبة');const n=Number(x);if(!Number.isFinite(n)||n<0||n>1e9)throw Error('الكمية المدخلة غير صالحة');return Math.round(n*1000)/1000;};
const nowISO=ms=>new Date(ms).toISOString();
const leaseMs=5*60*1000;
const idRx=/^[a-zA-Z0-9_.:-]{12,110}$/;
const validName=s=>{const n=String(s||'').trim().slice(0,65);if(n.length<2)throw Error('أدخل اسم الشخص الذي يقوم بالجرد');return n;};
const sessions=db=>Array.isArray(db.nano_multi_count_sessions)?db.nano_multi_count_sessions:[];
const active=db=>sessions(db).find(s=>s.status==='open')||null;
const admin=(db,userId)=>{
 const u=(db.users||[]).find(x=>String(x.id)===String(userId));
 if(!u||u.is_active===false||u.is_active===0||String(u.is_active)==='0'||!['Admin','Manager'].includes(String(u.role)))throw Error('لا يمكن بدء أو إنهاء الجرد إلا من حساب مدير على الكمبيوتر الرئيسي');
 return u;
};
const ensure=(db,sessionId)=>{
 const s=active(db);
 if(!s||String(s.id)!==String(sessionId))throw Error('جلسة الجرد غير مفتوحة؛ اطلب بدء جرد جديد');
 return s;
};
const identity=(trusted,payload)=>{
 if(!trusted||trusted.origin!=='mobile'||!idRx.test(String(trusted.deviceId||'')))throw Error('هوية الهاتف المرتبط لم يتم التحقق منها');
 return {deviceId:String(trusted.deviceId),deviceName:String(trusted.deviceName||'هاتف').slice(0,65),operator:validName(payload.operatorName)};
};
const lookup=(db,payload)=>{
 const code=String(payload.barcode||'').trim(),productId=payload.productId;
 const hits=(db.products||[]).filter(p=> productId!=null ? String(p.id)===String(productId)
     : code && (String(p.barcode||'')===code|| (p.batches||[]).some(b=>String(b.barcode||'')===code)));
 if(hits.length!==1)throw Error(hits.length?'الباركود مرتبط بأكثر من منتج؛ لا يمكن الجرد دون اختيار منتج واضح':'المنتج غير موجود');
 const product=hits[0],batches=product.batches||[];
 if(!batches.length||batches.some(b=>b.id==null))throw Error('لا يمكن جرد منتج بلا دفعات معرفّة');
 return product;
};
const present=(s)=>{
 if(!s)return {active:false,session:null};
 return {active:true,session:{id:s.id,title:s.title,status:s.status,createdAt:s.createdAt,createdBy:s.createdBy,
  members:copy(s.members||{}),
  countedProducts:Object.values(s.counts||{}).map(v=>({productId:v.productId,productName:v.productName,barcode:v.barcode,
    deviceId:v.deviceId,operator:v.operator,deviceName:v.deviceName,countedAt:v.countedAt,rows:copy(v.rows)})),
  inProgress:Object.entries(s.locks||{}).map(([productId,l])=>({productId,deviceId:l.deviceId,operator:l.operator,deviceName:l.deviceName,expiresAt:l.expiresAt}))}};
};
function start(db,payload,userId,ms=Date.now()){
 admin(db,userId);
 if(active(db))throw Error('يوجد جرد مفتوح؛ أنهه أولًا قبل فتح جرد آخر');
 const id=String(payload?.sessionId||'');
 if(!idRx.test(id))throw Error('معرّف جلسة الجرد غير صالح');
 if(sessions(db).some(s=>s.id===id))throw Error('معرف الجرد مستعمل سابقًا');
 const next=copy(db);next.nano_multi_count_sessions=sessions(next);
 const session={id,title:String(payload.title||'الجرد الجماعي').trim().slice(0,100),status:'open',createdAt:nowISO(ms),
  createdBy:userId,locks:{},counts:{},members:{}};
 next.nano_multi_count_sessions.push(session);
 return {next,result:{success:true,session:present(session).session}};
}
function claim(db,payload,trusted,ms=Date.now()){
 const who=identity(trusted,payload),s=ensure(db,payload.sessionId);
 const product=lookup(db,payload),key=String(product.id),counted=(s.counts||{})[key],lock=(s.locks||{})[key];
 if(counted)return {next:db,result:{success:true,status:'counted',productName:product.name,barcode:product.barcode,
    operator:counted.operator,deviceName:counted.deviceName,deviceId:counted.deviceId,rows:copy(counted.rows),countedAt:counted.countedAt}};
 if(lock&&lock.expiresAt>ms&&lock.deviceId!==who.deviceId)return {next:db,result:{success:true,status:'busy',
   productName:product.name,operator:lock.operator,deviceName:lock.deviceName,expiresAt:lock.expiresAt}};
 const next=copy(db),a=ensure(next,payload.sessionId);
 a.members[who.deviceId]={deviceId:who.deviceId,deviceName:who.deviceName,operator:who.operator,lastSeenAt:nowISO(ms)};
 const prior=a.locks[key],token=prior?.deviceId===who.deviceId&&prior.expiresAt>ms?prior.token:
   String(payload.requestId||'');
 if(!idRx.test(token))throw Error('رمز الحجز غير صالح');
 a.locks[key]={deviceId:who.deviceId,deviceName:who.deviceName,operator:who.operator,token,expiresAt:ms+leaseMs};
 const rows=product.batches.map(b=>({product_id:product.id,batch_id:b.id,book_qty:num(b.stock??0),
  expiry_date:b.expiry_date||null}));
 return {next,result:{success:true,status:'claimed',sessionId:a.id,productId:product.id,
   productName:product.name,barcode:product.barcode,token,expiresAt:ms+leaseMs,rows}};
}
function record(db,payload,trusted,ms=Date.now()){
 const who=identity(trusted,payload),s=ensure(db,payload.sessionId),product=lookup(db,{productId:payload.productId}),key=String(product.id);
 if(s.counts?.[key])return {next:db,result:{success:false,status:'counted',operator:s.counts[key].operator,deviceName:s.counts[key].deviceName,message:'سبق جرد هذا المنتج'}};
 const l=s.locks?.[key];
 if(!l||l.deviceId!==who.deviceId||l.operator!==who.operator||l.token!==String(payload.token)||l.expiresAt<=ms)
   throw Error('انتهى حجز المنتج أو أصبح تابعًا لهاتف آخر. امسح الباركود مجددًا');
 const submitted=payload.rows;
 if(!Array.isArray(submitted)||submitted.length!==product.batches.length)throw Error('يجب إدخال عدد كل دفعة للمنتج');
 const byId=new Map(),actual=[];
 for(const row of submitted){
   const k=String(row.batch_id);
   if(byId.has(k))throw Error('تكرار دفعة في نتيجة العد');
   byId.set(k,row);
 }
 for(const b of product.batches){
   const q=byId.get(String(b.id));
   if(!q)throw Error('الدفعة المطلوبة لم تُعد');
   if(num(q.book_qty)!==num(b.stock??0))throw Error('تغيّر المخزون أثناء العد؛ يجب إعادة جرد المنتج');
   actual.push({product_id:product.id,batch_id:b.id,book_qty:num(b.stock??0),counted_qty:num(q.counted_qty)});
 }
 const next=copy(db),a=ensure(next,payload.sessionId);
 a.counts[key]={productId:product.id,productName:String(product.name||''),barcode:String(product.barcode||''),
  deviceId:who.deviceId,deviceName:who.deviceName,operator:who.operator,countedAt:nowISO(ms),rows:actual};
 delete a.locks[key];
 a.members[who.deviceId]={deviceId:who.deviceId,deviceName:who.deviceName,operator:who.operator,lastSeenAt:nowISO(ms)};
 return {next,result:{success:true,status:'counted',productId:product.id,operator:who.operator,
   deviceName:who.deviceName,countedAt:nowISO(ms),rows:copy(actual)}};
}
function release(db,payload,trusted){
 const who=identity(trusted,payload),s=ensure(db,payload.sessionId),key=String(payload.productId);
 const lock=s.locks?.[key];
 if(!lock||lock.deviceId!==who.deviceId||lock.token!==payload.token)return {next:db,result:{success:true,changed:false}};
 const next=copy(db);delete ensure(next,payload.sessionId).locks[key];
 return {next,result:{success:true,changed:true}};
}
function finish(db,payload,userId,guard,ms=Date.now()){
 admin(db,userId);const s=ensure(db,payload.sessionId);
 const rows=Object.values(s.counts||{}).flatMap(c=>c.rows);
 if(!rows.length)throw Error('لم يسجل أي هاتف نتائج جرد');
 if(Object.values(s.locks||{}).some(l=>l.expiresAt>ms))throw Error('لا تزال هناك منتجات قيد الجرد من هواتف مرتبطة');
 if(!guard?.submit)throw Error('آلية اعتماد الجرد غير متاحة');
 const out=guard.submit(db,{requestId:'multi-draft-'+s.id,rows,deviceId:'PRIMARY',note:'جرد جماعي '+s.title},userId,root.NANO_TX_GUARD_165,new Date(ms));
 const next=out.next,changed=sessions(next).find(v=>v.id===s.id);
 changed.status='closed';changed.closedAt=nowISO(ms);changed.closedBy=userId;changed.draftId=out.result.id;
 return {next,result:{success:true,sessionId:s.id,draftId:out.result.id,products:Object.keys(s.counts).length,
    rows:rows.length,session:present(changed).session}};
}
const API={start,claim,record,release,finish,present,active,identity};
if(typeof module!=='undefined'&&module.exports)module.exports=API;
root.NANO_MULTI_COUNT_169=API;
})(typeof window!=='undefined'?window:globalThis);