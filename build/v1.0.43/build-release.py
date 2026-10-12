#!/usr/bin/env python3
"""Rebuild NANO POS 1.0.43 from verified published 1.0.42 to pin modern login.

Restricts modifications to login HTML/CSS/JS and app version/release highlights.
All business data, authentication, license, databases and MEGA modules are unchanged.
"""
import hashlib, json, pathlib, re, struct, subprocess, urllib.request, zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.42/NANO-POS-Patch-1.0.41-to-1.0.42-LOGIN-INPUT-FIX.zip'
BASE_SHA='1a477a8fdb963b2c1af1d54f27396d51e7f93eaf22cfb66060dd7c01ae93fcc7'
BASE_ASAR_SHA='236a89a8113d418f59488370746fbf3189aa62e7b3ddc2326e1a5bd34adc9fe4'
ASSET='NANO-POS-Patch-1.0.42-to-1.0.43-MODERN-LOGIN.zip'
def sha(b): return hashlib.sha256(b).hexdigest()
def parse(blob):
    length=struct.unpack_from('<I',blob,12)[0]
    header=json.loads(blob[16:16+length])
    data_base=8+struct.unpack_from('<I',blob,4)[0]
    files={}
    def descend(node,prefix=''):
        for name,meta in node['files'].items():
            key=prefix+name
            if 'files' in meta:descend(meta,key+'/')
            else:
                pos=data_base+int(meta['offset']);payload=blob[pos:pos+meta['size']]
                assert len(payload)==meta['size'], 'Invalid source app.asar: '+key
                files[key]=(meta,payload)
    descend(header);return files
def repack(files):
    header={'files':{}};blobs=[];offset=0
    for filename,(old,content) in files.items():
        node=header;parts=filename.split('/')
        for part in parts[:-1]:node=node['files'].setdefault(part,{'files':{}})
        meta={'size':len(content),'offset':str(offset)}
        if 'integrity' in old:
            block=old['integrity'].get('blockSize',4194304)
            meta['integrity']={'algorithm':'SHA256','hash':sha(content),'blockSize':block,
             'blocks':[sha(content[i:i+block]) for i in range(0,len(content),block)]}
        node['files'][parts[-1]]=meta
        blobs.append(content);offset+=len(content)
    raw=json.dumps(header,ensure_ascii=False,separators=(',',':')).encode('utf8')
    padded=(len(raw)+3)&~3
    return struct.pack('<IIII',4,padded+8,padded+4,len(raw))+raw+b'\0'*(padded-len(raw))+b''.join(blobs)
def main():
    base=pathlib.Path('nano-pos-1.0.42-base.zip')
    if not base.exists():
        req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-modern-login-verifier'})
        with urllib.request.urlopen(req,timeout=180) as response:base.write_bytes(response.read())
    assert sha(base.read_bytes())==BASE_SHA,'Base published ZIP integrity mismatch'
    with zipfile.ZipFile(base) as z:original=z.read('payload/app.asar')
    assert sha(original)==BASE_ASAR_SHA,'Base app.asar integrity mismatch'
    files=parse(original)
    names={'index.html','nano-commerce-ui.css','nano-commerce-ui.js','package.json','app-config.js','release-notes.js'}
    assert names <= set(files), 'Missing login source files'
    html=files['index.html'][1].decode('utf8')
    assert html.count('href="nano-login-v8.css"')==1,'Expected one legacy login stylesheet'
    assert html.count('href="nano-commerce-ui.css"')==1,'Modern login CSS missing'
    assert html.count('src="nano-commerce-ui.js"')==1,'Modern login script missing'
    assert 'class="hidden fixed inset-0 z-[1000] nano-commerce-login"' in html,'Unexpected login overlay'
    assert 'class="nano-commerce-login-layout"' in html and 'id="loginForm"' in html
    # Remove ONLY the obsolete competing login stylesheet, not its file or other UI resources.
    clean_html,num=re.subn(r'<link\s+rel="stylesheet"\s+href="nano-login-v8\.css"\s*/?>\s*','',html,count=1)
    assert num==1 and 'href="nano-commerce-ui.css"' in clean_html
    css_extension=(ROOT/'modern-login-permanent.css').read_text().strip()
    js_extension=(ROOT/'modern-login-permanent.js').read_text().strip()
    assert 'nano-commerce-login-layout' in css_extension and 'MutationObserver' in js_extension
    css=files['nano-commerce-ui.css'][1].decode('utf8')
    js=files['nano-commerce-ui.js'][1].decode('utf8')
    assert '1.0.43' not in css and '__nanoModernLoginPermanent143' not in js,'Fix already present'
    updated={
      'index.html':clean_html.encode('utf8'),
      'nano-commerce-ui.css':(css.rstrip()+'\n\n'+css_extension+'\n').encode('utf8'),
      'nano-commerce-ui.js':(js.rstrip()+'\n\n'+js_extension+'\n').encode('utf8')}
    pkg=json.loads(files['package.json'][1]);assert pkg['version']=='1.0.42','Wrong source release'
    pkg['version']='1.0.43';updated['package.json']=(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    config=files['app-config.js'][1].decode('utf8')
    assert "'1.0.42'" in config,'Source config version not found'
    updated['app-config.js']=config.replace("'1.0.42'","'1.0.43'").encode('utf8')
    notes=files['release-notes.js'][1].decode('utf8')
    features={'ar':['تثبيت واجهة الدخول العصرية وإلغاء العودة إلى تخطيط الدخول البسيط.','تحسين ثبات حقول اسم المستخدم وكلمة المرور أثناء بدء التشغيل.'],
      'fr':["Conservation permanente de l’écran de connexion moderne sans retour à l’ancien formulaire.",'Stabilité améliorée de la saisie du nom d’utilisateur et du mot de passe au démarrage.'],
      'en':['Keep the modern login screen permanently without falling back to the simple form.','Improve username and password input stability while the app starts.']}
    replacement='const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+';let R='
    notes,num=re.subn(r'const F=\{.*?\};let R=',lambda _:replacement,notes,count=1,flags=re.S)
    assert num==1,'Unexpected release-notes implementation'
    updated['release-notes.js']=notes.encode('utf8')
    for name,payload in updated.items():
        meta,_=files[name];files[name]=(meta,payload)
    for name in ('nano-commerce-ui.js','app-config.js','release-notes.js'):
        p=ROOT/('syntax-'+name);p.write_bytes(updated[name]);subprocess.run(['node','--check',str(p)],check=True,timeout=30)
    assert set(updated)==names,'Unexpected change outside UI/version/highlights'
    rebuilt=repack(files);actual=parse(rebuilt)
    for name,payload in updated.items():assert actual[name][1]==payload,'Repacked data mismatch '+name
    assert 'node_modules/megajs/package.json' in actual,'Preserve cloud-backup integration'
    assert 'license-access.js' in actual and 'renderer.js' in actual,'Preserve authentication logic'
    for path in ('renderer.js','license-access.js','mega-cloud-backup.cjs'):
        if path in actual:assert actual[path][1]==parse(original)[path][1],'Sensitive file changed: '+path
    with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',rebuilt)
    with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    data={'fileName':ASSET,'version':'1.0.43','fromVersion':'1.0.42',
          'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(rebuilt),
          'sizeBytes':pathlib.Path(ASSET).stat().st_size,'changedFiles':sorted(updated)}
    pathlib.Path('build-result.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':main()