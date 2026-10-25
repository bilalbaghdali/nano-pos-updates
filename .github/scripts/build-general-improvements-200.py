#!/usr/bin/env python3
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
SPEECH = r"""
;
/* NANO POS v2.0.1: reliable cart change detection and price speech */
(function(){
  if (window.__nanoCartSpeechV201) return;
  window.__nanoCartSpeechV201 = true;
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
      pkg['version']='2.0.1'; blob=(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(); found.add(name)
    elif name=='renderer.js':
      text=blob.decode('utf-8')
      assert 'cartItemsList' in text and 'speechSynthesis' not in text
      blob=(text+SPEECH).encode('utf-8'); found.add(name)
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
  print(json.dumps({'version':'2.0.1','patchSha256':sha(dest.read_bytes()),'appAsarSha256':sha(out),'sizeBytes':dest.stat().st_size}))
if __name__=='__main__':
  if len(sys.argv)!=4: raise SystemExit('build-v201.py BASE.zip OUTPUT.zip WORKDIR')
  build(*sys.argv[1:])
