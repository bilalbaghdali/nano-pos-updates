#!/usr/bin/env python3
"""Rebuild v1.0.36 with tested differential sources, verify every file digest."""
import base64,hashlib,json,pathlib,struct,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.35/NANO-POS-Patch-1.0.34-to-1.0.35-AUTO.zip'
BASE_ZIP_SHA='8215a93b898b82b425e9a9a0db8f37e79f44f953303d56f12a02e41b3811549a'
BASE_ASAR_SHA='485d5662f9e53cbbbc52fb22a72a9616950224d7aea34a07dab23c42ee73d73c'
DELTA_SHA='b0ee477581f9e351b6c703be7aafc38d8c58a48d14e0566d62b9f2f7448f7404'
EXPECTED_ASAR_SHA='ad8ab6edb01620cd3970fa9eca64ed5b844e599adfe4111d905d338315401fc4'
ASSET='NANO-POS-Patch-1.0.35-to-1.0.36-MEGA.zip'
def sha(x):return hashlib.sha256(x).hexdigest()
def entries(archive):
    header=json.loads(archive[16:16+struct.unpack('<I',archive[12:16])[0]])
    start=8+struct.unpack('<I',archive[4:8])[0]
    result={}
    def walk(n,base=''):
        for filename,meta in n['files'].items():
            name=base+filename
            if 'files' in meta:walk(meta,name+'/')
            else: result[name]=(start+int(meta['offset']),meta['size'])
    walk(header)
    return result
def main():
    request=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-release-builder'})
    basezip=pathlib.Path('nano135-base.zip')
    if not basezip.exists():
        with urllib.request.urlopen(request,timeout=180) as response:basezip.write_bytes(response.read())
    assert sha(basezip.read_bytes())==BASE_ZIP_SHA,'Base archive hash mismatch'
    with zipfile.ZipFile(basezip) as z:old=z.read('payload/app.asar')
    assert sha(old)==BASE_ASAR_SHA,'Base ASAR hash mismatch'
    chunks=sorted(ROOT.glob('delta-part-*.b64'))
    assert len(chunks)==4,'Missing delta parts'
    delta_bytes=base64.b64decode(''.join(x.read_text().strip() for x in chunks),validate=True)
    assert sha(delta_bytes)==DELTA_SHA,'Delta SHA mismatch'
    dz=pathlib.Path('delta.zip');dz.write_bytes(delta_bytes)
    with zipfile.ZipFile(dz) as z:
        new_header=z.read('header.bin')
        replacements={p.removeprefix('modified/'):z.read(p) for p in z.namelist() if p.startswith('modified/') and not p.endswith('/')}
    old_table=entries(old);new_table=entries(new_header)
    base=len(new_header)
    result=bytearray(new_header)
    for filename,(offset,size) in sorted(new_table.items(),key=lambda x:x[1][0]):
        if filename in replacements:payload=replacements[filename]
        else:
            start,length=old_table[filename]
            assert length==size,'Changed file missing from delta: '+filename
            payload=old[start:start+length]
        assert len(payload)==size and offset==len(result),'ASAR offset mismatch '+filename
        result.extend(payload)
    assert sha(result)==EXPECTED_ASAR_SHA,'Rebuilt ASAR does not match locally tested image'
    with zipfile.ZipFile(ASSET,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',result)
    with zipfile.ZipFile(ASSET) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    output={'fileName':ASSET,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':EXPECTED_ASAR_SHA,'sizeBytes':pathlib.Path(ASSET).stat().st_size}
    pathlib.Path('build-result.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))
if __name__=='__main__':main()
