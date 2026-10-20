#!/usr/bin/env python3
"""Patch the real NANO POS 1.0.90 login screen to show PC mode choice in static HTML."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

EXPECTED_ZIP_SHA="e4bc124b6b76107ccf5e47f86250c7ee300d10eec618c502450c84aaa123c169"
def sha(data):return hashlib.sha256(data).hexdigest()
def build(source,destination):
 assert sha(source.read_bytes())==EXPECTED_ZIP_SHA,"Unexpected base v1.0.90 ZIP"
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==["payload/app.asar"]
  data=bytearray(z.read("payload/app.asar"))
 a,n,c,d=struct.unpack_from("<4I",data)
 header=json.loads(data[16:16+d]);base=8+n
 def item(path):
  entry=header["files"][path];return entry,base+int(entry["offset"]),int(entry["size"])
 entry,start,size=item("index.html")
 html=bytes(data[start:start+size]).decode("utf-8").rstrip()
 opening='<script id="nano-secondary-login-190">'
 assert html.count(opening)==1 and html.count('<form id="loginForm"')==1
 begin=html.index(opening);end=html.index("</script>",begin)+9
 javascript=html[begin+len(opening):end-9]
 # Support both inspected local builds and the published 1.0.90 renderer.
 if "const block=document.createElement('div');block.id='nanoLoginPcRoles'" in javascript:
  javascript=javascript.replace("if(!form||$('nanoLoginPcRoles'))return;","if(!form)return;")
  p1=javascript.index("const block=document.createElement('div');block.id='nanoLoginPcRoles'")
  p2=javascript.index("form.insertBefore(block,$('loginBtn'));",p1)
  javascript=javascript[:p1]+"const block=$('nanoLoginPcRoles');if(!block)return;\n"+javascript[p2:]
  javascript=javascript.replace("form.insertBefore(block,$('loginBtn'));","",1)
 elif "const container=document.createElement('div');" in javascript:
  p1=javascript.index("    const container=document.createElement('div');")
  p2=javascript.index("    const style=document.createElement('style');",p1)
  javascript=javascript[:p1]+"    const container=$('nanoLoginPcRoles');if(!container)return;\n"+javascript[p2:]
  marker="document.head.appendChild(style);form.insertBefore(container,$('loginBtn'));"
  assert javascript.count(marker)==1
  javascript=javascript.replace(marker,"document.head.appendChild(style);")
 else:raise AssertionError("Unknown original 1.0.90 login script; stop build")
 assert "document.addEventListener('submit',checkSubmit,true)" in javascript
 markup=Path(".github/assets/nano-login-191-static.html").read_text(encoding="utf-8")
 css=Path(".github/assets/nano-login-191.css").read_text(encoding="utf-8")
 assert 'id="nanoLoginPcRoles"' in markup and 'id="nanoSecondaryFields"' in markup
 form_start=html.index(">",html.index('<form id="loginForm"'))+1
 html=html[:form_start]+"\n"+markup+html[form_start:]
 begin=html.index(opening);end=html.index("</script>",begin)+9
 html=html[:begin]+'<style id="nanoSecondaryLoginVisible191">\n'+css+'\n</style>\n'+opening+javascript+'</script>'+html[end:]
 content=html.encode("utf-8")
 assert len(content)<=size,(len(content),size)
 assert content.count(b'id="nanoLoginPcRoles"')==1
 assert content.count(b'id="nanoLoginAsSecondary"')==1
 assert content.count(b'id="loginForm"')==1 and content.count(b'id="loginBtn"')==1
 content=content.ljust(size,b" ")
 data[start:start+size]=content
 entry["integrity"]["hash"]=sha(content);entry["integrity"]["blocks"]=[sha(content)]
 pkg,ps,psz=item("package.json")
 old=bytes(data[ps:ps+psz]);assert old.count(b'"version": "1.0.90"')==1
 new=old.replace(b'"version": "1.0.90"',b'"version": "1.0.91"')
 assert len(new)==len(old) and json.loads(new)["version"]=="1.0.91"
 data[ps:ps+psz]=new
 pkg["integrity"]["hash"]=sha(new);pkg["integrity"]["blocks"]=[sha(new)]
 packed=json.dumps(header,separators=(",",":"),ensure_ascii=False).encode("utf-8")
 assert len(packed)==d,"ASAR header layout mismatch"
 data[16:16+d]=packed
 destination.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(destination,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr("payload/app.asar",data)
 with zipfile.ZipFile(destination) as z:assert sha(z.read("payload/app.asar"))==sha(data)
 print("v1.0.91 SHA256",sha(destination.read_bytes()),"app.asar",sha(data))
 if len(sys.argv)>3:Path(sys.argv[3]).write_text(javascript,encoding="utf-8")
if __name__=="__main__":
 build(Path(sys.argv[1]),Path(sys.argv[2]))
