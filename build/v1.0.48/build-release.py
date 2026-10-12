#!/usr/bin/env python3
"""Build optional NANO POS 1.0.48 shop caption logo + unified currency display from v1.0.47."""
import hashlib,json,pathlib,re,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.47/NANO-POS-Patch-1.0.46-to-1.0.47-TITLE-LOGO.zip'
BASE_ZIP_SHA='0c7cb9bbe6421a814c786768191fbaeebfadfda4f07e0d5a2795a7257cfd3b0c'
BASE_ASAR_SHA='73ef5b9f664973f49ac721c4dd28780504d124fe39225ca485f58a1595bd9c22'
ASSET='NANO-POS-Patch-1.0.47-to-1.0.48-SHOP-LOGO-CURRENCY.zip'
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(raw):
 length=struct.unpack_from('<I',raw,12)[0]
 header=json.loads(raw[16:16+length]);start=8+struct.unpack_from('<I',raw,4)[0];out={}
 def walk(node,p=''):
  for name,meta in node.get('files',{}).items():
   n=p+name
   if 'files' in meta:walk(meta,n+'/')
   else:
    off=start+int(meta['offset']);data=raw[off:off+meta['size']]
    assert len(data)==meta['size'], 'Invalid source ASAR: '+n
    out[n]=(meta,data)
 walk(header);return out
def pack(files):
 header={'files':{}};data=[];offset=0
 for filename,(old,blob) in files.items():
  node=header;parts=filename.split('/')
  for part in parts[:-1]:node=node['files'].setdefault(part,{'files':{}})
  meta={'size':len(blob),'offset':str(offset)}
  if 'integrity' in old:
   size=old['integrity'].get('blockSize',4194304)
   meta['integrity']={'algorithm':'SHA256','hash':sha(blob),'blockSize':size,'blocks':[sha(blob[i:i+size]) for i in range(0,len(blob),size)]}
  node['files'][parts[-1]]=meta;data.append(blob);offset+=len(blob)
 raw=json.dumps(header,ensure_ascii=False,separators=(',',':')).encode();padded=(len(raw)+3)&~3
 return struct.pack('<IIII',4,padded+8,padded+4,len(raw))+raw+b'\0'*(padded-len(raw))+b''.join(data)
def main():
 base=pathlib.Path('base-v147.zip')
 if not base.exists():
  with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-1.0.48-builder'}),timeout=180) as resp:base.write_bytes(resp.read())
 assert sha(base.read_bytes())==BASE_ZIP_SHA,'Unexpected base ZIP'
 with zipfile.ZipFile(base) as z:
  assert z.testzip() is None
  old_asar=z.read('payload/app.asar')
 assert sha(old_asar)==BASE_ASAR_SHA,'Unexpected base app.asar'
 files=parse(old_asar);original={k:v for k,(_,v) in files.items()}
 needed={'electron-main.cjs','electron-native-preload.cjs','index.html','renderer.js','browser-ui.js','app-config.js','package.json','release-notes.js','assets/branding/nano-pos-titlebar-blank.png'}
 assert needed<=set(files),'Some required files missing '+str(needed-set(files))
 main=original['electron-main.cjs'].decode()
 assert "require('electron')" in main, 'Electron import missing'
 key="const { registerUpdaterIpc } = require('./updater-main.cjs');"
 assert main.count(key)==1
 main=main.replace(key,key+"\nconst { initShopLogo } = require('./shop-logo-window.cjs');\nconst nanoShopNativeImage = require('electron').nativeImage;",1)
 key='registerUpdaterIpc(ipcMain);'
 assert main.count(key)==1
 main=main.replace(key,key+"\nconst shopLogoService = initShopLogo({ ipcMain, app, nativeImage: nanoShopNativeImage, getWindow: () => mainWindow, blankIconPath: path.join(root, 'assets', 'branding', 'nano-pos-titlebar-blank.png') });",1)
 key='  mainWindow = win;'
 assert main.count(key)==1
 main=main.replace(key,key+'\n  shopLogoService.restore();',1)
 preload=original['electron-native-preload.cjs'].decode()
 key='  appVersion: APP_VERSION,'
 assert preload.count(key)==1
 preload=preload.replace(key,key+"\n  setShopCaptionLogo: payload => ipcRenderer.invoke('nano-shop-caption-logo', payload),",1)
 html=original['index.html'].decode()
 assert '<head>' in html and html.count('</body>')==1
 html=html.replace('<head>','<head>\n<script src="nano-currency-format.js"></script>',1)
 html=html.replace('</body>','<script src="nano-v148-shop-logo.js"></script>\n</body>',1)
 assert html.count('nano-currency-format.js')==1 and html.count('nano-v148-shop-logo.js')==1
 pkg=json.loads(original['package.json']);assert pkg['version']=='1.0.47','Wrong source version'
 pkg['version']='1.0.48'
 config=original['app-config.js'].decode();assert "'1.0.47'" in config
 config=config.replace("'1.0.47'","'1.0.48'")
 notes=original['release-notes.js'].decode()
 features={'ar':['إظهار شعار المتجر الذي تختاره من الإعدادات بجانب اسم المتجر، وإخفاؤه عند إزالة الشعار.','تحسين فواصل الأرقام ورمز العملة في الملصقات وعمليات الطباعة التي تستخدم تنسيق الأسعار المشترك.'],
 'fr':['Afficher le logo du magasin choisi dans les paramètres à côté de son nom, ou le masquer s’il est supprimé.','Améliorer les séparateurs et le symbole monétaire dans les étiquettes et les impressions utilisant le formatage commun.'],
 'en':['Use the saved shop logo beside the shop name, or leave the space blank when no logo is configured.','Improve currency symbols and numeric grouping in labels and prints that use shared money formatting.']}
 notes,n=re.subn(r'const F=\{.*?\};let R=',lambda _: 'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+';let R=',notes,count=1,flags=re.S)
 assert n==1,'Unexpected release notes'
 changes={'electron-main.cjs':main.encode(),'electron-native-preload.cjs':preload.encode(),
          'index.html':html.encode(),'package.json':(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(),
          'app-config.js':config.encode(),'release-notes.js':notes.encode()}
 for name in ('shop-logo-window.cjs','nano-v148-shop-logo.js','nano-currency-format.js'):
  assert name not in original,'Unexpected existing module '+name
  changes[name]=(ROOT/name).read_bytes()
 for name in changes:
  if name in files:files[name]=(files[name][0],changes[name])
  else:files[name]=({},changes[name])
 for name in ['electron-main.cjs','electron-native-preload.cjs','app-config.js','release-notes.js','shop-logo-window.cjs','nano-v148-shop-logo.js','nano-currency-format.js']:
  p=ROOT/('check-'+name);p.write_bytes(changes[name]);subprocess.run(['node','--check',str(p)],check=True,timeout=25)
 subprocess.run(['node','--test',str(ROOT/'test-currency-logo.cjs')],check=True,timeout=25)
 built=pack(files);again=parse(built)
 for key,v in changes.items():assert again[key][1]==v,'Modified file mismatch '+key
 for key in ('renderer.js','browser-ui.js','license-access.js','mega-cloud-backup.cjs','assets/branding/nano-pos-icon.ico','assets/branding/nano-pos-icon.png'):
  if key in original:assert again[key][1]==original[key],'Protected file unexpectedly changed '+key
 assert 'node_modules/megajs/package.json' in again,'MEGA integration disappeared'
 with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',built)
 with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
 result={'version':'1.0.48','fromVersion':'1.0.47','fileName':ASSET,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(built),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'tests':5,'changedFiles':sorted(changes)}
 pathlib.Path('build-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()