#!/usr/bin/env python3
"""Read-only audit of the SHA-verified NANO POS ASAR; never changes application files."""
import json,struct,sys,zipfile,hashlib,re
from pathlib import Path
base=Path(sys.argv[1]);assert base.is_file()
with zipfile.ZipFile(base) as z:
 assert z.namelist()==['payload/app.asar']
 data=z.read('payload/app.asar')
magic,block,size,n=struct.unpack_from('<4I',data)
assert magic==4 and block==size+4
h=json.loads(data[16:16+n]); start=8+block
files=[]
def walk(node,prefix=''):
 for name,ent in node.get('files',{}).items():
  if 'files' in ent:walk(ent,prefix+name+'/')
  elif 'offset' in ent:files.append((prefix+name,ent))
walk(h)
print('ASAR bytes',len(data),'files',len(files),'sha256',hashlib.sha256(data).hexdigest())
sel=[(k,e) for k,e in files if re.search('inventory|stock|reorder|low-stock|supplier|purchase|product|sales|dashboard|report|analytics|insight|forecast',k,re.I)]
print('INVENTORY RELATED FILES (name | bytes | sha256):')
for k,e in sel[:100]:
 raw=data[start+int(e['offset']):start+int(e['offset'])+e['size']]
 print(f'{k} | {e["size"]} | {hashlib.sha256(raw).hexdigest()}')
def snippet(s,pattern,size=190):
 results=[]
 for m in list(re.finditer(pattern,s,re.I))[:10]:
  a=max(m.start()-size,0);b=min(m.end()+size,len(s))
  results.append(s[a:b].replace('\n',' ')[:2*size])
 return results
for k,e in sel:
 if e['size']>750000 or not k.endswith(('.js','.cjs','.html')):continue
 raw=data[start+int(e['offset']):start+int(e['offset'])+e['size']]
 try:s=raw.decode('utf8')
 except:continue
 print('\nSOURCE:',k)
 if k.endswith('html'):
  for w in ['inventorySection','stockSection','productsSection','lowStock','reorder','restock','suggest','stockAlert']:
   print(' ',w,snippet(s,re.escape(w),180)[:3])
 else:
  print('HEAD:',s[:1300].replace('\n',' '))
  for w in ['reorder','recommended','slow.mov','lowStock','stockAlert','stockThreshold','minimum_stock','minStock']:
   matches=snippet(s,w,180)
   if matches:print(' ',w,matches[:4])
