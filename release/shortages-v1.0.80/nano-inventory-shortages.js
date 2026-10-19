/* NANO POS v1.0.80 — visible inventory shortages, printable and shareable restock draft.
 * Inventory read-only. Does not create purchase invoices, alter stock, or send automatically. */
(function(root){
'use strict';
const doc=root.document;
if(!doc||root.NANO_INVENTORY_SHORTAGES_180)return;
root.NANO_INVENTORY_SHORTAGES_180=true;
const ID='nanoShortageModal180';
const languages={
 ar:{button:'المنتجات الناقصة',title:'اقتراح شراء المنتجات الناقصة',hint:'قائمة اقتراحية لا تعدّل المخزون ولا تنشئ فاتورة شراء. راجع الكميات قبل الطلب.',refresh:'تحديث القائمة',print:'طباعة القائمة',send:'إرسال القائمة',csv:'تنزيل CSV',copy:'نسخ القائمة',mail:'إرسال بالبريد',whatsapp:'إرسال عبر واتساب',close:'إغلاق',loading:'جارٍ تحميل المنتجات…',empty:'لا توجد منتجات ناقصة حسب الكميات المسجلة.',error:'تعذّر جلب المنتجات: ',partial:'تنبيه: القائمة جزئية بسبب الحد الأقصى للمنتجات المقروءة.',count:'المنتجات التي تحتاج تموينًا',product:'المنتج',barcode:'الباركود',stock:'المخزون الحالي',minimum:'الحد الأدنى',suggest:'الكمية المقترحة',status:'الحالة',out:'نفد المخزون',low:'كمية منخفضة',noMinimum:'لا يوجد حد أدنى محدد',copied:'تم نسخ القائمة ويمكن إرسالها.',copyFail:'تعذّر نسخ القائمة. يمكن تنزيل ملف CSV.',sendHint:'لإرسال القائمة كاملة استخدم مشاركة النظام إن توفرت، أو نزّل CSV وأرفقه. قد تقتصر رسائل واتساب والبريد على جزء من القائمة.',shared:'تم فتح مشاركة النظام.',sendError:'تعذّرت المشاركة، استخدم النسخ أو تنزيل CSV.',limited:'الرسالة طويلة؛ تم نسخ القائمة كاملة والرسالة تحتوي ملخصًا فقط.',date:'تاريخ التقرير'},
 fr:{button:'Articles à réapprovisionner',title:'Suggestions de réapprovisionnement',hint:'Liste indicative seulement. Aucun stock ou bon de commande ne sera modifié.',refresh:'Actualiser',print:'Imprimer',send:'Partager',csv:'Exporter CSV',copy:'Copier la liste',mail:'Envoyer par e-mail',whatsapp:'Envoyer par WhatsApp',close:'Fermer',loading:'Chargement des produits…',empty:'Aucun manque selon les stocks enregistrés.',error:'Erreur de chargement : ',partial:'Attention : liste partielle.',count:'Articles à réapprovisionner',product:'Produit',barcode:'Code-barres',stock:'Stock actuel',minimum:'Stock minimum',suggest:'Quantité suggérée',status:'Statut',out:'Rupture',low:'Stock bas',noMinimum:'Seuil non défini',copied:'Liste copiée.',copyFail:'Copie impossible ; exportez le CSV.',sendHint:'Pour envoyer la liste complète, joignez le CSV ou utilisez le partage système.',shared:'Partage lancé.',sendError:'Échec de partage.',limited:'Message abrégé, liste complète copiée.',date:'Date du rapport'},
 en:{button:'Low-stock suggestions',title:'Suggested restock list',hint:'Suggestions only; no stock or purchase records will change.',refresh:'Refresh',print:'Print list',send:'Send list',csv:'Download CSV',copy:'Copy list',mail:'Send by email',whatsapp:'Send via WhatsApp',close:'Close',loading:'Loading products…',empty:'No shortages were found in recorded inventory.',error:'Could not load products: ',partial:'Warning: this list is incomplete.',count:'Items needing restock',product:'Product',barcode:'Barcode',stock:'Current stock',minimum:'Minimum stock',suggest:'Suggested quantity',status:'Status',out:'Out of stock',low:'Low stock',noMinimum:'No minimum specified',copied:'Full list copied.',copyFail:'Copy failed; download the CSV instead.',sendHint:'For complete delivery, attach the exported CSV or use system sharing.',shared:'System share started.',sendError:'Sharing unavailable.',limited:'Full list copied; message was shortened.',date:'Report date'}
};
const L=()=>{let l=String(root.currentLanguage||doc.documentElement.lang||'ar').toLowerCase().slice(0,2);return languages[l]||languages.ar;};
const byId=id=>doc.getElementById(id);
const safeNumber=n=>n==null||n===''?null:typeof n==='number'&&Number.isFinite(n)?n:Number.isFinite(Number(n))?Number(n):null;
const dateStr=()=>new Date().toLocaleString(root.currentLanguage||doc.documentElement.lang||'ar');
const escapeCSV=v=>'"'+String(v??'').replace(/"/g,'""').replace(/\r?\n/g,' ')+'"';
const formatQty=x=>x==null?'—':new Intl.NumberFormat('fr-DZ',{maximumFractionDigits:2}).format(x);
let data=[],partial=false,loading=false;
const el=(tag,text='',className='')=>{const n=doc.createElement(tag);if(text)n.textContent=text;if(className)n.className=className;return n;};
const notify=(message,kind='info')=>{if(typeof root.showToast==='function')root.showToast(message,kind);else {const t=byId('nanoShortageNotice180');if(t)t.textContent=message;}};
function parseResponse(value){
 if(Array.isArray(value))return {items:value,total:null};
 if(!value||value.success===false)throw Error(value?.message||'Invalid inventory response');
 const obj=value.data&&typeof value.data==='object'?value.data:value;
 const items=['items','products','rows','results'].map(key=>obj[key]).find(Array.isArray);
 if(!items)throw Error('Unexpected inventory response');
 return {items,total:safeNumber(obj.total??obj.totalCount??obj.count)};
}
async function fetchInventory(){
 if(typeof root.api?.getProducts!=='function')throw Error('Product service is unavailable');
 const all=[],seen=new Set();let incomplete=false;
 for(let page=1;page<=100;page++){
   const {items,total}=parseResponse(await root.api.getProducts({page,perPage:200}));
   let added=0;
   for(const product of items){
     if(!product||typeof product!=='object')continue;
     const id=product.id??product.product_id;
     if(id!=null){const key=String(id);if(seen.has(key))continue;seen.add(key);}
     all.push(product);added++;
   }
   if(items.length===0||added===0||(total!=null&&all.length>=total)||(total==null&&items.length<200))break;
   if(page===100)incomplete=true;
 }
 return {all,incomplete};
}
function suggest(product){
 const helper=root.NANO_REORDER_162;
 if(!helper?.stock||!helper?.num)return null;
 const qty=helper.stock(product);
 if(qty===null||!Number.isFinite(qty))return null;
 const minKeys=['min_stock','minStock','minimum_stock','reorder_point'];
 let minimum=null;
 for(const key of minKeys){const n=helper.num(product[key]);if(n!=null){minimum=n;break;}}
 const depleted=qty<=0,low=minimum>0&&qty<minimum;
 if(!depleted&&!low)return null;
 // When the product has no configured reorder threshold, suggest just one unit.
 // With a configured threshold, suggest restoring a 50%-above-minimum buffer.
 const target=minimum>0?Math.ceil(minimum*1.5*100)/100:1;
 const recommended=Math.max(0,Math.ceil((target-qty)*100)/100);
 return {name:String(product.name||product.product_name||product.title||'').trim()||'—',
    barcode:String(product.barcode||product.code||'').trim(),qty,minimum,order:recommended,depleted};
}
function buildRows(all){
 return all.map(suggest).filter(Boolean).sort((a,b)=>Number(b.depleted)-Number(a.depleted)||a.qty-b.qty||a.name.localeCompare(b.name));
}
function textual(max=Infinity){
 const t=L();
 const header=[t.title,t.date+': '+dateStr(),t.count+': '+data.length,''];
 const cols=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status].join(' | ');
 const lines=data.slice(0,max).map((p,i)=>[i+1,p.name,p.barcode||'—',formatQty(p.qty),
   p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low].join(' | '));
 return [...header,cols,...lines].join('\n');
}
function csvText(){
 const t=L();
 const fields=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status];
 const rows=data.map(p=>[p.name,p.barcode,p.qty,p.minimum??'',p.order,p.depleted?t.out:t.low]);
 return '\uFEFF'+[fields,...rows].map(row=>row.map(escapeCSV).join(';')).join('\r\n')+'\r\n';
}
function downloadCSV(){
 if(!data.length)return;
 const blob=new Blob([csvText()],{type:'text/csv;charset=utf-8'});
 const href=URL.createObjectURL(blob);
 const a=el('a');a.href=href;a.download='NANO-POS-LOW-STOCK-'+new Date().toISOString().slice(0,10)+'.csv';
 doc.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(href),1500);
}
async function copyList(){
 try{
   const content=textual();
   if(root.navigator?.clipboard?.writeText)await root.navigator.clipboard.writeText(content);
   else {
     const area=el('textarea');area.value=content;area.style.position='fixed';area.style.left='-9999px';
     doc.body.append(area);area.select();
     const success=doc.execCommand?.('copy');area.remove();if(!success)throw Error('clipboard unavailable');
   }
   notify(L().copied,'success');return true;
 }catch{notify(L().copyFail,'warning');return false;}
}
function openTrusted(url){
 if(!/^https:\/\/wa\.me\/\?text=|^mailto:/i.test(url))return false;
 try{
   const open=root.nanoNative?.openExternal;
   if(typeof open==='function'){Promise.resolve(open(url)).catch(()=>root.open?.(url,'_blank','noopener'));return true;}
   if(url.startsWith('mailto:')){root.location.href=url;return true;}
   root.open?.(url,'_blank','noopener');return true;
 }catch{return false;}
}
async function send(kind){
 if(!data.length)return;
 const t=L();
 if(kind==='copy'){await copyList();return;}
 if(kind==='csv'){downloadCSV();return;}
 const full=textual(),short=textual(20),text=full.length>1800?short+'\n… ('+data.length+')':full;
 // For many products, copy full list before launching a message limited to a summary.
 if(full.length>1800){await copyList();notify(t.limited,'info');}
 const title=t.title;
 if(kind==='whatsapp'){openTrusted('https://wa.me/?text='+encodeURIComponent(text));return;}
 if(kind==='mail'){openTrusted('mailto:?subject='+encodeURIComponent(title)+'&body='+encodeURIComponent(text));return;}
 if(kind==='system'&&root.navigator?.share){
   try{
     const file=new File([csvText()],'NANO-POS-LOW-STOCK.csv',{type:'text/csv'});
     if(root.navigator.canShare?.({files:[file]}))await root.navigator.share({title,files:[file],text:t.hint});
     else await root.navigator.share({title,text:full.slice(0,5000)});
     notify(t.shared,'success');return;
   }catch(err){if(err?.name==='AbortError')return;}
 }
 notify(t.sendError,'warning');
}
function printList(){
 if(!data.length)return;
 const t=L();
 const frame=doc.createElement('iframe');frame.setAttribute('title',t.title);
 frame.style.cssText='position:fixed;width:0;height:0;border:0;opacity:0;pointer-events:none;';
 doc.body.append(frame);
 const other=frame.contentDocument;
 if(!other){frame.remove();notify(t.sendError,'warning');return;}
 other.open();other.write('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>Inventory shortages</title>'+
   '<style>body{font:13px Arial,sans-serif;color:#132b2b;margin:20px}h1{font-size:21px}p{color:#475569}table{border-collapse:collapse;width:100%;direction:rtl}th,td{border:1px solid #a9b8b0;padding:7px;text-align:right;vertical-align:top}th{background:#e7f0e8}tr{break-inside:avoid}thead{display:table-header-group}@page{size:A4 landscape;margin:12mm}</style></head><body></body></html>');
 other.close();
 const body=other.body;
 for(const [tag,value] of [['h1',t.title],['p',t.date+': '+dateStr()+' · '+t.count+': '+data.length],['p',t.hint]]){
    const node=other.createElement(tag);node.textContent=value;body.append(node);
 }
 const table=other.createElement('table'),thead=other.createElement('thead'),tr=other.createElement('tr');
 for(const s of [t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status]){
   const th=other.createElement('th');th.textContent=s;tr.append(th);
 }thead.append(tr);table.append(thead);
 const tbody=other.createElement('tbody');
 for(const p of data){
   const tr=other.createElement('tr');
   for(const v of [p.name,p.barcode||'—',formatQty(p.qty),p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low]){
     const td=other.createElement('td');td.textContent=v;tr.append(td);
   }tbody.append(tr);
 }
 table.append(tbody);body.append(table);
 const popup=frame.contentWindow;
 const cleanup=()=>setTimeout(()=>frame.remove(),1200);
 popup.addEventListener('afterprint',cleanup,{once:true});
 setTimeout(()=>{try{popup.focus();popup.print();}catch(e){notify(t.sendError,'warning');cleanup();}},150);
 setTimeout(()=>{if(frame.isConnected)frame.remove();},60000);
}
let modal=null;
function draw(){
 const content=byId('nanoShortageRows180');if(!content)return;
 const t=L();content.replaceChildren();
 byId('nanoShortageCount180').textContent=t.count+': '+data.length;
 byId('nanoShortageHint180').textContent=t.hint;
 byId('nanoShortageNotice180').textContent=partial?t.partial:'';
 const headings=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status];
 const head=byId('nanoShortageHead180');head.replaceChildren();
 for(const label of headings)head.append(el('th',label));
 if(!data.length){
    const row=el('tr'),td=el('td',t.empty);td.colSpan=6;row.append(td);content.append(row);
 }else for(const p of data){
    const row=el('tr');if(p.depleted)row.classList.add('nano-shortage-empty');
    for(const value of [p.name,p.barcode||'—',formatQty(p.qty),
       p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low])
       row.append(el('td',value));
    content.append(row);
 }
 for(const name of ['nanoShortagePrint180','nanoShortageSend180','nanoShortageCSV180'])
    byId(name).disabled=!data.length;
}
async function refresh(){
 if(loading||!modal)return;loading=true;
 const refreshBtn=byId('nanoShortageRefresh180');refreshBtn.disabled=true;
 byId('nanoShortageNotice180').textContent=L().loading;
 try{const result=await fetchInventory();data=buildRows(result.all);partial=result.incomplete;draw();}
 catch(e){data=[];draw();byId('nanoShortageNotice180').textContent=L().error+(e?.message||'');}
 finally{loading=false;refreshBtn.disabled=false;}
}
function close(){if(modal){modal.remove();modal=null;byId('nanoShortageOpen180')?.focus();}}
function open(){
 if(modal){modal.focus();return;}
 const t=L(),overlay=el('div','','nano-shortage-overlay');overlay.id=ID;
 const box=el('section','','nano-shortage-dialog');box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label',t.title);box.tabIndex=-1;
 const h=el('header','','nano-shortage-header'),heading=el('h2',t.title);
 const actions=el('div','','nano-shortage-actions');
 const make=(id,label,action)=>{const b=el('button',label);b.type='button';b.id=id;b.addEventListener('click',action);return b};
 actions.append(make('nanoShortageRefresh180',t.refresh,refresh),make('nanoShortagePrint180',t.print,printList));
 const sendBtn=make('nanoShortageSend180',t.send,()=>byId('nanoShortageShareMenu180').hidden=!byId('nanoShortageShareMenu180').hidden);
 actions.append(sendBtn,make('nanoShortageCSV180',t.csv,downloadCSV),make('nanoShortageClose180',t.close,close));
 h.append(heading,actions);box.append(h);
 const share=el('div','','nano-shortage-share');share.id='nanoShortageShareMenu180';share.hidden=true;
 for(const [key,label] of [['system',t.send],['whatsapp',t.whatsapp],['mail',t.mail],['copy',t.copy],['csv',t.csv]])
    share.append(make('nanoShortageShare'+key,label,()=>send(key)));
 share.append(el('p',t.sendHint));box.append(share);
 const counter=el('p','','nano-shortage-count');counter.id='nanoShortageCount180';box.append(counter);
 const hint=el('p',t.hint,'nano-shortage-hint');hint.id='nanoShortageHint180';box.append(hint);
 const notice=el('p',t.loading,'nano-shortage-notice');notice.id='nanoShortageNotice180';notice.setAttribute('role','status');box.append(notice);
 const scroll=el('div','','nano-shortage-scroll'),table=el('table','','nano-shortage-table'),thead=el('thead');
 const tr=el('tr');tr.id='nanoShortageHead180';thead.append(tr);table.append(thead);
 const tbody=el('tbody');tbody.id='nanoShortageRows180';table.append(tbody);scroll.append(table);box.append(scroll);
 overlay.append(box);doc.body.append(overlay);modal=overlay;overlay.addEventListener('click',event=>{if(event.target===overlay)close();});box.focus();refresh();
}
function init(){
 const section=byId('productsSection');
 if(!section)return;
 // The legacy 1.0.62 helper appends a button at the bottom of the inventory section:
 // remove only that redundant entry; keep its stock classifier and business API intact.
 const old=byId('nanoRestockAssistantBtn');if(old)old.remove();
 if(byId('nanoShortageOpen180'))return;
 const heading=section.querySelector('h2[data-i18n="inventory_management_title"]');
 const header=heading?.parentElement;
 const actions=header?.querySelector('div');
 const button=el('button','','nano-shortage-open');
 button.id='nanoShortageOpen180';button.type='button';
 const icon=el('span','inventory_2','material-symbols-outlined'),label=el('span',L().button);
 button.append(icon,label);
 (actions||header||section).append(button);button.addEventListener('click',open);
 doc.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal){e.stopPropagation();close();}});
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);