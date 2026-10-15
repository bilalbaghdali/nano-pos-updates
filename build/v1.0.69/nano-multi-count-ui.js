/* NANO POS v1.0.69 — collaborative mobile inventory count interface. */
(function(root){'use strict';
const doc=root.document;
if(!doc||root.NANO_MULTI_COUNT_UI_169)return;root.NANO_MULTI_COUNT_UI_169=true;
const isPhone=()=>/\/mobile(?:\/|$)/.test(String(root.location?.pathname||''))||!!root.NanoNative;
let overlay=null,session=null,pending=null,lastSeen='',currentProduct=null,operator='',busy=false,pollBusy=false;
const el=(tag,text,cls)=>{const x=doc.createElement(tag);if(text!==undefined&&text!==null)x.textContent=String(text);if(cls)x.className=cls;return x;};
const t=(selector)=>overlay?.querySelector(selector);
const msg=s=>{const n=t('[data-mc-message]');if(n)n.textContent=String(s||'');};
const invoke=async(channel,payload)=>{
  if(typeof root.__browserElectron?.ipcRenderer?.invoke==='function')return await root.__browserElectron.ipcRenderer.invoke(channel,payload||{});
  if(typeof root.api?.invoke==='function')return root.api.invoke(channel,payload||{});
  throw Error('لا يمكن الاتصال بخدمة الجرد على الكمبيوتر الرئيسي');
};
const okay=r=>{if(!r||r.success===false)throw Error(r?.message||r?.error||'تعذر تنفيذ عملية الجرد');return r;};
const genId=prefix=>prefix+'-'+(root.crypto?.randomUUID?.()||(Date.now()+'-'+Math.random().toString(36).slice(2)));
const actor=()=>{try{return JSON.parse(root.localStorage?.getItem('pos_current_user')||'null')}catch{return null}};
const ident=()=>{const x=t('[data-mc-operator]');return String(x?.value||operator||'').trim()};
const status=(data)=>{
  const count=data?.session?.countedProducts||[],members=data?.session?.members||{};
  const n=t('[data-mc-progress]');if(!n)return;
  const part=count.reduce((o,a)=>(o[a.deviceId]=(o[a.deviceId]||0)+1,o),{});
  n.replaceChildren(el('strong','تم جرد '+count.length+' منتج'));
  const p=el('div',null,'nano-mc-members');
  for(const m of Object.values(members)){const item=el('span',m.operator+' • '+m.deviceName+' ('+(part[m.deviceId]||0)+')');p.append(item);}
  n.append(p);
  const list=t('[data-mc-history]');if(!list)return;list.replaceChildren();
  for(const entry of count.slice(-100).reverse()){
    const item=el('div',null,'nano-mc-history-item');
    item.append(el('b',entry.productName||String(entry.productId)));
    item.append(el('span',' — تم جرده بواسطة '+entry.operator+' ('+entry.deviceName+')'));
    item.append(el('small',' | '+entry.rows.map(r=>r.counted_qty+' / '+r.book_qty).join('، ')));
    list.append(item);
  }
};
function close(){overlay?.remove();overlay=null;currentProduct=null;}
function open(data){
 if(!data?.session)return;
 session=data.session;
 if(overlay){status(data);return;}
 const rootLayer=el('div',null,'nano-mc-overlay');overlay=rootLayer;
 const box=el('section',null,'nano-mc-panel');box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');
 box.setAttribute('aria-label','الجرد الجماعي من الهاتف');
 const top=el('div',null,'nano-mc-row');
 top.append(el('h2',isPhone()?'جرد الهاتف — '+session.title:'إدارة الجرد الجماعي'));
 const exit=el('button','إغلاق الشاشة');exit.type='button';exit.addEventListener('click',close);top.append(exit);box.append(top);
 const identity=el('div',null,'nano-mc-row');
 identity.append(el('label','اسم الشخص الذي يجرد:'));
 const op=el('input');op.dataset.mcOperator='1';op.type='text';op.maxLength=65;
 op.placeholder='الاسم الكامل للجارد';
 op.value=operator||root.localStorage?.getItem('nano_mc_operator')||'';
 op.addEventListener('change',()=>{operator=op.value.trim();root.localStorage?.setItem('nano_mc_operator',operator);});
 identity.append(op);box.append(identity);
 const progress=el('div',null,'nano-mc-progress');progress.dataset.mcProgress='1';box.append(progress);
 if(isPhone()){
   const controls=el('div',null,'nano-mc-row');
   const code=el('input');code.type='text';code.placeholder='امسح أو أدخل باركود المنتج';code.dataset.mcCode='1';code.autocomplete='off';
   code.addEventListener('keydown',ev=>{if(ev.key==='Enter'){ev.preventDefault();claimProduct();}});
   const go=el('button','فحص المنتج');go.type='button';go.addEventListener('click',claimProduct);
   controls.append(code,go);box.append(controls);
   box.append(el('p','عند مسح المنتج تظهر الكمية المسجلة في الكمبيوتر، ويُمنع تسجيله من هاتفين في الوقت نفسه.','nano-mc-hint'));
 }else{
   const actions=el('div',null,'nano-mc-row');
   const done=el('button','إنهاء الجرد وإرساله للموافقة');done.type='button';done.addEventListener('click',finishSession);
   const refresh=el('button','تحديث النتائج');refresh.type='button';refresh.addEventListener('click',refreshSession);
   actions.append(done,refresh);box.append(actions);
 }
 const edit=el('div',null,'nano-mc-editor');edit.dataset.mcEditor='1';box.append(edit);
 const info=el('p','', 'nano-mc-hint');info.dataset.mcMessage='1';box.append(info);
 box.append(el('h3','المنتجات التي جُردت (مع اسم كل جارد)'));
 const history=el('div',null,'nano-mc-history');history.dataset.mcHistory='1';box.append(history);
 rootLayer.append(box);doc.body.append(rootLayer);
 rootLayer.addEventListener('click',ev=>{if(ev.target===rootLayer)close();});
 status(data);
 if(isPhone()){t('[data-mc-code]')?.focus();msg('الجرد مفتوح. امسح باركود أي منتج لعرض كميته وإدخال العدد الفعلي.');}
}
async function refreshSession(){
 if(pollBusy)return;pollBusy=true;
 try{
  const d=okay(await invoke('nano-count-active',{}));
  if(!d.active||!d.session){session=null;if(overlay){msg('انتهت جلسة الجرد على الكمبيوتر الرئيسي.');}return;}
  const change=d.session.id!==lastSeen;
  lastSeen=d.session.id;
  if(isPhone()&&change)open(d);
  else if(overlay&&session?.id===d.session.id){session=d.session;status(d);}
  else if(!isPhone()&&overlay&&session?.id===d.session.id)status(d);
 }catch(ex){if(overlay)msg('فشل الاتصال بالكمبيوتر الرئيسي. لن تُحفَظ أعداد أثناء الانقطاع.');}
 finally{pollBusy=false;}
}
function drawProduct(result){
 const content=t('[data-mc-editor]');if(!content)return;
 content.replaceChildren();currentProduct=result;
 const title=el('h3',result.productName+' — '+String(result.barcode||''));
 content.append(title);
 content.append(el('p','الكمية المسجلة: '+result.rows.reduce((n,r)=>n+Number(r.book_qty||0),0)+' | صلاحية الحجز حتى '+new Date(result.expiresAt).toLocaleTimeString(),'nano-mc-hint'));
 const table=el('table',null,'nano-mc-table'),head=el('tr');
 for(const n of ['الدفعة','الكمية المسجلة','العدد الفعلي'])head.append(el('th',n));table.append(head);
 for(const r of result.rows){
   const tr=el('tr');tr.append(el('td',String(r.batch_id)+(r.expiry_date?' | '+r.expiry_date:'')));
   tr.append(el('td',String(r.book_qty)));
   const cell=el('td'),input=el('input');input.type='number';input.step='0.001';input.min='0';input.placeholder='أدخل الكمية';
   input.dataset.batch=String(r.batch_id);cell.append(input);tr.append(cell);table.append(tr);
 }
 content.append(table);
 const actions=el('div',null,'nano-mc-row'),save=el('button','حفظ كمية هذا المنتج'),cancel=el('button','إلغاء الحجز');
 save.addEventListener('click',saveProduct);cancel.addEventListener('click',releaseProduct);
 actions.append(save,cancel);content.append(actions);
 content.querySelector('input')?.focus();
}
async function claimProduct(){
 if(busy||!session?.id)return;
 const code=t('[data-mc-code]')?.value.trim();
 operator=ident();
 if(operator.length<2){msg('أدخل اسم الجارد أولًا');return;}
 if(!code){msg('امسح باركود المنتج أولًا');return;}
 busy=true;
 try{
  const res=okay(await invoke('nano-count-claim',{sessionId:session.id,barcode:code,operatorName:operator,requestId:genId('claim')}));
  root.localStorage?.setItem('nano_mc_operator',operator);
  t('[data-mc-editor]')?.replaceChildren();currentProduct=null;
  if(res.status==='counted'){msg('تم جرد هذا المنتج مسبقًا بواسطة '+res.operator+' على '+res.deviceName+
    '. النتيجة السابقة: '+(res.rows||[]).map(r=>r.counted_qty).join('، '));return;}
  if(res.status==='busy'){msg('المنتج قيد الجرد الآن بواسطة '+res.operator+' على '+res.deviceName+
    '. انتقل إلى منتج آخر.');return;}
  if(res.status!=='claimed')throw Error('نتيجة الحجز غير معروفة');
  drawProduct(res);msg('اكتب الكمية الفعلية لكل دفعة، ثم اضغط حفظ.');
 }catch(ex){msg(ex.message||'فشل حجز المنتج');}
 finally{busy=false;}
}
async function saveProduct(){
 if(busy||!currentProduct||!session?.id)return;
 const inputs=[...t('[data-mc-editor]').querySelectorAll('[data-batch]')];
 if(inputs.some(n=>n.value.trim()===''||!Number.isFinite(Number(n.value))||Number(n.value)<0)){msg('أدخل العدد الفعلي لكل دفعة قبل الحفظ');return;}
 const rows=currentProduct.rows.map(r=>({batch_id:r.batch_id,book_qty:r.book_qty,
   counted_qty:Number(inputs.find(i=>i.dataset.batch===String(r.batch_id)).value)}));
 busy=true;
 try{
  const res=okay(await invoke('nano-count-record',{sessionId:session.id,operatorName:ident(),productId:currentProduct.productId,
    token:currentProduct.token,rows}));
  if(res.status!=='counted')throw Error('لم يتم تأكيد الحفظ');
  const name=currentProduct.productName;currentProduct=null;t('[data-mc-editor]')?.replaceChildren();
  t('[data-mc-code]').value='';t('[data-mc-code]')?.focus();
  msg('حُفظ جرد '+name+' باسم '+res.operator+'. عند إعادة مسحه سيظهر أنه تم جرده.');
  await refreshSession();
 }catch(ex){msg(ex.message||'لم تُحفَظ الكمية، أعد تحميل المنتج');}
 finally{busy=false;}
}
async function releaseProduct(){
 if(busy||!currentProduct||!session?.id)return;
 busy=true;
 try{okay(await invoke('nano-count-release',{sessionId:session.id,operatorName:ident(),productId:currentProduct.productId,token:currentProduct.token}));
  currentProduct=null;t('[data-mc-editor]')?.replaceChildren();msg('أُلغِي حجز المنتج ويمكن لأي هاتف جرده.');
 }catch(ex){msg(ex.message||'تعذر تحرير المنتج');}finally{busy=false;}
}
async function startSession(){
 if(busy)return;const me=actor();if(!me?.id){root.alert('يرجى تسجيل الدخول بحساب مدير');return;}
 const title=root.prompt('عنوان جلسة الجرد الجماعي','الجرد الجماعي')||'الجرد الجماعي';
 if(!root.confirm('فتح جرد جديد لجميع الهواتف المرتبطة؟ لن تتغير كميات المخزون قبل الموافقة من الكمبيوتر الرئيسي.'))return;
 busy=true;
 try{const result=okay(await invoke('nano-count-start',{sessionId:genId('count'),title,userId:me.id}));
   lastSeen=result.session.id;open({active:true,session:result.session});
   msg('جلسة الجرد مفتوحة؛ تظهر تلقائيًا على الهواتف المتصلة.');
 }catch(ex){root.alert(ex.message||'تعذر فتح الجرد');}finally{busy=false;}
}
async function finishSession(){
 if(busy||!session?.id)return;
 const me=actor();if(!me?.id)return msg('تسجيل الدخول مطلوب');
 if(!root.confirm('إنهاء جرد الهواتف وتجميع النتائج في مسودة تحتاج اعتمادًا من الكمبيوتر الرئيسي؟'))return;
 busy=true;
 try{const result=okay(await invoke('nano-count-finish',{sessionId:session.id,userId:me.id}));
   msg('أُغلق الجرد. المسودة رقم '+result.draftId+' جاهزة للمراجعة والاعتماد ضمن قسم الجرد.');
   session=null;lastSeen='';}
 catch(ex){msg(ex.message||'تعذر إنهاء الجرد');}finally{busy=false;}
}
function scanned(ev){
 if(!isPhone()||!overlay||!session?.id)return;
 const code=String(ev.detail?.code||'').trim();if(!code)return;
 const input=t('[data-mc-code]');if(input){input.value=code;claimProduct();}
}
function init(){
 if(doc.getElementById('nanoMultiCountStart'))return;
 const section=doc.getElementById('stocktakeSection');if(!section)return;
 const style=el('style');style.textContent=[
 '.nano-mc-start{background:#ecfdf5;color:#065f46;border:1px solid #059669;border-radius:10px;padding:9px 15px;font:700 13px Arial;cursor:pointer;margin:8px}',
 '.nano-mc-overlay{position:fixed;inset:0;z-index:99997;display:flex;align-items:center;justify-content:center;padding:12px;background:rgba(3,15,28,.78);box-sizing:border-box}',
 '.nano-mc-panel{direction:rtl;background:white;color:#0f172a;border-radius:17px;padding:16px;width:min(900px,100%);max-height:94vh;overflow:auto;box-sizing:border-box;font-family:Arial}',
 '.nano-mc-row{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin:10px 0}',
 '.nano-mc-row h2{flex:1;font-size:18px;font-weight:800}',
 '.nano-mc-panel button{padding:9px 12px;border:1px solid #0d9488;background:#ecfdf5;color:#065f46;border-radius:9px;font-weight:700;cursor:pointer}',
 '.nano-mc-panel input{padding:10px;border:1px solid #cbd5e1;border-radius:9px;max-width:100%;box-sizing:border-box}',
 '.nano-mc-table{width:100%;border-collapse:collapse;font-size:12px}',
 '.nano-mc-table th,.nano-mc-table td{padding:8px;border-bottom:1px solid #e2e8f0;text-align:right}',
 '.nano-mc-history{max-height:25vh;overflow:auto}.nano-mc-history-item{padding:7px;border-bottom:1px solid #cbd5e1;font-size:12px}',
 '.nano-mc-members{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}',
 '.nano-mc-members span{background:#eff6ff;border-radius:8px;padding:6px;font-size:12px}',
 '.nano-mc-hint{font-size:12px;color:#475569}.nano-mc-editor{margin:12px 0}',
 '@media(max-width:520px){.nano-mc-panel{padding:10px}.nano-mc-table input{width:110px}.nano-mc-row h2{font-size:15px}}'
 ].join('\n');doc.head.append(style);
 const button=el('button','بدء جرد جماعي للهواتف','nano-mc-start');button.type='button';button.id='nanoMultiCountStart';
 if(isPhone())button.textContent='الجرد الجماعي المفتوح';
 button.addEventListener('click',()=>{if(isPhone())refreshSession().then(()=>session&&open({active:true,session}));else if(session)open({active:true,session});else startSession();});
 (section.querySelector('header')||section).append(button);
 root.addEventListener('nano-native-barcode',scanned);
 const timer=()=>{if(!doc.hidden)void refreshSession();};
 root.setInterval(timer,4000);timer();
 doc.addEventListener('visibilitychange',timer);
 doc.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&overlay)close();});
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);