#!/usr/bin/env python3
"""Build NANO POS 1.0.52 from exact v1.0.51, making success animation a gate.

Only after the successful authentication animation ends may the app create its
current user session and remove the login overlay. When animation is missing or
fails, do not transition to the home screen.
"""
import copy, hashlib, json, pathlib, struct, subprocess, urllib.request, zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.51/NANO-POS-Patch-1.0.50-to-1.0.51-LOGIN-EFFECT-FIX.zip'
BASE_SHA='a5ba6460f3f2682f1e00cf47bb2efdcc13a9fdccd27aea544683efda573cceeb'
BASE_ASAR_SHA='4fd2e71feba617e069daa80d4cc120cfa9c0cbe6a4f0e46c636c44ea79c49f4e'
ASSET='NANO-POS-Patch-1.0.51-to-1.0.52-LOGIN-GATE.zip'

def sha(data):return hashlib.sha256(data).hexdigest()
def parse(raw):
 length=struct.unpack('<I',raw[12:16])[0];header=json.loads(raw[16:16+length]);start=8+struct.unpack('<I',raw[4:8])[0];files={}
 def walk(n,base=''):
  for name,metadata in n['files'].items():
   key=base+name
   if 'files' in metadata:walk(metadata,key+'/')
   else:
    assert 'offset' in metadata and 'size' in metadata
    pos=start+int(metadata['offset']);size=metadata['size'];data=raw[pos:pos+size]
    assert len(data)==size
    files[key]=(metadata,data)
 walk(header)
 return files

def write_asar(files):
 tree={'files':{}};chunks=[];offset=0
 for name,(prior,data) in files.items():
  parts=name.split('/');node=tree
  for key in parts[:-1]:node=node['files'].setdefault(key,{'files':{}})
  meta=copy.deepcopy(prior);meta['offset']=str(offset);meta['size']=len(data)
  block=meta.get('integrity',{}).get('blockSize',4194304)
  meta['integrity']={'algorithm':'SHA256','hash':sha(data),'blockSize':block,
                     'blocks':[sha(data[i:i+block]) for i in range(0,len(data),block)]}
  node['files'][parts[-1]]=meta;offset+=len(data);chunks.append(data)
 body=json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode('utf-8')
 padded=(len(body)+3)&~3
 return struct.pack('<IIII',4,padded+8,padded+4,len(body))+body+b'\0'*(padded-len(body))+b''.join(chunks)

# exact source branch from v1.0.51: previous version commits currentUser, hides
# the login modal, then tries to play visual; all premature side effects removed.
OLD="""currentUser=_0x586903['user'],localStorage[_0x4e9dc7(0x2c5)]('pos_current_user',JSON[_0x4e9dc7(0xfe9)](currentUser)),document['getElementById'](_0x4e9dc7(0xe2a))['value']='';const _0x3019a5=document['getElementById'](_0x4e9dc7(0x2d3));_0x3019a5['classList'][_0x4e9dc7(0xe5b)]('opacity-0','pointer-events-none'),setTimeout(()=>{const _0x485620=_0x4e9dc7;_0x3019a5[_0x485620(0x43b)][_0x485620(0xe5b)](_0x485620(0x89e)),_0x3019a5[_0x485620(0x43b)]['remove']('flex','opacity-0','pointer-events-none');},0x1f4),await window.NANOLoginSuccessEffect.play().catch(_nanoVisualError=>console.warn("NANO login visual unavailable",_nanoVisualError)),initUserSession(),setTimeout(()=>window.nanoPlayLoginBlessing?.(),120);"""
NEW="""const _0x3019a5=document['getElementById'](_0x4e9dc7(0x2d3));if(!window.NANOLoginSuccessEffect||typeof window.NANOLoginSuccessEffect.play!=='function')throw new Error('تأثير تأكيد الدخول غير متاح. لا يمكن فتح البرنامج قبل إكماله.');await window.NANOLoginSuccessEffect.play();currentUser=_0x586903['user'],localStorage[_0x4e9dc7(0x2c5)]('pos_current_user',JSON[_0x4e9dc7(0xfe9)](currentUser)),document['getElementById'](_0x4e9dc7(0xe2a))['value']='';_0x3019a5['classList'][_0x4e9dc7(0xe5b)]('opacity-0','pointer-events-none'),setTimeout(()=>{const _0x485620=_0x4e9dc7;_0x3019a5[_0x485620(0x43b)][_0x485620(0xe5b)](_0x485620(0x89e)),_0x3019a5[_0x485620(0x43b)]['remove']('flex','opacity-0','pointer-events-none');},0x1f4),initUserSession(),setTimeout(()=>window.nanoPlayLoginBlessing?.(),120);"""

def revise(old):
 files=dict(old)
 def put(name,data):
  assert name in old, 'Missing required file '+name
  files[name]=(old[name][0],data.encode('utf-8'))
 src=old['renderer.js'][1].decode('utf-8')
 assert src.count(OLD)==1,'Login success code changed; cannot apply patch safely.'
 # The login flow is only allowed to call the effect after loginUser succeeds.
 start=src.index("['loginUser'](_0x17f195,_0x102f46)")
 success=src.index("if(_0x586903[_0x4e9dc7(0x328)])",start)
 hook=src.index(OLD,success)
 failure=src.index('}else _0x1d867b',hook)
 assert start<success<hook<failure,'Patch not located within authenticated success branch'
 src=src.replace(OLD,NEW)
 assert src.count('NANOLoginSuccessEffect.play()')==1
 assert src.index('await window.NANOLoginSuccessEffect.play()',success)<src.index("currentUser=_0x586903['user']",success)<src.index('initUserSession()',success)<src.index('}else _0x1d867b',success), 'State changes are not gated'
 put('renderer.js',src)
 # Enforce reliable preload before the main renderer and keep existing unchanged animation assets.
 html=old['index.html'][1].decode('utf-8')
 assert html.count('nano-login-success-effect.js')==1
 assert html.index('nano-login-success-effect.js')<html.index('<script src="renderer.js"></script>'), 'Animation must load before renderer'
 assert 'id="loginOverlay"' in html,'Existing login overlay missing'
 # The animation must match the verified v1.0.51 asset, without any silent substitution.
 for visual in ('nano-login-success-effect.js','nano-login-success-effect.css'):
  assert sha(old[visual][1])==sha((ROOT/visual).read_bytes()), 'Unexpected visual file changed: '+visual
 pkg=json.loads(old['package.json'][1]);assert pkg['version']=='1.0.51'
 pkg['version']='1.0.52';put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
 if 'package-lock.json' in old:
  lock=json.loads(old['package-lock.json'][1]);lock['version']='1.0.52'
  if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):lock['packages']['']['version']='1.0.52'
  put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
 if 'app-config.js' in old:
  conf=old['app-config.js'][1].decode('utf-8');new_conf=conf.replace("|| '1.0.51'","|| '1.0.52'")
  assert new_conf!=conf,'Version fallback not found'
  put('app-config.js',new_conf)
 if 'release-notes.js' in old:
  notes=old['release-notes.js'][1].decode('utf8');a=notes.find('const F=');assert a>=0
  b=notes.find(';',a);assert b>a
  feature={'ar':['تحسينات استقرار النظام.'],'fr':['Améliorations de stabilité du système.'],'en':['System stability improvements.']}
  put('release-notes.js',notes[:a]+'const F='+json.dumps(feature,ensure_ascii=False,separators=(',',':'))+notes[b:])
 for name in ['renderer.js','nano-login-success-effect.js']:
  p=pathlib.Path('_check-'+name);p.write_bytes(files[name][1])
  subprocess.run(['node','--check',str(p)],check=True,timeout=20)
 # Test the real effect module and the sequence guard against premature access.
 subprocess.run(['node',str(ROOT/'test_effect.cjs')],check=True,timeout=30)
 subprocess.run(['node',str(ROOT/'test_gate.cjs')],check=True,timeout=30)
 return files

def main():
 base=pathlib.Path('nano-v151-base.zip')
 if not base.exists():
  req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v1.0.52-builder'})
  with urllib.request.urlopen(req,timeout=180) as response:base.write_bytes(response.read())
 assert sha(base.read_bytes())==BASE_SHA,'Published base ZIP SHA mismatch'
 with zipfile.ZipFile(base) as z:
  assert z.testzip() is None
  orig=z.read('payload/app.asar')
 assert sha(orig)==BASE_ASAR_SHA,'Published base ASAR SHA mismatch'
 original=parse(orig)
 patched=revise(original)
 packed=write_asar(patched)
 reread=parse(packed)
 assert set(reread)==set(original),'Packaged file list changed unexpectedly'
 assert all(reread[k][1]==v[1] for k,v in patched.items()),'Rebuild content mismatch'
 modified=[name for name in original if patched[name][1]!=original[name][1]]
 assert set(modified).issubset({'renderer.js','package.json','package-lock.json','app-config.js','release-notes.js'}) and 'renderer.js' in modified, modified
 with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',packed)
 with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
 result={'fileName':ASSET,'sizeBytes':pathlib.Path(ASSET).stat().st_size,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(packed),'fromVersion':'1.0.51','toVersion':'1.0.52','verifiedAnimationBeforeUserSession':True,'verifiedLoginOverlayNotHiddenBeforeAnimation':True,'updatedFiles':modified}
 pathlib.Path('build-result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()