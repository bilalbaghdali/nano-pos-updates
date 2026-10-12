#!/usr/bin/env python3
"""Rebuild verified NANO POS v1.0.44 with icon branding and fixed split login.
No business data, license, activation or accounting code is modified.
"""
import base64,hashlib,json,pathlib,re,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.43/NANO-POS-Patch-1.0.42-to-1.0.43-MODERN-LOGIN.zip'
BASE_ZIP_SHA='30ae340970185c8c68f85181c0dddb5a1d11373ac5485988fb698b12376d5d11'
BASE_ASAR_SHA='a58d710a8ae0e54c9318e97c188d0317048703dbda36dfd302296dce0ef23705'
ASSET='NANO-POS-Patch-1.0.43-to-1.0.44-LOGIN-BRANDING.zip'
def sha(data):return hashlib.sha256(data).hexdigest()
def parse(raw):
    length=struct.unpack_from('<I',raw,12)[0]
    head=json.loads(raw[16:16+length]);start=8+struct.unpack_from('<I',raw,4)[0]
    found={}
    def walk(node,prefix=''):
        for key,meta in node['files'].items():
            name=prefix+key
            if 'files' in meta:walk(meta,name+'/')
            else:
                p=start+int(meta['offset']);data=raw[p:p+meta['size']]
                assert len(data)==meta['size'],'Truncated '+name
                found[name]=(meta,data)
    walk(head)
    return found
def pack(files):
    head={'files':{}};buf=[];offset=0
    for path,(old,payload) in files.items():
        node=head;names=path.split('/')
        for item in names[:-1]:node=node['files'].setdefault(item,{'files':{}})
        meta={'size':len(payload),'offset':str(offset)}
        if 'integrity' in old:
            block=old['integrity'].get('blockSize',4194304)
            meta['integrity']={'algorithm':'SHA256','hash':sha(payload),'blockSize':block,
                'blocks':[sha(payload[i:i+block]) for i in range(0,len(payload),block)]}
        node['files'][names[-1]]=meta
        buf.append(payload);offset+=len(payload)
    raw=json.dumps(head,ensure_ascii=False,separators=(',',':')).encode()
    padded=(len(raw)+3)&~3
    return struct.pack('<IIII',4,padded+8,padded+4,len(raw))+raw+b'\0'*(padded-len(raw))+b''.join(buf)
def main():
    base=pathlib.Path('base-v1.0.43.zip')
    if not base.exists():
        req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v1.0.44-verified-builder'})
        with urllib.request.urlopen(req,timeout=180) as r:base.write_bytes(r.read())
    assert sha(base.read_bytes())==BASE_ZIP_SHA,'Unexpected source zip'
    with zipfile.ZipFile(base) as z:raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR_SHA,'Unexpected source ASAR'
    files=parse(raw)
    needed={'index.html','nano-commerce-ui.css','electron-main.cjs','package.json','app-config.js','release-notes.js','renderer.js','license-access.js'}
    assert needed <= set(files),'Missing expected source files'
    def original(name):return files[name][1].decode('utf8')
    html=original('index.html')
    old='<div class="nano-commerce-logo3d">N</div>'
    assert html.count(old)==1, 'Expected existing logo once'
    html=html.replace(old,'<img class="nano-commerce-brand-icon" src="assets/branding/nano-pos-icon.png" alt="NANO POS" width="68" height="68">',1)
    assert 'href="nano-commerce-ui.css"' in html
    html=html.replace('<link rel="stylesheet" href="nano-commerce-ui.css">',
        '<link rel="stylesheet" href="nano-commerce-ui.css">\n<link rel="stylesheet" href="nano-v144-brand-login.css">',1)
    assert 'href="nano-v144-brand-login.css"' in html,'New CSS not linked'
    assert '</head>' in html
    html=html.replace('</head>','<link rel="icon" type="image/png" href="assets/branding/nano-pos-icon.png">\n</head>',1)
    assert all(s in html for s in ['class="nano-commerce-login-layout"','class="nano-commerce-visual"','class="nano-commerce-login-side"','id="loginUsername"','id="loginPassword"','setLanguage(\'ar\')','setLanguage(\'fr\')','setLanguage(\'en\')']), 'Login layout or language handlers altered'
    main=original('electron-main.cjs')
    marker='    title: APP_DISPLAY_NAME,'
    assert main.count(marker)==1,'Unexpected BrowserWindow constructor'
    main=main.replace(marker,marker+"\n    icon: path.join(__dirname, 'assets', 'branding', 'nano-pos-icon.png'),",1)
    pkg=json.loads(original('package.json'))
    assert pkg['version']=='1.0.43','Base version wrong'
    pkg['version']='1.0.44'
    pkg.setdefault('build',{}).setdefault('win',{})['icon']='assets/branding/nano-pos-icon.ico'
    config=original('app-config.js')
    assert "'1.0.43'" in config,'Source fallback version missing'
    config=config.replace("'1.0.43'","'1.0.44'")
    notes=original('release-notes.js')
    features={
      'ar':['اعتماد أيقونة NANO POS الجديدة في نافذة البرنامج وشاشة الدخول وشعار المتجر.','تثبيت شاشة الدخول العصرية بقسم أبيض لاسم المستخدم وكلمة المرور وبقسم أزرق للمبيعات والمخزون، مع أزرار AR وFR وEN.'],
      'fr':['Nouvelle icône NANO POS dans la fenêtre, le logo du magasin et la connexion.','Écran de connexion moderne permanent : formulaire blanc à gauche, visuel bleu foncé à droite et langues AR/FR/EN.'],
      'en':['New NANO POS icon in the application window, store brand and login screen.','Permanent modern split login: white sign-in form on the left, dark-blue sales/inventory visual on the right, AR/FR/EN buttons.']}
    replacement='const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+';let R='
    notes,num=re.subn(r'const F=\{.*?\};let R=',lambda _:replacement,notes,count=1,flags=re.S)
    assert num==1,'Release note format changed'
    icon_png=base64.b64decode((ROOT/'icon-png.b64').read_text().strip(),validate=True)
    icon_ico=base64.b64decode((ROOT/'icon-ico.b64').read_text().strip(),validate=True)
    assert icon_png.startswith(b'\x89PNG\r\n\x1a\n') and icon_ico[:4]==b'\x00\x00\x01\x00','Corrupt icon assets'
    css=(ROOT/'modern-login-brand.css').read_bytes()
    assert b'.nano-commerce-login-layout' in css and b'.nano-commerce-brand-icon' in css
    changed={
      'index.html':html.encode(),'electron-main.cjs':main.encode(),
      'package.json':(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(),
      'app-config.js':config.encode(),'release-notes.js':notes.encode(),
      'nano-v144-brand-login.css':css,
      'assets/branding/nano-pos-icon.png':icon_png,
      'assets/branding/nano-pos-icon.ico':icon_ico
    }
    for name,payload in changed.items():
        if name in files:files[name]=(files[name][0],payload)
        else:files[name]=({},payload)
    for name in ('electron-main.cjs','app-config.js','release-notes.js'):
        p=ROOT/('check-'+name);p.write_bytes(changed[name]);subprocess.run(['node','--check',str(p)],check=True,timeout=25)
    assert files['renderer.js'][1]==parse(raw)['renderer.js'][1],'Authentication/renderer logic modified'
    assert files['license-access.js'][1]==parse(raw)['license-access.js'][1], 'License logic modified'
    assert 'node_modules/megajs/package.json' in files,'Lost MEGA backups'
    output=pack(files)
    packed=parse(output)
    for name,payload in changed.items(): assert packed[name][1]==payload,'Lost file '+name
    with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',output)
    with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    result={'fileName':ASSET,'version':'1.0.44','fromVersion':'1.0.43',
       'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(output),
       'sizeBytes':pathlib.Path(ASSET).stat().st_size,'changedFiles':sorted(changed)}
    pathlib.Path('build-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()