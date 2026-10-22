#!/usr/bin/env python3
import hashlib,json,struct,zipfile,re
from pathlib import Path
p=Path('source/NANO-POS-Patch-1.0.109-to-1.0.110-BLUE-PRINT.zip')
m=json.loads(Path('nano-pos-update.json').read_text())
with zipfile.ZipFile(p) as z:raw=z.read('payload/app.asar')
assert hashlib.sha256(raw).hexdigest()==m['patches'][0]['appAsarSha256']
_,b,_,n=struct.unpack_from('<4I',raw);h=json.loads(raw[16:16+n])['files']
def get(name):
 e=h[name];return raw[8+b+int(e['offset']):8+b+int(e['offset'])+e['size']].decode('utf8')
bridge=get('browser-bridge.js');render=get('renderer.js');center=get('document-print-preview.js')
slices={}
for name,source,pat,before,after in [
 ('sale_core',bridge,"const data = args[0] || {}, c = data.checkout || {};",400,9900),
 ('sale_object',bridge,"const sale = {",1800,3200),
 ('sale_object_compact',bridge,"const sale={",1800,3200),
 ('legacy_sale',bridge,"if (channel === 'process-sale')",800,5200),
 ('sale_edit',bridge,"if (channel === 'process-sale' && args[0]?.editSaleId != null)",100,8100),
 ('invoice_renderer',render,"async function printInvoice(",300,19700),
 ('receipt_renderer',render,"async function printReceipt(",300,12500),
 ('invoice_print_core',center,"async function W(",400,3500),
 ('invoice_preview',center,"function show(",400,9000)
]:
 at=source.find(pat);slices[name]=source[max(0,at-before):at+after] if at>=0 else '<NOT FOUND> '+pat
for name,value in slices.items():
 f=Path('development/invoices/review-111')/(name+'.txt')
 f.parent.mkdir(parents=True,exist_ok=True);f.write_text(value,'utf8')
 print(name,len(value))
