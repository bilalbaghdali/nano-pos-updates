#!/usr/bin/env python3
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
SPEECH = r"""
;
/* NANO POS v2.0.0: add-to-cart notice and localized price speech */
(function(){
  if (window.__nanoCartSpeechV200) return;
  window.__nanoCartSpeechV200 = true;
  function uiLang(){
    var lang=(document.documentElement.lang||'').toLowerCase();
    if(lang.indexOf('ar')===0 || document.documentElement.dir==='rtl') return 'ar';
    if(lang.indexOf('fr')===0) return 'fr';
    try { var s=JSON.stringify(localStorage); if(/"(fr|fr-FR)"/i.test(s)) return 'fr'; if(/"(ar|ar-DZ)"/i.test(s)) return 'ar'; } catch(e){}
    var txt=(document.body&&document.body.innerText||'').slice(0,5000);
    if(/[\u0600-\u06FF]/.test(txt) && document.documentElement.dir==='rtl') return 'ar';
    if(/Produits|Ventes|Paramètres|Ajouter au panier/i.test(txt)) return 'fr';
    return 'en';
  }
  function notify(lang){
    var msg=lang==='ar'?'تمت إضافة المنتج إلى السلة':lang==='fr'?'Produit ajouté au panier':'Product added to cart';
    var old=document.getElementById('__nanoCartSpeechToast'); if(old) old.remove();
    var el=document.createElement('div'); el.id='__nanoCartSpeechToast'; el.textContent='✓  '+msg;
    el.style.cssText='position:fixed;z-index:2147483647;top:18px;right:18px;max-width:calc(100vw - 36px);padding:12px 18px;border-radius:12px;background:#0f766e;color:white;font:700 14px/1.4 system-ui,sans-serif;box-shadow:0 8px 30px #0003;';
    if(lang==='ar') {el.style.right='auto';el.style.left='18px';el.dir='rtl';}
    document.body.appendChild(el); setTimeout(function(){if(el.isConnected)el.remove();},2200);
  }
  function speakPrice(row,lang){
    if(!('speechSynthesis' in window) || !window.SpeechSynthesisUtterance) return;
    var text=(row&&row.innerText||'').replace(/\s+/g,' ').trim();
    var matches=text.match(/(?:\d{1,3}(?:[ ,. ]\d{3})+|\d+)(?:[,.]\d{1,2})?/g)||[];
    var raw=matches.length?matches[matches.length-1]:'';
    var price=raw.replace(/ /g,'').replace(/,(?=\d{3}(?:\D|$))/g,'').replace(/,(?=\d{1,2}$)/,'.');
    if(!price || !/\d/.test(price)){var total=document.getElementById('cartTotal');price=total?total.innerText.trim():'';}
    if(!price)return;
    var prefix=lang==='ar'?'سعر المنتج':lang==='fr'?'Prix du produit':'Product price';
    var currency=lang==='ar'?'دينار جزائري':lang==='fr'?'dinars algériens':'Algerian dinars';
    var utter=new SpeechSynthesisUtterance(prefix+' '+price+' '+currency);
    utter.lang=lang==='ar'?'ar-DZ':lang==='fr'?'fr-FR':'en-US'; utter.rate=0.95;
    try{window.speechSynthesis.cancel();window.speechSynthesis.speak(utter);}catch(e){}
  }
  function init(){
    var list=document.getElementById('cartItemsList'); if(!list || list.__nanoSpeechObserved)return;
    list.__nanoSpeechObserved=true;
    function rows(){return Array.from(list.children).filter(function(n){return n.nodeType===1 && !n.querySelector('[data-i18n="empty_cart_msg"]') && !/text-center.*text-slate-400/.test(n.className||'') && (n.innerText||'').trim().length>0;});}
    var previous=rows().length;
    new MutationObserver(function(){
      var current=rows(); if(current.length>previous){
        var row=current[current.length-1], lang=uiLang(); notify(lang); speakPrice(row,lang);
      }
      previous=current.length;
    }).observe(list,{childList:true,subtree:false});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
  var tries=0; var retry=setInterval(function(){init();if(document.getElementById('cartItemsList')||++tries>30)clearInterval(retry);},500);
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
      pkg['version']='2.0.0'; blob=(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(); found.add(name)
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
  print(json.dumps({'version':'2.0.0','patchSha256':sha(dest.read_bytes()),'appAsarSha256':sha(out),'sizeBytes':dest.stat().st_size}))
if __name__=='__main__':
  if len(sys.argv)!=4: raise SystemExit('build-v200.py BASE.zip OUTPUT.zip WORKDIR')
  build(*sys.argv[1:])
