/* NANO POS Multi-Commerce phase 1: authoritative per-store activity configuration.
 * No product, stock, sales, invoice or activation migrations in this release.
 */
(()=>{'use strict';
const KEY='nano_commerce_profile_v1';
const sectors=[
 ['grocery','shopping_basket','المواد الغذائية','الميزان • الكغ والغرام','kg,g,piece','expiry,batch,weighted_barcode'],
 ['electronics','devices','الهواتف والإلكترونيات','IMEI • الأرقام التسلسلية والضمان','piece','imei,serial,warranty'],
 ['fashion','checkroom','الملابس والأحذية','المقاسات • الألوان','piece','size,color,sku'],
 ['beauty','spa','العطور والتجميل','الملليلتر • أحجام التعبئة','ml,l,piece','volume,batch,expiry'],
 ['hardware','hardware','الخردوات والعقاقير','المتر • الكغ • القطعة','m,cm,kg,piece','dimensions,length'],
 ['parts','build','قطع الغيار','Reference • OEM • التوافق','piece','reference,oem,vehicle_model'],
 ['cars','directions_car','بيع السيارات','VIN • بيانات المركبة • التقسيط','vehicle','vin,make,model,year,installments'],
 ['mixed','storefront','تجارة متعددة','منتجات من أكثر من قطاع','piece,kg,g,ml,l,m,cm','activity_per_product']
];
const d=document,$=id=>d.getElementById(id);
let profile=null, busy=false, lastHome=false, ready=false, dismissed=false, pending=false, seq=0;
const selected=new Set();
const logged=()=>{const overlay=$('loginOverlay');if(overlay&&!overlay.classList.contains('hidden')&&getComputedStyle(overlay).display!=='none')return false;let u;try{u=JSON.parse(localStorage.getItem('pos_current_user')||'null')}catch{};return !!(u&&u.id!=null)};
const admin=()=>{let u;try{u=JSON.parse(localStorage.getItem('pos_current_user')||'null')}catch{}return !!u&&u.role==='Admin'};
const homeVisible=()=>{const e=$('nanoHomeSection');return !!e&&!e.classList.contains('hidden')&&getComputedStyle(e).display!=='none'&&logged()};
const icon=name=>{const s=d.createElement('span');s.className='material-symbols-outlined';s.textContent=name;return s};
const valid=p=>!!p&&p.schema===1&&sectors.some(x=>x[0]===p.primary)&&Array.isArray(p.activities)&&p.activities.includes(p.primary);
const parse=v=>{try{const p=JSON.parse(v||'');return valid(p)?p:null}catch{return null}};
async function fetchProfile(){if(!window.api?.getSettings)throw Error('خدمة إعدادات المتجر غير متوفرة');const values=await window.api.getSettings();return parse(values?.[KEY])}
function status(s){const el=$('nanoCommerceStatus');if(el)el.textContent=s||''}
function label(){const e=$('nanoCommerceChoice');if(e){const sector=sectors.find(s=>s[0]===profile?.primary);e.textContent=sector?'النشاط: '+sector[2]:'تحديد النشاط التجاري'}}
function build(){if($('nanoCommerceOverlay'))return;
const hero=$('nanoHomeSection')?.querySelector('.nano-home-hero-copy');
if(hero){const control=d.createElement('div');control.className='nano-commerce-home-choice';const tag=d.createElement('span');tag.id='nanoCommerceChoice';tag.textContent='النشاط التجاري';control.append(tag);const btn=d.createElement('button');btn.id='nanoCommerceChange';btn.type='button';btn.append(icon('edit_square'),d.createTextNode(' تغيير النشاط'));btn.addEventListener('click',()=>open());control.append(btn);hero.append(control)}
const backdrop=d.createElement('div');backdrop.id='nanoCommerceOverlay';backdrop.className='nano-commerce-shade';backdrop.hidden=true;backdrop.dir='rtl';backdrop.innerHTML='<div class="nano-commerce-dialog" role="dialog" aria-modal="true" aria-labelledby="nanoCommerceTitle"><div class="nano-commerce-head"><div><div class="nano-commerce-eyebrow">NANO POS · MULTI-COMMERCE</div><h2 id="nanoCommerceTitle">اختر نشاط متجرك</h2><p>مرة واحدة عند الإعداد الأول، وبعدها تدخل مباشرة إلى لوحة التحكم. يمكن للمدير تغيير النشاط لاحقًا.</p></div><span class="material-symbols-outlined">storefront</span></div><div class="nano-commerce-tiles" id="nanoCommerceTiles" role="radiogroup" aria-label="أنشطة المتجر"></div><div class="nano-commerce-notice"><b>المرحلة التأسيسية:</b> يتم حفظ إعداد النشاط والوحدات والحقول المقترحة فقط؛ البيع والمخزون والفواتير تعمل بالنظام الحالي حتى تفعيل وحدات كل قطاع بعد اختبارها.</div><div id="nanoCommerceStatus" role="status" aria-live="polite"></div><div class="nano-commerce-actions"><button type="button" id="nanoCommerceCancel">لاحقًا</button><button type="button" id="nanoCommerceSave" class="primary" disabled>حفظ النشاط والمتابعة</button></div></div>';
const grid=backdrop.querySelector('#nanoCommerceTiles');sectors.forEach(([key,symbol,name,desc])=>{const b=d.createElement('button');b.type='button';b.className='nano-commerce-tile';b.dataset.activity=key;b.setAttribute('role','radio');b.setAttribute('aria-checked','false');const img=icon(symbol);b.append(img);const texts=d.createElement('span');texts.className='nano-commerce-tile-copy';let strong=d.createElement('b');strong.textContent=name;let small=d.createElement('small');small.textContent=desc;texts.append(strong,small);b.append(texts);b.addEventListener('click',()=>choose(key));grid.append(b)});
backdrop.querySelector('#nanoCommerceCancel').addEventListener('click',close);backdrop.querySelector('#nanoCommerceSave').addEventListener('click',save);d.body.append(backdrop);
label();}
function choose(key){selected.clear();selected.add(key);d.querySelectorAll('.nano-commerce-tile').forEach(e=>{const active=e.dataset.activity===key;e.classList.toggle('chosen',active);e.setAttribute('aria-checked',String(active))});$('nanoCommerceSave').disabled=false;status('')}
function open(){if(!admin()){status('تعديل النشاط متاح لمدير المتجر فقط');return}if(!homeVisible())return;build();dismissed=false;if(profile)choose(profile.primary);else if(selected.size)choose([...selected][0]);const modal=$('nanoCommerceOverlay');modal.hidden=false;modal.querySelector('.nano-commerce-tile')?.focus();}
function close(){const el=$('nanoCommerceOverlay');if(el)el.hidden=true;dismissed=true}
async function save(){if(busy||!selected.size)return;busy=true;const saveBtn=$('nanoCommerceSave');saveBtn.disabled=true;status('جار حفظ النشاط في إعدادات المتجر...');try{
 if(!window.api?.updateSettings||!window.api?.getSettings)throw Error('تعذر الوصول إلى إعدادات المتجر');
 const mode=await window.nanoNative?.getPcSyncInfo?.().catch(()=>null);if(mode?.mode==='client')throw Error('غيّر نشاط المتجر من الكمبيوتر الرئيسي فقط لضمان توحيد الإعدادات');
 const key=[...selected][0],sector=sectors.find(x=>x[0]===key);
 const p={schema:1,primary:key,activities:key==='mixed'?sectors.filter(x=>x[0]!=='mixed').map(x=>x[0]):[key],units:sector[4].split(','),fields:sector[5].split(','),updatedAt:new Date().toISOString()};
 const result=await window.api.updateSettings({[KEY]:JSON.stringify(p)});if(result?.success===false)throw Error(result.message||'رفض النظام حفظ الإعدادات');
 const check=await fetchProfile();if(!check||check.primary!==key)throw Error('تعذر التأكد من حفظ النشاط. لم يتم اعتماده');
 profile=check;label();close();
 }catch(e){status('تعذر الحفظ: '+(e?.message||String(e)))}finally{busy=false;saveBtn.disabled=false}}
async function entered(){if(pending)return;pending=true;const id=++seq;try{const p=await fetchProfile();if(id!==seq)return;profile=p;label();if(!profile&&!dismissed&&admin()&&homeVisible())open()}catch(e){console.warn('[NANO Multi-Commerce] Could not load store profile',e)}finally{pending=false}}
function refresh(){const shown=homeVisible();if(!shown){lastHome=false;return}if(!lastHome){lastHome=true;entered()}label();const btn=$('nanoCommerceChange');if(btn)btn.hidden=!admin()}
function init(){if(ready||!$('nanoHomeSection'))return;ready=true;build();const obs=new MutationObserver(refresh);obs.observe($('nanoHomeSection'),{attributes:true,attributeFilter:['style','class','hidden']});const log=$('loginOverlay');if(log)obs.observe(log,{attributes:true,attributeFilter:['style','class','hidden']});window.addEventListener('nano-pos-login-success',()=>setTimeout(refresh,900));window.addEventListener('nano-section-shown',refresh);window.addEventListener('focus',refresh);refresh()}
window.NANO_COMMERCE={getProfile:()=>profile,refresh};if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
