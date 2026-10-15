/* NANO POS v1.0.63 — unified read-only operations and alert center.
   No business write, no new ledger, no permission or activation changes. */
(function(root){
  'use strict';
  const doc=root.document;
  const array=r=>{
    if(Array.isArray(r))return r;
    if(!r||typeof r!=='object'||r.success===false)throw Error('تعذر قراءة بيانات التنبيهات');
    const d=r.data&&typeof r.data==='object'?r.data:r;
    const rows=['items','rows','products','results'].map(k=>d[k]).find(Array.isArray);
    if(!rows)throw Error('استجابة منتجات غير معروفة');
    const count=Number(d.total??d.totalCount??d.count);
    return {rows,total:Number.isFinite(count)&&count>=0?count:null};
  };
  const normalizeNotifications=(rows)=>{
    if(!Array.isArray(rows))return [];
    return rows.filter(x=>x&&typeof x==='object').map((x,i)=>({
      id:String(x.id??i),title:String(x.title??x.message??x.text??'تنبيه'),
      category:String(x.type??x.category??'general')
    })).slice(0,50);
  };
  const safeLabel=s=>String(s??'').slice(0,220);
  const refs=[
    ['caisseSection','الصندوق والمناوبات','إدارة المناوبة والمصاريف والمراجعة'],
    ['salesLogSection','الفواتير والمرتجعات','مراجعة البيع ثم إجراءات الاسترجاع'],
    ['promotionsSection','الأسعار والعروض','العروض والخصومات حسب القواعد الحالية'],
    ['salesSection','البيع وأسعار الجملة','الدفع والبيع بالجملة'],
    ['stocktakeSection','الجرد بالهاتف','فتح الجرد ومزامنة العد عبر الواجهة المخصصة'],
    ['analyticsSection','الأرباح والتقارير','التحقق من تقارير الربح والتكلفة'],
    ['usersSection','المستخدمون والصلاحيات','مراجعة الصلاحيات وسجلات النظام المتاحة']
  ];
  const model=(products,reorder,today)=>{
    if(!reorder||typeof reorder.summarize!=='function')throw Error('مساعد المخزون غير متاح');
    const result=reorder.summarize(products,today);
    return {low:result.low,expired:result.expired,expiring:result.expiring,
      warnings:result.rows.slice(0,100).map(r=>({
        label:r.name,
        message:r.expired?'منتهية الصلاحية — '+String(r.expiry??''):
                r.expiring?'تنتهي خلال '+r.expiryDays+' يوم — '+String(r.expiry??''):
                'مخزون منخفض: '+String(r.stock??'—')+' / '+String(r.minimum??'—'),
        type:r.expired?'expired':r.expiring?'expiring':'low'
      }))};
  };
  const API={normalizeNotifications,safeLabel,refs,model};
  if(typeof module!=='undefined'&&module.exports)module.exports=API;
  if(!doc||root.NANO_OPERATIONS_163)return;
  root.NANO_OPERATIONS_163=API;
  let modal=null,last=null,loading=false,closed=false;
  const mk=(tag,txt,klass)=>{
    const n=doc.createElement(tag);
    if(txt)n.textContent=safeLabel(txt);
    if(klass)n.className=klass;
    return n;
  };
  const style=mk('style');style.textContent=[
    '.nano-op-trigger{border:1px solid #0d9488;background:#ecfdf5;color:#065f46;border-radius:12px;padding:7px 12px;font:bold 12px Arial;cursor:pointer}',
    '.nano-op-overlay{position:fixed;inset:0;z-index:99994;background:rgba(2,6,23,.65);padding:14px;display:flex;align-items:center;justify-content:center;box-sizing:border-box}',
    '.nano-op-dialog{width:min(970px,100%);max-height:92vh;overflow:auto;border-radius:18px;background:#fff;color:#0f172a;padding:18px;box-sizing:border-box;direction:rtl;font-family:Arial,sans-serif}',
    '.nano-op-head{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}',
    '.nano-op-controls{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}',
    '.nano-op-controls button,.nano-op-links button{padding:10px 13px;background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;color:#0f172a;cursor:pointer;font:700 12px Arial}',
    '.nano-op-controls button:disabled{opacity:.5;cursor:wait}',
    '.nano-op-layout{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}',
    '.nano-op-card{border:1px solid #e2e8f0;border-radius:14px;padding:12px;background:#fff}',
    '.nano-op-card h3{font-size:14px;margin:0 0 9px;font-weight:900}',
    '.nano-op-card p,.nano-op-card li{font-size:12px;color:#334155;line-height:1.65}',
    '.nano-op-card ul{padding-inline-start:22px;max-height:250px;overflow:auto}',
    '.nano-op-links{display:flex;flex-wrap:wrap;gap:7px;margin-top:8px}',
    '.nano-op-note{margin:8px 0;font-size:11px;color:#64748b}',
    '.nano-op-trigger:focus-visible,.nano-op-dialog button:focus-visible{outline:3px solid #2563eb;outline-offset:2px}',
    '@media(max-width:550px){.nano-op-dialog{padding:12px}.nano-op-layout{grid-template-columns:1fr}}'
  ].join('\n');
  const openSection=id=>{
    const section=doc.getElementById(id);
    if(!section){return false;}
    // Route through existing application navigation and permissions.
    if(typeof root.navigate!=='function')return false;
    try{root.navigate(id);return true;}catch{return false;}
  };
  async function getProducts(){
    if(typeof root.api?.getProducts!=='function')throw Error('لا يمكن قراءة المنتجات من الكمبيوتر الرئيسي');
    const all=[],seen=new Set;let partial=false;
    for(let page=1;page<=25;page++){
      const r=array(await root.api.getProducts({page,perPage:200}));
      const rows=Array.isArray(r)?r:r.rows;
      let fresh=0;
      for(const item of rows){
        if(!item||typeof item!=='object')continue;
        const id=item.id??item.product_id;
        if(id!=null){const k=String(id);if(seen.has(k))continue;seen.add(k);}
        all.push(item);fresh++;
      }
      const total=Array.isArray(r)?null:r.total;
      if(!rows.length||fresh===0||(total!==null&&all.length>=total)||(total===null&&rows.length<200))break;
      if(page===25)partial=true;
    }
    return {all,partial};
  }
  async function alerts(){
    const items=[];
    try{
      if(typeof root.api?.getNotifications==='function'){
        const r=await root.api.getNotifications();
        for(const n of normalizeNotifications(r))items.push({label:n.title,message:'إشعار من البرنامج',type:n.category});
      }
    }catch{}
    const {all,partial}=await getProducts();
    const summary=model(all,root.NANO_REORDER_162);
    return {items:[...summary.warnings,...items].slice(0,150),summary,partial};
  }
  function renderTarget(host,data){
    host.replaceChildren();
    const totals=mk('p','مخزون منخفض: '+data.summary.low+' | منتهية الصلاحية: '+data.summary.expired+' | قريبة الانتهاء: '+data.summary.expiring,'nano-op-note');
    host.append(totals);
    if(data.partial)host.append(mk('p','النتائج جزئية بعد قراءة 5000 منتج.','nano-op-note'));
    if(!data.items.length){host.append(mk('p','لا توجد تنبيهات ضمن البيانات التي أمكن قراءتها.'));return;}
    const ul=mk('ul');
    for(const item of data.items){
      const li=mk('li');li.append(mk('strong',item.label+' — '));li.append(doc.createTextNode(safeLabel(item.message)));ul.append(li);
    }
    host.append(ul);
  }
  async function refresh(){
    if(!modal||loading)return;
    loading=true;
    const target=modal.querySelector('[data-alerts]'),button=modal.querySelector('[data-refresh]');
    button.disabled=true;target.replaceChildren(mk('p','جارٍ جلب تنبيهات المخزون…'));
    try{const data=await alerts();if(modal&&!closed)renderTarget(target,data);}
    catch(err){if(modal&&!closed)target.replaceChildren(mk('p','تعذر قراءة التنبيهات: '+safeLabel(err?.message||'')));}
    finally{loading=false;if(button)button.disabled=false;}
  }
  function close(){closed=true;if(modal){modal.remove();modal=null;}last?.focus();}
  function open(){
    if(modal)return;
    closed=false;last=doc.activeElement;
    modal=mk('div',null,'nano-op-overlay');
    const dialog=mk('section',null,'nano-op-dialog');
    dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');
    dialog.setAttribute('aria-label','مركز عمليات وتنبيهات نانو بوز');
    const head=mk('div',null,'nano-op-head');
    head.append(mk('h2','مركز العمليات والتنبيهات'));
    const controls=mk('div',null,'nano-op-controls');
    const again=mk('button','تحديث التنبيهات'),exit=mk('button','إغلاق');
    again.type=exit.type='button';again.dataset.refresh='1';
    again.addEventListener('click',refresh);exit.addEventListener('click',close);
    controls.append(again,exit);head.append(controls);dialog.append(head);
    dialog.append(mk('p','العمليات المالية والجرد تستخدم الأقسام الأصلية وصلاحياتها. لا تُنشأ أو تُعدّل أي معاملات من هذا المركز.','nano-op-note'));
    const grid=mk('div',null,'nano-op-layout');
    const a=mk('article',null,'nano-op-card'),b=mk('article',null,'nano-op-card');
    a.append(mk('h3','التنبيهات الموحّدة'));
    const target=mk('div');target.dataset.alerts='1';a.append(target);
    b.append(mk('h3','الأقسام التشغيلية الحالية'));
    const links=mk('div',null,'nano-op-links');
    for(const [id,title,help] of refs){
      if(!doc.getElementById(id))continue;
      const btn=mk('button',title);btn.type='button';btn.title=help;
      btn.addEventListener('click',()=>{if(openSection(id))close();});
      links.append(btn);
    }
    b.append(links);
    b.append(mk('p','إدارة المرتجعات، المناوبات، أسعار الجملة، الجرد والأرباح تتم داخل شاشاتها الحالية. تقارير الأرباح وسجل التدقيق المالي يحتاجان مراجعة محاسبية قبل اعتماد النتائج.','nano-op-note'));
    grid.append(a,b);dialog.append(grid);modal.append(dialog);doc.body.append(modal);
    modal.addEventListener('click',e=>{if(e.target===modal)close();});
    exit.focus();refresh();
  }
  function init(){
    if(doc.getElementById('nanoOperationsOpen'))return;
    const target=doc.getElementById('notificationToggle');
    if(!target)return;
    doc.head.append(style);
    const button=mk('button','مركز العمليات','nano-op-trigger');
    button.id='nanoOperationsOpen';button.type='button';
    target.parentElement?.insertAdjacentElement('afterend',button);
    button.addEventListener('click',open);
    doc.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal)close();});
  }
  if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);
