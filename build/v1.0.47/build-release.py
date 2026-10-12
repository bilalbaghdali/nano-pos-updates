#!/usr/bin/env python3
"""NANO POS 1.0.47: remove only the *window caption* logo on Windows.

Rebuild from the SHA-verified published 1.0.46 app.asar. Windows EXE icon,
login-screen logo, shop name, license, and shop business data remain unchanged.
"""
import base64
import hashlib
import json
import pathlib
import re
import struct
import subprocess
import urllib.request
import zipfile

ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.46/NANO-POS-Patch-1.0.45-to-1.0.46-SECTION-SEARCH.zip'
BASE_ZIP_SHA='84502693aedb4b705790d6ed71363ee5f6ef861b7c4ce0faba2b5322b116ee20'
BASE_ASAR_SHA='03e973037a569d7f8fc7bb88e496ba2b1d254bd8130445e0fc32776b2acb8c99'
ASSET='NANO-POS-Patch-1.0.46-to-1.0.47-TITLE-LOGO.zip'
ICON_REL='assets/branding/nano-pos-titlebar-blank.png'
PNG_SHA='ba04f531df0c7a12124750d521add77c55b16a6432d653c5559c16680dbd9f50'
def sha(data):return hashlib.sha256(data).hexdigest()
def parse(blob):
    length=struct.unpack_from('<I',blob,12)[0]
    header=json.loads(blob[16:16+length]);start=8+struct.unpack_from('<I',blob,4)[0]
    files={}
    def walk(node,prefix=''):
        for name,meta in node.get('files',{}).items():
            path=prefix+name
            if 'files' in meta:walk(meta,path+'/')
            else:
                position=start+int(meta['offset']);data=blob[position:position+meta['size']]
                assert len(data)==meta['size'],'Corrupt base entry '+path
                files[path]=(meta,data)
    walk(header)
    return files

def pack(files):
    tree={'files':{}};data=[];offset=0
    for path,(previous,blob) in files.items():
        node=tree;parts=path.split('/')
        for part in parts[:-1]:node=node['files'].setdefault(part,{'files':{}})
        meta={'size':len(blob),'offset':str(offset)}
        if 'integrity' in previous:
            bs=previous['integrity'].get('blockSize',4194304)
            meta['integrity']={'algorithm':'SHA256','hash':sha(blob),'blockSize':bs,
                'blocks':[sha(blob[i:i+bs]) for i in range(0,len(blob),bs)]}
        node['files'][parts[-1]]=meta
        data.append(blob);offset+=len(blob)
    encoded=json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode()
    padding=(len(encoded)+3)&~3
    return struct.pack('<IIII',4,padding+8,padding+4,len(encoded))+encoded+b'\0'*(padding-len(encoded))+b''.join(data)

def main():
    base=pathlib.Path('base-v1.0.46.zip')
    if not base.is_file():
        req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-verified-caption-icon-patch'})
        with urllib.request.urlopen(req,timeout=180) as response:base.write_bytes(response.read())
    assert sha(base.read_bytes())==BASE_ZIP_SHA,'Base release ZIP SHA-256 mismatch'
    with zipfile.ZipFile(base) as z:
        assert z.testzip() is None
        before_asar=z.read('payload/app.asar')
    assert sha(before_asar)==BASE_ASAR_SHA,'Base app.asar SHA-256 mismatch'
    files=parse(before_asar)
    original={name:blob for name,(_,blob) in files.items()}
    assert ICON_REL not in original,'Window caption blank logo was already installed'
    assert {'electron-main.cjs','index.html','package.json','app-config.js','release-notes.js','renderer.js','browser-ui.js','assets/branding/nano-pos-icon.png'}<=set(original)
    old_main=original['electron-main.cjs'].decode('utf8')
    old_line="icon: path.join(__dirname, 'assets', 'branding', 'nano-pos-icon.png'),"
    assert old_main.count(old_line)==1,'Unexpected Windows window caption icon assignment'
    # Only Windows caption icon changes; continue to use the original app logo on other OSes.
    new_line="icon: process.platform === 'win32' ? path.join(__dirname, 'assets', 'branding', 'nano-pos-titlebar-blank.png') : path.join(__dirname, 'assets', 'branding', 'nano-pos-icon.png'),"
    new_main=old_main.replace(old_line,new_line,1)
    # Transparent image hides the artwork; Win32 reserves the native icon gutter.
    blank_png=base64.b64decode((ROOT/'titlebar-blank.b64').read_text().strip(),validate=True)
    assert sha(blank_png)==PNG_SHA,'Blank icon pixels do not match verified asset'
    assert blank_png[:8]==b'\x89PNG\r\n\x1a\n'
    pkg=json.loads(original['package.json']);assert pkg['version']=='1.0.46','Expected source v1.0.46'
    assert pkg.get('build',{}).get('win',{}).get('icon')=='assets/branding/nano-pos-icon.ico','Do not change Windows EXE/shortcut icon'
    pkg['version']='1.0.47'
    config=original['app-config.js'].decode('utf8');assert "'1.0.46'" in config
    config=config.replace("'1.0.46'","'1.0.47'")
    notes=original['release-notes.js'].decode('utf8')
    features={
      'ar':['إزالة الشعار الصغير بجانب اسم المتجر في شريط عنوان نافذة البرنامج.'],
      'fr':["Masquer le petit logo à côté du nom du magasin dans la barre de titre."],
      'en':['Hide the small icon beside the shop name in the window title bar.']}
    replacement='const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+';let R='
    notes,n=re.subn(r'const F=\{.*?\};let R=',lambda _:replacement,notes,count=1,flags=re.S)
    assert n==1,'Release notes format changed'
    changed={
      'electron-main.cjs':new_main.encode(),ICON_REL:blank_png,
      'package.json':(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(),
      'app-config.js':config.encode(),
      'release-notes.js':notes.encode()
    }
    for name,data in changed.items():files[name]=(files[name][0] if name in files else {},data)
    for name in ('electron-main.cjs','app-config.js','release-notes.js'):
        filename=ROOT/('check-'+name);filename.write_bytes(changed[name])
        subprocess.run(['node','--check',str(filename)],check=True,timeout=30)
    built=pack(files);after=parse(built)
    for name,blob in changed.items():assert after[name][1]==blob, 'ASAR reassembly changed '+name
    for name in ('index.html','renderer.js','browser-ui.js','assets/branding/nano-pos-icon.png','license-access.js','mega-cloud-backup.cjs'):
        if name in original:assert after[name][1]==original[name], 'Must not touch existing content '+name
    assert 'node_modules/megajs/package.json' in after,'Cloud backup vendor missing'
    with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',built)
    with zipfile.ZipFile(ASSET) as z: assert z.testzip() is None and z.namelist()==['payload/app.asar']
    result={'fileName':ASSET,'version':'1.0.47','fromVersion':'1.0.46','sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(built),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'changedFiles':sorted(changed)}
    pathlib.Path('build-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()