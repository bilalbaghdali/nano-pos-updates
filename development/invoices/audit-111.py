#!/usr/bin/env python3
"""Print/sale numbering audit of official 1.0.110. Log excerpts only, no user data."""
import json,hashlib,struct,zipfile,re
from pathlib import Path
p=Path('source/NANO-POS-Patch-1.0.109-to-1.0.110-BLUE-PRINT.zip')
m=json.loads(Path('nano-pos-update.json').read_text())
assert m['version']=='1.0.110' and hashlib.sha256(p.read_bytes()).hexdigest()==m['patches'][0]['sha256']
with zipfile.ZipFile(p) as z:raw=z.read('payload/app.asar')
assert hashlib.sha256(raw).hexdigest()==m['patches'][0]['appAsarSha256']
magic,block,hs,n=struct.unpack_from('<4I',raw);assert magic==4 and block==hs+4
files=json.loads(raw[16:16+n])['files']
def get(name):
 e=files[name]
 return raw[8+block+int(e['offset']):8+block+int(e['offset'])+e['size']].decode('utf8')
out=[]
def section(title,src,terms=None,width=1500,maxper=5):
 out.append('=== '+title+' ('+str(len(src))+')')
 if terms is None:out.append(src[:21000]);return
 for term in terms:
  hits=list(re.finditer(re.escape(term),src,re.I))
  out.append('MARKER '+term+' '+str(len(hits)))
  for x in hits[:maxper]:
   a=max(0,x.start()-350);b=min(len(src),x.end()+width)
   out.append('MATCH '+repr(src[a:b]))
s=get('browser-bridge.js')
section('BRIDGE-SALE',s,[ "if (channel === 'process-sale')",'db.sales.unshift(sale)','invoice_number','invoiceNumber','receipt_number','sale_number','saveDb','save()', 'editSaleId','nano_checkout_operation_id'],2500)
s=get('renderer.js')
section('RENDERER',s,['function processSale(','async function processSale','openCheckoutModal','printInvoice','printReceipt','invoice_number','invoiceNumber','sale.invoice_number','sale.number','FA-','renderSales','editSaleId','get-sales'],1800)
s=get('print-engine.js')
section('PRINT-ENGINE',s,['function generateInvoice','function printInvoice','function printReceipt','invoice_number','invoiceNumber','documentNo','invoiceNo','sale.number','invoice-number','receipt_number','Factura','template','renderInvoice','renderReceipt'],2000)
s=get('document-print-preview.js')
section('PREVIEW',s,['const origInvoice','window.printInvoice','window.printReceipt','scope:', 'function show(', 'const styleText', 'function applyPaper', 'function decorate', 'function paper','let L=lang'],2800)
for name in ['invoice-models-engine.js','invoice_template_modern.html','invoice_template_detailed.html','receipt_template_1.html','invoice_thermal_modern_80.html']:
 try:s=get(name)
 except:continue
 section(name,s,['invoice_number','invoiceNumber','invoice-no','numero','رقم الفاتورة','رقم','sale.id','sale.number','invoice','total','header','table','title'],800,3)
dest=Path('development/invoices/audit-111.txt');dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text('\n'.join(out),encoding='utf8')
print('AUDIT GENERATED',len(out),'size',dest.stat().st_size)
