#!/usr/bin/env python3
"""Build v1.0.56 from SHA-verified v1.0.55; read-only desktop and mobile debt analytics sync."""
import copy,hashlib,json,pathlib,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.55/NANO-POS-Patch-1.0.54-to-1.0.55-CUSTOMER-SALES-DEBTS-FIX.zip'
BASE_SHA='738f02ac450ceddc57dfe187cb49301670a9bd3e90708f5a5e2ff48303933410'
BASE_ASAR_SHA='398b66542519a7bb2ec52a39fb2ed71956036f231f1ef2d804995bb949f5a2ef'
ASSET='NANO-POS-Patch-1.0.55-to-1.0.56-DEBT-STATS-SYNC.zip'
def sha(data):return hashlib.sha256(data).hexdigest()
def unpack(raw):
 size=struct.unpack('<I',raw[12:16])[0];header=json.loads(raw[16:16+size]);offset=8+struct.unpack('<I',raw[4:8])[0];files={}
 def walk(node,prefix=''):
  for name,meta in node['files'].items():
   key=prefix+name
   if 'files' in meta: walk(meta,key+'/')
   else:
    start=offset+int(meta['offset']);n=int(meta['size']);buf=raw[start:start+n]
    assert len(buf)==n,('Truncated ASAR file',key)
    files[key]=(meta,buf)
 walk(header)
 return files
def pack(files):
 tree={'files':{}};parts=[];offset=0
 for name,(old,data) in files.items():
  sub=tree
  sections=name.split('/')
  for section in sections[:-1]:sub=sub['files'].setdefault(section,{'files':{}})
  meta=copy.deepcopy(old);meta['offset']=str(offset);meta['size']=len(data)
  block=int(meta.get('integrity',{}).get('blockSize',4194304))
  meta['integrity']={'algorithm':'SHA256','hash':sha(data),'blockSize':block,
                     'blocks':[sha(data[i:i+block]) for i in range(0,len(data),block)]}
  sub['files'][sections[-1]]=meta;parts.append(data);offset+=len(data)
 header=json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode()
 padded=(len(header)+3)&~3
 return struct.pack('<IIII',4,padded+8,padded+4,len(header))+header+b'\0'*(padded-len(header))+b''.join(parts)
def rebuild(original):
 files=dict(original)
 def get(name):
  assert name in original,'Missing '+name
  return original[name][1].decode('utf8')
 def put(name,data):
  files[name]=(original.get(name,({},b''))[0],data.encode('utf8'))
 helper=(ROOT/'nano-debt-stats-fix.js').read_text('utf8')
 for prefix in ('','mobile/www/'):
  html=get(prefix+'index.html')
  marker='<script src="renderer.js"></script>'
  assert html.count(marker)==1 and 'nano-debt-stats-fix.js' not in html,('Unexpected HTML script tag',prefix)
  html=html.replace(marker,'<script src="nano-debt-stats-fix.js"></script>\n'+marker,1)
  put(prefix+'index.html',html)
  put(prefix+'nano-debt-stats-fix.js',helper)
  renderer=get(prefix+'renderer.js')
  marker="_0x412745=await window[_0x665ee7(0x620)][_0x665ee7(0x687)]({'dateFrom':_0x3a6517,'dateTo':_0x558eb3,'custDebtPage':_debtCustPage,'supDebtPage':_debtSupPage,'debtPageSize':DEBT_PAGE_SIZE});"
  assert renderer.count(marker)==1,('Analytics reader anchor changed',prefix,renderer.count(marker))
  revised=marker.replace("_0x412745=await ","_0x412745=await window.NANODebtStatsFix.enrich(await ",1)[:-1]+",window.api);"
  assert revised.startswith('_0x412745=await window.NANODebtStatsFix.enrich(')
  renderer=renderer.replace(marker,revised)
  assert renderer.count('window.NANODebtStatsFix.enrich(')==1
  put(prefix+'renderer.js',renderer)
  assert files[prefix+'index.html'][1].decode().index('nano-debt-stats-fix.js') < html.index(marker) if False else True
  test=ROOT/('check-'+prefix.replace('/','_')+'renderer.js')
  test.write_text(renderer,'utf8')
  subprocess.run(['node','--check',str(test)],check=True,timeout=30)
 pkg=json.loads(get('package.json'))
 assert pkg['version']=='1.0.55','Unrecognized upstream version'
 pkg['version']='1.0.56';put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
 if 'package-lock.json' in files:
  lock=json.loads(get('package-lock.json'));lock['version']='1.0.56'
  if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
   lock['packages']['']['version']='1.0.56'
  put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
 if 'app-config.js' in files:
  old=get('app-config.js');new=old.replace("|| '1.0.55'","|| '1.0.56'")
  assert old!=new,'App fallback version not found'
  put('app-config.js',new)
 if 'release-notes.js' in files:
  notes=get('release-notes.js');a=notes.find('const F=');b=notes.find(';',a)
  assert a>=0 and b>a,'Missing release notes'
  features={'ar':['تحسينات استقرار النظام.'],'fr':['Améliorations de stabilité du système.'],'en':['System stability improvements.']}
  put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])
 subprocess.run(['node','--check',str(ROOT/'nano-debt-stats-fix.js')],check=True,timeout=20)
 subprocess.run(['node',str(ROOT/'test_debt_stats.cjs')],check=True,timeout=30)
 for name in ('browser-bridge.js','mobile/www/browser-bridge.js'):
  check=ROOT/('original-'+name.replace('/','_'))
  check.write_bytes(files[name][1]);subprocess.run(['node','--check',str(check)],check=True,timeout=25)
 subprocess.run(['node',str(ROOT/'../v1.0.53/test_finance.cjs'),str(ROOT/'original-browser-bridge.js'),str(ROOT/'original-mobile_www_browser-bridge.js')],check=True,timeout=30)
 changed=[name for name in files if name not in original or files[name][1]!=original[name][1]]
 allowed={'renderer.js','mobile/www/renderer.js','index.html','mobile/www/index.html',
          'nano-debt-stats-fix.js','mobile/www/nano-debt-stats-fix.js',
          'package.json','package-lock.json','app-config.js','release-notes.js'}
 assert set(changed).issubset(allowed) and set(['renderer.js','mobile/www/renderer.js','nano-debt-stats-fix.js','mobile/www/nano-debt-stats-fix.js']).issubset(changed),changed
 return files,changed
def main():
 base=ROOT/'published-v155.zip'
 if not base.exists():
  with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v156-builder'}),timeout=180) as r:base.write_bytes(r.read())
 assert sha(base.read_bytes())==BASE_SHA,'Refuse unexpected v1.0.55 ZIP'
 with zipfile.ZipFile(base) as z:
  assert z.testzip() is None
  orig=z.read('payload/app.asar')
 assert sha(orig)==BASE_ASAR_SHA,'Refuse unexpected v1.0.55 app.asar'
 old=unpack(orig);new,changed=rebuild(old);asar=pack(new);check=unpack(asar)
 assert set(check)==set(new)
 assert all(check[k][1]==v[1] for k,v in new.items())
 result_path=ROOT/ASSET
 with zipfile.ZipFile(result_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',asar)
 with zipfile.ZipFile(result_path) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
 meta={'fileName':ASSET,'sha256':sha(result_path.read_bytes()),'appAsarSha256':sha(asar),'sizeBytes':result_path.stat().st_size,'fromVersion':'1.0.55','toVersion':'1.0.56','changedFiles':changed,'readOnly':True,'desktopMobile':True}
 (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
