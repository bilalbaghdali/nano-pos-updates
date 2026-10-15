/* NANO POS v1.0.67 — count from phone, review on primary PC. */
(function(root){'use strict';const doc=root.document;if(!doc||root.NANO_STOCKTAKE_UI_167)return;
root.NANO_STOCKTAKE_UI_167=true;let modal=null,rows=[],busy=false,controller=null;
const el=(t,s='',cls='')=>{const n=doc.createElement(t);if(s)n.textContent=String(s);if(cls)n.className=cls;return n;};
const rpc=async(channel,args)=>{
 const map={'get-stocktake-sheet':'getStocktakeSheet','get-stocktake-drafts':'getStocktakeDrafts',
 'create-stocktake-draft':'createStocktakeDraft','approve-stocktake-draft':'approveStocktakeDraft','reject-stocktake-draft':'rejectStocktakeDraft'};
 const method=map[channel];if(typeof root.api?.[method]==='function')return root.api[method](args);
 if(typeof root.__browserElectron?.ipcRenderer?.invoke==='function')return root.__browserElectron.ipcRenderer.invoke(channel,args);
 throw Error('خدمة الجرد غير متاحة');
};
const actor=()=>{try{return JSON.parse(root.localStorage?.getItem('pos_current_user')||'null')}catch{return null}};
function show(t){const p=modal?.querySelector('[data-status]');if(p)p.textContent=t;}
function close(){modal?.remove();modal=null;rows=[];controller=null;}
function table(rowsToShow){
 const wrap=modal?.querySelector('[data-list]');if(!wrap)return;wrap.replaceChildren();
 const filter=modal.querySelector('[data-search]')?.value.trim().toLowerCase()||'';
 const visible=rowsToShow.filter(r=>(String(r.product_name)+' '+String(r.barcode)).toLowerCase().includes(filter)).slice(0,250);
 const tab=el('table','','nano-stock-draft-table'),head=el('tr');
 for(const title of ['الباركود','المنتج والدفعة','المخزون','العدد الفعلي'])head.append(el('th',title));tab.append(head);
 for(const r of visible){
  const tr=el('tr');tr.append(el('td',r.barcode||'—'),el('td',String(r.product_name||'')+' / '+String(r.batch_id||'—')),el('td',String(r.book_qty)));
  const cell=el('td'),inp=el('input');inp.type='number';inp.min='0';inp.step='0.001';inp.placeholder='—';
  inp.value=r.counted_qty===null||r.counted_qty===undefined?'':String(r.counted_qty);
  inp.setAttribute('aria-label','الكمية الفعلية');inp.addEventListener('change',()=>{
   const v=inp.value.trim();r.counted_qty=v===''?null:Number(v);
  });
  cell.append(inp);tr.append(cell);tab.append(tr);
 }
 wrap.append(tab);
 if(rowsToShow.length>visible.length)wrap.append(el('p','استخدم البحث لتحديد بقية المنتجات والدفعات.','nano-stock-draft-note'));
}
async function loadSheet(){
 if(busy||!modal)return;busy=true;show('جارٍ تحميل مخزون الكمبيوتر الرئيسي...');
 try{
  const payload=await rpc('get-stocktake-sheet',{scope_type:'all'});
  if(payload?.success===false)throw Error(payload.message||payload.error);
  rows=(payload.rows||payload.items||[]).filter(x=>x.batch_id!==null).map(x=>({...x,counted_qty:null}));
  table(rows);show('امسح الباركود بالكاميرا أو ابحث ثم سجّل الكمية الفعلية. لن يتغير المخزون حتى الاعتماد.');
 }catch(e){show(e.message||'تعذر جلب المخزون');}finally{busy=false;}
}
async function submit(){
 if(busy||!modal)return;
 const selected=rows.filter(r=>r.counted_qty!==null&&r.counted_qty!==undefined);
 if(!selected.length){show('حدد كميات الجرد أولًا');return;}
 if(selected.some(r=>!Number.isFinite(Number(r.counted_qty))||Number(r.counted_qty)<0)){show('توجد كمية غير صالحة');return;}
 if(!root.confirm('رفع مسودة جرد للمراجعة؟ لا يتغير المخزون حتى يعتمدها الكمبيوتر الرئيسي.'))return;
 busy=true;
 try{
  const uid=actor()?.id;if(!uid)throw Error('تسجيل الدخول مطلوب');
  const key='draft-'+(root.crypto?.randomUUID?.()||Date.now()+'-'+Math.random().toString(36).slice(2));
  const result=await rpc('create-stocktake-draft',{requestId:key,userId:uid,
    deviceId:String(root.NanoNative?.deviceId||'web-mobile'),rows:selected.map(r=>({product_id:r.product_id,batch_id:r.batch_id,
      book_qty:Number(r.book_qty),counted_qty:Number(r.counted_qty)}))});
  if(result?.success===false)throw Error(result.message||result.error||'فشل رفع الجرد');
  if(!result?.id)throw Error('لم يؤكد الخادم تسجيل مسودة الجرد');
  show('أُرسلت المسودة إلى الكمبيوتر الرئيسي. رقم المسودة: '+result.id);rows=[];
  modal.querySelector('[data-list]')?.replaceChildren();
 }catch(e){show(e.message||'تعذر رفع المسودة');}finally{busy=false;}
}
async function drafts(){
 if(busy||!modal)return;busy=true;const list=modal.querySelector('[data-list]');list.replaceChildren();show('جارٍ قراءة مسودات الجرد...');
 try{
  const items=await rpc('get-stocktake-drafts',{status:'pending'});
  if(!Array.isArray(items))throw Error('استجابة الجرد غير صالحة');
  if(!items.length)list.append(el('p','لا توجد مسودات تنتظر الاعتماد.'));
  for(const draft of items.slice(0,100)){
   const card=el('div','','nano-stock-draft-card');
   card.append(el('strong','المسودة '+String(draft.id)),el('p','المستخدم: '+String(draft.submitted_by_name||'—')+
    ' | عدد الدفعات: '+String(draft.rows?.length||0)+' | '+String(draft.submitted_at||'')));
   const btns=el('div','','nano-stock-draft-actions');
   const approve=el('button','اعتماد الجرد'),reject=el('button','رفض المسودة');
   approve.addEventListener('click',()=>review(draft.id,true));
   reject.addEventListener('click',()=>review(draft.id,false));
   btns.append(approve,reject);card.append(btns);list.append(card);
  }
  show('يُسمح بالاعتماد فقط من شاشة الكمبيوتر الرئيسي وبحساب مخول.');
 }catch(e){show(e.message||'تعذر جلب المسودات');}finally{busy=false;}
}
async function review(id,accept){
 if(busy||!modal)return;
 const uid=actor()?.id;if(!uid){show('تسجيل الدخول مطلوب');return;}
 if(!root.confirm(accept?'اعتماد المسودة بعد مراجعة الأعداد؟':'رفض هذه المسودة؟'))return;
 busy=true;try{
  const result=await rpc(accept?'approve-stocktake-draft':'reject-stocktake-draft',{draftId:id,userId:uid});
  if(result?.success===false)throw Error(result.message||result.error||'رفض الخادم العملية');
  show(accept?'تم اعتماد الجرد بنجاح.':'تم رفض المسودة.');
  busy=false;await drafts();
 }catch(e){show(e.message||'فشلت مراجعة الجرد');}finally{busy=false;}
}
function scanned(ev){
 if(!modal||!rows.length)return;
 const code=String(ev.detail?.code||'').trim();
 const matches=rows.filter(r=>String(r.barcode||'')===code);
 if(!matches.length){show('الباركود غير موجود ضمن الدفعات: '+code);return;}
 if(matches.length>1){modal.querySelector('[data-search]').value=code;table(rows);show('المنتج له دفعات متعددة، اختر الدفعة المطلوبة.');return;}
 const r=matches[0];r.counted_qty=(r.counted_qty===null?0:Number(r.counted_qty))+1;
 modal.querySelector('[data-search]').value=code;table(rows);show('تم احتساب وحدة من '+String(r.product_name));
}
function open(){
 if(modal)return;
 modal=el('div','','nano-stock-draft-overlay');
 const box=el('section','','nano-stock-draft-dialog');box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');
 box.append(el('h2','جرد الهاتف واعتماد الكمبيوتر'));
 const bar=el('div','','nano-stock-draft-actions');
 for(const [title,handler] of [['إعداد جرد جديد',loadSheet],['طلبات تنتظر الموافقة',drafts],['إرسال للمراجعة',submit],['إغلاق',close]]){
  const b=el('button',title);b.type='button';b.addEventListener('click',handler);bar.append(b);
 }box.append(bar);
 const search=el('input');search.type='search';search.placeholder='بحث بالاسم أو الباركود';search.dataset.search='1';
 search.addEventListener('input',()=>table(rows));box.append(search);
 const status=el('p','جهّز الجرد أو افتح مسودات الموافقة.','nano-stock-draft-note');status.dataset.status='1';box.append(status);
 const list=el('div','','nano-stock-draft-scroll');list.dataset.list='1';box.append(list);
 modal.append(box);doc.body.append(modal);modal.addEventListener('click',e=>{if(e.target===modal)close();});search.focus();
}
function init(){
 if(doc.getElementById('nanoStocktakeDraftButton'))return;
 const section=doc.getElementById('stocktakeSection');if(!section)return;
 const style=el('style');style.textContent=[
  '.nano-stock-draft-button{margin:8px;background:#ecfdf5;color:#065f46;border:1px solid #10b981;border-radius:10px;padding:10px 14px;font:bold 12px Arial}',
  '.nano-stock-draft-overlay{position:fixed;inset:0;z-index:99995;background:rgba(2,6,23,.7);display:flex;align-items:center;justify-content:center;padding:12px}',
  '.nano-stock-draft-dialog{background:white;color:#0f172a;border-radius:16px;width:min(940px,100%);max-height:94vh;overflow:auto;direction:rtl;box-sizing:border-box;padding:16px;font-family:Arial}',
  '.nano-stock-draft-actions{display:flex;flex-wrap:wrap;gap:7px;margin:10px 0}',
  '.nano-stock-draft-actions button{padding:9px 11px;border:1px solid #0d9488;border-radius:9px;background:#ecfdf5;color:#065f46;font-weight:bold;cursor:pointer}',
  '.nano-stock-draft-dialog input{padding:9px;border:1px solid #cbd5e1;border-radius:9px;max-width:100%}',
  '.nano-stock-draft-scroll{max-height:56vh;overflow:auto}',
  '.nano-stock-draft-table{width:100%;border-collapse:collapse;font-size:12px}',
  '.nano-stock-draft-table th,.nano-stock-draft-table td{border-bottom:1px solid #e2e8f0;text-align:right;padding:8px}',
  '.nano-stock-draft-card{margin:8px 0;border:1px solid #cbd5e1;border-radius:10px;padding:10px}',
  '.nano-stock-draft-note{color:#64748b;font-size:12px;margin:8px 0}',
  '@media(max-width:500px){.nano-stock-draft-dialog{padding:10px}.nano-stock-draft-table{font-size:11px}}'
 ].join('\n');doc.head.append(style);
 const button=el('button','جرد الهاتف والموافقة','nano-stock-draft-button');button.type='button';button.id='nanoStocktakeDraftButton';
 (section.querySelector('header')||section).append(button);button.addEventListener('click',open);
 root.addEventListener('nano-native-barcode',scanned);
 doc.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&modal)close();});
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);