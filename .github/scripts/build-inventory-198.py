#!/usr/bin/env python3
"""Build read-only stock forecast 1.0.98 from SHA-verified official 1.0.97 ASAR."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
OFFICIAL='6cb54593d444e93faef4f2bd5d72959e1d8268d1a69f0fa9310c55a77e360571'
SHORTAGES_SHA='3e52607b9608c5de5a4b7bc262893611ede5b387af7430091a0091226afcc97b'
def once(s,old,new):
 assert s.count(old)==1,('source_marker_changed',old[:110],s.count(old))
 return s.replace(old,new)
def shortages(s):
 s=once(s,"const L=()=>{let l=String(root.currentLanguage||doc.documentElement.lang||'ar').toLowerCase().slice(0,2);return languages[l]||languages.ar;};",
 """const L=()=>{let l=String(root.currentLanguage||doc.documentElement.lang||'ar').toLowerCase().slice(0,2);return languages[l]||languages.ar;};
const forecastTexts={
 ar:{button:'تحليل الاحتياج المتوقع',daily:'المبيعات اليومية المقدرة',coverage:'أيام تغطية المخزون',loading:'جارٍ تحليل المبيعات التاريخية…',result:'تقديرات استرشادية حسب معدل البيع المتاح، راجع الكميات قبل الشراء.',missing:'تعذر تقدير بعض المنتجات أو تجاوز عددها 60؛ بقيت كمياتها المقترحة دون تغيير.',service:'خدمة تحليلات المنتجات غير متاحة.'},
 fr:{button:'Estimer les besoins',daily:'Ventes moyennes/jour',coverage:'Couverture (jours)',loading:'Analyse de l’historique…',result:'Estimations indicatives ; vérifiez les quantités avant commande.',missing:'Certaines lignes restent sans estimation (limite 60).',service:'Analyse des ventes indisponible.'},
 en:{button:'Estimate demand',daily:'Average sales/day',coverage:'Stock cover (days)',loading:'Analyzing sales history…',result:'Indicative averages only; review orders before purchasing.',missing:'Some items were not estimated (maximum 60).',service:'Product analytics service is unavailable.'}
};
const FL=()=>forecastTexts[String(root.currentLanguage||doc.documentElement.lang||'ar').toLowerCase().slice(0,2)]||forecastTexts.ar;""")
 s=once(s,"let data=[],partial=false,loading=false;",
        "let data=[],partial=false,loading=false,forecastApplied=false,forecastLoading=false,forecastMissing=0;")
 s=once(s,"return {name:String(product.name||product.product_name||product.title||'').trim()||'—',",
        "return {id:product.id??product.product_id,name:String(product.name||product.product_name||product.title||'').trim()||'—',")
 s=once(s," const cols=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status].join(' | ');",
        " const cols=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status,...(forecastApplied?[FL().daily,FL().coverage]:[])].join(' | ');")
 s=once(s,"   p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low].join(' | '));",
        "   p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low,...(forecastApplied?[formatQty(p.estimatedDaily),formatQty(p.coverDays)]:[])].join(' | '));")
 s=once(s," const fields=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status];",
        " const fields=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status,...(forecastApplied?[FL().daily,FL().coverage]:[])];")
 s=once(s," const rows=data.map(p=>[p.name,p.barcode,p.qty,p.minimum??'',p.order,p.depleted?t.out:t.low]);",
        " const rows=data.map(p=>[p.name,p.barcode,p.qty,p.minimum??'',p.order,p.depleted?t.out:t.low,...(forecastApplied?[p.estimatedDaily??'',p.coverDays??'']:[])]);")
 s=once(s," for(const s of [t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status]){",
        " for(const s of [t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status,...(forecastApplied?[FL().daily,FL().coverage]:[])]){")
 s=once(s,"   for(const v of [p.name,p.barcode||'—',formatQty(p.qty),p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low]){",
        "   for(const v of [p.name,p.barcode||'—',formatQty(p.qty),p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low,...(forecastApplied?[formatQty(p.estimatedDaily),formatQty(p.coverDays)]:[])]){")
 s=once(s," byId('nanoShortageNotice180').textContent=partial?t.partial:'';",
        " byId('nanoShortageNotice180').textContent=[partial?t.partial:'',forecastApplied?FL().result:'',forecastMissing?FL().missing:''].filter(Boolean).join(' ');")
 s=once(s," const headings=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status];",
        " const headings=[t.product,t.barcode,t.stock,t.minimum,t.suggest,t.status,...(forecastApplied?[FL().daily,FL().coverage]:[])];")
 s=once(s,"    const row=el('tr'),td=el('td',t.empty);td.colSpan=6;row.append(td);content.append(row);",
        "    const row=el('tr'),td=el('td',t.empty);td.colSpan=forecastApplied?8:6;row.append(td);content.append(row);")
 s=once(s,"       p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low])",
        "       p.minimum==null?t.noMinimum:formatQty(p.minimum),formatQty(p.order),p.depleted?t.out:t.low,...(forecastApplied?[formatQty(p.estimatedDaily),formatQty(p.coverDays)]:[])])")
 marker="async function refresh(){"
 assert s.count(marker)==1
 forecast="""async function estimateDemand(){
 if(forecastLoading||loading||!modal||!data.length)return;
 if(typeof root.api?.getProductAnalytics!=='function'||!root.NANO_STOCK_FORECAST_198?.recommend){
   notify(FL().service,'warning');return;
 }
 const button=byId('nanoShortageForecast198');
 forecastLoading=true;if(button)button.disabled=true;
 const notice=byId('nanoShortageNotice180');if(notice)notice.textContent=FL().loading;
 const snapshot=data.map(row=>({...row}));
 const candidates=snapshot.slice(0,60);
 let cursor=0,missing=Math.max(0,snapshot.length-candidates.length);
 async function worker(){
   while(cursor<candidates.length){
     const row=candidates[cursor++];
     if(row.id==null){missing++;continue;}
     try{
       const info=await root.api.getProductAnalytics(row.id);
       if(!info||info.success===false)throw Error('analytics_unavailable');
       const rate=safeNumber(info.avgDailySales??info.avgDaily);
       const estimate=root.NANO_STOCK_FORECAST_198.recommend({
         stock:row.qty,minimum:row.minimum,avgDaily:rate,baselineOrder:row.order
       });
       if(!estimate.ok){missing++;continue;}
       row.estimatedDaily=estimate.avgDaily;
       row.coverDays=estimate.coverDays;
       row.order=estimate.order;
     }catch{missing++;}
   }
 }
 try{
   await Promise.all(Array.from({length:Math.min(3,candidates.length)},()=>worker()));
   if(modal){
     data=snapshot;forecastApplied=true;forecastMissing=missing;
     draw();
   }
 }finally{forecastLoading=false;if(button&&button.isConnected)button.disabled=false;}
}
"""
 s=once(s,marker,forecast+marker)
 s=once(s," if(loading||!modal)return;loading=true;",
        " if(loading||!modal||forecastLoading)return;loading=true;forecastApplied=false;forecastMissing=0;")
 s=once(s," actions.append(make('nanoShortageRefresh180',t.refresh,refresh),make('nanoShortagePrint180',t.print,printList));",
        " actions.append(make('nanoShortageRefresh180',t.refresh,refresh),make('nanoShortageForecast198',FL().button,estimateDemand),make('nanoShortagePrint180',t.print,printList));")
 return s
def release_notes(s):
 s=once(s,"const FALLBACK_VERSION = '1.0.97';","const FALLBACK_VERSION = '1.0.98';")
 i=s.index('  const OFFLINE = {');j=s.index('  const TITLES = {',i)
 return s[:i]+"""  const OFFLINE = {
    ar:['إضافة تحليل اختياري للاحتياج المتوقع داخل قائمة المنتجات الناقصة.',
        'عرض معدل المبيعات اليومي وأيام تغطية المخزون والكمية المقترحة في القائمة والطباعة والتصدير.',
        'حسابات استرشادية للقراءة فقط، دون تعديل المخزون أو بيانات المتجر أو التفعيل.'],
    fr:['Estimation facultative des besoins de réapprovisionnement.',
        'Ventes moyennes, jours de couverture, quantité suggérée et export.',
        'Calcul indicatif sans modification du stock ni des données.'],
    en:['Optional demand estimator inside existing low-stock list.',
        'Average daily sales, stock coverage days and suggested amounts in export and print.',
        'Read-only estimates; no stock, store data or activation changes.']
  };
"""+s[j:]
def build(zip_path,out_path,testdir):
 with zipfile.ZipFile(zip_path) as z:
  assert z.namelist()==['payload/app.asar']
  raw=z.read('payload/app.asar')
 assert sha(raw)==OFFICIAL, 'Official 1.0.97 app.asar has changed'
 magic,block,content_size,n=struct.unpack_from('<4I',raw)
 assert magic==4 and block==content_size+4
 header=json.loads(raw[16:16+n])
 assert 'nano-stock-forecast-198.js' not in header['files']
 start=8+block
 entries=[]
 def walk(node,prefix=''):
  for k,entry in node.get('files',{}).items():
   if 'files' in entry:walk(entry,prefix+k+'/')
   elif 'offset' in entry:entries.append((prefix+k,entry))
 walk(header);assert len(entries)>200
 entries.sort(key=lambda x:int(x[1]['offset']))
 new=bytearray();changed=set()
 for name,ent in entries:
  old=raw[start+int(ent['offset']):start+int(ent['offset'])+ent['size']]
  assert len(old)==ent['size']
  if name=='nano-inventory-shortages.js':
   assert sha(old)==SHORTAGES_SHA,'shortage UI source drift'
   blob=shortages(old.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='index.html':
   text=old.decode('utf8')
   text=once(text,'<script defer src="nano-inventory-shortages.js"></script>',
       '<script defer src="nano-stock-forecast-198.js"></script>\n   <script defer src="nano-inventory-shortages.js"></script>')
   blob=text.encode('utf8');changed.add(name)
  elif name=='release-notes.js':
   blob=release_notes(old.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='package.json':
   src=old.decode('utf8');assert json.loads(src)['version']=='1.0.97'
   blob=once(src,'"version": "1.0.97"','"version": "1.0.98"').encode('utf8')
   changed.add(name)
  else:blob=old
  ent['offset']=str(len(new));ent['size']=len(blob)
  if name in changed and 'integrity' in ent:
   integrity=ent['integrity'];integrity['hash']=sha(blob)
   bs=int(integrity.get('blockSize',4194304))
   integrity['blocks']=[sha(blob[i:i+bs]) for i in range(0,len(blob),bs)]
  new.extend(blob)
  if name in changed:
   (testdir/name).parent.mkdir(parents=True,exist_ok=True)
   (testdir/name).write_bytes(blob)
 assert changed=={'index.html','nano-inventory-shortages.js','release-notes.js','package.json'}
 extra=Path('.github/assets/nano-stock-forecast-198.js').read_bytes()
 entry={'size':len(extra),'offset':str(len(new)),
  'integrity':{'algorithm':'SHA256','hash':sha(extra),'blockSize':4194304,'blocks':[sha(extra)]}}
 header['files']['nano-stock-forecast-198.js']=entry
 new.extend(extra)
 (testdir/'nano-stock-forecast-198.js').write_bytes(extra)
 head=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8')
 pad=(len(head)+7)&~3
 out=struct.pack('<4I',4,pad+4,pad,len(head))+head+b'\0'*(pad-4-len(head))+new
 with zipfile.ZipFile(out_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',out)
 with zipfile.ZipFile(out_path) as z:assert sha(z.read('payload/app.asar'))==sha(out)
 print(json.dumps({'version':'1.0.98','modified':sorted(changed),'new':['nano-stock-forecast-198.js'],'asarSha256':sha(out),'zipSha256':sha(out_path.read_bytes())}))
if __name__=='__main__':
 src,dst,work=map(Path,sys.argv[1:4]);work.mkdir(parents=True,exist_ok=True);build(src,dst,work)
