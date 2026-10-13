#!/usr/bin/env python3
"""Rebuild v1.0.51 from exact published v1.0.50, fixing post-auth animation sequence.
Fail closed if authentication pathway changes or source checksums do not match.
"""
import copy,hashlib,json,pathlib,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.50/NANO-POS-Patch-1.0.49-to-1.0.50-LOGIN-EFFECT.zip'
BASE_SHA='e165cfa63480c0346034f21620e1bc87fbcb4a49c69c56423f280c7d2b78b0ce'
BASE_ASAR_SHA='613fb99fa44f2ff8f5b4de3c036c3623172cee3d392fa414943203ed30a0b26f'
ASSET='NANO-POS-Patch-1.0.50-to-1.0.51-LOGIN-EFFECT-FIX.zip'
def sha(data):return hashlib.sha256(data).hexdigest()
def parse(raw):
 length=struct.unpack('<I',raw[12:16])[0];header=json.loads(raw[16:16+length]);start=8+struct.unpack('<I',raw[4:8])[0];files={}
 def walk(n,base=''):
  for name,metadata in n['files'].items():
   key=base+name
   if 'files' in metadata:walk(metadata,key+'/')
   else:
    assert 'offset' in metadata and 'size' in metadata
    pos=start+int(metadata['offset']);size=metadata['size'];data=raw[pos:pos+size];assert len(data)==size
    files[key]=(metadata,data)
 walk(header)
 return files
def write_asar(files):
 tree={'files':{}};chunks=[];offset=0
 for name,(prior,data) in files.items():
  parts=name.split('/');node=tree
  for k in parts[:-1]:node=node['files'].setdefault(k,{'files':{}})
  meta=copy.deepcopy(prior);meta['offset']=str(offset);meta['size']=len(data)
  if 'integrity' in meta:
   block=meta['integrity'].get('blockSize',4194304)
   meta['integrity']={'algorithm':'SHA256','hash':sha(data),'blockSize':block,'blocks':[sha(data[i:i+block]) for i in range(0,len(data),block)]}
  else:
   block=4194304
   meta['integrity']={'algorithm':'SHA256','hash':sha(data),'blockSize':block,'blocks':[sha(data[i:i+block]) for i in range(0,len(data),block)]}
  node['files'][parts[-1]]=meta;offset+=len(data);chunks.append(data)
 body=json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode('utf-8')
 padded=(len(body)+3)&~3
 return struct.pack('<IIII',4,padded+8,padded+4,len(body))+body+b'\0'*(padded-len(body))+b''.join(chunks)
def revise(old):
 files=dict(old)
 def put(name,content):
  assert name in old,'Missing required file: '+name
  files[name]=(old[name][0],content.encode('utf-8'))
 html=old['index.html'][1].decode('utf-8')
 bundle='<link rel="stylesheet" href="nano-login-success-effect.css">\n<script src="nano-login-success-effect.js"></script>\n'
 assert html.count(bundle)==1,'Previous login animation resource not found exactly once'
 assert html.count('<script src="renderer.js"></script>')==1
 assert html.index('<script src="renderer.js"></script>')<html.index(bundle)
 html=html.replace(bundle,'')
 html=html.replace('<script src="renderer.js"></script>',
                   '<link rel="stylesheet" href="nano-login-success-effect.css">\n    <script src="nano-login-success-effect.js"></script>\n    <script src="renderer.js"></script>')
 assert html.index('<script src="nano-login-success-effect.js"></script>')<html.index('<script src="renderer.js"></script>')
 assert html.count('nano-login-success-effect.js')==1 and html.count('nano-login-success-effect.css')==1
 put('index.html',html)
 renderer=old['renderer.js'][1].decode('utf-8')
 needle='initUserSession(),window.NANOLoginSuccessEffect?.play(),setTimeout(()=>window.nanoPlayLoginBlessing?.(),120);'
 assert renderer.count(needle)==1,'Existing login handler not found exactly once'
 # Await visible transition before entering the home screen. Catch only visual failures; auth remains committed.
 new='await window.NANOLoginSuccessEffect.play().catch(_nanoVisualError=>console.warn("NANO login visual unavailable",_nanoVisualError)),initUserSession(),setTimeout(()=>window.nanoPlayLoginBlessing?.(),120);'
 renderer=renderer.replace(needle,new)
 auth=renderer.index("['loginUser'](_0x17f195,_0x102f46)")
 success=renderer.index('if(_0x586903[_0x4e9dc7(0x328)])',auth)
 anim=renderer.index('await window.NANOLoginSuccessEffect.play()',success)
 failure=renderer.index('}else _0x1d867b',anim)
 assert auth<success<anim<failure,'Animation is not solely in successful authentication branch'
 assert renderer.count('NANOLoginSuccessEffect.play')==1
 put('renderer.js',renderer)
 for name in ('nano-login-success-effect.js','nano-login-success-effect.css'):
  blob=(ROOT/name).read_text('utf-8')
  put(name,blob)
 pkg=json.loads(old['package.json'][1]);assert pkg['version']=='1.0.50'
 pkg['version']='1.0.51';put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
 if 'package-lock.json' in old:
  lock=json.loads(old['package-lock.json'][1]);lock['version']='1.0.51'
  if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):lock['packages']['']['version']='1.0.51'
  put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
 if 'app-config.js' in old:
  conf=old['app-config.js'][1].decode('utf8');updated=conf.replace("|| '1.0.50'","|| '1.0.51'")
  assert updated!=conf,'Version fallback missing'
  put('app-config.js',updated)
 if 'release-notes.js' in old:
  notes=old['release-notes.js'][1].decode('utf8');start=notes.find('const F=');assert start>=0
  end=notes.find(';',start);assert end>start
  features={'ar':['تحسينات استقرار النظام.'],'fr':['Améliorations de stabilité du système.'],'en':['System stability improvements.']}
  put('release-notes.js',notes[:start]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[end:])
 for name in ('renderer.js','nano-login-success-effect.js'):
  src=pathlib.Path('_check-'+name);src.write_bytes(files[name][1]);subprocess.run(['node','--check',str(src)],check=True,timeout=25)
 test=ROOT/'test_effect.cjs'
 assert test.is_file(),'Isolated actual animation behavior test missing'
 subprocess.run(['node',str(test)],check=True,timeout=30)
 return files

def main():
 base=pathlib.Path('nano-v150-base.zip')
 if not base.exists():
  req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v1.0.51-builder'})
  with urllib.request.urlopen(req,timeout=180) as response:base.write_bytes(response.read())
 assert sha(base.read_bytes())==BASE_SHA,'Published base ZIP SHA mismatch'
 with zipfile.ZipFile(base) as z: assert z.testzip() is None;orig=z.read('payload/app.asar')
 assert sha(orig)==BASE_ASAR_SHA,'Published base asar SHA mismatch'
 current=parse(orig);new=revise(current);binary=write_asar(new);check=parse(binary)
 assert set(check)==set(new)
 assert all(check[k][1]==v[1] for k,v in new.items()),'ASAR reconstruction mismatch'
 for path,(_,olddata) in current.items():
  if path not in ('index.html','renderer.js','nano-login-success-effect.js','nano-login-success-effect.css','package.json','package-lock.json','app-config.js','release-notes.js'):
   assert check[path][1]==olddata,'Unrelated source was modified: '+path
 with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',binary)
 with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
 result={'fileName':ASSET,'sizeBytes':pathlib.Path(ASSET).stat().st_size,'sha256':sha(pathlib.Path(ASSET).read_bytes()),
  'appAsarSha256':sha(binary),'fromVersion':'1.0.50','toVersion':'1.0.51',
  'authSuccessBranchVerified':True,'animationLoadedBeforeRenderer':True,
  'animationAwaitedBeforeHome':True,'unchangedFileCount':len(current)-8}
 pathlib.Path('build-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()