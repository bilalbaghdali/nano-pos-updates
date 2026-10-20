#!/usr/bin/env python3
"""Build 1.0.89 app.asar from the verified published 1.0.87 codebase.
v1.0.88 changed the Windows installer icon, not renderer business logic.
Patch is compatible with installed v1.0.88 only (preserves the desktop EXE icon).
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

SOURCE_ZIP_SHA = 'c273ac3a9ce72be5f742b1410871eb54669f1fa19fb728867a7c4fc64e7d268f'
SOURCE_ASAR_SHA = 'a6cbd3920e5eea86e4aa885b1988b1738ad004b1d29cea827388389e4b9f79a7'
SOURCE_FILE = 'nano-faith-login.js'
TARGET_VERSION = b'"version": "1.0.89"'
def sha(data): return hashlib.sha256(data).hexdigest()
def build(source_zip, replacement_js, dest_zip):
    assert sha(source_zip.read_bytes()) == SOURCE_ZIP_SHA, 'Unexpected source ZIP'
    with zipfile.ZipFile(source_zip) as z:
        assert z.namelist() == ['payload/app.asar'], 'Unexpected release contents'
        data = bytearray(z.read('payload/app.asar'))
    assert sha(data) == SOURCE_ASAR_SHA, 'Source asar SHA mismatch'
    a,n,c,d=struct.unpack_from('<4I',data)
    header=json.loads(data[16:16+d]); base=8+n
    def lookup(path):
        obj=header['files'][path]; start=base+int(obj['offset']);size=obj['size'];return obj,start,size
    old,st,size=lookup(SOURCE_FILE)
    assert b'NANO_FAITH_186' in data[st:st+size], 'Wrong faith source'
    updated=replacement_js.read_bytes()
    assert len(updated)<=size,'Unexpectedly long banner script'
    updated=updated.ljust(size,b' ')
    data[st:st+size]=updated
    assert 'integrity' in old,'Old JS integrity missing'
    old['integrity']['hash']=sha(updated)
    old['integrity']['blocks']=[sha(updated)]
    pkg,ps,pl=lookup('package.json')
    old_pkg=bytes(data[ps:ps+pl])
    assert old_pkg.count(b'"version": "1.0.87"')==1
    new_pkg=old_pkg.replace(b'"version": "1.0.87"',TARGET_VERSION)
    assert len(old_pkg)==len(new_pkg)
    data[ps:ps+pl]=new_pkg
    pkg['integrity']['hash']=sha(new_pkg)
    pkg['integrity']['blocks']=[sha(new_pkg)]
    assert json.loads(new_pkg)['version']=='1.0.89'
    head=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    assert len(head)==d,'Header length changed'
    data[16:16+d]=head
    dest_zip.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest_zip,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('payload/app.asar',data)
    with zipfile.ZipFile(dest_zip) as z:
        assert sha(z.read('payload/app.asar'))==sha(data)
    print(json.dumps({'file':dest_zip.name,'zip_sha256':sha(dest_zip.read_bytes()),'asar_sha256':sha(data),'size':dest_zip.stat().st_size}))
if __name__=='__main__':
    src,new,out=map(Path,sys.argv[1:4])
    build(src,new,out)
