#!/usr/bin/env python3
"""Create the small, versioned NANO POS customer-list RPC repair from exact v1.0.53."""
import copy, hashlib, json, pathlib, struct, subprocess, urllib.request, zipfile
from patch_v154 import patch_files
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.53/NANO-POS-Patch-1.0.52-to-1.0.53-MOBILE-CREDIT-DEBTS.zip'
BASE_SHA='f37fcff274d031b308ac36e8363a7ef3bc815bbd2070eca2e26d130f77788a23'
BASE_ASAR_SHA='790d58cd46d315bd903334de5c09d00198e4aa9c61557a4ff979e057ebc622de'
ASSET='NANO-POS-Patch-1.0.53-to-1.0.54-CUSTOMER-FETCH-FIX.zip'

def sha(data):return hashlib.sha256(data).hexdigest()
def unpack(data):
 n=struct.unpack('<I',data[12:16])[0];tree=json.loads(data[16:16+n]);base=8+struct.unpack('<I',data[4:8])[0];files={}
 def walk(node,prefix=''):
  for key,item in node['files'].items():
   path=prefix+key
   if 'files' in item:walk(item,path+'/')
   else:
    size=item['size'];pos=base+int(item['offset']);content=data[pos:pos+size]
    assert len(content)==size,('truncated asar',path)
    files[path]=(item,content)
 walk(tree);return files

def pack(files):
 header={'files':{}};data=[];offset=0
 for path,(metadata,content) in files.items():
  node=header
  keys=path.split('/')
  for part in keys[:-1]:node=node['files'].setdefault(part,{'files':{}})
  meta=copy.deepcopy(metadata)
  meta['offset']=str(offset);meta['size']=len(content)
  block=meta.get('integrity',{}).get('blockSize',4194304)
  meta['integrity']={'algorithm':'SHA256','hash':sha(content),'blockSize':block,'blocks':[sha(content[i:i+block]) for i in range(0,len(content),block)]}
  node['files'][keys[-1]]=meta
  offset+=len(content);data.append(content)
 body=json.dumps(header,ensure_ascii=False,separators=(',',':')).encode();padded=(len(body)+3)&~3
 return struct.pack('<IIII',4,padded+8,padded+4,len(body))+body+b'\0'*(padded-len(body))+b''.join(data)

def main():
 base=pathlib.Path('base-v153.zip')
 if not base.exists():
  request=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v154-verified-build'})
  with urllib.request.urlopen(request,timeout=200) as response:base.write_bytes(response.read())
 assert sha(base.read_bytes())==BASE_SHA,'Base 1.0.53 ZIP checksum invalid'
 with zipfile.ZipFile(base) as z:
  assert z.testzip() is None
  raw=z.read('payload/app.asar')
 assert sha(raw)==BASE_ASAR_SHA,'Base v1.0.53 app.asar checksum invalid'
 original=unpack(raw);updated=dict(original)
 def get(name):
  assert name in original,'Expected packed file missing: '+name
  return original[name][1].decode('utf8')
 def put(name,content):
  metadata=original[name][0] if name in original else {}
  updated[name]=(metadata,content.encode('utf8'))
 patch_files(get,put)
 assert 'nano-customer-contract.cjs' not in original
 put('nano-customer-contract.cjs',(ROOT/'nano-customer-contract.cjs').read_text('utf8'))
 pkg=json.loads(get('package.json'));assert pkg['version']=='1.0.53',pkg['version']
 pkg['version']='1.0.54';put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
 if 'package-lock.json' in original:
  lock=json.loads(get('package-lock.json'));lock['version']='1.0.54'
  if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):lock['packages']['']['version']='1.0.54'
  put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
 if 'app-config.js' in original:
  config=get('app-config.js');new=config.replace("|| '1.0.53'","|| '1.0.54'")
  assert new!=config,'Version fallback not found in original'
  put('app-config.js',new)
 if 'release-notes.js' in original:
  notes=get('release-notes.js');a=notes.find('const F=');b=notes.find(';',a)
  assert a>=0 and b>a,'Release notes layout changed'
  features={'ar':['تحسينات استقرار النظام وإصلاح جلب بيانات الزبائن على الهاتف.'],'fr':['Améliorations de stabilité et correction de la liste clients sur mobile.'],'en':['System stability improvements and mobile customer lookup reliability.']}
  put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])
 changed=[p for p in updated if p not in original or updated[p][1]!=original[p][1]]
 allowed={'mobile-sync-server.cjs','mobile/www/mobile-sync-bridge.js','mobile/www/nano-mobile-credit.js','nano-customer-contract.cjs','package.json','package-lock.json','app-config.js','release-notes.js'}
 assert set(changed).issubset(allowed) and {'mobile-sync-server.cjs','mobile/www/mobile-sync-bridge.js','mobile/www/nano-mobile-credit.js','nano-customer-contract.cjs'}.issubset(changed),changed
 for p in ('mobile-sync-server.cjs','mobile/www/mobile-sync-bridge.js','mobile/www/nano-mobile-credit.js','nano-customer-contract.cjs'):
  candidate=ROOT/('_check_'+p.replace('/','_'))
  candidate.write_bytes(updated[p][1]);subprocess.run(['node','--check',str(candidate)],check=True,timeout=20)
 subprocess.run(['node',str(ROOT/'test_customers.cjs')],check=True,timeout=25)
 # Unchanged sale/purchase accounting must keep passing the previous release regression cases.
 for name in ('browser-bridge.js','mobile/www/browser-bridge.js'):
  (ROOT/('_test_'+name.replace('/','_'))).write_bytes(updated[name][1])
 subprocess.run(['node',str(ROOT/'test_finance.cjs'),str(ROOT/'_test_browser-bridge.js'),str(ROOT/'_test_mobile_www_browser-bridge.js')],check=True,timeout=45)
 archive=pack(updated)
 check=unpack(archive)
 assert set(check)==set(updated) and all(check[p][1]==v[1] for p,v in updated.items())
 with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',archive)
 with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
 result={'fileName':ASSET,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'appAsarSha256':sha(archive),'fromVersion':'1.0.53','toVersion':'1.0.54','changedFiles':changed,'customerTestsPassed':True,'existingFinanceTestsPassed':True}
 pathlib.Path('build-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()