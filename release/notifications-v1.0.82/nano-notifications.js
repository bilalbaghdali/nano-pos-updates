/* NANO POS v1.0.82 — working, read-only notification center.
   Uses actual inventory API, existing notification dropdown and navigation permissions. */
(function(w){
'use strict';
const d=w.document;if(!d||w.NANO_NOTIFICATIONS_182)return;
const $=id=>d.getElementById(id);
const tr={
 ar:{none:'لا توجد تنبيهات حالياً',loading:'جارٍ تحديث التنبيهات...',error:'تعذر جلب التنبيهات. تحقق من الاتصال بقاعدة البيانات.',out:'نفاد المخزون',low:'مخزون منخفض',expired:'صلاحية منتهية',soon:'صلاحية تقترب',promo:'انتهاء عرض قريب',remains:'الكمية',minimum:'الحد الأدنى',expiry:'تاريخ الصلاحية',end:'ينتهي في',total:'إجمالي التنبيهات',more:'تنبيه آخر غير معروض',reload:'تحديث',partial:'تنبيهات جزئية — تعذر تحميل جميع المنتجات'},
 fr:{none:'Aucune alerte',loading:'Actualisation des alertes…',error:'Impossible de lire les alertes.',out:'Rupture de stock',low:'Stock faible',expired:'Produit périmé',soon:'Expiration proche',promo:'Promotion expire bientôt',remains:'Stock',minimum:'Seuil',expiry:'Date de péremption',end:'Fin le',total:'Alertes',more:'autres alertes',reload:'Actualiser',partial:'Alertes partielles — produits non entièrement chargés'},
 en:{none:'No current alerts',loading:'Refreshing alerts…',error:'Could not load alerts.',out:'Out of stock',low:'Low stock',expired:'Expired',soon:'Expiring soon',promo:'Promotion ending soon',remains:'Stock',minimum:'Minimum',expiry:'Expiry date',end:'Ends',total:'Alerts',more:'additional alerts not shown',reload:'Refresh',partial:'Partial alerts — not all products loaded'}
};
const lang=()=>{const l=String(w.currentLanguage||d.documentElement.lang||'ar').toLowerCase().slice(0,2);return tr[l]||tr.ar;};
const number=v=>v==null||v===''?null:Number.isFinite(Number(v))?Number(v):null;
const value=(p,keys)=>{for(const k of keys){const n=number(p?.[k]);if(n!==null)return n;}return null;};
const isoDay=v=>{const m=/^(\d{4})-(\d{2})-(\d{2})/.exec(String(v||''));if(!m)return null;
 const n=Date.UTC(+m[1],+m[2]-1,+m[3]),z=new Date(n);
 return z.getUTCFullYear()===+m[1]&&z.getUTCMonth()===+m[2]-1&&z.getUTCDate()===+m[3]?n:null;};
const dayDelta=v=>{const n=isoDay(v);if(n===null)return null;const now=new Date();return Math.round((n-Date.UTC(now.getFullYear(),now.getMonth(),now.getDate()))/86400000)};
function normalizeProduct(p){
 const batches=Array.isArray(p.batches)?p.batches:[];
 const stock=value(p,['stock','total_stock','quantity','stock_quantity','current_stock'])??(batches.length?batches.reduce((n,b)=>n+(value(b,['stock','quantity'])||0),0):null);
 const minimum=value(p,['min_stock','minStock','minimum_stock','reorder_point']);
 const expiry=[];
 for(const b of batches){
   if(value(b,['stock','quantity'])!==null&&value(b,['stock','quantity'])<=0)continue;
   const date=b.expiry_date||b.expiration_date||b.expiryDate||b.expirationDate;
   const days=dayDelta(date);if(days!==null)expiry.push({date:String(date).slice(0,10),days});
 }
 if(!expiry.length){
   const date=p.expiry_date||p.expiration_date||p.expiryDate||p.expirationDate;
   const days=dayDelta(date);if(days!==null)expiry.push({date:String(date).slice(0,10),days});
 }
 expiry.sort((a,b)=>a.days-b.days);
 return {id:p.id??p.product_id??null,name:String(p.name||p.product_name||p.title||'—'),barcode:String(p.barcode||p.code||''),stock,minimum,expiry_date:expiry[0]?.date||'',days:expiry[0]?.days??null};
}
function fromProducts(all){
 const records={outOfStock:[],lowStock:[],expired:[],expiringSoon:[],promotionsEnding:[]};
 for(const original of all){
   if(!original||typeof original!=='object')continue;
   const p=normalizeProduct(original);
   if(p.stock!==null&&p.stock<=0)records.outOfStock.push(p);
   else if(p.minimum!==null&&p.minimum>0&&p.stock!==null&&p.stock<p.minimum)records.lowStock.push(p);
   if(p.stock!==null&&p.stock<=0)continue;
   if(p.days!==null&&p.days<0)records.expired.push(p);
   else if(p.days!==null&&p.days<=30)records.expiringSoon.push(p);
 }
 return records;
}
function unwrap(response){
 if(Array.isArray(response))return {rows:response,total:null};
 if(!response||response.success===false)throw Error(response?.error||response?.message||'Inventory unavailable');
 const obj=response.data&&typeof response.data==='object'?response.data:response;
 const rows=['items','products','rows','results'].map(k=>obj[k]).find(Array.isArray);
 if(!rows)throw Error('Unexpected inventory response');
 return {rows,total:number(obj.total??obj.totalCount??obj.count)};
}
async function loadFallback(){
 const method=w.api?.getProducts;if(typeof method!=='function')throw Error('Product API unavailable');
 const seen=new Set(),all=[];let partial=false;
 for(let page=1;page<=100;page++){
   const {rows,total}=unwrap(await method({page,perPage:200}));
   let fresh=0;
   for(const p of rows){
     const id=p?.id??p?.product_id;
     if(id!=null){if(seen.has(String(id)))continue;seen.add(String(id));}
     if(p&&typeof p==='object'){all.push(p);fresh++;}
   }
   if(!rows.length||!fresh||(total!==null&&all.length>=total)||(total===null&&rows.length<200))break;
   if(page===100)partial=true;
 }
 return {...fromProducts(all),partial};
}
async function getRecords(){
 if(typeof w.api?.getNotifications==='function'){
   try{
     const res=await w.api.getNotifications();
     if(res&&!Array.isArray(res)&&Array.isArray(res.outOfStock)&&Array.isArray(res.lowStock)&&Array.isArray(res.expired)&&Array.isArray(res.expiringSoon))return res;
   }catch(e){console.warn('[NANO notifications] Primary source unavailable; reading products',e);}
 }
 return loadFallback();
}
function make(tag,text,className){
 const x=d.createElement(tag);if(text!==undefined)x.textContent=String(text);
 if(className)x.className=className;return x;
}
function navigateTo(item){
 const destination=item.type==='promo'?'promotionsSection':'productsSection';
 if(typeof w.navigate==='function')w.navigate(destination);
 else d.querySelector('[onclick*="navigate(\\''+destination+'\\')"]')?.click();
 const section=$(destination);
 if(!section||section.classList.contains('hidden'))return; // preserve permission checks
 const dropdown=$('notificationsDropdown');
 if(dropdown&&!dropdown.classList.contains('hidden')&&typeof w.toggleNotifications==='function')w.toggleNotifications();
 if(item.type!=='promo'){
   const search=$('inventorySearch');
   if(search){
     search.value=item.barcode||item.name;
     search.dispatchEvent(new w.Event('input',{bubbles:true}));
     search.dispatchEvent(new w.KeyboardEvent('keyup',{bubbles:true,key:'Enter'}));
     if(typeof w.debouncedInventorySearch==='function')w.debouncedInventorySearch();
     search.focus({preventScroll:true});
   }
 }
}
let busy=null,lastRun=0,cached=[],timer=null;
function display(alerts,partial){
 const target=$('notificationsContent'),badge=$('notifBadge');
 if(!target||!badge)return;
 const t=lang();target.replaceChildren();
 badge.replaceChildren();
 if(alerts.length){
   badge.classList.remove('hidden');
   badge.classList.add('nano-alert-count-badge');
   badge.append(make('span',alerts.length>99?'99+':alerts.length,'nano-alert-count'));
   badge.setAttribute('aria-label',t.total+': '+alerts.length);
 }else{
   badge.classList.add('hidden');badge.classList.remove('nano-alert-count-badge');
   badge.removeAttribute('aria-label');
 }
 if(partial)target.append(make('p',t.partial,'nano-alert-partial'));
 if(!alerts.length){target.append(make('p',t.none,'nano-alert-empty'));return;}
 for(const item of alerts.slice(0,60)){
   const btn=make('button',undefined,'nano-alert-item nano-alert-'+item.type);
   btn.type='button';
   btn.append(make('span',item.icon,'material-symbols-outlined nano-alert-symbol'));
   const body=make('span',undefined,'nano-alert-body');
   body.append(make('strong',item.title));
   body.append(make('span',item.desc,'nano-alert-description'));
   btn.append(body);
   btn.addEventListener('click',()=>navigateTo(item));
   target.append(btn);
 }
 if(alerts.length>60)target.append(make('p','+ '+(alerts.length-60)+' '+t.more,'nano-alert-partial'));
}
function prepare(result){
 const t=lang(),out=[];
 const groups=[
  ['outOfStock','out','inventory_2',p=>p.name+' · '+t.remains+': '+(p.stock??0)],
  ['lowStock','low','warning',p=>p.name+' · '+t.remains+': '+p.stock+' · '+t.minimum+': '+p.minimum],
  ['expired','expired','event_busy',p=>p.name+' · '+t.expiry+': '+(p.expiry_date||'—')],
  ['expiringSoon','soon','event',p=>p.name+' · '+t.expiry+': '+(p.expiry_date||'—')],
  ['promotionsEnding','promo','sell',p=>p.name+' · '+t.end+': '+(p.end_date||'—')]
 ];
 for(const [key,type,icon,description] of groups){
   for(const rec of Array.isArray(result[key])?result[key]:[]){
     out.push({type,icon,title:t[type],desc:description(rec),
       barcode:String(rec.barcode||''),name:String(rec.name||'—'),id:rec.id??null});
   }
 }
 return out;
}
async function refresh(force=false){
 if(busy)return busy;
 if(!force&&Date.now()-lastRun<1500)return cached;
 busy=(async()=>{
   const list=$('notificationsContent');
   if(list&&!cached.length)list.replaceChildren(make('p',lang().loading,'nano-alert-empty'));
   try{
     const data=await getRecords();
     cached=prepare(data);
     display(cached,!!data.partial);lastRun=Date.now();
     return cached;
   }catch(error){
     console.error('[NANO notifications] Refresh failed',error);
     if(list)list.replaceChildren(make('p',lang().error,'nano-alert-error'));
     return cached;
   }finally{busy=null;}
 })();
 return busy;
}
function queue(){
 if(timer)clearTimeout(timer);
 timer=setTimeout(()=>{timer=null;refresh(true);},350);
}
function initialize(){
 if(!$('notificationToggle')||!$('notificationsContent'))return;
 const button=$('notificationToggle');
 button.setAttribute('aria-label',tr.ar.total);
 w.addEventListener('nano-pos-data-saved',queue);
 w.addEventListener('nano-pc-sync-snapshot-applied',queue);
 w.addEventListener('nano-inventory-changed',queue);
 d.addEventListener('visibilitychange',()=>{if(!d.hidden)queue();});
 w.addEventListener('focus',queue);
 setInterval(()=>{if(!d.hidden)queue();},60000);
 button.addEventListener('click',()=>refresh(true));
 const dropdown=$('notificationsDropdown');
 dropdown?.querySelector('button[onclick*="fetchNotifications"]')?.addEventListener('click',()=>refresh(true));
 setTimeout(()=>refresh(true),1500);
}
w.NANO_NOTIFICATIONS_182={refresh,queue,fromProducts,prepare,normalizeProduct};
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',initialize,{once:true});
else initialize();
})(typeof window!=='undefined'?window:globalThis);