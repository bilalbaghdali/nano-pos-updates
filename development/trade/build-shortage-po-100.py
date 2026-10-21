#!/usr/bin/env python3
"""Build v1.0.100 solely from official SHA-verified v1.0.99. No data migrations."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
SHA=lambda blob:hashlib.sha256(blob).hexdigest()
BASE='4bb28eafd2486691beb80769bfc8d0daca6bc8d2a02d2917794c95014b6c0bc4'
def one(s,a,b):
    assert s.count(a)==1,('source_marker_changed',a[:110],s.count(a))
    return s.replace(a,b)
def modify_shortages(s):
    s=one(s,
      "return {id:product.id??product.product_id,name:String(product.name||product.product_name||product.title||'').trim()||'—',",
      "return {id:product.id??product.product_id,supplierId:product.supplier_id??product.supplierId??null,"
      "costPrice:product.cost_price??product.purchase_price??null,"
      "name:String(product.name||product.product_name||product.title||'').trim()||'—',")
    s=one(s,
      "for(const name of ['nanoShortagePrint180','nanoShortageSend180','nanoShortageCSV180'])",
      "for(const name of ['nanoShortagePrint180','nanoShortageSend180','nanoShortageCSV180','nanoShortageCreatePO100'])")
    marker="actions.append(make('nanoShortageRefresh180',t.refresh,refresh),make('nanoShortageForecast198',FL().button,estimateDemand),make('nanoShortagePrint180',t.print,printList));"
    replacement=marker+"""
 const poLang=String(root.currentLanguage||doc.documentElement.lang||'ar').toLowerCase().slice(0,2);
 const poButtonText={ar:'إنشاء أوامر شراء — اختيار المورد تلقائيًا',fr:'Commander — fournisseur automatique',
   en:'Create orders — auto supplier'};
 actions.append(make('nanoShortageCreatePO100',poButtonText[poLang]||poButtonText.ar,()=>{
   const handler=root.NANO_PO_SHORTAGE_100?.open;
   if(typeof handler!=='function'){notify(L().sendError,'warning');return;}
   Promise.resolve(handler(data.map(row=>({...row})))).catch(error=>notify(error?.message||L().sendError,'warning'));
 }));
"""
    s=one(s,marker,replacement)
    return s
def release_notes(s):
    s=one(s,"const FALLBACK_VERSION = '1.0.99';","const FALLBACK_VERSION = '1.0.100';")
    start=s.index('  const OFFLINE = {')
    end=s.index('  const TITLES = {',start)
    return s[:start]+"""  const OFFLINE = {
    ar:['إنشاء أوامر شراء مباشرة من المنتجات الناقصة مع اختيار المورد المعروف تلقائيًا.',
        'اقتراح المورد حسب ربط المنتج أو أقل سعر شراء حديث موثق؛ المنتجات بلا مورد تحتاج مراجعة.',
        'خصم الكميات المطلوبة بالفعل في أوامر شراء مفتوحة لمنع طلبها مرتين.',
        'مراجعة الكميات والأسعار والموردين قبل إنشاء الأوامر، دون تعديل المخزون أو ديون الموردين.'],
    fr:['Créer des bons de commande à partir des ruptures avec fournisseur suggéré.',
        'Fournisseur du produit ou meilleur prix récent ; sélection manuelle si inconnue.',
        'Déduction des quantités déjà commandées mais non reçues.',
        'Validation manuelle avant création, sans mouvement de stock ni de dettes.'],
    en:['Create purchase orders from low-stock products with auto-selected known suppliers.',
        'Product supplier or best recent recorded purchase price; review unknown suppliers.',
        'Subtract outstanding quantities from pending purchase orders.',
        'Review supplier, quantity and cost before saving; no stock/debt postings.']
  };
"""+s[end:]
def build(source,target,work):
    with zipfile.ZipFile(source) as z:
        assert z.namelist()==['payload/app.asar']
        raw=z.read('payload/app.asar')
    assert SHA(raw)==BASE,'unverified_asar_source'
    magic,block,hs,n=struct.unpack_from('<4I',raw)
    assert magic==4 and block==hs+4
    head=json.loads(raw[16:16+n]);start=8+block;parts=[]
    for name in ('nano-po-auto-supplier-100.js','nano-po-shortage-ui-100.js'):
        assert name not in head['files'], 'duplicate_module'
    def walk(node,prefix=''):
        for k,v in node.get('files',{}).items():
            if 'files' in v:walk(v,prefix+k+'/')
            elif 'offset' in v:parts.append((prefix+k,v))
    walk(head);assert len(parts)>200
    parts.sort(key=lambda t:int(t[1]['offset']))
    new=bytearray();changed=set()
    for path,entry in parts:
        pos=start+int(entry['offset']);original=raw[pos:pos+entry['size']]
        assert len(original)==entry['size']
        if path=='nano-inventory-shortages.js':
            content=modify_shortages(original.decode('utf8')).encode('utf8');changed.add(path)
        elif path=='index.html':
            html=original.decode('utf8')
            html=one(html,'<script defer src="nano-inventory-shortages.js"></script>',
                '<script defer src="nano-po-auto-supplier-100.js"></script>\\n'
                '  <script defer src="nano-po-shortage-ui-100.js"></script>\\n'
                '  <script defer src="nano-inventory-shortages.js"></script>')
            # The script elements need real newline between them.
            html=html.replace('</script>\\n','</script>\n')
            content=html.encode('utf8');changed.add(path)
        elif path=='release-notes.js':
            content=release_notes(original.decode('utf8')).encode('utf8');changed.add(path)
        elif path=='package.json':
            src=original.decode('utf8')
            assert json.loads(src)['version']=='1.0.99'
            content=one(src,'"version": "1.0.99"','"version": "1.0.100"').encode('utf8');changed.add(path)
        else:content=original
        entry['offset']=str(len(new));entry['size']=len(content)
        if path in changed and 'integrity' in entry:
            integ=entry['integrity'];integ['hash']=SHA(content)
            size=int(integ.get('blockSize',4194304))
            integ['blocks']=[SHA(content[i:i+size]) for i in range(0,len(content),size)]
        new.extend(content)
        if path in changed:
            (work/path).parent.mkdir(parents=True,exist_ok=True);(work/path).write_bytes(content)
    assert changed=={'nano-inventory-shortages.js','index.html','release-notes.js','package.json'}
    for name in ['nano-po-auto-supplier-100.js','nano-po-shortage-ui-100.js']:
        blob=Path('development/trade/'+name).read_bytes()
        head['files'][name]={'size':len(blob),'offset':str(len(new)),
          'integrity':{'algorithm':'SHA256','hash':SHA(blob),'blockSize':4194304,'blocks':[SHA(blob)]}}
        new.extend(blob);(work/name).write_bytes(blob)
    meta=json.dumps(head,separators=(',',':'),ensure_ascii=False).encode('utf8')
    pad=(len(meta)+7)&~3
    out=struct.pack('<4I',4,pad+4,pad,len(meta))+meta+b'\0'*(pad-4-len(meta))+new
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',out)
    with zipfile.ZipFile(target) as z:
        assert SHA(z.read('payload/app.asar'))==SHA(out)
    print(json.dumps({'version':'1.0.100','modified':sorted(changed),
      'ASARSha256':SHA(out),'PatchSha256':SHA(target.read_bytes())}))
if __name__=='__main__':
    src,dst,work=map(Path,sys.argv[1:4]);work.mkdir(parents=True,exist_ok=True)
    build(src,dst,work)
