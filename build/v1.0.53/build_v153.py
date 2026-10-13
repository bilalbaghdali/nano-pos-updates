#!/usr/bin/env python3
"""NANO POS v1.0.53: mobile credit, customer selection and live ledger correctness.

Rebuilds only from the published v1.0.52, never overwriting store data. Any
unrecognized upstream code, failing financial test or checksum stops release.
"""
from __future__ import annotations
import copy, hashlib, json, pathlib, struct, subprocess, sys, urllib.request, zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.52/NANO-POS-Patch-1.0.51-to-1.0.52-LOGIN-GATE.zip'
BASE_ZIP_SHA='ac19741214cde85b597ecc5bfb12819fb11cfc8af92317064211be16066d99ba'
BASE_ASAR_SHA='67cff5a6d45d0dcbc900654db32dba169b0ee86c92cb302be5e0f0eef3f82e55'
ASSET='NANO-POS-Patch-1.0.52-to-1.0.53-MOBILE-CREDIT-DEBTS.zip'

def sha(data):return hashlib.sha256(data).hexdigest()
def parse(data):
  size=struct.unpack('<I',data[12:16])[0];tree=json.loads(data[16:16+size]);start=8+struct.unpack('<I',data[4:8])[0]
  files={}
  def walk(branch,prefix=''):
    for name,info in branch['files'].items():
      path=prefix+name
      if 'files' in info:walk(info,path+'/')
      else:
        off=start+int(info['offset']);length=int(info['size']);payload=data[off:off+length]
        assert len(payload)==length,('Truncated asar entry',path)
        files[path]=(info,payload)
  walk(tree)
  return files

def write_asar(files):
  tree={'files':{}};payload=[];offset=0
  for path,(prior,raw) in files.items():
    node=tree
    parts=path.split('/')
    for name in parts[:-1]:node=node['files'].setdefault(name,{'files':{}})
    info=copy.deepcopy(prior)
    info['size']=len(raw);info['offset']=str(offset)
    block=int(info.get('integrity',{}).get('blockSize',4194304))
    info['integrity']={'algorithm':'SHA256','hash':sha(raw),'blockSize':block,
                       'blocks':[sha(raw[i:i+block]) for i in range(0,len(raw),block)]}
    node['files'][parts[-1]]=info
    payload.append(raw);offset+=len(raw)
  header=json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode()
  padded=(len(header)+3)&~3
  return struct.pack('<IIII',4,padded+8,padded+4,len(header))+header+b'\0'*(padded-len(header))+b''.join(payload)

def revise(original):
  from patch_bridge import patch as patch_financial_db
  files=dict(original)
  def get(path):
    assert path in original,'Published version missing required file: '+path
    return original[path][1].decode('utf8')
  def put(path,content):
    old=original.get(path,({},b''))[0]
    files[path]=(old,content.encode('utf8'))
  for name in ('browser-bridge.js','mobile/www/browser-bridge.js'):
    src=get(name)
    revised=patch_financial_db(src)
    assert 'customerVisibleDebt' in revised and 'received_payment_method' in revised
    put(name,revised)
  src=get('mobile/www/mobile-sync-bridge.js')
  old="""      if (mutation && isNetworkError(error)) return enqueueOperation(channel, args, operationId, error);
      throw error;"""
  new="""      if (mutation && isNetworkError(error)) {
        const critical = new Set(['process-sale','save-purchase','add-sale-payment','add-invoice-payment','add-customer-payment','add-supplier-payment','delete-sale','delete-purchase']);
        if (critical.has(channel)) {
          // Do not falsely report success or queue money movements when the PC's reply is missing.
          const uncertain = new Error('لم يؤكد الكمبيوتر العملية المالية. تحقق من سجل الفواتير والمدفوعات على الكمبيوتر قبل إعادة المحاولة، لتجنب تسجيلها مرتين.');
          uncertain.code = 'NANO_FINANCIAL_CONFIRMATION_UNCERTAIN';
          throw uncertain;
        }
        return enqueueOperation(channel, args, operationId, error);
      }
      throw error;"""
  assert src.count(old)==1,'Financial offline queue code changed unexpectedly'
  put('mobile/www/mobile-sync-bridge.js',src.replace(old,new))
  src=get('mobile/www/renderer.js')
  old='executeSalePayload(_0x2447c2,![]);}async function executeSalePayload'
  assert src.count(old)==1,'Mobile sale processing function changed unexpectedly'
  put('mobile/www/renderer.js',src.replace(old,'return await executeSalePayload(_0x2447c2,![]);}async function executeSalePayload'))
  html=get('mobile/www/index.html')
  marker='<script src="mobile-shell.js"></script>'
  assert html.count(marker)==1 and 'nano-mobile-credit.js' not in html,'Unexpected mobile script bootstrap'
  put('mobile/www/index.html',html.replace(marker,marker+'\n<link rel="stylesheet" href="nano-mobile-credit.css">\n<script src="nano-mobile-credit.js"></script>',1))
  for name in ('nano-mobile-credit.js','nano-mobile-credit.css'):
    target='mobile/www/'+name
    assert target not in files,'Mobile credit UI already exists; check duplicate bootstrap'
    put(target,(ROOT/name).read_text('utf8'))
  pkg=json.loads(get('package.json'))
  assert pkg['version']=='1.0.52','Unexpected source release'
  pkg['version']='1.0.53';put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
  if 'package-lock.json' in files:
    lock=json.loads(get('package-lock.json'));lock['version']='1.0.53'
    if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):lock['packages']['']['version']='1.0.53'
    put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
  if 'app-config.js' in files:
    conf=get('app-config.js')
    revised=conf.replace("|| '1.0.52'","|| '1.0.53'")
    assert revised!=conf,'App version fallback not found'
    put('app-config.js',revised)
  if 'release-notes.js' in files:
    notes=get('release-notes.js');a=notes.find('const F=');b=notes.find(';',a)
    assert a>=0 and b>a,'Release notes format changed'
    generic={'ar':['تحسينات استقرار النظام.'],'fr':['Améliorations de stabilité du système.'],'en':['System stability improvements.']}
    put('release-notes.js',notes[:a]+'const F='+json.dumps(generic,ensure_ascii=False,separators=(',',':'))+notes[b:])
  for name in ('browser-bridge.js','mobile/www/browser-bridge.js','mobile/www/mobile-sync-bridge.js','mobile/www/renderer.js','mobile/www/nano-mobile-credit.js'):
    tmp=ROOT/('_validate_'+name.replace('/','_'))
    tmp.write_bytes(files[name][1]);subprocess.run(['node','--check',str(tmp)],check=True,timeout=25)
  # Tests load the exact bridge bytes staged for release, including mock license check.
  subprocess.run(['node',str(ROOT/'test_finance.cjs'),str(ROOT/'_validate_mobile_www_browser-bridge.js'),str(ROOT/'_validate_browser-bridge.js')],check=True,timeout=30)
  diff=[path for path in files if path not in original or files[path][1]!=original[path][1]]
  allowed={'browser-bridge.js','mobile/www/browser-bridge.js','mobile/www/mobile-sync-bridge.js','mobile/www/renderer.js','mobile/www/index.html','mobile/www/nano-mobile-credit.js','mobile/www/nano-mobile-credit.css','package.json','package-lock.json','app-config.js','release-notes.js'}
  assert set(diff).issubset(allowed) and {'mobile/www/nano-mobile-credit.js','mobile/www/index.html'}.issubset(diff),'Unexpected extra writes'
  return files,diff

def main():
  saved=pathlib.Path('base-v152.zip')
  if not saved.exists():
    req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v1.0.53-release-builder'})
    with urllib.request.urlopen(req,timeout=180) as r:saved.write_bytes(r.read())
  assert sha(saved.read_bytes())==BASE_ZIP_SHA,'Published base ZIP hash changed'
  with zipfile.ZipFile(saved) as z:
    assert z.testzip() is None
    original= z.read('payload/app.asar')
  assert sha(original)==BASE_ASAR_SHA,'Published app.asar hash mismatch'
  base=parse(original)
  updated,changed=revise(base)
  packed=write_asar(updated)
  verified=parse(packed)
  assert set(updated)==set(verified),'Repacked file set differs'
  assert all(verified[k][1]==updated[k][1] for k in updated),'Repacked file contents differ'
  with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',packed)
  with zipfile.ZipFile(ASSET) as z: assert z.testzip() is None and z.namelist()==['payload/app.asar']
  obj={'fileName':ASSET,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'appAsarSha256':sha(packed),'fromVersion':'1.0.52','toVersion':'1.0.53','changedFiles':changed,'testedFinancialCases':['partial-sale','customer-balance','sale-payment','customer-payment','purchase','supplier-payment','live-analytics']}
  pathlib.Path('build-result.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(obj,ensure_ascii=False,indent=2))
if __name__=='__main__':main()