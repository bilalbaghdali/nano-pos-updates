#!/usr/bin/env python3
"""Read only printer/receipt architecture audit from verified v1.0.109."""
import hashlib,json,re,struct,zipfile
from pathlib import Path
p=Path("source/NANO-POS-Patch-1.0.108-to-1.0.109-PAYMENT-LABEL.zip")
manifest=json.loads(Path('nano-pos-update.json').read_text())
assert manifest['version']=='1.0.109'
assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['patches'][0]['sha256']
with zipfile.ZipFile(p) as z:
 assert z.namelist()==['payload/app.asar'];raw=z.read('payload/app.asar')
assert hashlib.sha256(raw).hexdigest()==manifest['patches'][0]['appAsarSha256']
magic,block,hs,n=struct.unpack_from('<4I',raw);assert magic==4 and block==hs+4
head=json.loads(raw[16:16+n]);start=8+block
def fetch(name):
 e=head
 for part in name.split('/'):e=e['files'][part]
 return raw[start+int(e['offset']):start+int(e['offset'])+e['size']].decode('utf-8')
allfiles=[]
def walk(tree,prefix=''):
 for name,e in tree['files'].items():
  if 'files' in e:walk(e,prefix+name+'/')
  else:allfiles.append((prefix+name,e))
walk(head)
lines=[f"VERIFIED OFFICIAL {manifest['version']} SHA={manifest['patches'][0]['appAsarSha256']}"]
targets=[(n,e) for n,e in allfiles if n.endswith(('.js','.cjs','.html','.css')) and
 any(k in n.lower() for k in ('print','invoice','receipt','ticket','sale','renderer','index','template','pos','main'))]
lines.append('RELEVANT FILES '+repr([(n,e.get('size',0)) for n,e in targets[:200]]))
patterns=[r'print\(',r'printPreview',r'print-preview',r'printReceipt',r'openPrint',r'printInvoice',r'print-sales',r'print-sale',
 r'58mm',r'80mm',r'\bA4\b',r'invoiceTemplate',r'printTemplate',r'print-settings',r'thermal',
 r'فاتورة بيع',r'وصل البيع',r'printLanguage',r'printFormat',r'window.open',r'print\(\)',r'createPrint',
 r'printJob',r'printReceipt',r'printInvoice',r'generateReceipt']
for filename,e in targets:
 if e.get('size',0)>3500000:continue
 try:s=fetch(filename)
 except:continue
 match=[(m,len(list(re.finditer(m,s,re.I)))) for m in patterns if re.search(m,s,re.I)]
 if not match:continue
 lines.append('\nFILE '+filename+' LENGTH '+str(len(s))+' MATCHES '+repr(match))
 intervals=[]
 for pat,_ in match:
  ms=list(re.finditer(pat,s,re.I))
  for m in ms[:8]:
   a=max(0,m.start()-330);b=min(len(s),m.end()+1350)
   intervals.append((a,b))
 intervals.sort()
 fused=[]
 for a,b in intervals:
  if fused and a<=fused[-1][1]:fused[-1]=(fused[-1][0],max(b,fused[-1][1]))
  else:fused.append((a,b))
 for a,b in fused[:20]: lines.append('EXCERPT '+repr(s[a:min(b,a+7500)]))
lines.append('INDEX END SNIPPET '+repr(fetch('index.html')[-12000:]))
out=Path('development/print/print-architecture-audit-110.txt')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text('\n'.join(lines),encoding='utf8')
print('AUDIT READY bytes',out.stat().st_size,'files',len(targets))
