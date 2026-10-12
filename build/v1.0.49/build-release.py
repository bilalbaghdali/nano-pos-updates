#!/usr/bin/env python3
"""Produce v1.0.49 product barcode currency deduplication patch from published v1.0.48."""
import hashlib,json,pathlib,re,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.48/NANO-POS-Patch-1.0.47-to-1.0.48-SHOP-LOGO-CURRENCY.zip'
BASE_ZIP_SHA='d358d001ce68e7b959e7bb5069820fdede337962e95223962b866c28845cb4cd'
BASE_ASAR_SHA='0bee160c82abda3dd27e3a1610638179acc9804f60d92743f7ecb636aaaec4e1'
ASSET='NANO-POS-Patch-1.0.48-to-1.0.49-BARCODE-CURRENCY-FIX.zip'
def sha(b):return hashlib.sha256(b).hexdigest()
def unpack(a):
 n=struct.unpack_from('<I',a,12)[0]; header=json.loads(a[16:16+n]); base=8+struct.unpack_from('<I',a,4)[0]; result={}
 def visit(node,prefix=''):
  for name,meta in node.get('files',{}).items():
   key=prefix+name
   if 'files' in meta:visit(meta,key+'/')
   else:
    pos=base+int(meta['offset']);buf=a[pos:pos+meta['size']]
    assert len(buf)==meta['size'],'Truncated ASAR file '+key
    result[key]=(meta,buf)
 visit(header);return result
def repack(files):
 head={'files':{}};chunks=[];offset=0
 for name,(old,data) in files.items():
  node=head;parts=name.split('/')
  for part in parts[:-1]:node=node['files'].setdefault(part,{'files':{}})
  meta={'size':len(data),'offset':str(offset)}
  if 'integrity' in old:
   bs=old['integrity'].get('blockSize',4194304)
   meta['integrity']={'algorithm':'SHA256','hash':sha(data),'blockSize':bs,'blocks':[sha(data[i:i+bs]) for i in range(0,len(data),bs)]}
  node['files'][parts[-1]]=meta;chunks.append(data);offset+=len(data)
 raw=json.dumps(head,ensure_ascii=False,separators=(',',':')).encode();length=(len(raw)+3)&~3
 return struct.pack('<IIII',4,length+8,length+4,len(raw))+raw+b'\0'*(length-len(raw))+b''.join(chunks)
def main():
 base=pathlib.Path('base-v148.zip')
 if not base.exists():
  with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v1.0.49-build'}),timeout=180) as response:base.write_bytes(response.read())
 assert sha(base.read_bytes())==BASE_ZIP_SHA,'Unexpected published base ZIP'
 with zipfile.ZipFile(base) as z:
  assert z.testzip() is None
  old=z.read('payload/app.asar')
 assert sha(old)==BASE_ASAR_SHA,'Unexpected published base app.asar'
 files=unpack(old);original={key:blob for key,(_,blob) in files.items()}
 needed={'renderer.js','barcode_label_template_1.html','index.html','package.json','app-config.js','release-notes.js','electron-main.cjs','mega-cloud-backup.cjs'}
 assert needed<=set(files), 'Expected files missing: '+str(needed-set(files))
 code=original['renderer.js'].decode('utf8')
 begin=code.index('function plLabelFields(')
 end=code.index('}function ',begin)+1
 body=code[begin:end]
 old_expr="'priceText':(t('dzd')||'DA')+'\\x20'+Number(_0x543bd4['price']||0x0)[_0x142734(0x68b)](0x2),"
 new_expr="'priceText':Number(_0x543bd4['price']||0x0)[_0x142734(0x68b)](0x2),"
 assert body.count(old_expr)==1,'Unexpected price-generating function; refuse unsafe patch'
 assert code.count(old_expr)==1,'Another site unexpectedly formats label price'
 assert original['barcode_label_template_1.html'].count(b'{{PRICE_TEXT}}')==1
 assert original['barcode_label_template_1.html'].count(b'{{CURRENCY_TEXT}}')==1
 corrected=code.replace(old_expr,new_expr,1)
 pkg=json.loads(original['package.json']);assert pkg['version']=='1.0.48','Wrong predecessor version'
 pkg['version']='1.0.49'
 config=original['app-config.js'].decode('utf8');assert "'1.0.48'" in config
 config=config.replace("'1.0.48'","'1.0.49'")
 notes=original['release-notes.js'].decode('utf8')
 features={
  'ar':['إصلاح تكرار رمز العملة في معاينة ملصقات الباركود، وطباعة الملصقات، وتصديرها إلى PDF.'],
  'fr':['Correction du symbole monétaire affiché deux fois dans les aperçus, impressions et PDF des étiquettes à code-barres.'],
  'en':['Fix the duplicated currency symbol in barcode label preview, printing, and PDF export.']}
 replacement='const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+';let R='
 notes,count=re.subn(r'const F=\{.*?\};let R=',lambda _:replacement,notes,count=1,flags=re.S)
 assert count==1,'Unexpected release-notes shape'
 changes={
  'renderer.js':corrected.encode('utf8'),
  'package.json':(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode('utf8'),
  'app-config.js':config.encode('utf8'),
  'release-notes.js':notes.encode('utf8')
 }
 for key,buf in changes.items():files[key]=(files[key][0],buf)
 (ROOT/'checked-renderer.js').write_bytes(changes['renderer.js'])
 (ROOT/'checked-label-template.html').write_bytes(original['barcode_label_template_1.html'])
 for key in ['renderer.js','app-config.js','release-notes.js']:
  tmp=ROOT/('syntax-'+key);tmp.write_bytes(changes[key]);subprocess.run(['node','--check',str(tmp)],check=True,timeout=30)
 subprocess.run(['node','--test',str(ROOT/'test-price-label.cjs')],check=True,timeout=30)
 built=repack(files);actual=unpack(built)
 for key,buf in changes.items():assert actual[key][1]==buf, 'Patched file changed during packaging '+key
 for key in ['barcode_label_template_1.html','electron-main.cjs','mega-cloud-backup.cjs','browser-ui.js','license-access.js','index.html']:
  if key in original:assert actual[key][1]==original[key],'Protected source changed: '+key
 with zipfile.ZipFile(ASSET,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',built)
 with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
 info={'fileName':ASSET,'version':'1.0.49','fromVersion':'1.0.48','sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(built),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'modified':list(changes.keys()),'tests':3}
 pathlib.Path('build-result.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(info,ensure_ascii=False,indent=2))
if __name__=='__main__':main()