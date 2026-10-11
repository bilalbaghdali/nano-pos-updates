#!/usr/bin/env python3
"""Rebuild the exact NANO POS 1.0.37 app.asar for the optional updater."""
import base64,hashlib,json,pathlib,struct,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL="https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.36/NANO-POS-Patch-1.0.35-to-1.0.36-MEGA.zip"
BASE_ZIP_SHA="4f850bba6ab53842763673ee2493cfe3c1b8172973339038c849878798c98e16"
BASE_ASAR_SHA="ad8ab6edb01620cd3970fa9eca64ed5b844e599adfe4111d905d338315401fc4"
DELTA_SHA="f2377d60ae3d7ecd8b440c211f2177155e1ebd22c74fc6b5ff43f4ecc187690a"
EXPECTED_ASAR_SHA="174187656df21a5cffd3d4bd8a977d1e551bbbd1b1f9a3ab56b26d84587026e7"
ASSET="NANO-POS-Patch-1.0.36-to-1.0.37-MEGA-LOGIN.zip"
def digest(data):return hashlib.sha256(data).hexdigest()
def table(raw):
    tree=json.loads(raw[16:16+struct.unpack('<I',raw[12:16])[0]])
    start=8+struct.unpack('<I',raw[4:8])[0]
    d={}
    def walk(n,p=''):
        for name,item in n['files'].items():
            key=p+name
            if 'files' in item:walk(item,key+'/')
            else:d[key]=(start+int(item['offset']),item['size'])
    walk(tree)
    return d
def main():
    base=pathlib.Path("base-v1.0.36.zip")
    if not base.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-build'}),timeout=180) as u:base.write_bytes(u.read())
    assert digest(base.read_bytes())==BASE_ZIP_SHA,'Refuse unexpected base ZIP'
    with zipfile.ZipFile(base) as z:old=z.read('payload/app.asar')
    assert digest(old)==BASE_ASAR_SHA,'Refuse unexpected base app.asar'
    chunks=sorted(ROOT.glob('delta-part-*.b64'))
    assert len(chunks)==1,'Incomplete delta'
    blob=base64.b64decode(''.join(x.read_text().strip() for x in chunks),validate=True)
    assert digest(blob)==DELTA_SHA,'Delta checksum mismatch'
    dz=pathlib.Path('delta.zip');dz.write_bytes(blob)
    with zipfile.ZipFile(dz) as z:
        header=z.read('header.bin')
        changes={p[len('modified/'):]:z.read(p) for p in z.namelist() if p.startswith('modified/') and not p.endswith('/')}
    before=table(old);after=table(header);asar=bytearray(header)
    for key,(pos,size) in sorted(after.items(),key=lambda x:x[1][0]):
        if key in changes:data=changes[key]
        else:
            begin,original_size=before[key]
            assert original_size==size, 'Missing changed file: '+key
            data=old[begin:begin+size]
        assert len(data)==size and len(asar)==pos,'Invalid ASAR layout: '+key
        asar.extend(data)
    assert digest(asar)==EXPECTED_ASAR_SHA,'Candidate bytes differ from tested local build'
    with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(ASSET) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    info={'fileName':ASSET,'sha256':digest(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':EXPECTED_ASAR_SHA,'sizeBytes':pathlib.Path(ASSET).stat().st_size}
    pathlib.Path('build-result.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))
if __name__=='__main__':main()
