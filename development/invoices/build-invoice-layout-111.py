#!/usr/bin/env python3
"""NANO POS 1.0.111: annual FA invoice numbers committed with sales, true blue print DOM.
Source: SHA-256-verified official 1.0.110 ASAR. Existing business data untouched.
"""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
H=lambda s:hashlib.sha256(s).hexdigest()
BASE="2de62f917f321a629148cfe9e5dd906949330f668f218809d29b68137c286ba9"
def once(src,old,new):
 count=src.count(old)
 assert count==1,("source_drift",old[:130],count)
 return src.replace(old,new)
def bridge(src):
 src=once(src,
   "     if (remaining > 0 && !customer) return fail('البيع بالدين أو التسديد الجزئي يتطلب اختيار زبون مسجّل.');",
   """     if (remaining > 0 && !customer) return fail('البيع بالدين أو التسديد الجزئي يتطلب اختيار زبون مسجّل.');
     // Reserve a yearly invoice number before editing stock. The counter will
     // only be committed with this sale in the one atomic data snapshot.
     let invoicePlan111;
     try { invoicePlan111=window.NANO_INVOICE_SEQUENCE_111.next(db,new Date()); }
     catch(error){return fail('تعذر توليد رقم فاتورة فريد: '+String(error.message||error));}""")
 src=once(src,"     db.sales.unshift(sale);\n     if(__nanoId105){",
   """     sale.invoice_number=window.NANO_INVOICE_SEQUENCE_111.commit(db,invoicePlan111);
     db.sales.unshift(sale);
     if(__nanoId105){""")
 src=once(src,
   "         return {success:true,id:old.id,saleId:old.id,alreadyProcessed:true,",
   "         return {success:true,id:old.id,saleId:old.id,invoice_number:old.invoice_number,alreadyProcessed:true,")
 src=once(src,
   "     return { success:true,id,saleId:id,paid_amount:sale.paid_amount,remaining_amount:remaining,customerId:sale.customer_id };",
   "     return { success:true,id,saleId:id,invoice_number:sale.invoice_number,paid_amount:sale.paid_amount,remaining_amount:remaining,customerId:sale.customer_id };")
 return src
def preview(src):
 old="h=window.NANO_BLUE_PRINT_110.render(h,{paper:paper,language:l,color:color,scope:scope});"
 new="""h=window.NANO_BLUE_PRINT_110.render(h,{paper:paper,language:l,color:color,scope:scope});
   if(!window.NANO_INVOICE_LAYOUT_111?.render)throw Error('NANO POS 111 invoice layout missing');
   h=window.NANO_INVOICE_LAYOUT_111.render(h,{paper:paper,language:l,scope:scope});"""
 return once(src,old,new)
def notes(src):
 src=once(src,"const FALLBACK_VERSION = '1.0.110';","const FALLBACK_VERSION = '1.0.111';")
 i=src.index("  const OFFLINE = {");j=src.index("  const TITLES = {",i)
 return src[:i]+"""  const OFFLINE = {
    ar:['إصلاح تصميم فاتورة ووصل البيع: إعادة تركيب العنوان وبيانات المتجر والزبون والمجاميع بالأزرق والأبيض لكل المقاسات.',
        'الترقيم السنوي للفواتير الجديدة FA-2026-01 ثم FA-2026-02، ويبدأ من 01 في السنة التالية.',
        'الترقيم محفوظ مع الفاتورة في نفس عملية تسجيل المخزون والدين، ولا يتغير بالتعديل أو إعادة الطباعة.',
        'الحفاظ على معلومات الفواتير القديمة وصور شعار المتجر وQR دون صور المنتجات، ومطابقة المعاينة للطابعة وPDF.'],
    fr:['Recomposition du design bleu/blanc des factures et tickets, pour tous les formats de papier.',
        'Numéros annuels FA-AAAA-01, enregistrés atomiquement avec chaque nouvelle vente.',
        'Numéro inchangé lors de la modification/réimpression; anciennes factures conservées.',
        'Aperçu, impression et PDF identiques, logo et QR préservés, sans photos produit.'],
    en:['Recompose blue and white invoices/receipts across all paper sizes.',
        'New sales receive yearly sequential FA-YYYY-01 invoice numbers in the atomic sale record.',
        'Reprint and edit preserve numbers; prior invoices are not rewritten.',
        'Preview matches printing and PDF, with logo/QR intact and no product photographs.']
  };
"""+src[j:]
def build(source,out,work):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar'];raw=z.read('payload/app.asar')
 assert H(raw)==BASE,('source_asar_mismatch',H(raw))
 magic,block,hs,n=struct.unpack_from('<4I',raw);assert magic==4 and block==hs+4
 head=json.loads(raw[16:16+n]);base=8+block
 for new in ['nano-invoice-sequence-111.js','nano-invoice-layout-111.js']:
  assert new not in head['files']
 members=[]
 def walk(node,p=''):
  for name,e in node.get('files',{}).items():
   if 'files' in e:walk(e,p+name+'/')
   elif 'offset' in e:members.append((p+name,e))
 walk(head);assert len(members)>200
 members.sort(key=lambda v:int(v[1]['offset']))
 changes={'browser-bridge.js':bridge,'document-print-preview.js':preview,'release-notes.js':notes}
 payload=bytearray();modified=set()
 for name,e in members:
  blob=raw[base+int(e['offset']):base+int(e['offset'])+e['size']]
  assert len(blob)==e['size']
  if name in changes:
   blob=changes[name](blob.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='renderer.js':
   # The original print engine had a FAC fallback that would prefix "FA-..."
   # with FAC. Recognize the stored FA numbering as a finished reference.
   script=blob.decode('utf8')
   assert script.count("!/^(FAC|AV|FR)-/i")==2,'Expected both invoice print branches'
   script=script.replace("!/^(FAC|AV|FR)-/i","!/^(FA|FAC|AV|FR)-/i")
   blob=script.encode('utf8');modified.add(name)
  elif name=='index.html':
   script=blob.decode('utf8')
   script=once(script,
     '<script src="nano-blue-print-110.js"></script>',
     '<script src="nano-blue-print-110.js"></script>\n    <script src="nano-invoice-layout-111.js"></script>')
   script=once(script,'src="browser-bridge.js"',
     'src="nano-invoice-sequence-111.js"></script>\n    <script src="browser-bridge.js"')
   assert script.index('src="nano-invoice-sequence-111.js"')<script.index('src="browser-bridge.js"')
   blob=script.encode('utf8');modified.add(name)
  elif name=='package.json':
   script=blob.decode('utf8');assert json.loads(script)['version']=='1.0.110'
   blob=once(script,'"version": "1.0.110"','"version": "1.0.111"').encode('utf8');modified.add(name)
  e['offset']=str(len(payload));e['size']=len(blob)
  if name in modified and 'integrity' in e:
   integrity=e['integrity'];integrity['hash']=H(blob)
   stride=int(integrity.get('blockSize',4194304))
   integrity['blocks']=[H(blob[i:i+stride]) for i in range(0,len(blob),stride)]
  payload.extend(blob)
  if name in modified or name in ('nano-blue-print-110.js','invoice_template_modern.html','invoice_thermal_modern_80.html','receipt_template_1.html','nano-payment-ledger-102.js'):
   dest=work/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob)
 assert modified=={'browser-bridge.js','document-print-preview.js','release-notes.js','renderer.js','index.html','package.json'}
 for name in ['nano-invoice-sequence-111.js','nano-invoice-layout-111.js']:
  blob=Path('development/invoices/'+name).read_bytes()
  head['files'][name]={'size':len(blob),'offset':str(len(payload)),
    'integrity':{'algorithm':'SHA256','hash':H(blob),'blockSize':4194304,'blocks':[H(blob)]}}
  payload.extend(blob);(work/name).write_bytes(blob)
 metadata=json.dumps(head,separators=(',',':'),ensure_ascii=False).encode('utf8')
 padded=(len(metadata)+7)&~3
 asar=struct.pack('<4I',4,padded+4,padded,len(metadata))+metadata+b'\0'*(padded-4-len(metadata))+payload
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',asar)
 with zipfile.ZipFile(out) as z:assert H(z.read('payload/app.asar'))==H(asar)
 print(json.dumps({'version':'1.0.111','modified':sorted(modified),'asar_sha256':H(asar),'zip_sha256':H(out.read_bytes())}))
if __name__=='__main__':
 a,b,c=map(Path,sys.argv[1:4]);c.mkdir(parents=True,exist_ok=True);build(a,b,c)
