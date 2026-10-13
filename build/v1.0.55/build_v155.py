#!/usr/bin/env python3
"""NANO POS 1.0.55. Fix customer Sales & Debts window return shape in desktop and mobile.

Only reads customer ledgers, never changes store data. Builder rejects changed upstream
bytes, failed tests, unexpected changes, and mismatched GitHub release checksums.
"""
from __future__ import annotations
import copy,hashlib,json,pathlib,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.54/NANO-POS-Patch-1.0.53-to-1.0.54-CUSTOMER-FETCH-FIX.zip'
BASE_SHA='91fd9cb683747b693a323f48b04142deb4ddf423999d1924ac9b02f5a80663fe'
BASE_ASAR_SHA='de8a0f89a838dc8f66718ce27ae66601bd12e7bfae10e5844416345d1242a65b'
ASSET='NANO-POS-Patch-1.0.54-to-1.0.55-CUSTOMER-SALES-DEBTS-FIX.zip'
def sha(data):return hashlib.sha256(data).hexdigest()
def parse(raw):
 n=struct.unpack('<I',raw[12:16])[0];h=json.loads(raw[16:16+n]);start=8+struct.unpack('<I',raw[4:8])[0];out={}
 def walk(branch,prefix=''):
  for name,item in branch['files'].items():
   path=prefix+name
   if 'files' in item:walk(item,path+'/')
   else:
    pos=start+int(item['offset']);size=int(item['size']);d=raw[pos:pos+size]
    assert len(d)==size,('truncated asar entry',path)
    out[path]=(item,d)
 walk(h);return out
def pack(files):
 tree={'files':{}};content=[];offset=0
 for path,(old,data) in files.items():
  node=tree
  parts=path.split('/')
  for p in parts[:-1]:node=node['files'].setdefault(p,{'files':{}})
  meta=copy.deepcopy(old);meta['size']=len(data);meta['offset']=str(offset)
  block=int(meta.get('integrity',{}).get('blockSize',4194304))
  meta['integrity']={'algorithm':'SHA256','hash':sha(data),'blockSize':block,
    'blocks':[sha(data[i:i+block]) for i in range(0,len(data),block)]}
  node['files'][parts[-1]]=meta
  offset+=len(data);content.append(data)
 body=json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode('utf8');padded=(len(body)+3)&~3
 return struct.pack('<IIII',4,padded+8,padded+4,len(body))+body+b'\x00'*(padded-len(body))+b''.join(content)
def revised(original):
 files=dict(original)
 def get(name):
  assert name in original,('Missing source file',name)
  return original[name][1].decode('utf8')
 def put(name,s):files[name]=(original.get(name,({},b''))[0],s.encode('utf8'))
 legacy="if (channel === 'get-customer-sales') return clone(db.sales.filter(s => s.customer_id == args[0]));"
 canonical="""if (channel === 'get-customer-sales') {
     // Customer details window expects sales, payments and customer (not a bare array).
     // This is read-only: never change customer balance, invoice, or payment records here.
     const customerId=String(args[0]);
     const customer=(db.customers || []).find(c=>String(c.id)===customerId) || null;
     const sales=(db.sales || []).filter(s=>String(s.customer_id)===customerId);
     const general=(db.customer_payments || []).filter(p=>String(p.customer_id)===customerId).map(p=>({...p,amount:Number(p.amount ?? 0)}));
     const invoice=sales.flatMap(s=>(Array.isArray(s.payments)?s.payments:[])
       .filter(p=>p && p.source!=='customer-payment')
       .map(p=>({...p,amount:Number(p.amount ?? 0),invoice_num:p.invoice_num ?? s.invoice_num ?? s.id,date:p.date || s.sale_date || s.created_at})));
     return {sales:clone(sales),payments:clone([...general,...invoice]),customer:clone(customer)};
   }"""
 for name in ('browser-bridge.js','mobile/www/browser-bridge.js'):
  src=get(name)
  assert src.count(legacy)==1,('Browser bridge contract changed',name,src.count(legacy))
  put(name,src.replace(legacy,canonical,1))
 old="const {sales:_0x5cb309,payments:_0x34a4af,customer:_0x1d53ef}=await window[_0xacf453(0x620)]['getCustomerSales'](_0x1d1c37),"
 new="const {sales:_0x5cb309,payments:_0x34a4af,customer:_0x1d53ef}=await window.nanoGetCustomerSalesAndDebts(_0x1d1c37,_0x5129dd),"
 for name in ('renderer.js','mobile/www/renderer.js'):
  src=get(name)
  assert src.count(old)==1,('Customer details view signature changed',name,src.count(old))
  put(name,src.replace(old,new,1))
 for name in ('index.html','mobile/www/index.html'):
  html=get(name);marker='<script src="renderer.js"></script>'
  assert html.count(marker)==1,('Renderer script tag changed',name)
  assert 'nano-customer-details-fix.js' not in html
  put(name,html.replace(marker,'<script src="nano-customer-details-fix.js"></script>\n'+marker,1))
 js=(ROOT/'nano-customer-details-fix.js').read_text('utf8')
 for name in ('nano-customer-details-fix.js','mobile/www/nano-customer-details-fix.js'):
  assert name not in original,('Helper already exists',name)
  put(name,js)
 pkg=json.loads(get('package.json'))
 assert pkg['version']=='1.0.54',pkg['version']
 pkg['version']='1.0.55';put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
 if 'package-lock.json' in files:
  lock=json.loads(get('package-lock.json'));lock['version']='1.0.55'
  if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):lock['packages']['']['version']='1.0.55'
  put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
 if 'app-config.js' in files:
  cfg=get('app-config.js');updated=cfg.replace("|| '1.0.54'","|| '1.0.55'")
  assert updated!=cfg,'App config version tag changed';put('app-config.js',updated)
 if 'release-notes.js' in files:
  notes=get('release-notes.js');a=notes.find('const F=');b=notes.find(';',a)
  assert a>=0 and b>a
  feature={'ar':['تحسينات استقرار النظام.'],'fr':['Améliorations de stabilité du système.'],'en':['System stability improvements.']}
  put('release-notes.js',notes[:a]+'const F='+json.dumps(feature,ensure_ascii=False,separators=(',',':'))+notes[b:])
 for name in ('renderer.js','mobile/www/renderer.js','browser-bridge.js','mobile/www/browser-bridge.js','nano-customer-details-fix.js'):
  f=ROOT/('_check_'+name.replace('/','_'));f.write_bytes(files[name][1]);subprocess.run(['node','--check',str(f)],check=True,timeout=20)
 subprocess.run(['node',str(ROOT/'test_customer_detail.cjs'),str(ROOT/'nano-customer-details-fix.js')],check=True,timeout=20)
 subprocess.run(['node',str(ROOT/'test_bridge.cjs'),str(ROOT/'_check_browser-bridge.js'),str(ROOT/'_check_mobile_www_browser-bridge.js')],check=True,timeout=30)
 subprocess.run(['node',str(ROOT/'../v1.0.53/test_finance.cjs'),str(ROOT/'_check_browser-bridge.js'),str(ROOT/'_check_mobile_www_browser-bridge.js')],check=True,timeout=30)
 allowed={'browser-bridge.js','mobile/www/browser-bridge.js','renderer.js','mobile/www/renderer.js','index.html','mobile/www/index.html','nano-customer-details-fix.js','mobile/www/nano-customer-details-fix.js','package.json','package-lock.json','app-config.js','release-notes.js'}
 changed=[k for k in files if k not in original or files[k][1]!=original[k][1]]
 assert set(changed).issubset(allowed) and set(['browser-bridge.js','renderer.js','nano-customer-details-fix.js','index.html']).issubset(changed),changed
 # Enforce script ordering and avoid any change in persisted data, app business modules, or DB code.
 for name in ('index.html','mobile/www/index.html'):
  html=files[name][1].decode('utf8');assert html.index('nano-customer-details-fix.js')<html.index('<script src="renderer.js"></script>')
 return files,changed

def main():
 base=ROOT/'published-base-v154.zip'
 if not base.exists():
  with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v155-verified-builder'}),timeout=180) as response:base.write_bytes(response.read())
 assert sha(base.read_bytes())==BASE_SHA,'Refusing unexpected published v1.0.54 file'
 with zipfile.ZipFile(base) as z:
  assert z.testzip() is None
  raw=z.read('payload/app.asar')
 assert sha(raw)==BASE_ASAR_SHA,'Refusing changed original app.asar'
 before=parse(raw)
 files,changed=revised(before)
 packed=pack(files)
 extracted=parse(packed)
 assert set(files)==set(extracted)
 assert all(files[k][1]==extracted[k][1] for k in files)
 output=ROOT/ASSET
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',packed)
 with zipfile.ZipFile(output) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
 result={'fileName':ASSET,'sizeBytes':output.stat().st_size,'sha256':sha(output.read_bytes()),'appAsarSha256':sha(packed),'fromVersion':'1.0.54','toVersion':'1.0.55','changedFiles':changed,'verifiedCustomerSalesDetailsShape':True,'passedExistingAccountingRegression':True,'modifiedBusinessData':False}
 (ROOT/'build-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()