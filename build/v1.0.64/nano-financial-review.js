/* NANO POS v1.0.64 - read-only financial review and transaction timeline.
   No claim of certified net profit or immutable audit. No business-data writes. */
(function(root){
'use strict';
const round=n=>Math.round((n+Number.EPSILON)*100)/100;
const finite=n=>typeof n==='number'&&Number.isFinite(n);
function financial(analytics){
  if(!analytics||typeof analytics!=='object'||analytics.success===false)throw Error('التحليلات غير متاحة');
  const s=analytics.sales;
  if(!s||typeof s!=='object')throw Error('تفاصيل المبيعات غير مكتملة');
  const revenue=Number(s.net_revenue??s.revenue);
  const cogs=Number(analytics.cogs);
  const expenses=Number(analytics.totalExpenses);
  if(![revenue,cogs,expenses].every(finite)||[revenue,cogs,expenses].some(x=>x<0)){
    throw Error('لا تتوفر معلومات كافية عن المبيعات أو التكلفة أو المصاريف');
  }
  const gross=round(revenue-cogs);
  const provisional=round(gross-expenses);
  return {revenue:round(revenue),cogs:round(cogs),expenses:round(expenses),
    gross,provisional,returnsRecorded:Number(s.returns_count??0),
    returnsValue:Number(s.returns_value??0),
    limitations:['قد لا تشمل البيانات تأثير كل المرتجعات والاستبدالات.',
      'قد توجد مصاريف أو فروقات صندوق خارج مصاريف التحليلات.',
      'صافي الربح المعروض تقديري وليس اعتمادًا محاسبيًا نهائيًا.']};
}
const rows=payload=>{
  if(Array.isArray(payload))return payload;
  if(!payload||typeof payload!=='object'||payload.success===false)throw Error('سجل العمليات غير متاح');
  if(Array.isArray(payload.rows))return payload.rows;
  if(Array.isArray(payload.items))return payload.items;
  if(Array.isArray(payload.data))return payload.data;
  return [];
};
const norm=(collection,kind)=>{
  return rows(collection).slice(0,300).filter(x=>x&&typeof x==='object').map(x=>({
    kind,id:String(x.id??x.invoice_no??'—'),
    when:String(x.sale_date??x.invoice_date??x.created_at??x.date??''),
    by:String(x.user_name??x.cashier_name??x.created_by_name??'—'),
    total:finite(Number(x.total))?round(Number(x.total)):null
  }));
};
const timeline=(sales,purchases)=>[
  ...norm(sales,'بيع'),...norm(purchases,'شراء')
].sort((a,b)=>b.when.localeCompare(a.when)).slice(0,80);
const fmt=n=>new Intl.NumberFormat('fr-DZ',{minimumFractionDigits:2,maximumFractionDigits:2}).format(n);
const API={financial,rows,norm,timeline,fmt};
if(typeof module!=='undefined'&&module.exports)module.exports=API;
const doc=root.document;
if(!doc||root.NANO_FIN_REVIEW_164)return;
root.NANO_FIN_REVIEW_164=API;
let modal=null,busy=false,last=null,session=0;
const elt=(tag,t,klass)=>{
  const e=doc.createElement(tag);
  if(t!==undefined&&t!==null)e.textContent=String(t).slice(0,280);
  if(klass)e.className=klass;
  return e;
};
function close(){
  ++session;
  if(modal){modal.remove();modal=null;}
  last?.focus();
}
async function load(){
  if(!modal||busy)return;
  busy=true;
  const generation=session;
  const output=modal.querySelector('[data-content]'),button=modal.querySelector('[data-reload]');
  button.disabled=true;
  output.replaceChildren(elt('p','جارٍ جلب بيانات التحليلات وسجل المعاملات…'));
  const cards=elt('div',null,'nano-fin-grid');
  const earnings=elt('section',null,'nano-fin-card'),activity=elt('section',null,'nano-fin-card');
  earnings.append(elt('h3','مراجعة هامش الربح والمصاريف'));
  activity.append(elt('h3','سجل مرجعي للمعاملات المسجلة'));
  let errorCount=0;
  try{
    if(typeof root.api?.getAnalytics!=='function')throw Error('خدمة الإحصائيات غير متاحة');
    const raw=await root.api.getAnalytics({});
    const a=financial(raw);
    const table=elt('table',null,'nano-fin-table');
    for(const [label,value] of [
      ['صافي إيراد المبيعات المتاح',a.revenue],
      ['تكلفة البضاعة المباعة',a.cogs],
      ['الربح الإجمالي',a.gross],
      ['المصاريف المسجلة بالتقرير',a.expenses],
      ['صافي تقديري قبل التحقق من المرتجعات',a.provisional]
    ]){
      const tr=elt('tr');tr.append(elt('th',label),elt('td',fmt(value)+' دج'));table.append(tr);
    }
    earnings.append(table);
    for(const warning of a.limitations)earnings.append(elt('p',warning,'nano-fin-warning'));
  }catch(e){errorCount++;earnings.append(elt('p','تعذرت المراجعة: '+String(e?.message||'غير معروف'),'nano-fin-warning'));}
  try{
    if(typeof root.api?.getSales!=='function'||typeof root.api?.getPurchases!=='function')throw Error('واجهات فواتير البيع والشراء غير متاحة');
    const [sales,purchases]=await Promise.all([root.api.getSales({limit:150}),root.api.getPurchases()]);
    const events=timeline(sales,purchases);
    activity.append(elt('p','عرض آخر العمليات التي أمكن قراءتها. هذا ليس سجلًا غير قابل للتعديل ولا يثبت الحذف أو التغييرات القديمة.','nano-fin-warning'));
    if(!events.length)activity.append(elt('p','لا توجد عمليات متاحة في البيانات المقروءة.'));
    const list=elt('div',null,'nano-fin-scroll');
    const tab=elt('table',null,'nano-fin-table');
    const head=elt('tr');
    for(const h of ['النوع','رقم المعاملة','التاريخ','المستخدم المسجل','المبلغ'])head.append(elt('th',h));
    tab.append(head);
    for(const entry of events){
      const tr=elt('tr');
      for(const value of [entry.kind,entry.id,entry.when||'—',entry.by,entry.total===null?'—':fmt(entry.total)+' دج'])tr.append(elt('td',value));
      tab.append(tr);
    }
    list.append(tab);activity.append(list);
  }catch(e){errorCount++;activity.append(elt('p','تعذر قراءة سجل المعاملات: '+String(e?.message||'غير معروف'),'nano-fin-warning'));}
  cards.append(earnings,activity);
  if(modal&&generation===session)output.replaceChildren(cards);
  if(button)button.disabled=false;
  busy=false;
}
function open(){
  if(modal)return;
  last=doc.activeElement;session++;
  modal=elt('div',null,'nano-fin-overlay');
  const panel=elt('section',null,'nano-fin-dialog');panel.setAttribute('role','dialog');
  panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','مراجعة الأرباح والمعاملات');
  const head=elt('div',null,'nano-fin-head');
  head.append(elt('h2','مراجعة الأرباح والمعاملات'));
  const buttons=elt('div'),refresh=elt('button','تحديث'),exit=elt('button','إغلاق');
  refresh.dataset.reload='1';refresh.type=exit.type='button';
  buttons.append(refresh,exit);head.append(buttons);panel.append(head);
  panel.append(elt('p','هذه مراجعة للقراءة فقط من سجلات النظام الحالي؛ لا تغيّر أي فاتورة أو رصيد أو ترخيص.','nano-fin-warning'));
  const content=elt('div');content.dataset.content='1';panel.append(content);
  modal.append(panel);doc.body.append(modal);
  refresh.addEventListener('click',load);exit.addEventListener('click',close);
  modal.addEventListener('click',e=>{if(e.target===modal)close();});
  exit.focus();load();
}
function init(){
  if(doc.getElementById('nanoFinancialReviewButton'))return;
  const openOps=doc.getElementById('nanoOperationsOpen');
  if(!openOps)return;
  const style=elt('style');style.textContent=[
    '.nano-fin-trigger{border:1px solid #0ea5e9;background:#eff6ff;color:#075985;border-radius:12px;padding:7px 12px;font:bold 12px Arial;cursor:pointer}',
    '.nano-fin-overlay{position:fixed;inset:0;z-index:99996;background:rgba(2,6,23,.67);padding:14px;display:flex;align-items:center;justify-content:center;box-sizing:border-box}',
    '.nano-fin-dialog{width:min(1000px,100%);max-height:92vh;overflow:auto;border-radius:18px;background:#fff;color:#0f172a;padding:18px;box-sizing:border-box;direction:rtl;font-family:Arial,sans-serif}',
    '.nano-fin-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}',
    '.nano-fin-head button{border:1px solid #cbd5e1;border-radius:9px;background:#f8fafc;padding:8px 12px;margin:3px;cursor:pointer}',
    '.nano-fin-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:15px}',
    '.nano-fin-card{border:1px solid #e2e8f0;border-radius:13px;padding:13px;min-width:0}',
    '.nano-fin-card h3{font-size:14px;font-weight:900}',
    '.nano-fin-table{width:100%;border-collapse:collapse;font-size:12px}',
    '.nano-fin-table th,.nano-fin-table td{padding:8px;border-bottom:1px solid #e2e8f0;text-align:start}',
    '.nano-fin-warning{font-size:12px;color:#9a3412;margin:8px 0}',
    '.nano-fin-scroll{overflow:auto;max-height:50vh}',
    '.nano-fin-trigger:focus-visible,.nano-fin-head button:focus-visible{outline:3px solid #2563eb;outline-offset:2px}'
  ].join('\n');doc.head.append(style);
  const btn=elt('button','مراجعة مالية','nano-fin-trigger');btn.type='button';btn.id='nanoFinancialReviewButton';
  openOps.insertAdjacentElement('afterend',btn);btn.addEventListener('click',open);
  doc.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal)close();});
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);
