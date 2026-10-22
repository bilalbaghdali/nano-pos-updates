#!/usr/bin/env python3
"""Build targeted internal integration audit, no business user files included."""
from pathlib import Path
import json,hashlib,struct,zipfile,re
p=Path('source/NANO-POS-Patch-1.0.105-to-1.0.106-CASH-FASTSTART.zip')
manifest=json.loads(Path('nano-pos-update.json').read_text())
assert manifest['version']=='1.0.106'
assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['patches'][0]['sha256']
with zipfile.ZipFile(p) as z:
 assert z.namelist()==['payload/app.asar']
 raw=z.read('payload/app.asar')
assert hashlib.sha256(raw).hexdigest()==manifest['patches'][0]['appAsarSha256']
magic,block,hsize,n=struct.unpack_from('<4I',raw)
assert magic==4 and block==hsize+4
head=json.loads(raw[16:16+n])['files']
def get(name):
 try:
  e={'files':head}
  for key in name.split('/'):e=e['files'][key]
  return raw[8+block+int(e['offset']):8+block+int(e['offset'])+e['size']].decode('utf8')
 except: return ''
sections=[]
def append(title,text,max_len=7000):
 sections.append(f'\n==== {title} ({len(text)} chars) ====\n'+text[:max_len])
html=get('index.html')
for ident in ['checkoutModal','checkoutPaymentMethod','posCustomerSelect','checkoutPaidAmount','checkoutTotalUI',
              'addCustomerModal','customerModal','customerName','newCustomerName','customerAddModal']:
 m=re.search(r'''id=["']'''+re.escape(ident)+r'''["']''',html)
 if m: append('index #'+ident,html[max(0,m.start()-950):m.start()+2200],3300)
for name in ['renderer.js','browser-bridge.js','nano-payment-quality-105.js','nano-checkout-choice-104.js','nano-cash-guide-106.js']:
 src=get(name)
 if not src:continue
 append(name+' HEAD',src[:400],400)
 tokens={
  'renderer.js':['function openCheckoutModal','function processSale(','function processSaleAndPrintReceipt',
     'function checkoutMarkAsDebt','function checkoutCalcChange','function openAddCustomerModal','function saveCustomer',
     'function addCustomer','get-customers','create-customer','add-customer','posCustomerSelect','function renderCustomer',
     'function openCustomerModal','function showCustomerModal','function newCustomer','function loadCustomers'],
  'browser-bridge.js':["if (channel === 'process-sale')","channel === 'get-customers'",
    "channel === 'create-customer'","channel === 'add-customer'",'db.customers.push(','db.customers.unshift(',
    'function reviseCustomerBalance','function ensureCustomer','nano_checkout_operation_id'],
  'nano-payment-quality-105.js':['function render','function onModal','if(channel','process-sale','posCustomerSelect'],
  'nano-checkout-choice-104.js':['function paidFull','readTotal'],
  'nano-cash-guide-106.js':['function render','function eligible']
 }[name]
 for token in tokens:
  matches=list(re.finditer(re.escape(token),src,re.I))
  append(name+' '+token+' ['+str(len(matches))+']','\n---\n'.join(src[max(0,m.start()-260):m.start()+1400] for m in matches[:3]),4400)
# Search source for customer API across all JS to avoid missing name.
def walk(node,prefix=''):
 for name,e in node.items():
  if 'files' in e:yield from walk(e['files'],prefix+name+'/')
  elif name.endswith(('.js','.cjs')) and e.get('size',0)<3000000:
   yield prefix+name
allnames=list(walk(head))
needle=['add-customer','create-customer','save-customer','get-customers','nano-add-customer']
found=[]
for name in allnames:
 src=get(name)
 for token in needle:
  if token in src:found.append((name,token,src.count(token)))
append('all customer API symbols',repr(found),7000)
out=Path('development/trade/credit-checkout-audit-107.txt')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text('\n'.join(sections),encoding='utf8')
print('Audit source verified. Excerpts:',len(sections),'bytes:',out.stat().st_size)
