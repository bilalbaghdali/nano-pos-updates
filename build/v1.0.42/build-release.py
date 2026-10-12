#!/usr/bin/env python3
"""Build NANO POS 1.0.42 hotfix from verified v1.0.41; preserve customer files."""
import hashlib, json, pathlib, re, struct, urllib.request, zipfile, subprocess
ROOT = pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.41/NANO-POS-Patch-1.0.40-to-1.0.41-MEGA-RESTORE.zip'
BASE_SHA='76c54c7263fc91a063eaf1f6e946a155c046853e46c97af1ffd908bf4bbe6527'
BASE_ASAR_SHA='d34b38fd2389dd2a558d211afb8573471af41072f192703e04b76e81422eaa59'
ASSET='NANO-POS-Patch-1.0.41-to-1.0.42-LOGIN-INPUT-FIX.zip'
def digest(data):return hashlib.sha256(data).hexdigest()
def parse(data):
    n=struct.unpack_from('<I',data,12)[0];h=json.loads(data[16:16+n]);pos=8+struct.unpack_from('<I',data,4)[0];result={}
    def rec(node,prefix=''):
        for name,meta in node['files'].items():
            path=prefix+name
            if 'files' in meta:rec(meta,path+'/')
            else:
                start=pos+int(meta['offset'])
                blob=data[start:start+meta['size']]
                assert len(blob)==meta['size'], 'Truncated file '+path
                result[path]=(meta,blob)
    rec(h);return result

def pack(files):
    h={'files':{}};blobs=[];offset=0
    for path,(old,blob) in files.items():
        node=h
        parts=path.split('/')
        for p in parts[:-1]:node=node['files'].setdefault(p,{'files':{}})
        meta={'size':len(blob),'offset':str(offset)}
        if 'integrity' in old:
            bs=old['integrity'].get('blockSize',4194304)
            meta['integrity']={'algorithm':'SHA256','hash':digest(blob),'blockSize':bs,'blocks':[digest(blob[i:i+bs]) for i in range(0,len(blob),bs)]}
        node['files'][parts[-1]]=meta
        blobs.append(blob);offset+=len(blob)
    b=json.dumps(h,ensure_ascii=False,separators=(',',':')).encode('utf8');length=(len(b)+3)&~3
    return struct.pack('<IIII',4,length+8,length+4,len(b))+b+b'\x00'*(length-len(b))+b''.join(blobs)

def main():
    base=pathlib.Path('base-v141.zip')
    if not base.exists():
        req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-login-fix-verifier'})
        with urllib.request.urlopen(req,timeout=180) as resp:base.write_bytes(resp.read())
    assert digest(base.read_bytes())==BASE_SHA, 'Refuse unexpected base archive'
    with zipfile.ZipFile(base) as z:old=z.read('payload/app.asar')
    assert digest(old)==BASE_ASAR_SHA, 'Refuse unexpected installed app.asar'
    files=parse(old)
    for name in ('nano-commerce-ui.css','nano-commerce-ui.js','package.json','app-config.js','release-notes.js','index.html'):
        assert name in files,'Missing file '+name
    html=files['index.html'][1].decode('utf8')
    assert 'id="loginUsername"' in html and 'id="loginPassword"' in html and 'src="nano-commerce-ui.js"' in html and 'href="nano-commerce-ui.css"' in html, 'Existing login layout is unexpected'
    css=(ROOT/'login-repair.css').read_text(encoding='utf8').strip()
    js=(ROOT/'login-repair.js').read_text(encoding='utf8').strip()
    assert '2147483640' in css and '2147483647' in css and 'loginPassword' in js
    oldcss=files['nano-commerce-ui.css'][1].decode('utf8')
    oldjs=files['nano-commerce-ui.js'][1].decode('utf8')
    assert 'NANO POS 1.0.42' not in oldcss and '__nanoLoginInputRepair142' not in oldjs,'Fix already present'
    changed={}
    changed['nano-commerce-ui.css']=(oldcss.rstrip()+'\n\n'+css+'\n').encode('utf8')
    changed['nano-commerce-ui.js']=(oldjs.rstrip()+'\n\n'+js+'\n').encode('utf8')
    pkg=json.loads(files['package.json'][1]);assert pkg['version']=='1.0.41','Unexpected base version'
    pkg['version']='1.0.42';changed['package.json']=(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    config=files['app-config.js'][1].decode('utf8')
    assert "'1.0.41'" in config,'Version fallback must be explicitly updated'
    changed['app-config.js']=config.replace("'1.0.41'","'1.0.42'").encode('utf8')
    notes=files['release-notes.js'][1].decode('utf8')
    features={'ar':['إصلاح كتابة اسم المستخدم وكلمة المرور في شاشة الدخول.','إصلاح تعارض شاشة القفل والتحميل مع حقول تسجيل الدخول.'], 'fr':['Correction de la saisie du nom d’utilisateur et du mot de passe à la connexion.','Correction des interactions bloquées par les écrans de verrouillage ou de chargement.'], 'en':['Fixed username and password typing on the login screen.','Fixed startup/lock overlays blocking login fields.']}
    replacement='const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+';let R='
    patched,num=re.subn(r'const F=\{.*?\};let R=',lambda _:replacement,notes,count=1,flags=re.S)
    assert num==1,'Unsupported release-notes format'
    changed['release-notes.js']=patched.encode('utf8')
    for name,data in changed.items():
        meta,_=files[name];files[name]=(meta,data)
    for name in ('nano-commerce-ui.js','app-config.js','release-notes.js'):
        path=ROOT/('syntax-'+name);path.write_bytes(changed[name]);subprocess.run(['node','--check',str(path)],check=True,timeout=25)
    # Static check that fixes do not alter license, business data or credential storage.
    assert set(changed)=={'nano-commerce-ui.css','nano-commerce-ui.js','package.json','app-config.js','release-notes.js'}
    result=pack(files);parsed=parse(result)
    assert len(parsed)==len(files)
    for name,data in changed.items():assert parsed[name][1]==data
    assert 'node_modules/megajs/package.json' in parsed, 'Must preserve MEGA cloud integration'
    with zipfile.ZipFile(ASSET,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',result)
    with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    info={'fileName':ASSET,'version':'1.0.42','fromVersion':'1.0.41','sha256':digest(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':digest(result),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'changedFiles':list(changed)}
    pathlib.Path('build-result.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(info,indent=2,ensure_ascii=False))
if __name__=='__main__':main()