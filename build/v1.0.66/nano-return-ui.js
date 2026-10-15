/* NANO POS v1.0.66 - safe, explicit sale-return entry dialog.
 * Uses authorized invoice APIs; no direct storage or ledger edits. */
(function(root){
'use strict';
const doc=root.document;
if(!doc||root.NANO_RETURNS_UI_166)return;
root.NANO_RETURNS_UI_166=true;
let dlg=null,busy=false,lines=[],saleId=null;
const e=(tag,text,cls)=>{const el=doc.createElement(tag);if(text!==undefined&&text!==null)el.textContent=String(text);if(cls)el.className=cls;return el;};
const apiCall=async(method,...args)=>{
  if(typeof root.api?.[method]==='function')return await root.api[method](...args);
  const channel=method==='getSaleDetails'?'get-sale-details':method==='issueCreditNote'?'issue-credit-note':'';
  if(channel&&typeof root.__browserElectron?.ipcRenderer?.invoke==='function'){
    return await root.__browserElectron.ipcRenderer.invoke(channel,...args);
  }
  throw Error('واجهة الفواتير غير متاحة في هذه النسخة');
};
function close(){if(dlg){dlg.remove();dlg=null;}}
async function lookup(){
  if(busy||!dlg)return;
  const id=dlg.querySelector('[data-sale-id]')?.value?.trim();
  if(!id){message('أدخل رقم الفاتورة');return;}
  busy=true;saleId=null;lines=[];
  const holder=dlg.querySelector('[data-lines]');holder.replaceChildren();
  try{
    const result=await apiCall('getSaleDetails',id);
    const sale=result?.sale||result;
    if(!sale||!Array.isArray(result?.items||sale.items))throw Error('لم يتم العثور على الفاتورة');
    const items=result.items||sale.items;
    if(!items.length)throw Error('الفاتورة لا تحتوي منتجات');
    saleId=sale.id;
    const table=e('table',null,'nano-return-table');
    const heading=e('tr');
    for(const s of ['المنتج','الكمية المباعة','الكمية المطلوب إرجاعها'])heading.append(e('th',s));
    table.append(heading);
    for(let i=0;i<items.length;i++){
      const item=items[i],row=e('tr');
      const sold=Number(item.quantity??item.qty??0);
      row.append(e('td',item.name||item.product_name||('منتج '+(i+1))),e('td',String(sold)));
      const td=e('td'),input=e('input');
      input.type='number';input.min='0';input.max=String(sold);input.step='0.001';input.value='0';
      input.dataset.line=String(i);input.setAttribute('aria-label','الكمية المسترجعة');
      td.append(input);row.append(td);table.append(row);
    }
    holder.append(table);
    message('حدد الكميات المطلوب إرجاعها ثم اعتمد العملية.');
  }catch(error){message(error.message||'تعذر قراءة تفاصيل الفاتورة');}
  finally{busy=false;}
}
function message(value){
  const target=dlg?.querySelector('[data-message]');
  if(target)target.textContent=String(value||'');
}
async function submit(){
  if(busy||!dlg||saleId===null)return;
  const elements=[...dlg.querySelectorAll('[data-line]')];
  const picked=elements.map(input=>({lineIndex:Number(input.dataset.line),quantity:Number(input.value)}))
    .filter(x=>Number.isFinite(x.quantity)&&x.quantity>0);
  if(!picked.length){message('اختر كمية واحدة على الأقل');return;}
  if(!root.confirm('تأكيد المرتجع؟ ستُعدّل الفاتورة والمخزون ودين الزبون وقد يُرد جزء من المبلغ نقدًا.'))return;
  let logged=null;try{logged=JSON.parse(root.localStorage?.getItem('pos_current_user')||'null');}catch{}
  if(!logged?.id){message('تسجيل الدخول مطلوب لاعتماد المرتجع');return;}
  const requestId=(root.crypto?.randomUUID?.()||('ret-'+Date.now()+'-'+Math.random().toString(36).slice(2))).replace(/[^a-zA-Z0-9_.:\-]/g,'');
  busy=true;
  try{
    const result=await apiCall('issueCreditNote',{requestId,saleId,userId:logged.id,lines:picked,note:dlg.querySelector('[data-note]')?.value||''});
    if(result?.success===false)throw Error(result.message||result.error||'فشل تسجيل المرتجع');
    if(!result?.credit_note_id)throw Error('لم تؤكد خدمة الفواتير حفظ العملية');
    message('تم تسجيل المرتجع: '+result.credit_note_id+' — ردّ نقدي: '+Number(result.refund_amount||0).toFixed(2));
    dlg.querySelector('[data-lines]')?.replaceChildren();
    saleId=null;
  }catch(err){message(err.message||'تعذر تسجيل المرتجع');}
  finally{busy=false;}
}
function open(){
 if(dlg)return;
 const backdrop=e('div',null,'nano-return-backdrop');dlg=backdrop;
 const panel=e('section',null,'nano-return-panel');panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','المرتجعات');
 const title=e('h2','مرتجعات البيع');
 panel.append(title);
 const hint=e('p','ابحث برقم فاتورة البيع الأصلي، ثم حدد المنتجات والكميات. لا يمكن إعادة دفعات مجهولة.','nano-return-hint');panel.append(hint);
 const row=e('div',null,'nano-return-row');const inp=e('input');inp.placeholder='رقم فاتورة البيع';inp.dataset.saleId='1';
 const find=e('button','جلب الفاتورة');find.type='button';find.addEventListener('click',lookup);row.append(inp,find);panel.append(row);
 const holder=e('div',null,'nano-return-scroll');holder.dataset.lines='1';panel.append(holder);
 const note=e('textarea');note.rows=2;note.placeholder='سبب المرتجع (اختياري)';note.dataset.note='1';panel.append(note);
 const msg=e('p',null,'nano-return-hint');msg.dataset.message='1';panel.append(msg);
 const controls=e('div',null,'nano-return-row'),apply=e('button','اعتماد المرتجع'),exit=e('button','إغلاق');
 apply.type=exit.type='button';apply.addEventListener('click',submit);exit.addEventListener('click',close);
 controls.append(apply,exit);panel.append(controls);backdrop.append(panel);doc.body.append(backdrop);
 backdrop.addEventListener('click',ev=>{if(ev.target===backdrop)close();});inp.focus();
}
function init(){
 if(doc.getElementById('nanoReturnSalesBtn'))return;
 const sales=doc.getElementById('salesLogSection')||doc.getElementById('salesSection');
 if(!sales)return;
 const style=e('style');style.textContent=[
  '.nano-return-button{padding:9px 15px;border:1px solid #0f766e;border-radius:12px;background:#ccfbf1;color:#115e59;font:bold 12px Arial;cursor:pointer;margin:8px}',
  '.nano-return-backdrop{position:fixed;inset:0;z-index:99999;background:rgba(2,6,23,.70);display:flex;align-items:center;justify-content:center;padding:12px;box-sizing:border-box}',
  '.nano-return-panel{max-height:92vh;overflow:auto;width:min(760px,100%);background:#fff;color:#0f172a;border-radius:18px;padding:20px;box-sizing:border-box;direction:rtl;font-family:Arial,sans-serif}',
  '.nano-return-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0}',
  '.nano-return-panel input,.nano-return-panel textarea{border:1px solid #cbd5e1;border-radius:10px;padding:10px;color:#0f172a;min-width:120px;max-width:100%;box-sizing:border-box}',
  '.nano-return-panel button{padding:10px 14px;border-radius:9px;border:1px solid #0d9488;background:#ecfdf5;color:#065f46;font-weight:bold;cursor:pointer}',
  '.nano-return-scroll{overflow:auto}.nano-return-table{border-collapse:collapse;width:100%;font-size:12px}',
  '.nano-return-table th,.nano-return-table td{padding:9px;text-align:right;border-bottom:1px solid #e2e8f0}',
  '.nano-return-table input{width:120px}.nano-return-hint{font-size:12px;color:#64748b}',
  '.nano-return-panel button:focus-visible,.nano-return-panel input:focus-visible{outline:2px solid #2563eb;outline-offset:2px}'
 ].join('\n');doc.head.append(style);
 const button=e('button','مرتجعات البيع','nano-return-button');button.type='button';button.id='nanoReturnSalesBtn';
 (sales.querySelector('header')||sales).append(button);button.addEventListener('click',open);
 doc.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&dlg)close();});
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);