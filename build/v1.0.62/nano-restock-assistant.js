/* NANO POS 1.0.62: read-only restock and expiry assistant. */
(function(root){
'use strict';
const num=v=>{if(v===undefined||v===null||v==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;};
const pick=(o,keys)=>{for(const k of keys){const n=num(o?.[k]);if(n!==null)return n;}return null;};
const utc=v=>{const m=/^(\d{4})-(\d\d)-(\d\d)/.exec(String(v||''));if(!m)return null;const y=+m[1],mo=+m[2],d=+m[3],t=Date.UTC(y,mo-1,d),x=new Date(t);return x.getUTCFullYear()===y&&x.getUTCMonth()===mo-1&&x.getUTCDate()===d?t:null;};
const days=(v,today=new Date())=>{const date=utc(v);return date===null?null:Math.round((date-Date.UTC(today.getFullYear(),today.getMonth(),today.getDate()))/86400000);};
const fromResponse=r=>{
  if(Array.isArray(r))return {items:r,total:null};
  if(!r||typeof r!=='object'||r.success===false)throw Error('تعذر قراءة سجل المنتجات');
  const d=r.data&&typeof r.data==='object'?r.data:r;
  const items=['items','rows','products','results'].map(k=>d[k]).find(Array.isArray);
  if(!items)throw Error('استجابة غير صالحة من خدمة المنتجات');
  return {items,total:pick(d,['total','totalCount','count'])};
};
const stock=p=>{
  const fromBatches=Array.isArray(p.batches)?p.batches.reduce((n,b)=>n+(pick(b,['stock','quantity'])||0),0):null;
  return pick(p,['stock','total_stock','quantity','stock_quantity','current_stock'])??fromBatches;
};
const expiration=(p,today)=>{
  const dates=[];
  if(Array.isArray(p.batches))for(const b of p.batches){
    const qty=pick(b,['stock','quantity']);
    if(qty!==null&&qty<=0)continue;
    const v=b.expiry_date||b.expiration_date||b.expiryDate;
    if(utc(v)!==null)dates.push(String(v).slice(0,10));
  }
  const direct=p.expiry_date||p.expiration_date||p.expiryDate||p.expirationDate;
  if(!dates.length&&utc(direct)!==null)dates.push(String(direct).slice(0,10));
  if(!dates.length)return null;
  dates.sort();return {date:dates[0],days:days(dates[0],today)};
};
const classify=(p,today=new Date())=>{
  if(!p||typeof p!=='object')return null;
  const qty=stock(p),min=pick(p,['min_stock','minStock','minimum_stock','reorder_point']);
  const exp=expiration(p,today),low=qty!==null&&min!==null&&min>0&&qty<min;
  if(!low&&!(exp&&exp.days<=30))return null;
  return {name:String(p.name||p.product_name||p.title||'منتج'),barcode:String(p.barcode||''),
    stock:qty,minimum:min,reorder:low?Math.ceil((min*1.5-qty)*100)/100:0,
    expiry:exp?.date||null,expiryDays:exp?.days??null,low,expired:!!exp&&exp.days<0,
    expiring:!!exp&&exp.days>=0&&exp.days<=30};
};
const summarize=(products,today=new Date())=>{
  const rows=(products||[]).map(p=>classify(p,today)).filter(Boolean);
  rows.sort((a,b)=>Number(b.expired)-Number(a.expired)||Number(b.expiring)-Number(a.expiring)||Number(b.low)-Number(a.low)||(a.expiryDays??99999)-(b.expiryDays??99999)||a.name.localeCompare(b.name));
  return {rows,low:rows.filter(x=>x.low).length,expired:rows.filter(x=>x.expired).length,expiring:rows.filter(x=>x.expiring).length};
};
const API={num,days,fromResponse,stock,expiration,classify,summarize};
if(typeof module!=='undefined'&&module.exports)module.exports=API;
const doc=root.document;
if(!doc||root.NANO_REORDER_162)return;
root.NANO_REORDER_162=API;
let modal=null,entry=null,busy=false;
const el=(tag,text='',className='')=>{const e=doc.createElement(tag);if(text)e.textContent=text;if(className)e.className=className;return e;};
const nf=n=>n===null?'—':new Intl.NumberFormat('fr-DZ',{maximumFractionDigits:2}).format(n);
async function load(){
  if(typeof root.api?.getProducts!=='function')throw Error('خدمة المنتجات غير متاحة، يرجى تسجيل الدخول');
  const all=[],seen=new Set();let partial=false;
  for(let page=1;page<=50;page++){
    const r=fromResponse(await root.api.getProducts({page,perPage:200}));
    let fresh=0;
    for(const p of r.items){
      if(!p||typeof p!=='object')continue;
      const id=p.id??p.product_id;
      if(id!=null){if(seen.has(String(id)))continue;seen.add(String(id));}
      all.push(p);fresh++;
    }
    if(!r.items.length||fresh===0||(r.total!==null&&all.length>=r.total)||(r.total===null&&r.items.length<200))break;
    if(page===50)partial=true;
  }
  return {all,partial};
}
function report(host,result,partial){
  host.replaceChildren();
  host.append(el('p','مخزون منخفض: '+result.low+' | منتهية الصلاحية: '+result.expired+' | تنتهي خلال 30 يومًا: '+result.expiring,'nano-restock-note'));
  host.append(el('p','هذه اقتراحات فقط. لن تتغير كميات المخزون أو الفواتير. تواريخ الصلاحية مستمدة من الدفعات الموجودة.','nano-restock-note'));
  if(partial)host.append(el('p','القائمة جزئية: تم الوصول إلى حد قراءة 10000 منتج.','nano-restock-note'));
  if(!result.rows.length){host.append(el('p','لا توجد تنبيهات وفق البيانات المتاحة','nano-restock-note'));return;}
  const sc=el('div','','nano-restock-scroll'),table=el('table','','nano-restock-table'),thead=el('thead'),tr=el('tr');
  for(const t of ['المنتج','الباركود','المخزون','الحد الأدنى','الشراء المقترح','انتهاء الصلاحية','الحالة'])tr.append(el('th',t));
  thead.append(tr);table.append(thead);
  const body=el('tbody');
  for(const p of result.rows.slice(0,500)){
    const row=el('tr'),status=[];
    if(p.low)status.push('مخزون منخفض');
    if(p.expired)status.push('منتهي');
    if(p.expiring)status.push('ينتهي خلال '+p.expiryDays+' يوم');
    for(const value of [p.name,p.barcode||'—',nf(p.stock),nf(p.minimum),p.low?nf(p.reorder):'—',p.expiry||'—',status.join(' • ')])row.append(el('td',value));
    body.append(row);
  }
  table.append(body);sc.append(table);host.append(sc);
  if(result.rows.length>500)host.append(el('p','يُعرض أول 500 تنبيه فقط.','nano-restock-note'));
}
async function refresh(){
  if(busy||!modal)return;
  busy=true;
  const content=modal.querySelector('[data-results]'),button=modal.querySelector('[data-refresh]');
  button.disabled=true;content.replaceChildren(el('p','جارٍ قراءة المنتجات…','nano-restock-note'));
  try{const {all,partial}=await load();if(modal)report(content,summarize(all),partial);}
  catch(err){if(modal)content.replaceChildren(el('p','تعذر تحميل التنبيهات: '+(err?.message||'خطأ غير معروف'),'nano-restock-note'));}
  finally{busy=false;button.disabled=false;}
}
function close(){if(!modal)return;modal.remove();modal=null;entry?.focus();}
function open(){
  if(modal)return;
  modal=el('div','','nano-restock-overlay');
  const dialog=el('section','','nano-restock-dialog');dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');
  dialog.setAttribute('aria-label','مساعد إعادة الطلب');
  const h=el('div','','nano-restock-head');h.append(el('h2','قائمة إعادة الطلب وتنبيهات الصلاحية'));
  const actions=el('div'),reload=el('button','تحديث'),exit=el('button','إغلاق');
  reload.type=exit.type='button';reload.dataset.refresh='1';exit.dataset.close='1';
  actions.append(reload,exit);h.append(actions);dialog.append(h);
  const content=el('div');content.dataset.results='1';dialog.append(content);
  modal.append(dialog);doc.body.append(modal);
  reload.addEventListener('click',refresh);exit.addEventListener('click',close);
  modal.addEventListener('click',e=>{if(e.target===modal)close();});
  exit.focus();refresh();
}
function init(){
  const section=doc.getElementById('productsSection');
  if(!section||doc.getElementById('nanoRestockAssistantBtn'))return;
  const style=el('style');
  style.textContent=[
    '.nano-restock-button{border:1px solid #0d9488;border-radius:12px;background:#ecfdf5;color:#0f766e;padding:9px 12px;font:bold 12px Arial;cursor:pointer;margin:8px}',
    '.nano-restock-overlay{position:fixed;inset:0;z-index:99990;background:rgba(15,23,42,.66);display:flex;justify-content:center;align-items:center;padding:16px;box-sizing:border-box}',
    '.nano-restock-dialog{width:min(840px,100%);max-height:90vh;overflow:auto;background:#fff;color:#0f172a;border-radius:20px;padding:20px;box-sizing:border-box;text-align:start;direction:rtl;font-family:Arial,sans-serif}',
    '.nano-restock-dialog button{padding:7px 12px;border:1px solid #cbd5e1;border-radius:10px;background:#f8fafc;color:#0f172a;cursor:pointer;font-weight:bold;margin:2px}',
    '.nano-restock-head{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}',
    '.nano-restock-table{width:100%;border-collapse:collapse;font-size:12px}',
    '.nano-restock-table th,.nano-restock-table td{padding:10px 7px;border-bottom:1px solid #e2e8f0;text-align:start}',
    '.nano-restock-scroll{overflow:auto}.nano-restock-note{font-size:12px;color:#475569;margin:12px 0}',
    '.nano-restock-button:focus-visible,.nano-restock-dialog button:focus-visible{outline:3px solid #2563eb;outline-offset:2px}',
    '.nano-restock-dialog button:disabled{opacity:.5;cursor:wait}'
  ].join('\n');
  doc.head.append(style);
  entry=el('button','اقتراح إعادة الطلب · تنبيهات الصلاحية','nano-restock-button');
  entry.type='button';entry.id='nanoRestockAssistantBtn';
  (section.querySelector('header')||section).append(entry);
  entry.addEventListener('click',open);
  doc.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal)close();});
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);
