#!/usr/bin/env python3
"""Create the exact optional NANO POS 1.0.41 restore patch from public v1.0.40."""
import base64, hashlib, json, pathlib, struct, subprocess, zipfile, urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.40/NANO-POS-Patch-1.0.39-to-1.0.40-IMPROVEMENTS.zip'
BASE_ZIP_SHA='b9a7cd8318a5e94a2ed46ff07fb965dc798972ede15336c0cd4241f4dd6dd363'
BASE_ASAR_SHA='a1059a3d516296febe84e3695bab35017b48a3bbe7c67306e9dc4358fcd158fb'
ASSET='NANO-POS-Patch-1.0.40-to-1.0.41-MEGA-RESTORE.zip'
DELTA_SHA='4da0e6810172aece976a4d89a47c93d27c45ff729fc5082a970b46abafebd390'
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(asar):
  length=struct.unpack('<I',asar[12:16])[0]
  header=json.loads(asar[16:16+length])
  data_start=8+struct.unpack('<I',asar[4:8])[0]
  files={}
  def walk(node,prefix=''):
    for name,meta in node['files'].items():
      key=prefix+name
      if 'files' in meta:walk(meta,key+'/')
      else:
        offset=data_start+int(meta['offset'])
        files[key]=(meta,asar[offset:offset+meta['size']])
  walk(header)
  return files
def pack(files):
  header={'files':{}};data=[];offset=0
  for name,(previous,contents) in files.items():
    node=header;parts=name.split('/')
    for part in parts[:-1]:node=node['files'].setdefault(part,{'files':{}})
    meta={'size':len(contents),'offset':str(offset)}
    if 'integrity' in previous:
      block=previous['integrity'].get('blockSize',4194304)
      meta['integrity']={'algorithm':'SHA256','hash':sha(contents),'blockSize':block,
        'blocks':[sha(contents[i:i+block]) for i in range(0,len(contents),block)]}
    node['files'][parts[-1]]=meta
    data.append(contents);offset+=len(contents)
  raw=json.dumps(header,ensure_ascii=False,separators=(',',':')).encode()
  padded=(len(raw)+3)&~3
  return struct.pack('<IIII',4,padded+8,padded+4,len(raw))+raw+b'\0'*(padded-len(raw))+b''.join(data)
def main():
  base=pathlib.Path('nano-pos-1.0.40-base.zip')
  if not base.exists():
    req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-1.0.41-release-builder'})
    with urllib.request.urlopen(req,timeout=180) as res:base.write_bytes(res.read())
  assert sha(base.read_bytes())==BASE_ZIP_SHA,'Base ZIP checksum mismatch'
  with zipfile.ZipFile(base) as z:old=z.read('payload/app.asar')
  assert sha(old)==BASE_ASAR_SHA,'Base app.asar checksum mismatch'
  parts=sorted(ROOT.glob('delta-part-*.b64'))
  assert len(parts)==1,'Incorrect delta chunk count'
  delta=base64.b64decode(''.join(p.read_text().strip() for p in parts),validate=True)
  assert sha(delta)==DELTA_SHA,'Source delta checksum mismatch'
  import io
  with zipfile.ZipFile(io.BytesIO(delta)) as z:
    assert z.testzip() is None
    manifest=json.loads(z.read('manifest.json'))
    assert manifest['version']=='1.0.41' and manifest['requires']=='1.0.40'
    changes={n:z.read('changed/'+n) for n in manifest['changes']}
  files=parse(old)
  assert 'node_modules/megajs/package.json' in files,'MEGA SDK missing from existing app'
  assert set(changes)=={'electron-main.cjs','electron-native-preload.cjs','mega-backup-ui.js','mega-restore-safety.cjs','package.json','app-config.js','release-notes.js'}
  for name,hashes in manifest['changes'].items():
    assert sha(changes[name])==hashes['updatedSha256'],'Changed file checksum mismatch '+name
    if 'baseSha256' in hashes:
      assert name in files, 'Base file missing '+name
      assert sha(files[name][1])==hashes['baseSha256'],'Unexpected base '+name
    else:assert name not in files,'New module already exists: '+name
  assert json.loads(changes['package.json'])['version']=='1.0.41'
  for name in ['electron-main.cjs','electron-native-preload.cjs','mega-backup-ui.js','mega-restore-safety.cjs','app-config.js','release-notes.js']:
    target=ROOT/('check-'+name);target.write_bytes(changes[name])
    subprocess.run(['node','--check',str(target)],check=True,timeout=20)
  tmp=ROOT/'current';tmp.mkdir(exist_ok=True)
  (tmp/'backup-safety.cjs').write_bytes(files['backup-safety.cjs'][1])
  (tmp/'mega-restore-safety.cjs').write_bytes(changes['mega-restore-safety.cjs'])
  subprocess.run(['node','--test',str(ROOT/'tests/test-mega-restore.cjs')],check=True,timeout=30)
  for name,b in changes.items():files[name]=(files[name][0] if name in files else {},b)
  result=pack(files)
  check=parse(result)
  for name,b in changes.items():assert check[name][1]==b, 'ASAR content mismatch: '+name
  with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',result)
  with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
  info={'fileName':ASSET,'version':'1.0.41','fromVersion':'1.0.40','sha256':sha(pathlib.Path(ASSET).read_bytes()),
    'appAsarSha256':sha(result),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'restoreTests':4}
  pathlib.Path('build-result.json').write_text(json.dumps(info,indent=2)+'\n')
  print(json.dumps(info,indent=2))
if __name__=='__main__':main()