#!/usr/bin/env python3
import json,hashlib,zipfile,struct
from pathlib import Path
p=Path('source/NANO-POS-Patch-1.0.108-to-1.0.109-PAYMENT-LABEL.zip')
m=json.loads(Path('nano-pos-update.json').read_text())
with zipfile.ZipFile(p) as z:raw=z.read('payload/app.asar')
assert hashlib.sha256(raw).hexdigest()==m['patches'][0]['appAsarSha256']
magic,b,hs,n=struct.unpack_from('<4I',raw)
assert magic==4 and b==hs+4
head=json.loads(raw[16:16+n])
names=['document-print-preview.js','invoice-models-engine.js','invoice-models-preview.js','print-engine.js','receipt_template_1.html','receipt_template_2.html','receipt_template_3.html','receipt_template_4.html','receipt_template_5.html','receipt_template_premium_thermal.html','invoice_thermal_modern_80.html','invoice_template_modern.html','invoice_template_detailed.html','invoice_template_a5.html','order_receipt_ar.html','payment_receipt_ar.html']
for name in names:
 e=head['files'][name]
 content=raw[8+b+int(e['offset']):8+b+int(e['offset'])+e['size']]
 out=Path('development/print/reference-110')/name
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_bytes(content)
 print(name,len(content))
