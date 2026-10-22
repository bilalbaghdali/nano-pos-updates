#!/usr/bin/env python3
"""Read-only targeted audit of exact released NANO POS v1.0.111 ASAR."""
import json,hashlib,zipfile,struct,re
from pathlib import Path
manifest=json.loads(Path('nano-pos-update.json').read_text())
p=Path('source/NANO-POS-Patch-1.0.110-to-1.0.111-INVOICE-FA.zip')
assert manifest['version']=='1.0.111' and hashlib.sha256(p.read_bytes()).hexdigest()==manifest['patches'][0]['sha256']
with zipfile.ZipFile(p) as z:raw=z.read('payload/app.asar')
assert hashlib.sha256(raw).hexdigest()==manifest['patches'][0]['appAsarSha256']
magic,block,hs,n=struct.unpack_from('<4I',raw);assert magic==4 and block==hs+4
files=json.loads(raw[16:16+n])['files']
def source(name):
 e=files[name];return raw[8+block+int(e['offset']):8+block+int(e['offset'])+e['size']].decode('utf8')
out=[]
def excerpt(name,text,needle,before=500,after=1750,limit=4):
 found=list(re.finditer(re.escape(needle),text))
 out.append('\n### '+name+' '+needle+' MATCHES='+str(len(found)))
 for m in found[:limit]:out.append(text[max(0,m.start()-before):m.start()+after])
for name in ['electron-main.cjs','browser-bridge.js','backup-safety.cjs','updater-main.cjs','release-notes.js','index.html']:
 if name not in files:continue
 s=source(name)
 if name=='electron-main.cjs':
  for needle in ['ready-to-show','createWindow','showInactive','webPreferences','backgroundThrottling','onBeforeQuit','whenReady','nanoNative','loadFile(']:
   excerpt(name,s,needle,350,1200,2)
 elif name=='browser-bridge.js':
  for needle in ['function save()','function load()','function saveDb(','function saveDatabase','function commit','function normalize','const KEY','db.sales.unshift(sale)','const snapshot={...db','save();','save()','__nanoBrowserData']:
   excerpt(name,s,needle,420,1450,3)
 elif name=='backup-safety.cjs':
  for needle in ['function verifyBackup','function writeBackup','function pruneBackups','module.exports']:
   excerpt(name,s,needle,150,1900,2)
 elif name=='updater-main.cjs':
  for needle in ['function normalizeManifest','findApplicablePatch','const DEFAULT_MANIFEST_URL','function compareVersions']:
   excerpt(name,s,needle,180,900,2)
 elif name=='release-notes.js':
  out.append('\nNOTES_HEADER '+s[:3000])
 elif name=='index.html':
  tags=list(re.finditer(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>',s,re.I))
  out.append('\nINDEX_SCRIPT_TAGS '+json.dumps([{'name':m.group(1),'defer':bool(re.search(r'\bdefer\b',m.group(0))),'at':m.start()} for m in tags],ensure_ascii=False))
  excerpt(name,s,'<script src="nano-invoice-sequence-111.js"></script>',600,650,1)
outpath=Path('development/reviews/final-112-source-excerpts.txt')
outpath.parent.mkdir(exist_ok=True,parents=True)
outpath.write_text('\n'.join(out),'utf8')
print('Verified official archive; audit length',outpath.stat().st_size)
