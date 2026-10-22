#!/usr/bin/env python3
from pathlib import Path
import json,struct,zipfile,hashlib,re
f=Path('source/NANO-POS-Patch-1.0.106-to-1.0.107-CREDIT-CUSTOMER.zip')
m=json.loads(Path('nano-pos-update.json').read_text())
assert m['version']=='1.0.107' and hashlib.sha256(f.read_bytes()).hexdigest()==m['patches'][0]['sha256']
with zipfile.ZipFile(f) as z: b=z.read('payload/app.asar')
assert hashlib.sha256(b).hexdigest()==m['patches'][0]['appAsarSha256']
_,block,_,n=struct.unpack_from('<4I',b)
h=json.loads(b[16:16+n])['files']
def get(name):
 e=h[name];return b[8+block+int(e['offset']):8+block+int(e['offset'])+e['size']].decode()
out=[]
def emit(name,text):
 out.append('==== '+name+' ====\n'+text[:16000]+'\n')
bridge=get('browser-bridge.js')
p=bridge.index("if (channel === 'process-sale')")
emit('sale process bridge',bridge[p:p+16500])
p=bridge.find('const invoiceDebt')
if p>=0: emit('invoice debt helpers',bridge[p:p+3000])
for key in ['nano-record-settlement-102','cashTenderedAmount','nano_checkout_operation_id']:
 ps=[m.start() for m in re.finditer(re.escape(key),bridge)]
 emit('bridge refs '+key,'\n---\n'.join(bridge[max(0,p-320):p+850] for p in ps[:10]))
html=get('index.html')
p=html.index('<div id="checkoutModal"')
emit('checkout html',html[p:p+11500])
for name in ['nano-payment-quality-105.js','nano-cash-guide-106.js','nano-checkout-choice-104.js','nano-credit-picker-107.js']:
 emit(name,get(name)[:12500])
r=get('renderer.js')
for needle in ['async function processSale(){','function openCheckoutModal(){','function checkoutCalcChange(){']:
 p=r.index(needle);emit('renderer '+needle,r[p:p+3800])
dest=Path('development/trade/payment-audit-108.txt');dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text('\n'.join(out));print('verified audit',dest.stat().st_size)
