#!/usr/bin/env python3
"""Patch official NANO POS 1.0.94 ASAR, fail closed on any unexpected source."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
EXPECTED_ASAR='becb5bf183f2ac95e9c9b6f0b414eb84c19b643d2a8c9a7f471883c45bc4fc6f'
EXPECTED={
 'renderer.js':'457b6d9e1ae37c593fab57197fa9af8f45e2fb1c8a83eb611db8d0c39eabd86f',
 'index.html':'f94d0e02b449ca1859df5e0419d6ed9aaadabfb25e5a7662c6ff564e317c2335',
 'nano-v136-shortcuts.js':'b3ac2ed2dd790a932dc5e75446a15c391d16daf3b8dbec8b612e4d9305da66a1',
}
def replace_once(s,a,b):
    assert s.count(a)==1,(a[:75],s.count(a))
    return s.replace(a,b)
def modify(path,data):
    s=data.decode('utf-8')
    if path=='nano-v136-shortcuts.js':
        s=replace_once(s,"    if(e.key==='F2' && !e.altKey){",
          "    if(e.key==='F2' && !e.altKey && !e.shiftKey){\n"
          "      // F2 suspends the invoice in POS; search is only for other sections.\n"
          "      const sale=document.getElementById('salesSection');\n"
          "      if(sale && !sale.classList.contains('hidden')) return;")
    elif path=='index.html':
        s=replace_once(s,'<script defer src="nano-fast-pos.js"></script>',
          '<script defer src="nano-fast-pos.js"></script>\n'
          '<script defer src="nano-sales-safe-195.js"></script>')
    elif path=='renderer.js':
        key="const _0xb1e6f4=_0xec5601[_0x5ec8b1(0xa2b)],_0x1e11b4=_0xec5601['items'];"
        s=replace_once(s,key,key+
          "if(!Array.isArray(_0x1e11b4)||!_0x1e11b4.length){"
          "showToast('تعذر فتح فاتورة بلا بنود صالحة.','error');return false;}")
        key="cart=[],currentEditSaleId=_0xb1e6f4['id'];"
        s=replace_once(s,key,
          "const __nanoEditCheck195=window.NANO_SALE_SAFE_195?.inspectInvoice(_0x1e11b4,_0x1f1632);"
          "if(__nanoEditCheck195&&!__nanoEditCheck195.ok){"
          "showToast(__nanoEditCheck195.message,'error');return false;}"+key)
        key='async function executeSalePayload(_0x1ebf74,_0x8b1902){const _0x4ca74f=_0x427934;try{'
        s=replace_once(s,key,
          'async function executeSalePayload(_0x1ebf74,_0x8b1902){const _0x4ca74f=_0x427934;'
          'const __nanoSaleSafe195=window.NANO_SALE_SAFE_195;'
          'if(__nanoSaleSafe195&&!__nanoSaleSafe195.begin())return;try{')
        start=s.index('async function executeSalePayload(')
        end=s.index('async function loadCategories()',start)
        fn=s[start:end]
        assert fn.endswith('}}}') and 'catch(_0x31d03c)' in fn
        fn=fn[:-1]+'finally{__nanoSaleSafe195?.end();}}'
        s=s[:start]+fn+s[end:]
    elif path=='package.json':
        assert json.loads(s)['version']=='1.0.94'
        s=replace_once(s,'"version": "1.0.94"','"version": "1.0.95"')
    return s.encode('utf-8')
def build(raw,module,outdir):
    assert sha(raw)==EXPECTED_ASAR,'Wrong official v1.0.94 base ASAR SHA'
    magic,block,content_size,n=struct.unpack_from('<4I',raw)
    assert magic==4 and block==content_size+4
    header=json.loads(raw[16:16+n])
    assert 'nano-sales-safe-195.js' not in header['files']
    pos=8+block
    entries=[]
    def traverse(node,prefix=''):
        for name,entry in node.get('files',{}).items():
            if 'files' in entry:traverse(entry,prefix+name+'/')
            elif 'offset' in entry: entries.append((prefix+name,entry))
    traverse(header)
    entries.sort(key=lambda x:int(x[1]['offset']))
    data=bytearray()
    changed=set()
    def checksum(entry,blob):
        entry['integrity']={'algorithm':'SHA256','hash':sha(blob),
         'blockSize':4194304,
         'blocks':[sha(blob[i:i+4194304]) for i in range(0,len(blob),4194304)]}
    for name,entry in entries:
        old=raw[pos+int(entry['offset']):pos+int(entry['offset'])+entry['size']]
        assert len(old)==entry['size']
        if name in EXPECTED:
            assert sha(old)==EXPECTED[name],f'Source changed, abort: {name}'
            blob=modify(name,old)
            changed.add(name)
        elif name=='package.json':
            blob=modify(name,old)
            changed.add(name)
        else: blob=old
        entry['offset']=str(len(data))
        entry['size']=len(blob)
        if name in changed: checksum(entry,blob)
        data.extend(blob)
        if name in changed:
            (outdir/name).parent.mkdir(parents=True,exist_ok=True)
            (outdir/name).write_bytes(blob)
    assert changed==set(EXPECTED)|{'package.json'}
    newentry={'size':len(module),'offset':str(len(data))}
    checksum(newentry,module)
    header['files']['nano-sales-safe-195.js']=newentry
    data.extend(module)
    (outdir/'nano-sales-safe-195.js').write_bytes(module)
    packed=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    capacity=(len(packed)+7)&~3
    out=struct.pack('<4I',4,capacity+4,capacity,len(packed))+packed+b'\0'*(capacity-4-len(packed))+data
    npos=8+capacity+4+int(newentry['offset'])
    assert out[npos:npos+len(module)]==module
    return out
def main():
    src,dst,work=map(Path,sys.argv[1:4])
    work.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(src) as z:
        assert z.namelist()==['payload/app.asar']
        raw=z.read('payload/app.asar')
    module=Path('.github/assets/nano-sales-safe-195.js').read_bytes()
    out=build(raw,module,work)
    with zipfile.ZipFile(dst,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',out)
    with zipfile.ZipFile(dst) as z:assert sha(z.read('payload/app.asar'))==sha(out)
    print(json.dumps({'version':'1.0.95','asar_sha256':sha(out),'zip_sha256':sha(dst.read_bytes())}))
if __name__=='__main__':main()
