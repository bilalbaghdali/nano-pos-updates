#!/usr/bin/env python3
"""Build NANO POS 1.1.0 onboarding from the verified v1.0.91 desktop release.
Only index.html and package.json are modified. All store databases and user data stay untouched.
"""
from pathlib import Path
import hashlib, json, struct, sys, zipfile

ZIP_SHA='8116cd5ee114a5f8af79b66eca83f55441447af3e9a8b77d7a847a645f720b25'
ASAR_SHA='55424bde8d6767ba5e2e76b3736112ca6db51d11e259e52d82a44bd6eed4d55b'
def sha(data): return hashlib.sha256(data).hexdigest()
def build(source,out):
    assert sha(source.read_bytes())==ZIP_SHA,'Expected the published v1.0.91 patch'
    with zipfile.ZipFile(source) as z:
        assert z.namelist()==['payload/app.asar'],'Unexpected zip contents'
        data=bytearray(z.read('payload/app.asar'))
    assert sha(data)==ASAR_SHA,'Expected the authenticated v1.0.91 ASAR'
    a,n,c,d=struct.unpack_from('<4I',data)
    head=json.loads(data[16:16+d]);offset=8+n
    def find(path):
        entry=head['files'][path]
        return entry,offset+int(entry['offset']),entry['size']
    entry,start,size=find('index.html')
    html=bytes(data[start:start+size]).decode('utf-8').rstrip()
    assert html.count('</body>')==1 and 'nanoCommerce110' not in html
    assert 'id="nanoHomeSection"' in html
    css=Path('.github/assets/nano-commerce-110.css').read_text(encoding='utf-8').replace('\r\n','\n')
    js=Path('.github/assets/nano-commerce-110.js').read_text(encoding='utf-8').replace('\r\n','\n')
    script='<style id="nanoCommerceStyle110">'+css+'</style>\n<script id="nanoCommerce110">'+js+'</script>\n'
    html=html.replace('</body>',script+'</body>',1).encode('utf-8')
    assert len(html)<=size,(len(html),size)
    assert html.count(b'id="nanoCommerce110"')==1 and b'commerce_profile_v1' in html
    html=html.ljust(size,b' ')
    data[start:start+size]=html
    entry['integrity']['hash']=sha(html)
    entry['integrity']['blocks']=[sha(html)]
    pkg,pos,sz=find('package.json')
    old=bytes(data[pos:pos+sz])
    was=b'"version": "1.0.91"'
    now=b'"version": "1.1.0" '
    assert len(was)==len(now) and old.count(was)==1
    new=old.replace(was,now)
    assert len(new)==sz and json.loads(new)['version']=='1.1.0'
    data[pos:pos+sz]=new
    pkg['integrity']['hash']=sha(new)
    pkg['integrity']['blocks']=[sha(new)]
    header=json.dumps(head,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    assert len(header)==d,'ASAR header changed length'
    data[16:16+d]=header
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('payload/app.asar',data)
    with zipfile.ZipFile(out) as z: assert sha(z.read('payload/app.asar'))==sha(data)
    print('Verified version 1.1.0 ZIP SHA256',sha(out.read_bytes()),'ASAR',sha(data))
if __name__=='__main__':build(Path(sys.argv[1]),Path(sys.argv[2]))
