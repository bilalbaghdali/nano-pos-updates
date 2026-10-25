#!/usr/bin/env python3
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
SPEECH = r"""
;
/* NANO POS v2.0.7: robust prayer card placement and cart price speech */
(function(){
  if (window.__nanoCartSpeechV202) return;
  window.__nanoCartSpeechV202 = true;
  var activeList=null, listObserver=null, lastSignature='', timer=null;
  function uiLang(){
    var lang=(window.currentLanguage || document.getElementById('settLanguage')?.value || document.documentElement.lang || '').toLowerCase();
    if(lang.indexOf('ar')===0 || document.documentElement.dir==='rtl') return 'ar';
    if(lang.indexOf('fr')===0) return 'fr';
    var txt=(document.body&&document.body.innerText||'').slice(0,3000);
    if(/[\u0600-\u06FF]/.test(txt)) return 'ar';
    if(/Produits|Ventes|Paramètres|Ajouter au panier/i.test(txt)) return 'fr';
    return 'en';
  }
  function notify(lang){
    var msg=lang==='ar'?'تمت إضافة المنتج إلى السلة':lang==='fr'?'Produit ajouté au panier':'Product added to cart';
    var old=document.getElementById('__nanoCartSpeechToast'); if(old) old.remove();
    var el=document.createElement('div'); el.id='__nanoCartSpeechToast'; el.textContent='✓  '+msg;
    el.style.cssText='position:fixed;z-index:2147483647;top:18px;right:18px;max-width:calc(100vw - 36px);padding:12px 18px;border-radius:12px;background:#0f766e;color:white;font:700 14px/1.4 system-ui,sans-serif;box-shadow:0 8px 30px #0003;';
    if(lang==='ar'){el.style.right='auto';el.style.left='18px';el.dir='rtl';}
    document.body.appendChild(el); setTimeout(function(){if(el.isConnected)el.remove();},2200);
  }
  function normalizePrice(raw){
    var s=String(raw||'').replace(/[\s\u00a0]/g,'');
    if(!s)return null;
    var comma=s.lastIndexOf(','), dot=s.lastIndexOf('.');
    if(comma>=0 && dot>=0){
      var decimal=Math.max(comma,dot), decimals=s.length-decimal-1;
      s=s.slice(0,decimal).replace(/[.,]/g,'')+(decimals>0&&decimals<=2?'.'+s.slice(decimal+1):s.slice(decimal+1));
    }else if(comma>=0){
      var tail=s.length-comma-1;
      s=tail>0&&tail<=2?s.slice(0,comma)+'.'+s.slice(comma+1):s.replace(/,/g,'');
    }else if(dot>=0 && s.length-dot-1>2)s=s.replace(/\./g,'');
    var n=Number(s);
    return Number.isFinite(n)&&n>=0?String(n):null;
  }
  function priceFromRow(row){
    if(!row)return null;
    var selectors=['[data-unit-price]','[data-product-price]','[data-price]','.cart-item-price','.item-price','.product-price','[class*="unit-price"]','[class*="item-price"]','[class*="product-price"]','[class*="price"]:not([class*="total"]):not([class*="discount"])'];
    for(var i=0;i<selectors.length;i++){
      var nodes=[];
      try{nodes=(row.matches&&row.matches(selectors[i])?[row]:[]).concat(Array.from(row.querySelectorAll(selectors[i])))}catch(e){}
      for(var j=0;j<nodes.length;j++){
        var n=nodes[j], raw=n.getAttribute('data-unit-price')||n.getAttribute('data-product-price')||n.getAttribute('data-price')||n.textContent||'';
        var price=normalizePrice(String(raw).match(/\d[\d\s.,]*/)?.[0]||'');
        if(price!==null)return price;
      }
    }
    return null;
  }
  function speakPrice(row,lang){
    if(!('speechSynthesis' in window)||!window.SpeechSynthesisUtterance)return;
    var price=priceFromRow(row);
    if(price===null)return;
    var prefix=lang==='ar'?'سعر المنتج المضاف إلى السلة':lang==='fr'?'Prix du produit ajouté au panier':'Price of the added product';
    var currency=lang==='ar'?'دينار جزائري':lang==='fr'?'dinars algériens':'Algerian dinars';
    var utter=new SpeechSynthesisUtterance(prefix+' '+price+' '+currency);
    utter.lang=lang==='ar'?'ar-DZ':lang==='fr'?'fr-FR':'en-US'; utter.rate=0.92;
    try{window.speechSynthesis.cancel();window.speechSynthesis.speak(utter);}catch(e){}
  }
  function rows(list){
    return Array.from(list.children||[]).filter(function(n){
      var text=n.nodeType===1?(n.innerText||n.textContent||'').trim():'';
      return !!text&&!/empty cart|panier vide|السلة فارغة/i.test(text)&&!n.querySelector('[data-i18n="empty_cart_msg"]');
    });
  }
  function observeList(list){
    if(!list||activeList===list)return;
    if(listObserver)listObserver.disconnect();
    activeList=list; lastSignature='';
    function scan(){
      clearTimeout(timer);
      timer=setTimeout(function(){
        if(!activeList||!activeList.isConnected)return;
        var current=rows(activeList);
        var signature=current.map(function(r){return (r.innerText||r.textContent||'').replace(/\s+/g,' ').trim();}).join('||');
        if(signature && signature!==lastSignature){
          var hadPrevious=!!lastSignature; lastSignature=signature;
          if(hadPrevious){var row=current[current.length-1],lang=uiLang();notify(lang);speakPrice(row,lang);}
        }else lastSignature=signature;
      },120);
    }
    listObserver=new MutationObserver(scan);
    listObserver.observe(list,{childList:true,subtree:true,characterData:true,attributes:true});
    scan();
  }
  function findList(){return document.getElementById('cartItemsList')||document.querySelector('[id*="cartItemsList"],[data-cart-items],.cart-items-list');}
  function init(){var list=findList();if(list)observeList(list);}
  function start(){
    init();
    if(document.body)new MutationObserver(init).observe(document.body,{childList:true,subtree:true});
    setInterval(init,1000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
"""

PRAYER = r"""
;
(function(){
 if(window.__nanoPrayerSidebarV207)return;window.__nanoPrayerSidebarV206=true;
 var STORE='__nanoPrayerLocationV202',tab=null,panel=null,lastAlert='',minuteTimer=null,refreshTimer=null,busy=false,timings=null,fetchedDay='';
 var DEFAULT={city:'Algiers',country:'Algeria',method:'3'};
 function loadLocation(){try{return Object.assign({},DEFAULT,JSON.parse(localStorage.getItem(STORE)||'{}'));}catch(e){return DEFAULT;}}
 var location=loadLocation();
 function lang(){var l=(window.currentLanguage||document.documentElement.lang||'').toLowerCase();if(l.indexOf('ar')===0||document.documentElement.dir==='rtl')return'ar';if(l.indexOf('fr')===0)return'fr';return'en';}
 function t(ar,fr,en){var l=lang();return l==='ar'?ar:l==='fr'?fr:en;}
 function css(el,s){el.style.cssText=s;}
 function theme(){
  var s=getComputedStyle(document.documentElement),b=getComputedStyle(document.body);
  function v(names,fallback){for(var n of names){var x=s.getPropertyValue(n).trim()||b.getPropertyValue(n).trim();if(x)return x;}return fallback;}
  return {primary:v(['--primary-color','--primary','--accent-color','--brand-color','--bs-primary'],'#0f766e'),surface:v(['--card-bg','--card-background','--surface-color','--panel-bg','--bg-secondary'],'#ffffff'),text:v(['--text-color','--foreground','--color-text'],'#172033'),muted:v(['--muted-color','--text-muted','--secondary-text'],'#64748b'),border:v(['--border-color','--border','--line-color'],'#dbe4f0')};
 }
 function ensure(){
  if(!document.body)return;
  if(!tab||!tab.isConnected){
   tab=document.getElementById('__nanoPrayerSidebarTab');
   if(!tab){
    tab=document.createElement('button');tab.id='__nanoPrayerSidebarTab';tab.type='button';tab.setAttribute('aria-expanded','false');tab.setAttribute('aria-controls','__nanoPrayerSidebar');
    tab.innerHTML='<span aria-hidden="true" style="font-size:18px;line-height:1">☾</span><span id="__nanoPrayerTabLabel" style="font-size:11px;font-weight:700"></span>';
    tab.addEventListener('click',function(e){e.stopPropagation();if(panel&&panel.classList.contains('is-open'))close();else open();});
    document.body.appendChild(tab);
   }
  }
  if(!panel||!panel.isConnected){
   panel=document.getElementById('__nanoPrayerSidebar');
   if(!panel){
    panel=document.createElement('aside');panel.id='__nanoPrayerSidebar';panel.setAttribute('role','dialog');panel.setAttribute('aria-label',t('مواقيت الصلاة','Horaires de prière','Prayer times'));
    panel.innerHTML='<div id="__nanoPrayerSidebarHeader"><div style="min-width:0"><div id="__nanoPrayerSidebarTitle" style="font-size:16px;font-weight:800"></div><div id="__nanoPrayerSidebarSub" style="font-size:12px;opacity:.82;margin-top:2px"></div></div><button id="__nanoPrayerSidebarClose" type="button" aria-label="إغلاق">×</button></div><div id="__nanoPrayerSidebarBody"><div id="__nanoPrayerSidebarCity"></div><button id="__nanoPrayerSidebarLoc" type="button"></button><div id="__nanoPrayerSidebarRows"></div><div id="__nanoPrayerSidebarStatus" role="status"></div><div id="__nanoPrayerSidebarNote"></div></div>';
    document.body.appendChild(panel);
    panel.querySelector('#__nanoPrayerSidebarClose').addEventListener('click',close);
    panel.querySelector('#__nanoPrayerSidebarLoc').addEventListener('click',chooseLocation);
    document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
   }
  }
  paint();render();ensureHomeCard();
 }
 function paint(){
  if(!tab||!panel)return;var c=theme();
  css(tab,'position:static;z-index:2147482000;display:inline-flex;flex-direction:row;vertical-align:middle;align-items:center;justify-content:center;gap:5px;min-width:36px;min-height:34px;margin-inline-start:8px;padding:5px 8px;border:1px solid '+c.border+';border-radius:10px;background:'+c.primary+';color:#fff;box-shadow:0 3px 10px #0002;cursor:pointer;font:600 12px/1.2 system-ui,sans-serif;');
  css(panel,'position:fixed;top:0;right:0;bottom:0;z-index:2147483000;width:300px;max-width:min(88vw,340px);transform:translateX(105%);visibility:hidden;transition:transform .22s ease,visibility .22s;background:'+c.surface+';color:'+c.text+';border-left:1px solid '+c.border+';box-shadow:-12px 0 34px #0002;font:14px/1.5 system-ui,sans-serif;display:flex;flex-direction:column;overflow:auto;');
  var h=panel.querySelector('#__nanoPrayerSidebarHeader');css(h,'display:flex;align-items:center;justify-content:space-between;gap:12px;padding:18px 16px;background:'+c.primary+';color:#fff;');
  var closeBtn=panel.querySelector('#__nanoPrayerSidebarClose');css(closeBtn,'border:1px solid #ffffff66;background:#ffffff18;color:#fff;border-radius:9px;width:34px;height:34px;font-size:22px;line-height:1;cursor:pointer;flex:none;');
  css(panel.querySelector('#__nanoPrayerSidebarBody'),'padding:16px;overflow:auto;');
  css(panel.querySelector('#__nanoPrayerSidebarCity'),'color:'+c.muted+';font-size:12px;margin-bottom:10px;');
  var loc=panel.querySelector('#__nanoPrayerSidebarLoc');css(loc,'width:100%;border:1px solid '+c.border+';background:'+c.surface+';color:'+c.text+';border-radius:10px;padding:10px 12px;margin-bottom:14px;cursor:pointer;font:600 13px/1.4 system-ui,sans-serif;');
  css(panel.querySelector('#__nanoPrayerSidebarRows'),'display:grid;grid-template-columns:1fr;gap:8px;');
  css(panel.querySelector('#__nanoPrayerSidebarStatus'),'font-size:12px;color:'+c.muted+';margin-top:14px;');
  css(panel.querySelector('#__nanoPrayerSidebarNote'),'font-size:11px;color:'+c.muted+';margin-top:12px;padding-top:10px;border-top:1px solid '+c.border+';');
 }
 function placeTab(){
  if(!tab||!tab.isConnected||!document.body)return;
  var candidates=Array.from(document.querySelectorAll('h1,h2,h3,h4,p,span,strong,div'))
   .filter(function(el){
    if(!el||el===tab||panel&&panel.contains(el)||el.closest('#__nanoPrayerSidebar')||el.closest('#__nanoPrayerSidebarTab'))return false;
    var txt=(el.innerText||el.textContent||'').replace(/\\s+/g,' ').trim();
    if(!txt||txt.length>110||!/(مرحبا|مرحباً|مرحبًا|مرحباً بك|اهلا|أهلاً|أهلا|welcome|bonjour|bienvenue)/i.test(txt))return false;
    var rect=el.getBoundingClientRect();return rect.width>0&&rect.height>0;
   });
  candidates.sort(function(a,b){var al=(a.innerText||a.textContent||'').trim().length,bl=(b.innerText||b.textContent||'').trim().length;if(al!==bl)return al-bl;var rank={H1:0,H2:1,H3:2,H4:3};return (rank[a.tagName]??4)-(rank[b.tagName]??4);});
  var target=candidates[0];
  if(target){
   if(target.nextElementSibling!==tab)target.insertAdjacentElement('afterend',tab);
   target.style.display='inline-block';target.style.verticalAlign='middle';
   tab.style.position='static';tab.style.right='auto';tab.style.bottom='auto';tab.style.marginInlineStart='8px';
  }else{
   if(tab.parentElement!==document.body)document.body.appendChild(tab);
   tab.style.position='fixed';tab.style.right='10px';tab.style.bottom='22px';tab.style.marginInlineStart='0';
   tab.style.flexDirection='row';tab.style.minHeight='38px';tab.style.borderRadius='12px';
  }
 }
 var homeCard=null,hijriDate='',gregorianDate='';
 function ensureHomeCard(){
  if(!document.body)return;
  if(!homeCard||!homeCard.isConnected){
   homeCard=document.createElement('section');homeCard.id='__nanoPrayerHomeCard';
   homeCard.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><strong id="__nphTitle"></strong><button id="__nphLoc" type="button"></button></div><div id="__nphDates" style="font-size:11px;margin-top:5px"></div><div id="__nphNext" style="margin-top:7px;padding:7px;border-radius:8px;font-weight:800"></div><div id="__nphRows" style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:5px;margin-top:7px"></div>';
   var btn=homeCard.querySelector('#__nphLoc');btn.addEventListener('click',chooseLocation);
  }
  /* Anchor the compact prayer card in the unused space opposite the General Manager profile on the home header. */
  var manager=Array.from(document.querySelectorAll('body *')).filter(function(e){
   if(!e||e===homeCard||e.closest('#__nanoPrayerSidebar')||e.closest('#__nanoPrayerHomeCard')||e.closest('#__nanoPrayerSidebarTab'))return false;
   var x=(e.innerText||e.textContent||'').replace(/\\s+/g,' ').trim();
   return x.length>0&&x.length<90&&/(المدير العام|مدير عام|general manager|directeur général|directeur general)/i.test(x)&&e.getBoundingClientRect().width>0;
  });
  manager.sort(function(a,b){return (a.innerText||a.textContent||'').trim().length-(b.innerText||b.textContent||'').trim().length;});
  var profile=manager[0],row=null;
  if(profile){
   for(var p=profile.parentElement,depth=0;p&&p!==document.body&&depth<6;p=p.parentElement,depth++){
    var r=p.getBoundingClientRect(),st=getComputedStyle(p);
    if(r.width>=720&&r.height>=38&&r.height<=220&&(st.display==='flex'||st.display==='grid'||/header|topbar|top-bar|navbar|welcome|user-info|profile/i.test(String(p.className||'')+' '+String(p.id||'')))){row=p;break;}
   }
  }
  if(row&&profile){
   var c=theme();css(homeCard,'position:relative;display:block;flex:0 1 440px;width:min(440px,48%);max-width:48%;min-width:280px;box-sizing:border-box;margin:4px 12px;padding:10px 12px;border:1px solid '+c.border+';border-radius:12px;background:'+c.surface+';color:'+c.text+';box-shadow:0 3px 12px #0002;z-index:1;font:12px/1.45 system-ui,sans-serif;');
   var btn=homeCard.querySelector('#__nphLoc');btn.style.cssText='border:1px solid '+c.border+';background:transparent;color:inherit;border-radius:8px;padding:4px 7px;cursor:pointer;font:600 11px system-ui';
   if(homeCard.parentElement!==row)row.insertBefore(homeCard,profile);
   if(getComputedStyle(row).display!=='flex'&&getComputedStyle(row).display!=='grid'){row.style.display='flex';row.style.alignItems='center';row.style.justifyContent='space-between';row.style.flexWrap='wrap';}
   row.style.gap=row.style.gap||'10px';
   /* Keep the card in the same header row and place it on the physical side opposite the manager profile. */
   var rr=row.getBoundingClientRect(),pr=profile.getBoundingClientRect();
   homeCard.style.order=(pr.left+pr.width/2>rr.left+rr.width/2)?'-1':'1';
  }else{
   /* Robust fallback: keep the card visible even when the app's translated profile/header labels differ. */
   var c=theme(),left=16,top=82,width=Math.min(420,Math.max(300,window.innerWidth-32));
   if(profile){var pr=profile.getBoundingClientRect();top=Math.max(72,Math.min(pr.top,window.innerHeight-240));if(pr.left+pr.width/2>window.innerWidth/2)left=16;else left=Math.max(16,window.innerWidth-width-16);}
   if(homeCard.parentElement!==document.body)document.body.appendChild(homeCard);
   css(homeCard,'position:fixed;display:block;top:'+top+'px;left:'+left+'px;width:'+width+'px;max-width:calc(100vw - 32px);min-width:0;box-sizing:border-box;margin:0;padding:12px 14px;border:1px solid '+c.border+';border-radius:12px;background:'+c.surface+';color:'+c.text+';box-shadow:0 6px 24px #0003;z-index:2147481000;font:12px/1.45 system-ui,sans-serif;');
  }
  var c=theme();css(homeCard.querySelector('#__nphNext'),'background:'+c.primary+';color:#fff;');renderHome();
 }
 function renderHome(){
  if(!homeCard||!homeCard.isConnected)return;var c=theme(),l=lang(),now=new Date(),next=null;homeCard.dir=l==='ar'?'rtl':'ltr';
  homeCard.querySelector('#__nphTitle').textContent=t('مواقيت الصلاة','Horaires de prière','Prayer times');homeCard.querySelector('#__nphLoc').textContent=t('تغيير المنطقة','Changer de région','Change region');
  homeCard.querySelector('#__nphDates').textContent=t('الميلادي: ','Grégorien : ','Gregorian: ')+(gregorianDate||today())+' • '+t('الهجري: ','Hégirien : ','Hijri: ')+(hijriDate||'—')+' • '+location.city+', '+location.country;
  ['Fajr','Dhuhr','Asr','Maghrib','Isha'].forEach(function(p){var d=timings&&parseTime(timings[p]);if(d&&d>now&&!next)next={p:p,d:d};});
  if(!next&&timings){var d=parseTime(timings.Fajr);if(d){d.setDate(d.getDate()+1);next={p:'Fajr',d:d};}}
  var labels={Fajr:['الفجر','Fajr','Fajr'],Dhuhr:['الظهر','Dohr','Dhuhr'],Asr:['العصر','Asr','Asr'],Maghrib:['المغرب','Maghrib','Maghrib'],Isha:['العشاء','Icha','Isha']};
  if(next){var ms=next.d-now,hh=Math.floor(ms/3600000),mm=Math.floor(ms%3600000/60000),ss=Math.floor(ms%60000/1000);homeCard.querySelector('#__nphNext').textContent=t('الصلاة القادمة: ','Prochaine prière : ','Next prayer: ')+labels[next.p][l==='ar'?0:l==='fr'?1:2]+' — '+String(hh).padStart(2,'0')+':'+String(mm).padStart(2,'0')+':'+String(ss).padStart(2,'0');}else homeCard.querySelector('#__nphNext').textContent=t('جارٍ تحميل المواقيت…','Chargement…','Loading times…');
  var rows=homeCard.querySelector('#__nphRows');rows.innerHTML='';[['Fajr','الفجر','Fajr','Fajr'],['Dhuhr','الظهر','Dohr','Dhuhr'],['Asr','العصر','Asr','Asr'],['Maghrib','المغرب','Maghrib','Maghrib'],['Isha','العشاء','Icha','Isha']].forEach(function(n){var x=document.createElement('div');x.style.cssText='border:1px solid '+c.border+';border-radius:7px;padding:5px;text-align:center;font-size:10px';x.textContent=n[l==='ar'?1:l==='fr'?2:3]+' '+(timings&&timings[n[0]]?String(timings[n[0]]).match(/\\d{1,2}:\\d{2}/)?.[0]:'--:--');rows.appendChild(x);});
 }
 function open(){ensure();if(!panel)return;panel.style.visibility='visible';panel.style.transform='translateX(0)';panel.classList.add('is-open');tab.setAttribute('aria-expanded','true');fetchTimes(false);}
 function close(){if(!panel)return;panel.style.transform='translateX(105%)';panel.style.visibility='hidden';panel.classList.remove('is-open');if(tab)tab.setAttribute('aria-expanded','false');}
 function chooseLocation(){
  var city=window.prompt(t('أدخل اسم المدينة بالإنجليزية أو الفرنسية','Saisissez la ville en anglais ou en français','Enter city name'),location.city);if(city===null||!city.trim())return;
  var country=window.prompt(t('أدخل الدولة','Saisissez le pays','Enter country'),location.country);if(country===null||!country.trim())return;
  location={city:city.trim(),country:country.trim(),method:location.method||'3'};try{localStorage.setItem(STORE,JSON.stringify(location));}catch(e){}
  timings=null;fetchedDay='';render();fetchTimes(true);
 }
 function today(){var d=new Date();return String(d.getDate()).padStart(2,'0')+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+d.getFullYear();}
 function parseTime(s){var m=String(s||'').match(/(\d{1,2}):(\d{2})/);if(!m)return null;var d=new Date();d.setHours(+m[1],+m[2],0,0);return d;}
 function render(){
  if(!tab||!tab.isConnected||!panel||!panel.isConnected)return;
  var c=theme();tab.title=t('مواقيت الصلاة','Horaires de prière','Prayer times');tab.setAttribute('aria-label',tab.title);
  panel.dir=lang()==='ar'?'rtl':'ltr';panel.querySelector('#__nanoPrayerSidebarTitle').textContent=t('مواقيت الصلاة','Horaires de prière','Prayer times');
  panel.querySelector('#__nanoPrayerSidebarSub').textContent=t('الصلوات اليومية','Prières quotidiennes','Daily prayer schedule');
  panel.querySelector('#__nanoPrayerTabLabel').textContent=timings?(function(){var ns=['Fajr','Dhuhr','Asr','Maghrib','Isha'];for(var n of ns){var d=parseTime(timings[n]);if(d&&d>new Date())return String(timings[n]).match(/\d{1,2}:\d{2}/)?.[0]||'';}return'';})():'';
  panel.querySelector('#__nanoPrayerSidebarCity').textContent=location.city+', '+location.country;
  panel.querySelector('#__nanoPrayerSidebarLoc').textContent=t('اختيار الموقع','Choisir le lieu','Choose location');
  var rows=panel.querySelector('#__nanoPrayerSidebarRows');rows.innerHTML='';
  var names=[['Fajr','الفجر','Fajr','Fajr'],['Sunrise','الشروق','Lever du soleil','Sunrise'],['Dhuhr','الظهر','Dohr','Dhuhr'],['Asr','العصر','Asr','Asr'],['Maghrib','المغرب','Maghrib','Maghrib'],['Isha','العشاء','Icha','Isha']];
  names.forEach(function(n){var cell=document.createElement('div'),left=document.createElement('span'),right=document.createElement('strong');var val=timings&&timings[n[0]]?String(timings[n[0]]).match(/\d{1,2}:\d{2}/)?.[0]:'--:--';left.textContent=n[lang()==='ar'?1:lang()==='fr'?2:3];right.textContent=val;var cc=theme();css(cell,'display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 12px;border:1px solid '+cc.border+';border-radius:10px;background:'+cc.surface+';');css(right,'font-variant-numeric:tabular-nums;color:'+cc.primary+';font-size:14px;');cell.appendChild(left);cell.appendChild(right);rows.appendChild(cell);});
  panel.querySelector('#__nanoPrayerSidebarStatus').textContent=timings?t('تم تحميل المواقيت لهذا اليوم.','Horaires chargés pour aujourd’hui.','Times loaded for today.'):t('جارٍ تحميل المواقيت…','Chargement des horaires…','Loading prayer times…');
  panel.querySelector('#__nanoPrayerSidebarNote').textContent=t('يظهر تنبيه قبل الصلاة بعشر دقائق.','Une alerte apparaît dix minutes avant la prière.','An alert appears ten minutes before prayer.');
  placeTab();ensureHomeCard();renderHome();
 }
 function notify(prayer){
  var labels={Fajr:['الفجر','Fajr','Fajr'],Dhuhr:['الظهر','Dohr','Dhuhr'],Asr:['العصر','Asr','Asr'],Maghrib:['المغرب','Maghrib','Maghrib'],Isha:['العشاء','Icha','Isha']},l=lang(),msg=t('اقترب وقت صلاة '+labels[prayer][0]+' — بقي نحو 10 دقائق','La prière '+labels[prayer][1]+' approche — environ 10 minutes restantes','Prayer '+labels[prayer][2]+' is approaching — about 10 minutes remaining');
  var old=document.getElementById('__nanoPrayerAlert');if(old)old.remove();var el=document.createElement('div');el.id='__nanoPrayerAlert';el.textContent='🔔 '+msg;
  css(el,'position:fixed;z-index:2147483647;top:16px;left:50%;transform:translateX(-50%);max-width:calc(100vw - 30px);background:'+theme().primary+';color:#fff;padding:13px 18px;border-radius:12px;box-shadow:0 8px 28px #0004;font:700 14px/1.5 system-ui,sans-serif;text-align:center;');
  document.body.appendChild(el);setTimeout(function(){if(el.isConnected)el.remove();},60000);
 }
 function checkAlerts(){if(!timings)return;var now=new Date(),day=now.toDateString();['Fajr','Dhuhr','Asr','Maghrib','Isha'].forEach(function(p){var at=parseTime(timings[p]);if(!at)return;var diff=Math.round((at.getTime()-now.getTime())/60000),key=day+'|'+p;if(diff===10&&lastAlert!==key){lastAlert=key;notify(p);}});}
 function fetchTimes(force){
  var day=today();if(busy||(!force&&fetchedDay===day&&timings))return;busy=true;
  var url='https://api.aladhan.com/v1/timingsByCity/'+encodeURIComponent(day)+'?city='+encodeURIComponent(location.city)+'&country='+encodeURIComponent(location.country)+'&method='+encodeURIComponent(location.method||'3');
  fetch(url,{cache:'no-store'}).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}).then(function(j){if(!j||j.code!==200||!j.data||!j.data.timings)throw new Error('No prayer timings');timings=j.data.timings;fetchedDay=day;gregorianDate=(j.data.date&&j.data.date.gregorian&&j.data.date.gregorian.date)||today();hijriDate=(j.data.date&&j.data.date.hijri&&j.data.date.hijri.date)||'';render();renderHome();}).catch(function(){if(panel&&panel.isConnected)panel.querySelector('#__nanoPrayerSidebarStatus').textContent=t('تعذر جلب المواقيت. تحقق من الإنترنت واسم المدينة.','Impossible de charger les horaires. Vérifiez Internet et la ville.','Could not load times. Check internet and city name.');}).finally(function(){busy=false;});
 }
 function start(){ensure();fetchTimes(false);if(!minuteTimer)minuteTimer=setInterval(function(){ensure();if(fetchedDay!==today())fetchTimes(true);renderHome();checkAlerts();},1000);if(!refreshTimer)refreshTimer=setInterval(function(){fetchTimes(false);},300000);}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
""";

def build(src,dest,work):
  with zipfile.ZipFile(src) as z:
    assert z.namelist()==['payload/app.asar'],z.namelist()
    raw=z.read('payload/app.asar')
  magic,block,hs,n=struct.unpack_from('<4I',raw)
  assert magic==4 and block==hs+4
  tree=json.loads(raw[16:16+n]); start=8+block
  entries=[]
  def walk(node,prefix=''):
    for name,e in node.get('files',{}).items():
      path=prefix+name
      if 'files' in e: walk(e,path+'/')
      elif 'offset' in e and 'size' in e: entries.append((path,e))
  walk(tree); entries.sort(key=lambda x:int(x[1]['offset']))
  buf=bytearray(); found=set()
  for name,e in entries:
    blob=raw[start+int(e['offset']):start+int(e['offset'])+int(e['size'])]
    assert len(blob)==int(e['size']),name
    if name=='package.json':
      pkg=json.loads(blob.decode()); assert pkg.get('version')=='1.0.118',pkg.get('version')
      pkg['version']='2.0.7'; blob=(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(); found.add(name)
    elif name=='renderer.js':
      text=blob.decode('utf-8')
      assert 'cartItemsList' in text and 'speechSynthesis' not in text
      blob=(text+SPEECH+PRAYER).encode('utf-8'); found.add(name)
    e['offset']=str(len(buf)); e['size']=len(blob)
    if name in found and 'integrity' in e:
      e['integrity']['hash']=sha(blob)
      bs=int(e['integrity'].get('blockSize',4194304))
      e['integrity']['blocks']=[sha(blob[i:i+bs]) for i in range(0,len(blob),bs)]
    buf.extend(blob)
    if name in found:
      p=Path(work)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob)
  assert found=={'package.json','renderer.js'},found
  header=json.dumps(tree,separators=(',',':'),ensure_ascii=False).encode()
  padded=(len(header)+7)&~3
  out=struct.pack('<4I',4,padded+4,padded,len(header))+header+b'\0'*(padded-4-len(header))+buf
  dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',out)
  check=zipfile.ZipFile(dest).read('payload/app.asar')
  assert sha(check)==sha(out)
  print(json.dumps({'version':'2.0.7','patchSha256':sha(dest.read_bytes()),'appAsarSha256':sha(out),'sizeBytes':dest.stat().st_size}))
if __name__=='__main__':
  if len(sys.argv)!=4: raise SystemExit('build-v207.py BASE.zip OUTPUT.zip WORKDIR')
  build(*sys.argv[1:])
