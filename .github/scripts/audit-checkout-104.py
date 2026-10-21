#!/usr/bin/env python3
"""Read-only checkout DOM and payment path audit from verified v1.0.103 ASAR."""
import zipfile,struct,json,re,hashlib,sys
from pathlib import Path
source=Path(sys.argv[1]);m=json.loads(Path('nano-pos-update.json').read_text())
assert m['version']=='1.0.103'
assert hashlib.sha256(source.read_bytes()).hexdigest()==m['patches'][0]['sha256']
with zipfile.ZipFile(source) as z:
 assert z.namelist()==['payload/app.asar'];data=z.read('payload/app.asar')
assert hashlib.sha256(data).hexdigest()==m['patches'][0]['appAsarSha256']
magic,block,hs,n=struct.unpack_from('<4I',data);assert magic==4 and block==hs+4
header=json.loads(data[16:16+n])
def find(name):
 node=header
 for part in name.split('/'):node=node['files'][part]
 offset=8+block+int(node['offset']);return data[offset:offset+node['size']]
print('OFFICIAL ASAR verified',hashlib.sha256(data).hexdigest())
patterns={
 'index.html':['checkoutPaidAmount','cashTenderedAmount','checkoutPaymentMethod','checkoutModal','nanoSplitEditor102','receivedAmount','مبلغ مستلم','المبلغ المستلم','المبلغ الذي قدمه','changeAmount','amountReceived'],
 'browser-bridge.js':["if (channel === 'process-sale')",'cashTenderedAmount','payment_method','paid_amount','__nanoSplit102','nano-record-settlement-102'],
 'nano-split-ui-102.js':['nanoSplitEditor102','checkoutPaidAmount','process-sale','checkoutPaymentMethod'],
 'nano-payment-ledger-102.js':['function split(','function settle('],
 'release-notes.js':['FALLBACK_VERSION'],
}
for name,needles in patterns.items():
 blob=find(name);s=blob.decode('utf8')
 print('FILE',name,'size',len(blob),'sha256',hashlib.sha256(blob).hexdigest())
 for needle in needles:
  ms=list(re.finditer(re.escape(needle),s,re.I));print('MATCH',needle,len(ms))
  for idx,x in enumerate(ms[:12]):
   a=max(0,x.start()-430);b=min(len(s),x.end()+550)
   print('CONTEXT',idx,repr(s[a:b]))
 print('HEAD',repr(s[:300]))

print('CHECKOUT_HTML_BEGIN')
html=find('index.html').decode('utf8')
begin=html.index('<div id="checkoutModal"');end=html.find('<!--',begin+500)
print(repr(html[begin:begin+7800]))
print('CHECKOUT_HTML_END')
terms=['checkoutCalcChange','checkoutUpdateStamp','checkoutPaidAmount','cashTenderedAmount','confirmCheckout','openCheckoutModal','closeCheckoutModal','processSale','process-sale','checkoutPay','checkoutChangeUI']
matches=[]
def walk(node,prefix=''):
 for k,e in node.get('files',{}).items():
  if 'files' in e:walk(e,prefix+k+'/')
  elif 'offset' in e and (prefix+k).endswith(('.js','.cjs')) and e.get('size',0)<1800000:
   matches.append((prefix+k,e))
walk(header)
for filename,entry in matches:
 try:s=find(filename).decode('utf8')
 except:continue
 located=[(term,list(re.finditer(re.escape(term),s,re.I))) for term in terms]
 matched=[(key,its) for key,its in located if its]
 if not matched:continue
 print('JAVASCRIPT',filename,'sha256',hashlib.sha256(s.encode()).hexdigest(),'size',len(s))
 for key,its in matched:
  print('MATCH',key,'COUNT',len(its))
  for m in its[:10]:
   a=max(0,m.start()-650);b=min(len(s),m.end()+950)
   print('CODE',repr(s[a:b]))
