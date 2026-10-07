import struct,json,hashlib,base64
from pathlib import Path
p=Path("payload/app.asar")
controller=base64.b64decode(Path("../tools/.tmp-controller-v1.0.32.b64").read_text().strip())
if hashlib.sha256(controller).hexdigest()!="f0a5e0e44ad3aaa4c68844308f699322f0b80ef9a45366665edeb4caf7aef29c":
    raise RuntimeError("controller checksum mismatch")
with p.open("rb") as f:
    f.read(4); hs=struct.unpack("<I",f.read(4))[0]; hb=f.read(hs); sl=struct.unpack("<I",hb[4:8])[0]; h=json.loads(hb[8:8+sl]); base=8+hs
nodes={}
def walk(n,pre=""):
    for name,m in n.get("files",{}).items():
        q=f"{pre}/{name}" if pre else name
        if "files" in m: walk(m,q)
        else: nodes[q]=m
walk(h)
version_files={"app-config.js","browser-ui.css","browser-ui.js","index.html","package-lock.json","package.json"}
targets=version_files|{"document-print-preview.js","mobile/www/document-print-preview.js"}
changed={}
with p.open("rb") as f:
    for path,m in nodes.items():
        if path not in targets: continue
        f.seek(base+int(m["offset"])); orig=f.read(m["size"]); data=orig
        if path in version_files:
            data=data.replace(b"1.0.31",b"1.0.32")
        if path in {"document-print-preview.js","mobile/www/document-print-preview.js"}:
            if len(controller)>m["size"]: raise RuntimeError("controller too large")
            data=controller+b" "*(m["size"]-len(controller))
        if data==orig: continue
        changed[path]=data
        integ=m.get("integrity") or {}; bs=int(integ.get("blockSize") or 4194304)
        integ["algorithm"]="SHA256"; integ["hash"]=hashlib.sha256(data).hexdigest(); integ["blockSize"]=bs
        integ["blocks"]=[hashlib.sha256(data[i:i+bs]).hexdigest() for i in range(0,len(data),bs)]
        m["integrity"]=integ
newjson=json.dumps(h,separators=(",",":"),ensure_ascii=False).encode()
if len(newjson)!=sl: raise RuntimeError("header length changed")
newhb=struct.pack("<I",struct.unpack("<I",hb[:4])[0])+struct.pack("<I",sl)+newjson+hb[8+sl:]
with p.open("r+b") as f:
    f.seek(8); f.write(newhb)
    for path,data in changed.items():
        m=nodes[path]; f.seek(base+int(m["offset"])); f.write(data)
sha=hashlib.sha256(p.read_bytes()).hexdigest()
print("app.asar sha256",sha)
if sha!="be83d542760750e67416ba0d7f7125fdd580a862aaa2dccca0ca849cff75cff8":
    raise RuntimeError("unexpected app.asar sha "+sha)
