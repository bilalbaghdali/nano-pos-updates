#!/usr/bin/env python3
import hashlib,json,struct,sys,zipfile,re
from pathlib import Path
d=json.loads(Path('nano-pos-update.json').read_text())
p=Path(sys.argv[1])
assert hashlib.sha256(p.read_bytes()).hexdigest()==d['patches'][0]['sha256']
with zipfile.ZipFile(p) as z:
 assert z.namelist()==['payload/app.asar'];data=z.read('payload/app.asar')
assert hashlib.sha256(data).hexdigest()==d['patches'][0]['appAsarSha256']
magic,block,hs,n=struct.unpack_from('<4I',data)
assert magic==4 and block==hs+4
h=json.loads(data[16:16+n])['files']
def get(path):
 e=h
 for k in path.split('/'):e=e['files'][k]
 return data[8+block+int(e['offset']):8+block+int(e['offset'])+e['size']].decode('utf8')
for name in ['index.html','nano-checkout-choice-104.js','nano-payment-quality-105.js','nano-cash-change.js','nano-fast-pos.js','renderer.js','electron-main.cjs','main.js','main.cjs','package.json']:
 try:s=get(name)
 except:continue
 print('\n'+'### FILE '+name+' LENGTH '+str(len(s)))
 needles={
 'index.html':['id="checkoutModal"','id="checkoutTotalUI"','checkoutMarkAsDebt','id="checkoutPaidAmount"','<script src="','<script defer src="'],
 'nano-checkout-choice-104.js':['function readTotal','function paidFull'],
 'nano-payment-quality-105.js':['function render','function setProcessing','checkoutRequestId'],
 'nano-cash-change.js':['function init','function prepare','function history','cashTendered','T().history'],
 'nano-fast-pos.js':['function setupPayment','DOMContentLoaded','setupPayment();'],
 'renderer.js':['function openCheckoutModal','function closeCheckoutModal','function processSale','function checkoutCalcChange','function checkoutMarkAsDebt','DOMContentLoaded','window.onload','setInterval(','refreshDashboard','loadProducts'],
 'electron-main.cjs':['whenReady','BrowserWindow','webPreferences','backgroundThrottling','show:','ready-to-show','setInterval','setTimeout','app.commandLine','disableHardwareAcceleration'],
 'main.js':['whenReady','BrowserWindow','webPreferences','ready-to-show'],
 'main.cjs':['whenReady','BrowserWindow','ready-to-show'],
 'package.json':['"main"']
 }.get(name,[])
 for k in needles:
  hits=list(re.finditer(re.escape(k),s))
  print('TERM',repr(k),'COUNT',len(hits))
  for match in hits[:4]:
   start=max(0,match.start()-(250 if name not in ('renderer.js','index.html') else 130))
   end=min(len(s),match.end()+(1450 if name in ('renderer.js','electron-main.cjs','nano-cash-change.js') else 650))
   print('SNIP',repr(s[start:end]))
 if name=='package.json':print('BODY',s[:6000])
