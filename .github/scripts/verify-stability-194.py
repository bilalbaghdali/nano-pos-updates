#!/usr/bin/env python3
"""Check NANO POS v1.0.94 against exact official 1.0.93 package."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
SHA=lambda data: hashlib.sha256(data).hexdigest()
original,updated,out=map(Path,sys.argv[1:4])
out.mkdir(exist_ok=True,parents=True)
def archive(path):
 with zipfile.ZipFile(path) as z:
  assert z.namelist()==['payload/app.asar']
  return z.read('payload/app.asar')
def files(data):
 magic,b,c,n=struct.unpack_from('<4I',data)
 assert magic==4 and b==c+4
 head=json.loads(data[16:16+n])
 results={}
 def walk(node,prefix=''):
  for name,item in node.get('files',{}).items():
   path=prefix+name
   if 'files' in item:walk(item,path+'/')
   elif 'offset' in item:
    pos=8+b+int(item['offset'])
    blob=data[pos:pos+item['size']]
    assert len(blob)==item['size'],path
    if item.get('integrity'):
     assert item['integrity']['hash']==SHA(blob),('hash mismatch',path)
    results[path]=blob
 walk(head)
 return results
a=files(archive(original));b=files(archive(updated))
assert a.keys()==b.keys(),'File inventory changed unexpectedly'
changes={name for name in a if a[name]!=b[name]}
expected={'package.json','updater-main.cjs','backup-safety.cjs','release-notes.js'}
assert changes==expected,('unexpected changed files',sorted(changes^expected))
assert json.loads(a['package.json'])['version']=='1.0.93'
assert json.loads(b['package.json'])['version']=='1.0.94'
assert a['renderer.js']==b['renderer.js']
assert a['index.html']==b['index.html']
assert a['license-client.js']==b['license-client.js']
for filename in ['updater-main.cjs','backup-safety.cjs','release-notes.js','update-manager.js','renderer.js','nano-v146-section-search.js','electron-main.cjs','package.json']:
 (out/filename).write_bytes(b[filename])
print('PASS: exactly 4 intended files changed, ASAR SHA-256 integrity valid, renderer and licensing preserved')
print('Patch:',updated.name,SHA(updated.read_bytes()))
