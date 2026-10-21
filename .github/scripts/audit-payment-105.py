#!/usr/bin/env python3
import hashlib,json,struct,sys,zipfile,re
from pathlib import Path
m=json.loads(Path('nano-pos-update.json').read_text())
with zipfile.ZipFile(sys.argv[1]) as z:
 assert z.namelist()==['payload/app.asar']
 data=z.read('payload/app.asar')
assert hashlib.sha256(data).hexdigest()==m['patches'][0]['appAsarSha256']
magic,block,hs,n=struct.unpack_from('<4I',data);assert magic==4 and block==hs+4
head=json.loads(data[16:16+n])['files']
def get(name):
 e=head[name];return data[8+block+int(e['offset']):8+block+int(e['offset'])+e['size']].decode('utf8')
bridge=get('browser-bridge.js')
p=bridge.index("if (channel === 'process-sale')")
print('BEGIN_SALE_BRIDGE')
print(bridge[p:p+17000])
print('END_SALE_BRIDGE')
h=get('index.html')
print('INDEX SCRIPT SNIPPETS')
for x in re.finditer(r'<script[^>]*src="[^"]+"[^>]*>',h):
 a=x.group()
 if any(key in a for key in ['renderer','bridge','nano-checkout','nano-payment','nano-cash','nano-fast','nano-split','nano-sale','nano-update']):
  print(a)
print('POS_CUSTOMER_ID REFS')
for k in ['posCustomerSelect','checkoutModal','checkoutTotalUI','nanoCheckoutChoice104','checkoutPaymentMethod']:
 print(k,h.count(k))
print('CHECKOUT CHOICE 104')
print(get('nano-checkout-choice-104.js'))
print('BRIDGE_START')
print(bridge[:5400])
print('BRIDGE_END')
