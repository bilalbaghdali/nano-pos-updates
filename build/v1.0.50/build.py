#!/usr/bin/env python3
"""Release NANO POS v1.0.50 based ONLY on verified latest v1.0.49 app.asar.
Fails rather than shipping if authentication success hook changed.
"""
import copy,hashlib,json,pathlib,re,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.49/NANO-POS-Patch-1.0.48-to-1.0.49-BARCODE-CURRENCY-FIX.zip'
BASE_SHA='b7fbb70e96521d92a487d57d3a4455bc1ad2cc4425f6d11c397005fcf8cd3bd0'
BASE_ASAR_SHA='77e7402bccbbe25928de8c3a5f99021900a1bf5557a240e18d3d4235dff2ed5a'
ASSET='NANO-POS-Patch-1.0.49-to-1.0.50-LOGIN-EFFECT.zip'

def sha(data): return hashlib.sha256(data).hexdigest()
def parse_asar(raw):
    header_len=struct.unpack('<I',raw[12:16])[0]
    header=json.loads(raw[16:16+header_len]);data_offset=8+struct.unpack('<I',raw[4:8])[0]
    files={}
    def walk(node,prefix=''):
        for name,entry in node['files'].items():
            key=prefix+name
            if 'files' in entry: walk(entry,key+'/')
            else:
                assert 'offset' in entry and 'size' in entry, 'Unpacked/nonstandard file: '+key
                begin=data_offset+int(entry['offset']);size=entry['size']
                chunk=raw[begin:begin+size]
                assert len(chunk)==size
                files[key]=(entry,chunk)
    walk(header)
    return files

def asar_write(files):
    tree={'files':{}};pieces=[];offset=0
    for name,(orig_meta,payload) in files.items():
        parts=name.split('/');node=tree
        for section in parts[:-1]:node=node['files'].setdefault(section,{'files':{}})
        meta=copy.deepcopy(orig_meta)
        meta['offset']=str(offset);meta['size']=len(payload)
        if 'integrity' in meta:
            size=meta['integrity'].get('blockSize') or 4194304
            meta['integrity']={'algorithm':'SHA256','hash':sha(payload),'blockSize':size,
                'blocks':[sha(payload[i:i+size]) for i in range(0,len(payload),size)]}
        else:
            meta['integrity']={'algorithm':'SHA256','hash':sha(payload),'blockSize':4194304,
                 'blocks':[sha(payload[i:i+4194304]) for i in range(0,len(payload),4194304)]}
        node['files'][parts[-1]]=meta
        pieces.append(payload);offset+=len(payload)
    header_raw=json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    padded=(len(header_raw)+3)&~3
    return struct.pack('<IIII',4,padded+8,padded+4,len(header_raw))+header_raw+b'\0'*(padded-len(header_raw))+b''.join(pieces)

def revise(orig):
    files=dict(orig)
    def update(name,blob):
        if name not in orig: raise RuntimeError('Unexpected missing source file: '+name)
        files[name]=(orig[name][0],blob.encode('utf8'))
    renderer=orig['renderer.js'][1].decode('utf8')
    # Exactly one authenticated success branch call. Must never run for wrong login.
    needle='initUserSession(),setTimeout(()=>window.nanoPlayLoginBlessing?.(),120);'
    assert renderer.count(needle)==1, 'Login handler changed; manual inspection required before publishing'
    idx=renderer.index(needle)
    context=renderer[max(0,idx-1600):idx]
    assert "'loginUser'" in context and "['success']" in context or 'loginUser' in context and 'if(_0x586903' in context, 'Could not prove authenticated branch context'
    renderer=renderer.replace(needle,'initUserSession(),window.NANOLoginSuccessEffect?.play(),setTimeout(()=>window.nanoPlayLoginBlessing?.(),120);')
    update('renderer.js',renderer)
    index=orig['index.html'][1].decode('utf8')
    assert index.count('</body>')==1
    assert 'id="loginForm"' in index and 'id="loginOverlay"' in index
    assert 'nano-login-success-effect.js' not in index
    index=index.replace('</body>','<link rel="stylesheet" href="nano-login-success-effect.css">\n<script src="nano-login-success-effect.js"></script>\n</body>')
    update('index.html',index)
    pkg=json.loads(orig['package.json'][1]); assert pkg['version']=='1.0.49','Unexpected package version'
    pkg['version']='1.0.50';update('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in orig:
        lock=json.loads(orig['package-lock.json'][1]);lock['version']='1.0.50'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):lock['packages']['']['version']='1.0.50'
        update('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in orig:
        conf=orig['app-config.js'][1].decode('utf8')
        conf2=conf.replace("|| '1.0.49'","|| '1.0.50'")
        assert conf2!=conf,'Expected app version fallback not found'
        update('app-config.js',conf2)
    if 'release-notes.js' in orig:
        notes=orig['release-notes.js'][1].decode('utf8')
        feature={'ar':['تحسينات استقرار النظام.'],'fr':['Améliorations de la stabilité du système.'],'en':['System stability improvements.']}
        start=notes.find('const F=')
        assert start>=0
        end=notes.find(';',start)
        assert end>start
        updated=notes[:start]+'const F='+json.dumps(feature,ensure_ascii=False,separators=(',',':'))+notes[end:]
        update('release-notes.js',updated)
    for name in ('nano-login-success-effect.js','nano-login-success-effect.css'):
        assert name not in files, 'File already exists in base release: '+name
        payload=(ROOT/name).read_bytes()
        files[name]=({'integrity':{'blockSize':4194304}},payload)
    return files

def main():
    base=pathlib.Path('base-v1.0.49.zip')
    if not base.exists():
        req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-build'});
        with urllib.request.urlopen(req,timeout=180) as response:base.write_bytes(response.read())
    assert sha(base.read_bytes())==BASE_SHA,'Unexpected base download SHA-256'
    with zipfile.ZipFile(base) as z:
        assert z.testzip() is None
        old=z.read('payload/app.asar')
    assert sha(old)==BASE_ASAR_SHA,'Wrong v1.0.49 app.asar'
    oldmap=parse_asar(old)
    newmap=revise(oldmap)
    for name in ('renderer.js','nano-login-success-effect.js'):
        file=pathlib.Path('_check-'+name);file.write_bytes(newmap[name][1]);subprocess.run(['node','--check',str(file)],check=True,timeout=20)
    binary=asar_write(newmap)
    check=parse_asar(binary)
    assert len(newmap)==len(check)
    assert all(check[k][1]==v[1] for k,v in newmap.items()),'ASAR data verification failed'
    assert b'window.NANOLoginSuccessEffect?.play()' in check['renderer.js'][1]
    assert b'nano-login-success-effect.js' in check['index.html'][1]
    with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',binary)
    with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    result={'fileName':ASSET,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'sizeBytes':pathlib.Path(ASSET).stat().st_size,
       'appAsarSha256':sha(binary),'fromVersion':'1.0.49','toVersion':'1.0.50',
       'authHookVerified':True,'preservedOriginalFiles':len(oldmap)}
    pathlib.Path('build-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()