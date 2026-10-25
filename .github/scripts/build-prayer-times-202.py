#!/usr/bin/env python3
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
SPEECH = r"""
;
/* NANO POS v2.0.2: reliable cart change detection and price speech */
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
/* NANO POS v2.0.2: prayer times, selectable city, and approaching-prayer alerts */
(function(){
  if (window.__nanoPrayerTimesV202) return;
  window.__nanoPrayerTimesV202 = true;
  var STORE='__nanoPrayerLocationV202', root=null, lastAlert='', refreshTimer=null, minuteTimer=null;
  var DEFAULT={city:'Algiers',country:'Algeria',method:'3'};
  function loadLocation(){try{return Object.assign({},DEFAULT,JSON.parse(localStorage.getItem(STORE)||'{}'));}catch(e){return DEFAULT;}}
  var location=loadLocation(), timings=null, fetchedDay='', busy=false;
  function lang(){var l=(window.currentLanguage||document.documentElement.lang||'').toLowerCase();if(l.indexOf('ar')===0||document.documentElement.dir==='rtl')return'ar';if(l.indexOf('fr')===0)return'fr';return'en';}
  function t(ar,fr,en){var l=lang();return l==='ar'?ar:l==='fr'?fr:en;}
  function style(el,css){el.style.cssText=css;}
  function ensure(){
    if(root&&root.isConnected)return;
    root=document.getElementById('__nanoPrayerTimesCard');
    if(root)return;
    root=document.createElement('section');root.id='__nanoPrayerTimesCard';root.dir=lang()==='ar'?'rtl':'ltr';
    style(root,'position:fixed;z-index:2147483000;right:18px;bottom:18px;width:300px;max-width:calc(100vw - 28px);background:#fff;color:#172033;border:1px solid #dbe4f0;border-radius:16px;box-shadow:0 12px 38px #0f172a30;font:14px/1.45 system-ui,sans-serif;overflow:hidden;');
    root.innerHTML='<div id="__nanoPrayerHead" style="background:#0f766e;color:#fff;padding:10px 12px;display:flex;align-items:center;justify-content:space-between;gap:8px"><strong id="__nanoPrayerTitle"></strong><button id="__nanoPrayerLoc" type="button" style="border:1px solid #ffffff88;background:#ffffff18;color:#fff;border-radius:8px;padding:5px 8px;cursor:pointer;font:inherit"></button></div><div style="padding:10px 12px"><div id="__nanoPrayerCity" style="font-size:12px;color:#64748b;margin-bottom:7px"></div><div id="__nanoPrayerRows" style="display:grid;grid-template-columns:1fr 1fr;gap:6px"></div><div id="__nanoPrayerStatus" style="font-size:12px;color:#64748b;margin-top:8px"></div></div>';
    document.body.appendChild(root);
    root.querySelector('#__nanoPrayerLoc').addEventListener('click',chooseLocation);
    render();
  }
  function chooseLocation(){
    var city=window.prompt(t('أدخل اسم المدينة بالإنجليزية أو الفرنسية','Saisissez la ville en anglais ou en français','Enter city name'),location.city);
    if(city===null||!city.trim())return;
    var country=window.prompt(t('أدخل الدولة','Saisissez le pays','Enter country'),location.country);
    if(country===null||!country.trim())return;
    location={city:city.trim(),country:country.trim(),method:location.method||'3'};
    try{localStorage.setItem(STORE,JSON.stringify(location));}catch(e){}
    timings=null;fetchedDay='';fetchTimes(true);
  }
  function today(){var d=new Date();return String(d.getDate()).padStart(2,'0')+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+d.getFullYear();}
  function parseTime(s){var m=String(s||'').match(/(\d{1,2}):(\d{2})/);if(!m)return null;var d=new Date();d.setHours(+m[1],+m[2],0,0);return d;}
  function render(){
    if(!root||!root.isConnected)return;
    root.dir=lang()==='ar'?'rtl':'ltr';
    root.querySelector('#__nanoPrayerTitle').textContent=t('مواقيت الصلاة','Horaires de prière','Prayer times');
    root.querySelector('#__nanoPrayerLoc').textContent=t('اختيار الموقع','Choisir le lieu','Choose location');
    root.querySelector('#__nanoPrayerCity').textContent=location.city+', '+location.country;
    var rows=root.querySelector('#__nanoPrayerRows');rows.innerHTML='';
    var names=[['Fajr','الفجر','الفجر'],['Sunrise','الشروق','الشروق'],['Dhuhr','الظهر','الظهر'],['Asr','العصر','العصر'],['Maghrib','المغرب','المغرب'],['Isha','العشاء','العشاء']];
    names.forEach(function(n){var value=timings&&timings[n[0]]?String(timings[n[0]]).match(/\d{1,2}:\d{2}/)?.[0]:'--:--';var cell=document.createElement('div');style(cell,'display:flex;justify-content:space-between;gap:6px;background:#f1f5f9;border-radius:8px;padding:7px 8px');var label=lang()==='ar'?n[1]:lang()==='fr'?({Fajr:'Fajr',Sunrise:'Lever du soleil',Dhuhr:'Dohr',Asr:'Asr',Maghrib:'Maghrib',Isha:'Icha'}[n[0]]):n[0];cell.textContent=label+'  '+value;rows.appendChild(cell);});
    root.querySelector('#__nanoPrayerStatus').textContent=timings?t('يتم تحديث المواقيت يوميًا. التنبيه قبل الصلاة بـ 10 دقائق.','Mise à jour quotidienne. Alerte 10 minutes avant la prière.','Times refresh daily. Alert 10 minutes before prayer.'):t('جارٍ تحميل المواقيت…','Chargement des horaires…','Loading prayer times…');
  }
  function notify(prayer,minutes){
    var label=({Fajr:['الفجر','Fajr','Fajr'],Dhuhr:['الظهر','Dohr','Dhuhr'],Asr:['العصر','Asr','Asr'],Maghrib:['المغرب','Maghrib','Maghrib'],Isha:['العشاء','Icha','Isha']})[prayer]||[prayer,prayer,prayer];
    var msg=t('اقترب وقت صلاة '+label[0]+' — بقي نحو '+minutes+' دقائق','La prière '+label[1]+' approche — environ '+minutes+' minutes restantes','Prayer '+label[2]+' is approaching — about '+minutes+' minutes remaining');
    var old=document.getElementById('__nanoPrayerAlert');if(old)old.remove();
    var el=document.createElement('div');el.id='__nanoPrayerAlert';el.textContent='🔔 '+msg;
    style(el,'position:fixed;z-index:2147483647;top:18px;left:50%;transform:translateX(-50%);max-width:calc(100vw - 30px);background:#b45309;color:#fff;padding:14px 18px;border-radius:12px;box-shadow:0 8px 28px #0004;font:700 15px/1.5 system-ui,sans-serif;text-align:center;');
    document.body.appendChild(el);setTimeout(function(){if(el.isConnected)el.remove();},60000);
  }
  function checkAlerts(){
    if(!timings)return;
    var now=new Date(), day=now.toDateString();
    ['Fajr','Dhuhr','Asr','Maghrib','Isha'].forEach(function(p){
      var at=parseTime(timings[p]);if(!at)return;
      var diff=Math.round((at.getTime()-now.getTime())/60000);
      var key=day+'|'+p;
      if(diff===10&&lastAlert!==key){lastAlert=key;notify(p,10);}
    });
  }
  function fetchTimes(force){
    var day=today();if(busy||(!force&&fetchedDay===day&&timings))return;
    busy=true;
    var url='https://api.aladhan.com/v1/timingsByCity/'+encodeURIComponent(day)+'?city='+encodeURIComponent(location.city)+'&country='+encodeURIComponent(location.country)+'&method='+encodeURIComponent(location.method||'3');
    fetch(url,{cache:'no-store'}).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}).then(function(j){
      if(!j||j.code!==200||!j.data||!j.data.timings)throw new Error('No prayer timings');
      timings=j.data.timings;fetchedDay=day;render();
    }).catch(function(){if(root&&root.isConnected)root.querySelector('#__nanoPrayerStatus').textContent=t('تعذر جلب المواقيت. تحقق من الاتصال واسم المدينة.','Impossible de charger les horaires. Vérifiez la connexion et la ville.','Could not load times. Check connection and city name.');}).finally(function(){busy=false;});
  }
  function start(){ensure();fetchTimes(false);if(!minuteTimer)minuteTimer=setInterval(function(){ensure();if(fetchedDay!==today())fetchTimes(true);checkAlerts();},15000);if(!refreshTimer)refreshTimer=setInterval(function(){fetchTimes(false);},300000);}
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
      pkg['version']='2.0.2'; blob=(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(); found.add(name)
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
  print(json.dumps({'version':'2.0.2','patchSha256':sha(dest.read_bytes()),'appAsarSha256':sha(out),'sizeBytes':dest.stat().st_size}))
if __name__=='__main__':
  if len(sys.argv)!=4: raise SystemExit('build-v202.py BASE.zip OUTPUT.zip WORKDIR')
  build(*sys.argv[1:])
