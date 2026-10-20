#!/usr/bin/env python3
"""Build NANO POS 1.0.90 from authenticated v1.0.89 ASAR without shifting offsets."""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

SOURCE_ASAR_SHA = "04f9120f6b1d890943abb199d452da92cc39f8d8d78c415a50cf119ef37af2ab"
def sha(b):return hashlib.sha256(b).hexdigest()
def build(source,jsfile,output):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==["payload/app.asar"], "Invalid source"
  data=bytearray(z.read("payload/app.asar"))
 assert sha(data)==SOURCE_ASAR_SHA, "Base ASAR SHA mismatch"
 a,n,c,d=struct.unpack_from("<4I",data)
 head=json.loads(data[16:16+d]);base=8+n
 def entry(name):
  obj=head["files"][name];return obj,base+int(obj["offset"]),int(obj["size"])
 e,start,size=entry("index.html")
 html=bytes(data[start:start+size]).decode("utf-8")
 js=jsfile.read_text(encoding="utf-8").replace("\r\n","\n")
 assert "nanoLoginPcRoles" in js and "stopImmediatePropagation" in js
 assert 'id="loginOverlay"' in html and 'id="loginForm"' in html
 assert "nano-secondary-login-190" not in html
 inserted='\n<script id="nano-secondary-login-190">\n'+js+'\n</script>\n'
 html=html.replace("</body>",inserted+"</body>",1)
 def clean(m):
  interior=m.group(0)[4:-3]
  return "" if "<" not in interior and ">" not in interior else m.group(0)
 html=re.sub(r"<!--[\s\S]*?-->",clean,html)
 new=html.encode("utf-8")
 assert len(new)<=size, f"HTML too long: {len(new)} > {size}"
 assert new.count(b'id="loginOverlay"')==1 and new.count(b'id="loginForm"')==1
 new=new.ljust(size,b" ")
 data[start:start+size]=new
 e["integrity"]["hash"]=sha(new);e["integrity"]["blocks"]=[sha(new)]
 pkg,p,sz=entry("package.json")
 orig=bytes(data[p:p+sz])
 assert orig.count(b'"version": "1.0.89"')==1
 fixed=orig.replace(b'"version": "1.0.89"',b'"version": "1.0.90"')
 assert len(fixed)==sz and json.loads(fixed)["version"]=="1.0.90"
 data[p:p+sz]=fixed
 pkg["integrity"]["hash"]=sha(fixed);pkg["integrity"]["blocks"]=[sha(fixed)]
 header=json.dumps(head,separators=(",",":"),ensure_ascii=False).encode("utf-8")
 assert len(header)==d, "ASAR header offset mismatch"
 data[16:16+d]=header
 output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr("payload/app.asar",data)
 with zipfile.ZipFile(output) as z:assert sha(z.read("payload/app.asar"))==sha(data)
 print("ZIP SHA256",sha(output.read_bytes()),"ASAR SHA256",sha(data),"size",output.stat().st_size)
if __name__=="__main__":
 source,js,output=map(Path,sys.argv[1:4]);build(source,js,output)
