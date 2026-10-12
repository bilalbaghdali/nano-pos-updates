#!/usr/bin/env python3
"""Fix *actual* auth overlay, not the hidden modern login template.
Rebuild directly from the published and SHA-pinned v1.0.44 release.
"""
import hashlib, json, pathlib, re, struct, subprocess, urllib.request, zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.44/NANO-POS-Patch-1.0.43-to-1.0.44-LOGIN-BRANDING.zip'
BASE_ZIP_SHA='18790f78db99f75f066a79c51647804526c90f51a029bcab6bfc846654b0d947'
BASE_ASAR_SHA='452d9c1033fabb1dbba9b24078d5029c6ed6d1e28882a77dc655d52e28249815'
BASE_BROWSER_UI_SHA='e815e2ad9ea195f6e834a01fdfb798712eb624facf3368b8c31ba920e70e3c47'
ASSET='NANO-POS-Patch-1.0.44-to-1.0.45-ACTUAL-LOGIN-FIX.zip'
def sha(data):return hashlib.sha256(data).hexdigest()
def files(asar):
  n=struct.unpack_from('<I',asar,12)[0]
  header=json.loads(asar[16:16+n]);offset=8+struct.unpack_from('<I',asar,4)[0]
  out={}
  def rec(node,prefix=''):
    for name,m in node['files'].items():
      key=prefix+name
      if 'files' in m:rec(m,key+'/')
      else:
        pos=offset+int(m['offset'])
        content=asar[pos:pos+m['size']]
        assert len(content)==m['size'],'Truncated '+key
        out[key]=(m,content)
  rec(header)
  return out
def pack(mapping):
  header={'files':{}};data=[];offset=0
  for name,(previous,blob) in mapping.items():
    node=header;parts=name.split('/')
    for p in parts[:-1]:node=node['files'].setdefault(p,{'files':{}})
    m={'size':len(blob),'offset':str(offset)}
    if 'integrity' in previous:
      block=previous['integrity'].get('blockSize',4194304)
      m['integrity']={'algorithm':'SHA256','hash':sha(blob),'blockSize':block,
        'blocks':[sha(blob[i:i+block]) for i in range(0,len(blob),block)]}
    node['files'][parts[-1]]=m;data.append(blob);offset+=len(blob)
  j=json.dumps(header,ensure_ascii=False,separators=(',',':')).encode()
  padded=(len(j)+3)&~3
  return struct.pack('<IIII',4,padded+8,padded+4,len(j))+j+b'\0'*(padded-len(j))+b''.join(data)
def main():
  archive=pathlib.Path('nano-pos-1.0.44-base.zip')
  if not archive.exists():
    req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v1.0.45-verified-builder'})
    with urllib.request.urlopen(req,timeout=180) as r:archive.write_bytes(r.read())
  assert sha(archive.read_bytes())==BASE_ZIP_SHA,'Refuse unexpected published base'
  with zipfile.ZipFile(archive) as z:asar=z.read('payload/app.asar')
  assert sha(asar)==BASE_ASAR_SHA,'Refuse unexpected base app.asar'
  filemap=files(asar)
  expected={'index.html','browser-ui.js','nano-commerce-ui.css','package.json',
    'app-config.js','release-notes.js','renderer.js','license-access.js',
    'assets/branding/nano-pos-icon.png','nano-v144-brand-login.css'}
  assert expected<=set(filemap),'Expected source files missing'
  before=lambda n:filemap[n][1].decode('utf8')
  browser=before('browser-ui.js')
  assert sha(filemap['browser-ui.js'][1])==BASE_BROWSER_UI_SHA,'Unexpected authentication source; STOP'
  assert browser.count('      document.body.appendChild(overlay);')==1, 'Login overlay insertion location changed'
  browser=browser.replace('      document.body.appendChild(overlay);',
     '      // v1.0.45: style the desktop login that actually authenticates users.\n'
     '      // Do NOT change the separate remote/browser user-picker.\n'
     '      if (!IS_REMOTE_WEB) window.NANO_MODERNIZE_AUTH_LOGIN?.(overlay);\n'
     '      document.body.appendChild(overlay);',1)
  assert browser.count('window.NANO_MODERNIZE_AUTH_LOGIN?.(overlay)')==1
  assert "overlay.querySelector('#nanoLoginForm')" in browser
  assert 'if (!IS_REMOTE_WEB) window.NANO_MODERNIZE_AUTH_LOGIN?.(overlay);' in browser
  html=before('index.html')
  assert html.count('src="browser-ui.js"')==1 and html.count('href="nano-v144-brand-login.css"')==1
  assert html.count('id="loginOverlay"')==1 and 'nano-commerce-visual' in html
  html=html.replace('<link rel="stylesheet" href="nano-v144-brand-login.css">',
     '<link rel="stylesheet" href="nano-v144-brand-login.css">\n<link rel="stylesheet" href="nano-v145-actual-login.css">',1)
  html=html.replace('<script src="browser-ui.js"></script>',
     '<script src="nano-v145-actual-login.js"></script>\n<script src="browser-ui.js"></script>',1)
  assert html.count('nano-v145-actual-login.js')==1
  pkg=json.loads(before('package.json'))
  assert pkg['version']=='1.0.44'
  pkg['version']='1.0.45'
  config=before('app-config.js')
  assert "'1.0.44'" in config
  config=config.replace("'1.0.44'","'1.0.45'")
  notes=before('release-notes.js')
  features={
    'ar':['إظهار شاشة الدخول العصرية فعليًا بالقسم الأبيض والرسومات الزرقاء بدل واجهة الدخول البسيطة.','إتاحة أزرار AR وFR وEN وحقول تسجيل الدخول بالشكل العصري دون تغيير حسابات المستخدمين.'],
    'fr':["Affichage du véritable écran de connexion moderne à deux panneaux à la place du formulaire simple.","Choix AR, FR et EN et champs de connexion conservés."],
    'en':['Show the modern two-panel login instead of the simple login screen.','Keep AR/FR/EN language choices and the existing working sign-in fields.']}
  replacement='const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+';let R='
  notes,count=re.subn(r'const F=\{.*?\};let R=',lambda _:replacement,notes,count=1,flags=re.S)
  assert count==1,'Unexpected release notes format'
  script=(ROOT/'nano-v145-actual-login.js').read_bytes()
  css=(ROOT/'nano-v145-actual-login.css').read_bytes()
  assert b'function enhance(overlay)' in script and b'.nano-v145-login-layout' in css
  changes={'browser-ui.js':browser.encode('utf8'), 'index.html':html.encode('utf8'),
    'package.json':(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode('utf8'),
    'app-config.js':config.encode('utf8'), 'release-notes.js':notes.encode('utf8'),
    'nano-v145-actual-login.js':script, 'nano-v145-actual-login.css':css}
  for name,blob in changes.items():
    filemap[name]=(filemap[name][0] if name in filemap else {},blob)
  for name in ('browser-ui.js','nano-v145-actual-login.js','app-config.js','release-notes.js'):
    local=ROOT/('check-'+name);local.write_bytes(changes[name])
    subprocess.run(['node','--check',str(local)],check=True,timeout=30)
  # Original core authentication/licensing/user data implementation is byte-identical.
  original=files(asar)
  for path in ('renderer.js','license-access.js','electron-main.cjs','mega-cloud-backup.cjs'):
    assert original[path][1]==filemap[path][1], 'Protected file changed: '+path
  assert 'node_modules/megajs/package.json' in filemap
  rebuilt=pack(filemap)
  actual=files(rebuilt)
  for name,data in changes.items():assert actual[name][1]==data, 'Repacked file mismatch '+name
  assert len(actual)==len(original)+2
  with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.writestr('payload/app.asar',rebuilt)
  with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
  summary={'fileName':ASSET,'version':'1.0.45','fromVersion':'1.0.44',
    'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(rebuilt),
    'sizeBytes':pathlib.Path(ASSET).stat().st_size,'changedFiles':sorted(changes)}
  pathlib.Path('build-result.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
  print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()