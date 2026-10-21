#!/usr/bin/env python3
"""Patch only the search routing and version in the verified NANO POS 1.0.91 ASAR."""
import sys,zipfile,hashlib,struct,json
from pathlib import Path
EXPECTED='55424bde8d6767ba5e2e76b3736112ca6db51d11e259e52d82a44bd6eed4d55b'
sha=lambda b:hashlib.sha256(b).hexdigest()
OLD="""    input.addEventListener('input',()=>{
      root.clearTimeout(searchTimer); searchTimer=root.setTimeout(()=>apply(input),120);
    });
    input.addEventListener('keydown',evt=>{
      if(evt.key==='Escape' && input.value){input.value='';apply(input,true);evt.stopPropagation();}
    });"""
NEW="""    // v1.0.92: keep top-bar search scoped to current active section.
    // Capture before the legacy global-search screen navigation.
    root.addEventListener('input', evt => {
      if (evt.target !== input) return;
      evt.stopImmediatePropagation();
      root.clearTimeout(searchTimer);
      searchTimer=root.setTimeout(()=>apply(input),120);
    }, true);
    root.addEventListener('keydown', evt => {
      if (evt.target !== input) return;
      if (evt.key === 'Enter') {
        evt.preventDefault(); evt.stopImmediatePropagation();
        root.clearTimeout(searchTimer); apply(input,true);
      } else if (evt.key === 'Escape') {
        evt.preventDefault(); evt.stopImmediatePropagation();
        input.value='';root.clearTimeout(searchTimer);apply(input,true);
      }
    }, true);
    root.addEventListener('click', evt => {
      if (evt.target !== input && !input.parentElement?.contains(evt.target)) return;
      evt.stopImmediatePropagation();
    }, true);"""
def build(source):
    assert sha(source)==EXPECTED,'v1.0.91 source ASAR does not match official manifest'
    magic,block,content_size,header_size=struct.unpack_from('<4I',source)
    assert magic==4 and block==content_size+4
    header=json.loads(source[16:16+header_size])
    entries=[]
    def walk(folder,p=''):
        for name,item in folder.get('files',{}).items():
            if 'files' in item:walk(item,p+name+'/')
            elif 'offset' in item:entries.append((p+name,item))
    walk(header)
    entries.sort(key=lambda pair:int(pair[1]['offset']))
    data=bytearray()
    changed=[]
    for path,item in entries:
        start=8+block+int(item['offset'])
        blob=source[start:start+int(item['size'])]
        assert len(blob)==item['size']
        if path=='nano-v146-section-search.js':
            text=blob.decode('utf8')
            assert text.count(OLD)==1 and "globalSearch" in text
            blob=text.replace(OLD,NEW).encode('utf8')
            changed.append(path)
        if path=='package.json':
            text=blob.decode('utf8')
            assert json.loads(text)['version']=='1.0.91' and text.count('"version": "1.0.91"')==1
            blob=text.replace('"version": "1.0.91"','"version": "1.0.92"').encode('utf8')
            changed.append(path)
        item['offset']=str(len(data))
        item['size']=len(blob)
        if path in changed and 'integrity' in item:
            item['integrity']['hash']=sha(blob)
            item['integrity']['blocks']=[sha(blob[i:i+4194304]) for i in range(0,len(blob),4194304)]
        data.extend(blob)
    assert set(changed)=={'nano-v146-section-search.js','package.json'}
    h=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8')
    cs=(len(h)+7)&~3
    bs=cs+4
    packaged=struct.pack('<4I',4,bs,cs,len(h))+h+(b'\0'*(cs-4-len(h)))+data
    assert json.loads(packaged[16:16+len(h)])['files']['package.json']['size']>0
    return packaged
if __name__=='__main__':
    src,dst,jsfile=sys.argv[1:]
    with zipfile.ZipFile(src) as z:
        assert z.namelist()==['payload/app.asar']
        asar=build(z.read('payload/app.asar'))
    Path(dst).parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dst,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('payload/app.asar',asar)
    m,b,c,n=struct.unpack_from('<4I',asar)
    h=json.loads(asar[16:16+n]);e=h['files']['nano-v146-section-search.js']
    Path(jsfile).write_bytes(asar[8+b+int(e['offset']):8+b+int(e['offset'])+int(e['size'])])
    print('ASAR_SHA256='+sha(asar))
    print('PATCH_SHA256='+sha(Path(dst).read_bytes()))
