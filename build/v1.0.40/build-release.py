#!/usr/bin/env python3
"""Build SHA-verified v1.0.40 update from the exact v1.0.39 published app.asar."""
import base64,hashlib,io,json,pathlib,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.39/NANO-POS-Patch-1.0.38-to-1.0.39-SYSTEM-STABILITY.zip'
BASE_ZIP_SHA='92fce0ec5be0364ca0118089b965a6265ec99b77c369841a89b83aeb94077f30'
BASE_ASAR_SHA='3798b58ea46f5b4d01a51e85dac07f6db8f1478213f2dbf7fb1dd1397ca76489'
DELTA_SHA='2f7e975f918da654f301c9e907e9677f7f4458f2f443b3f521ab293b5c14f7a7'
ASSET='NANO-POS-Patch-1.0.39-to-1.0.40-IMPROVEMENTS.zip'
def sha(b):return hashlib.sha256(b).hexdigest()
def unpack(archive):
    length=struct.unpack('<I',archive[12:16])[0]
    head=json.loads(archive[16:16+length])
    start=8+struct.unpack('<I',archive[4:8])[0]
    found={}
    def walk(node,prefix=''):
        for name,item in node['files'].items():
            key=prefix+name
            if 'files' in item:walk(item,key+'/')
            else:found[key]=(item,archive[start+int(item['offset']):start+int(item['offset'])+item['size']])
    walk(head)
    return found

def pack(files):
    head={'files':{}};parts=[];offset=0
    for name,(metadata,blob) in files.items():
        node=head
        path=name.split('/')
        for elem in path[:-1]:node=node['files'].setdefault(elem,{'files':{}})
        new={'size':len(blob),'offset':str(offset)}
        if 'integrity' in metadata:
            block=metadata['integrity'].get('blockSize',4194304)
            new['integrity']={'algorithm':'SHA256','hash':sha(blob),'blockSize':block,'blocks':[sha(blob[i:i+block]) for i in range(0,len(blob),block)]}
        node['files'][path[-1]]=new
        offset+=len(blob);parts.append(blob)
    data=json.dumps(head,ensure_ascii=False,separators=(',',':')).encode('utf8')
    padded=(len(data)+3)&~3
    return struct.pack('<IIII',4,padded+8,padded+4,len(data))+data+b'\0'*(padded-len(data))+b''.join(parts)

def main():
    base=pathlib.Path('nano-pos-base-1.0.39.zip')
    if not base.exists():
        req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v1.0.40-verified-builder'})
        with urllib.request.urlopen(req,timeout=180) as res:base.write_bytes(res.read())
    assert sha(base.read_bytes())==BASE_ZIP_SHA,'Unverified base update ZIP'
    with zipfile.ZipFile(base) as z:old_asar=z.read('payload/app.asar')
    assert sha(old_asar)==BASE_ASAR_SHA,'Unverified base app.asar'
    parts=sorted(ROOT.glob('delta-part-*.b64'))
    assert len(parts)==1,'Expected one checked delta fragment'
    delta=base64.b64decode(''.join(p.read_text().strip() for p in parts),validate=True)
    assert sha(delta)==DELTA_SHA,'Invalid release delta SHA256'
    with zipfile.ZipFile(io.BytesIO(delta)) as z:
        assert z.testzip() is None,'Invalid delta archive'
        descriptor=json.loads(z.read('manifest.json'))
        assert descriptor['version']=='1.0.40' and descriptor['requires']=='1.0.39'
        changed={name:z.read('changed/'+name) for name in descriptor['changes']}
    assert set(changed)=={'release-notes.js','app-config.js','package.json'}
    old=unpack(old_asar)
    for name,spec in descriptor['changes'].items():
        assert name in old,'Missing source app file: '+name
        assert sha(old[name][1])==spec['baseSha256'],'Changed base file: '+name
        assert sha(changed[name])==spec['updatedSha256'],'Changed candidate file: '+name
    assert json.loads(changed['package.json'])['version']=='1.0.40'
    notes=changed['release-notes.js'].decode()
    assert 'اقتراح المنتجات المطابقة بعد كتابة أربعة أحرف' in notes
    assert "['تحسينات','الإصدار المثبت']" in notes
    assert "const MIN = 4" in notes
    helper=(ROOT/'nano-v140-smart-lookup.js').read_text()
    assert notes.endswith(helper),'Tested lookup script differs from bundled script'
    for name in ('app-config.js','release-notes.js'):
        file=pathlib.Path('validate-'+name);file.write_bytes(changed[name]);
        subprocess.run(['node','--check',str(file)],check=True,timeout=30)
    subprocess.run(['node','--test',str(ROOT/'test-smart-lookup.cjs')],check=True,timeout=45)
    final=pack({name:(meta,changed.get(name,data)) for name,(meta,data) in old.items()})
    after=unpack(final)
    for name,data in changed.items():assert after[name][1]==data
    assert 'node_modules/megajs/package.json' in after, 'Lost direct MEGA feature'
    assert old['renderer.js'][1]==after['renderer.js'][1], 'Unexpected change to existing POS renderer'
    with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',final)
    with zipfile.ZipFile(ASSET) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
        assert z.read('payload/app.asar')==final
    output={'fileName':ASSET,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(final),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'fromVersion':'1.0.39','version':'1.0.40','testCount':10}
    pathlib.Path('build-result.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))
if __name__=='__main__':main()