/* NANO POS v1.0.100: review shortages, choose known supplier automatically, create one PO per supplier.
   No purchase orders are saved until the user explicitly confirms; no stock/debt postings. */
(function(win){
 'use strict';
 if(!win.document||win.NANO_PO_SHORTAGE_100)return;
 const doc=win.document,model=()=>win.NANO_PO_AUTO_SUPPLIER_100;
 const api={open};win.NANO_PO_SHORTAGE_100=api;
 const text={
  ar:{title:'أوامر شراء من المخزون الناقص',hint:'يختار البرنامج المورد من إعداد المنتج أو أقل سعر شراء حديث معروف، ثم يجمع المنتجات حسب المورد. راجع الاختيارات قبل الإنشاء. أوامر الشراء لا تغيّر المخزون أو ديون الموردين.',supplier:'المورد المقترح',qty:'الكمية المقترحة',cost:'آخر سعر شراء / تكلفة الوحدة',product:'المنتج',reason:'أساس الاختيار',create:'إنشاء أوامر الشراء المعتمدة',close:'إغلاق',loading:'تحليل الموردين وسجل الشراء…',ready:'جاهز للمراجعة',missing:'اختر موردًا وسعرًا صالحًا للمنتجات غير المحددة قبل الإنشاء.',covered:'مغطى بأمر شراء سابق',none:'لا توجد منتجات تحتاج طلبًا جديدًا.',done:'تم إنشاء أمر شراء للمورد',failed:'تعذّر إنشاء الطلب',check:'تحديد',all:'كل المنتجات',warning:'المورد غير مؤكد تلقائيًا؛ اختره يدويًا',finish:'اكتمل إنشاء الأوامر المختارة.',confirm:'يجب مراجعة الأوامر قبل إنشائها.',configured_supplier:'المورد المحدد للمنتج',recent_lowest_purchase_price:'أقل سعر شراء خلال سنة',last_known_supplier:'آخر أسعار شراء مسجلة',needs_supplier:'لا يوجد مورد معروف'},
  fr:{title:'Commandes depuis les ruptures',hint:'Fournisseur proposé selon la fiche article ou le meilleur prix d’achat récent. Vérifiez avant validation. Aucune modification de stock.',supplier:'Fournisseur',qty:'Quantité',cost:'Coût unitaire',product:'Produit',reason:'Sélection',create:'Créer les commandes',close:'Fermer',loading:'Analyse des achats…',ready:'À vérifier',missing:'Choisissez un fournisseur et un prix valide.',covered:'Déjà commandé',none:'Aucun article à commander.',done:'Bon créé pour',failed:'Création impossible',check:'Sélection',all:'Tous les produits',warning:'Fournisseur à sélectionner',finish:'Commandes créées.',confirm:'Vérifiez avant de valider.',configured_supplier:'Fournisseur du produit',recent_lowest_purchase_price:'Prix récent le plus bas',last_known_supplier:'Dernier fournisseur connu',needs_supplier:'Fournisseur inconnu'},
  en:{title:'Purchase orders from low stock',hint:'Suppliers are suggested from product assignments or recent lowest purchase prices. Review before creating. Orders do not post stock or debt.',supplier:'Suggested supplier',qty:'Quantity',cost:'Unit cost',product:'Product',reason:'Why selected',create:'Create reviewed purchase orders',close:'Close',loading:'Checking suppliers and purchase history…',ready:'Review required',missing:'Choose valid supplier and unit cost.',covered:'Already covered by open order',none:'No new orders needed.',done:'Created order for',failed:'Failed to create',check:'Selected',all:'All products',warning:'Supplier unknown — choose manually',finish:'Purchase orders created.',confirm:'Review orders before creating.',configured_supplier:'Product supplier',recent_lowest_purchase_price:'Recent lowest price',last_known_supplier:'Historical supplier',needs_supplier:'No known supplier'}
 };
 const t=()=>text[String(win.currentLanguage||doc.documentElement.lang||'ar').toLowerCase().slice(0,2)]||text.ar;
 const node=(tag,label)=>{const x=doc.createElement(tag);if(label!==undefined)x.textContent=String(label);return x;};
 const rpc=async(name)=>{const bridge=win.__browserElectron?.ipcRenderer?.invoke;if(typeof bridge!=='function')throw Error('purchase_service_unavailable');return bridge(name);};
 const newId=()=>('po-shortage-'+(win.crypto?.randomUUID?.()||Date.now().toString(36)+'-'+Math.random().toString(36).slice(2)));
 let popup=null,entries=[],suppliers=[],pending=null,busy=false,completed=new Set();
 function status(s,isError=false){const el=doc.getElementById('nanoPoShortageStatus100');if(el){el.textContent=s;el.style.color=isError?'#b91c1c':'#0f766e';}}
 function dropdown(selected){
  const select=node('select');select.style.cssText='min-width:140px;max-width:185px;padding:6px;border:1px solid #94a3b8;border-radius:8px';
  const unknown=node('option',t().warning);unknown.value='';select.append(unknown);
  for(const supplier of suppliers){
    const o=node('option',supplier.name||supplier.company_name||supplier.id);
    o.value=String(supplier.id);select.append(o);
  }
  select.value=String(selected||'');return select;
 }
 function input(value,step){
  const item=node('input');item.type='number';item.step=step;
  item.min=step==='0.001'?'0.001':'0.01';item.value=value===null||value===undefined?'':String(value);
  item.style.cssText='max-width:108px;width:100%;border:1px solid #94a3b8;border-radius:8px;padding:6px';
  return item;
 }
 function render(){
  const content=doc.getElementById('nanoPoShortageRows100');if(!content)return;content.replaceChildren();
  const nonSkipped=entries.filter(x=>!x.skip);
  if(!nonSkipped.length){content.append(node('p',t().none));return;}
  for(const entry of nonSkipped){
   const row=node('div');row.style.cssText='display:grid;grid-template-columns:minmax(115px,2fr) minmax(150px,1.6fr) minmax(85px,1fr) minmax(95px,1fr);gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid #e2e8f0';
   const item=node('div'),check=node('input');check.type='checkbox';check.checked=true;
   const label=node('span',entry.name+(entry.barcode?' ('+entry.barcode+')':''));
   item.style.cssText='display:flex;gap:7px;align-items:center;flex-wrap:wrap';item.append(check,label);
   if(entry.pending) item.append(node('small',' · '+t().covered+': '+entry.pending));
   const sel=dropdown(entry.supplierId),quantity=input(entry.quantity,'0.001'),cost=input(entry.unitCost,'0.01');
   const explanation=node('small',t()[entry.reason]||entry.reason);
   explanation.style.cssText='color:#64748b;display:block;min-width:100%';
   const vendor=node('div');vendor.append(sel,explanation);
   if(!entry.supplierId)vendor.style.borderLeft='2px solid #d97706';
   check.addEventListener('change',()=>{entry.checked=check.checked;pending=null;});
   sel.addEventListener('change',()=>{entry.supplierId=sel.value;entry.checked=check.checked;entry.reason='configured_supplier';pending=null;});
   quantity.addEventListener('input',()=>{entry.quantity=quantity.value;pending=null;});
   cost.addEventListener('input',()=>{entry.unitCost=cost.value;pending=null;});
   entry.checked=true;
   row.append(item,vendor,quantity,cost);content.append(row);
  }
 }
 function currentRows(){
  const filtered=entries.filter(x=>!x.skip&&x.checked&&!completed.has(x.productId));
  for(const r of filtered){
   if(!suppliers.some(s=>String(s.id)===String(r.supplierId)))throw Error(t().missing+' '+r.name);
   const qty=String(r.quantity||''),cost=String(r.unitCost??'');
   if(!/^\d+(?:\.\d{1,3})?$/.test(qty)||Number(qty)<=0||
      !/^\d+(?:\.\d{1,2})?$/.test(cost)||Number(cost)<=0)throw Error(t().missing+' '+r.name);
  }
  return filtered;
 }
 function prepare(){
  const grouped=new Map();
  for(const r of currentRows()){
    const id=String(r.supplierId);
    if(!grouped.has(id))grouped.set(id,[]);
    grouped.get(id).push({productId:r.productId,quantity:String(r.quantity),
      unitCost:String(r.unitCost)});
  }
  return [...grouped].map(([supplierId,lines])=>({
    supplierId,lines,operationId:newId(),done:false}));
 }
 async function save(){
  if(busy)return;
  try{
    if(pending===null)pending=prepare();
    if(!pending.length){status(t().none);return;}
    busy=true;
    const btn=doc.getElementById('nanoPoShortageSave100');btn.disabled=true;
    for(const request of pending){
      if(request.done)continue;
      try{
        const result=await win.__browserElectron.ipcRenderer.invoke('create-purchase-order',{
          supplierId:request.supplierId,operationId:request.operationId,lines:request.lines});
        if(!result||result.success===false)throw Error(result?.message||result?.error||t().failed);
        request.done=true;
        for(const line of request.lines)completed.add(String(line.productId));
        const supplier=suppliers.find(s=>String(s.id)===request.supplierId);
        status(t().done+' '+(supplier?.name||request.supplierId)+': '+result.id);
      }catch(error){
        // Stable operationId and unchanged payload for safe retry if the result was lost.
        status(t().failed+' ['+request.supplierId+']: '+error.message,true);
        return;
      }
    }
    status(t().finish);
  }catch(error){status(error.message,true);}
  finally{
    busy=false;
    const btn=doc.getElementById('nanoPoShortageSave100');if(btn)btn.disabled=false;
  }
 }
 function close(){if(popup){popup.remove();popup=null;entries=[];pending=null;completed.clear();}}
 async function open(rows){
  if(popup){popup.focus();return;}
  if(!Array.isArray(rows)||!rows.length)return;
  const overlay=node('div');overlay.id='nanoPoShortageOverlay100';
  overlay.style.cssText='position:fixed;inset:0;z-index:200100;background:rgba(15,23,42,.76);display:flex;align-items:center;justify-content:center;padding:12px;direction:rtl';
  const card=node('section');card.style.cssText='width:min(1040px,100%);max-height:95vh;overflow:auto;border-radius:15px;background:#fff;color:#0f172a;padding:18px';
  const head=node('div');head.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:10px';
  head.append(node('h2',t().title));
  const exit=node('button',t().close);exit.type='button';exit.addEventListener('click',close);head.append(exit);card.append(head);
  card.append(node('p',t().hint));
  const labels=node('p',t().product+'   |   '+t().supplier+'   |   '+t().qty+'   |   '+t().cost);
  labels.style.cssText='font-weight:bold;color:#475569';card.append(labels);
  const table=node('div');table.id='nanoPoShortageRows100';card.append(table);
  const submit=node('button',t().create);submit.type='button';submit.id='nanoPoShortageSave100';
  submit.style.cssText='background:#0369a1;color:white;border-radius:9px;padding:10px 18px;margin:14px 0;font-weight:bold';
  submit.disabled=true;submit.addEventListener('click',save);card.append(submit);
  const notice=node('p',t().loading);notice.id='nanoPoShortageStatus100';notice.setAttribute('role','status');card.append(notice);
  overlay.append(card);doc.body.append(overlay);popup=overlay;
  try{
    const values=await Promise.all(['get-suppliers','get-purchases','get-purchase-orders'].map(rpc));
    if(!popup||!overlay.isConnected)return;
    suppliers=Array.isArray(values[0])?values[0]:[];
    const plan=model()?.build(rows,suppliers,Array.isArray(values[1])?values[1]:[],
      Array.isArray(values[2])?values[2]:[]);
    if(!plan)throw Error('supplier_matching_unavailable');
    entries=plan.items;
    render();
    submit.disabled=!entries.some(x=>!x.skip);
    status(t().ready+': '+plan.ready+' · '+t().warning+': '+plan.needsReview+' · '+t().covered+': '+plan.skipped);
  }catch(error){
    submit.disabled=true;status(error.message,true);
  }
 }
})(typeof window!=='undefined'?window:globalThis);
