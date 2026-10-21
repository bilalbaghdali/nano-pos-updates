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

for name in ['package.json','index.html','nano-cash-change.js','nano-checkout-choice-104.js','renderer.js','electron-main.cjs','main.js','main.cjs']:
 try: content=get(name)
 except:continue
 print('FILE',name,'SIZE',len(content))
 if name=='package.json':
  obj=json.loads(content);print('MAIN',obj.get('main'));print('SCRIPTS',obj.get('scripts'))
  continue
 terms={
 'index.html':['id="checkoutTotalUI"','id="checkoutModal"','id="checkoutPaidAmount"'],
 'nano-cash-change.js':['function init(){','function prepare(payload){','function history(){','root.NANO_CASH_CHANGE_178','function T()'],
 'nano-checkout-choice-104.js':['function paidFull'],
 'renderer.js':['function checkoutMarkAsDebt','function processSale','function checkoutCalcChange','function openCheckoutModal','DOMContentLoaded'],
 'electron-main.cjs':['app.whenReady','new BrowserWindow','ready-to-show','loadFile','setInterval','setTimeout'],
 'main.js':['app.whenReady','new BrowserWindow','ready-to-show','loadFile','setInterval'],
 'main.cjs':['app.whenReady','new BrowserWindow','ready-to-show','loadFile','setInterval']
 }.get(name,[])
 for term in terms:
  pos=content.find(term);print('KEY',term,'POS',pos)
  if pos>=0:print('SAMPLE',repr(content[max(0,pos-160):pos+650]))
 print('SCRIPTS_COUNT',len(re.findall(r'<script[^>]+src=',content)) if name=='index.html' else '')
