#!/usr/bin/env python3
"""NANO POS 1.0.101 — verified original ASAR, only targeted read-only changes."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
SHA=lambda b:hashlib.sha256(b).hexdigest()
OFFICIAL='7649aeae82000f4439d9c98c1e4a4249f21a7937657816c093a1a5ac446c835d'
def once(src,a,b):
 assert src.count(a)==1,("source_drift",a[:120],src.count(a))
 return src.replace(a,b)
def patch_ui(src):
 src=once(src,
   "let popup=null,entries=[],suppliers=[],pending=null,busy=false,completed=new Set();",
   "let popup=null,entries=[],suppliers=[],pending=null,busy=false,completed=new Set(),purchaseHistory=[],estimateFees={};")
 src=once(src,"function currentRows(){",r"""
 function costText(){const lang=String(win.currentLanguage||doc.documentElement.lang||'ar').slice(0,2);
  return {
   ar:{heading:'مقارنة الموردين والتكلفة الحقيقية المقدّرة',compare:'أسعار الموردين المسجلة',none:'لا توجد أسعار شراء سابقة',fee:'نقل وشحن',other:'مصاريف إضافية',tax:'ضريبة غير قابلة للاسترداد',margin:'هامش الربح المستهدف (%)',estimate:'حساب التكلفة وهامش الربح',warning:'للمراجعة فقط: هذه تكلفة تقديرية ولا تُحفظ كمصروف شراء أو تغير المخزون أو سعر البيع.',landed:'التكلفة الإجمالية المقدّرة',unit:'تكلفة الوحدة بعد المصاريف',sale:'سعر بيع مقترح',price:'آخر تكلفة',supplier:'المورد',qty:'الكمية',cost:'تكلفة البضاعة'},
   fr:{heading:'Comparaison des fournisseurs et estimation du coût rendu',compare:'Historique des prix',none:'Aucun historique',fee:'Transport',other:'Frais divers',tax:'Taxe non récupérable',margin:'Marge cible (%)',estimate:'Calculer',warning:'Estimation uniquement; aucun montant, stock ou prix de vente ne sera modifié.',landed:'Coût total estimé',unit:'Coût unitaire rendu',sale:'Prix de vente suggéré',price:'Dernier prix',supplier:'Fournisseur',qty:'Quantité',cost:'Prix d’achat'},
   en:{heading:'Supplier comparison and estimated landed costs',compare:'Recorded supplier prices',none:'No purchase history',fee:'Shipping',other:'Other costs',tax:'Nonrecoverable tax',margin:'Target margin (%)',estimate:'Calculate estimates',warning:'Preview only: no accounting expense, stock cost or selling price will be changed.',landed:'Estimated landed total',unit:'Landed unit cost',sale:'Suggested sale price',price:'Last price',supplier:'Supplier',qty:'Quantity',cost:'Purchase cost'}
  }[lang]||{heading:'مقارنة الموردين والتكلفة المقدرة',compare:'أسعار الموردين',none:'غير متاح',fee:'النقل',other:'المصاريف',tax:'الضريبة غير المستردة',margin:'هامش الربح (%)',estimate:'حساب',warning:'تقدير فقط دون ترحيل.',landed:'التكلفة',unit:'تكلفة الوحدة',sale:'سعر البيع',price:'السعر',supplier:'المورد',qty:'الكمية',cost:'التكلفة'};}
 function money(n){return (Number(n)/100).toFixed(2);}
 function costReport(){
   const lib=win.NANO_TRADE_ANALYTICS_101,c=costText(),report=doc.getElementById('nanoPoCostReport101');
   if(!lib||!report)return;
   report.replaceChildren();
   const title=node('h3',c.heading);report.append(title);
   report.append(node('p',c.warning));
   const unselected=entries.filter(e=>!e.skip&&e.checked!==false&&!completed.has(String(e.productId)));
   for(const item of unselected){
     const quotes=lib.quotes(item.productId,suppliers,purchaseHistory);
     const line=node('p');
     line.append(node('strong',item.name+' — '+c.compare+': '));
     line.append(doc.createTextNode(quotes.length
       ?quotes.map(q=>q.supplierName+': '+q.unitCost.toFixed(2)).join(' · ')
       :c.none));
     report.append(line);
   }
   const groups=[...new Set(unselected.map(x=>String(x.supplierId||'')).filter(Boolean))];
   const heading=node('h4',c.heading);report.append(heading);
   for(const supplierId of groups){
     const supplier=suppliers.find(s=>String(s.id)===supplierId);
     const wrap=node('div');wrap.style.cssText='display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:8px;border-bottom:1px solid #ddd';
     wrap.append(node('strong',String(supplier?.name||supplierId)));
     const state=estimateFees[supplierId]||(estimateFees[supplierId]={freight:'0',other:'0',nonrecoverableTax:'0'});
     for(const field of [['freight',c.fee],['other',c.other],['nonrecoverableTax',c.tax]]){
       const label=node('label',field[1]+': ');
       const inp=node('input');inp.type='number';inp.min='0';inp.step='0.01';inp.style.cssText='width:100px;border:1px solid #aaa;padding:5px;border-radius:5px';
       inp.value=state[field[0]];inp.addEventListener('input',()=>{state[field[0]]=inp.value;renderTotals();});
       label.append(inp);wrap.append(label);
     }
     report.append(wrap);
   }
   const margin=node('label',c.margin+': '),marginInput=node('input');
   marginInput.id='nanoPoMargin101';marginInput.type='number';marginInput.step='0.01';marginInput.min='0';marginInput.max='99.99';
   marginInput.value=String(win.nanoPoTargetMargin101??20);
   marginInput.style.cssText='padding:6px;width:90px;border:1px solid #aaa;border-radius:6px';
   marginInput.addEventListener('input',()=>{win.nanoPoTargetMargin101=marginInput.value;renderTotals();});
   margin.append(marginInput);report.append(margin);
   const lines=node('div');lines.id='nanoPoCostTotals101';report.append(lines);
   function renderTotals(){
     lines.replaceChildren();
     try{
       const selected=unselected.filter(x=>x.supplierId&&Number(x.unitCost)>0&&Number(x.quantity)>0);
       const outcome=lib.estimate(selected,estimateFees,marginInput.value);
       for(const group of outcome.groups){
         const supplier=suppliers.find(s=>String(s.id)===group.supplierId);
         lines.append(node('h4',String(supplier?.name||group.supplierId)+' — '+c.landed+': '+money(group.totalCents)));
         for(const item of group.lines){
           const row=node('p',item.name+' — '+c.qty+': '+item.quantityMilli/1000+' — '+
            c.cost+': '+money(item.subtotalCents)+' — '+c.unit+': '+money(item.landedUnitCents)+' — '+
            c.sale+': '+money(item.targetSellingCents));
           lines.append(row);
         }
       }
     }catch(error){lines.append(node('p',String(error?.message||'invalid_cost_estimate')));}
   }
   renderTotals();
 }
 function currentRows(){""")
 src=once(src,
  "const table=node('div');table.id='nanoPoShortageRows100';card.append(table);",
  "const table=node('div');table.id='nanoPoShortageRows100';card.append(table);\n"
  "  const estimate=node('button',costText().estimate);estimate.type='button';\n"
  "  estimate.style.cssText='padding:9px;background:#0f766e;color:white;border-radius:8px;margin:8px';\n"
  "  estimate.addEventListener('click',costReport);card.append(estimate);\n"
  "  const report=node('div');report.id='nanoPoCostReport101';report.style.cssText='margin:8px 0;max-height:280px;overflow:auto';card.append(report);")
 src=once(src,
  "suppliers=Array.isArray(values[0])?values[0]:[];",
  "suppliers=Array.isArray(values[0])?values[0]:[];\n    purchaseHistory=Array.isArray(values[1])?values[1]:[];")
 return src
def notes(s):
 s=once(s,"const FALLBACK_VERSION = '1.0.100';","const FALLBACK_VERSION = '1.0.101';")
 a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
 return s[:a]+"""  const OFFLINE = {
    ar:['مقارنة أسعار الموردين المسجلة لكل منتج ناقص في المخزون.',
        'حاسبة تقديرية لتوزيع النقل والمصاريف والضريبة غير المستردة على بنود كل مورد حتى آخر سنتيم.',
        'عرض تكلفة الوحدة بعد المصاريف وسعر البيع المقترح وفق هامش ربح قابل للتعديل.',
        'الحسابات للمعاينة فقط ولا تسجل مصروفًا أو تغير السعر أو المخزون أو بيانات التفعيل.'],
    fr:['Comparaison des historiques des prix fournisseurs pour les stocks bas.',
        'Estimation des frais de transport, frais divers et taxes non récupérables.',
        'Coût unitaire rendu et prix de vente suggéré selon la marge choisie.',
        'Calculs consultatifs sans écriture comptable ni modification des stocks.'],
    en:['Compare historic supplier prices for low-stock products.',
        'Preview shipping, other fees and nonrecoverable tax allocations to the cent.',
        'Estimated landed unit costs and suggested selling prices at a chosen margin.',
        'Read-only preview, no stock, payable, license or selling-price changes.']
  };
"""+s[b:]
def build(source,target,work):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar'];raw=z.read('payload/app.asar')
 assert SHA(raw)==OFFICIAL,'unexpected_asar'
 magic,block,hs,n=struct.unpack_from('<4I',raw);assert magic==4 and block==hs+4
 header=json.loads(raw[16:16+n]);start=8+block
 assert 'nano-trade-analytics-101.js' not in header['files']
 members=[]
 def walk(node,prefix=''):
  for k,v in node.get('files',{}).items():
   if 'files' in v:walk(v,prefix+k+'/')
   elif 'offset' in v:members.append((prefix+k,v))
 walk(header);assert len(members)>200
 members.sort(key=lambda x:int(x[1]['offset']))
 data=bytearray();changed=set()
 for name,entry in members:
  blob=raw[start+int(entry['offset']):start+int(entry['offset'])+entry['size']]
  assert len(blob)==entry['size']
  if name=='nano-po-shortage-ui-100.js':
   blob=patch_ui(blob.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='index.html':
   h=blob.decode('utf8')
   h=once(h,'<script defer src="nano-po-shortage-ui-100.js"></script>',
     '<script defer src="nano-trade-analytics-101.js"></script>\n  <script defer src="nano-po-shortage-ui-100.js"></script>')
   blob=h.encode('utf8');changed.add(name)
  elif name=='release-notes.js':
   blob=notes(blob.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='package.json':
   h=blob.decode('utf8');assert json.loads(h)['version']=='1.0.100'
   blob=once(h,'"version": "1.0.100"','"version": "1.0.101"').encode('utf8');changed.add(name)
  entry['offset']=str(len(data));entry['size']=len(blob)
  if name in changed and 'integrity' in entry:
   i=entry['integrity'];i['hash']=SHA(blob);step=int(i.get('blockSize',4194304))
   i['blocks']=[SHA(blob[k:k+step]) for k in range(0,len(blob),step)]
  data.extend(blob)
  if name in changed:(work/name).write_bytes(blob)
 assert changed=={'index.html','release-notes.js','package.json','nano-po-shortage-ui-100.js'}
 name='nano-trade-analytics-101.js';blob=Path('development/trade/'+name).read_bytes()
 header['files'][name]={'size':len(blob),'offset':str(len(data)),
  'integrity':{'algorithm':'SHA256','hash':SHA(blob),'blockSize':4194304,'blocks':[SHA(blob)]}}
 data.extend(blob);(work/name).write_bytes(blob)
 packed=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8')
 padded=(len(packed)+7)&~3
 final=struct.pack('<4I',4,padded+4,padded,len(packed))+packed+b'\0'*(padded-4-len(packed))+data
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',final)
 with zipfile.ZipFile(target) as z:assert SHA(z.read('payload/app.asar'))==SHA(final)
 print(json.dumps({'version':'1.0.101','asar_sha256':SHA(final),'zip_sha256':SHA(target.read_bytes())}))
if __name__=='__main__':
 source,out,folder=map(Path,sys.argv[1:4]);folder.mkdir(parents=True,exist_ok=True)
 build(source,out,folder)
