#!/usr/bin/env python3
"""Build NANO POS 1.0.39 from the *published* 1.0.38 and reviewed source delta."""
import base64,hashlib,json,pathlib,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.38/NANO-POS-Patch-1.0.37-to-1.0.38-DIRECT-MEGA.zip'
BASE_ZIP_SHA='66154b4fe0798a899ff64aa716e789f0991918f2e87812fb2800af5d7844237d'
BASE_ASAR_SHA='132166cfb0773597c4d348bb922f59cb865463f95caf4c845e7539e1d4e546f7'
DELTA_SHA='8734b67ceb36e3f9d9acb68d11af8c7ff13b0a24459cd5750dabff773316423d'
ASSET='NANO-POS-Patch-1.0.38-to-1.0.39-SYSTEM-STABILITY.zip'
def sha(b):return hashlib.sha256(b).hexdigest()
def parse_files(archive):
 length=struct.unpack('<I',archive[12:16])[0]
 head=json.loads(archive[16:16+length])
 data_start=8+struct.unpack('<I',archive[4:8])[0]
 found={}
 def walk(n,prefix=''):
  for name,node in n['files'].items():
   key=prefix+name
   if 'files' in node:walk(node,key+'/')
   else:found[key]=(node,archive[data_start+int(node['offset']):data_start+int(node['offset'])+node['size']])
 walk(head)
 return found
def pack(files):
 header={'files':{}};data=[];pos=0
 for name,(old_meta,blob) in files.items():
  parent=header
  parts=name.split('/')
  for item in parts[:-1]:parent=parent['files'].setdefault(item,{'files':{}})
  meta={'size':len(blob),'offset':str(pos)}
  if 'integrity' in old_meta:
   block=old_meta['integrity'].get('blockSize',4194304)
   meta['integrity']={'algorithm':'SHA256','hash':sha(blob),'blockSize':block,'blocks':[sha(blob[i:i+block]) for i in range(0,len(blob),block)]}
  parent['files'][parts[-1]]=meta
  data.append(blob);pos+=len(blob)
 content=json.dumps(header,ensure_ascii=False,separators=(',',':')).encode('utf-8')
 padded=(len(content)+3)&~3
 return struct.pack('<IIII',4,padded+8,padded+4,len(content))+content+b'\x00'*(padded-len(content))+b''.join(data)
def main():
 base=pathlib.Path('nano-pos-base-1.0.38.zip')
 if not base.exists():
  req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-1.0.39-release-builder'})
  with urllib.request.urlopen(req,timeout=180) as res:base.write_bytes(res.read())
 assert sha(base.read_bytes())==BASE_ZIP_SHA,'Base release ZIP checksum mismatch'
 with zipfile.ZipFile(base) as z:old=z.read('payload/app.asar')
 assert sha(old)==BASE_ASAR_SHA,'Base release app.asar checksum mismatch'
 chunks=sorted(ROOT.glob('delta-part-*.b64'))
 assert len(chunks)==6,'Expected 6 source fragments'
 compressed=base64.b64decode(''.join(p.read_text().strip() for p in chunks),validate=True)
 assert sha(compressed)==DELTA_SHA,'Changed-files delta checksum mismatch'
 with zipfile.ZipFile(__import__('io').BytesIO(compressed)) as z:
  assert z.testzip() is None
  manifest=json.loads(z.read('manifest.json'))
  assert manifest['version']=='1.0.39' and manifest['requires']=='1.0.38'
  changes={name:z.read('changed/'+name) for name in manifest['changes']}
 original=parse_files(old)
 assert set(changes)=={'renderer.js','package.json','app-config.js','release-notes.js'}
 for name,checks in manifest['changes'].items():
  assert name in original, 'Missing base file '+name
  assert sha(original[name][1])==checks['baseSha256'], 'Unexpected base '+name
  assert sha(changes[name])==checks['updatedSha256'], 'Unexpected updated file '+name
 for name in ('renderer.js','app-config.js','release-notes.js'):
  f=pathlib.Path('check-'+name);f.write_bytes(changes[name])
  subprocess.run(['node','--check',str(f)],check=True,timeout=30)
 assert json.loads(changes['package.json'])['version']=='1.0.39'
 renderer=changes['renderer.js'].decode('utf8');notes=changes['release-notes.js'].decode('utf8')
 for condition in ["await loadSuppliersTable(),await populateSupplierSelect()", "await loadCustomersGrid(),await loadCustomersSelect()", "await openProductModal(),document.getElementById('productName')?.focus()", "await refreshSuppliersCache();const _0x371d2f=suppliersAllCache"]:
  assert condition in renderer,'Missing stability invariant '+condition
 assert 'تحسينات استقرار النظام' in notes,'Missing localized release title'
 files={name:(meta,changes.get(name,blob)) for name,(meta,blob) in original.items()}
 result=pack(files)
 output=parse_files(result)
 for name,blob in changes.items():assert output[name][1]==blob
 assert 'node_modules/megajs/package.json' in output, 'Existing direct MEGA integration lost'
 with zipfile.ZipFile(ASSET,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',result)
 with zipfile.ZipFile(ASSET) as z: assert z.testzip() is None and z.namelist()==['payload/app.asar']
 info={'fileName':ASSET,'sizeBytes':pathlib.Path(ASSET).stat().st_size,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(result),'sourceVersion':'1.0.38','targetVersion':'1.0.39'}
 pathlib.Path('build-result.json').write_text(json.dumps(info,indent=2)+'\n')
 print(json.dumps(info,indent=2))
if __name__=='__main__':main()