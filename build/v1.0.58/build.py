#!/usr/bin/env python3
"""Build NANO POS v1.0.58 with the NANO POS Mobile APK bundled and offline download routes."""
import copy
import hashlib
import json
import pathlib
import struct
import subprocess
import urllib.request
import zipfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent.parent
ASSET = "NANO-POS-Patch-1.0.57-to-1.0.58-EMBEDDED-APK.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.57/NANO-POS-Patch-1.0.56-to-1.0.57-MOBILE-DOWNLOAD.zip"
BASE_SHA = "7178acac99c3901023a5d6c50f21b2c39ef7da58ac91e1706f6281e2c0862758"
BASE_ASAR_SHA = "727ced84eee4a881209340b998cdef55ee41f2e1d4eacf693270bd6390ff6df9"

def sha(data): return hashlib.sha256(data).hexdigest()

def unpack(raw):
    size = struct.unpack_from('<I', raw, 12)[0]
    header = json.loads(raw[16:16+size])
    offset = 8 + struct.unpack_from('<I', raw, 4)[0]
    files = {}
    def walk(node, prefix=''):
        for name, meta in node['files'].items():
            key = prefix + name
            if 'files' in meta:
                walk(meta, key + '/')
            else:
                start = offset + int(meta['offset'])
                n = int(meta['size'])
                buf = raw[start:start+n]
                assert len(buf) == n, ('Truncated ASAR entry', key)
                files[key] = (meta, buf)
    walk(header)
    return files

def pack(files):
    root = {'files':{}}
    parts=[]
    offset=0
    for name, (old, data) in files.items():
        sub = root
        sections = name.split('/')
        for sec in sections[:-1]:
            sub = sub['files'].setdefault(sec, {'files':{}})
        meta=copy.deepcopy(old)
        meta['offset']=str(offset)
        meta['size']=len(data)
        block=int(meta.get('integrity',{}).get('blockSize',4194304))
        meta['integrity']={'algorithm':'SHA256','hash':sha(data),'blockSize':block,
                           'blocks':[sha(data[i:i+block]) for i in range(0,len(data),block)]}
        sub['files'][sections[-1]]=meta
        parts.append(data)
        offset+=len(data)
    header=json.dumps(root, ensure_ascii=False, separators=(',',':')).encode('utf8')
    padded=(len(header)+3)&~3
    return struct.pack('<IIII',4,padded+8,padded+4,len(header))+header+b'\0'*(padded-len(header))+b''.join(parts)


APK_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/mobile-v1.3.7/NANO-POS-Mobile-v1.3.7.apk"
APK_SHA256 = "49503c07f39d941e308005df40b7de3243e1a379704b042ef1f7bd7e2bd6174c"
APK_ASAR_PATH = "downloads/NANO-POS-Mobile-v1.3.7.apk"

def main():
    source = ROOT/'published-v157.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL, headers={'User-Agent':'NANO-POS-v158-builder'}), timeout=180) as response:
            source.write_bytes(response.read())
    assert sha(source.read_bytes()) == BASE_SHA, "Unrecognized v1.0.57 release"
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        orig=z.read('payload/app.asar')
    assert sha(orig) == BASE_ASAR_SHA, "Unrecognized v1.0.57 app.asar"
    original=unpack(orig)
    files=dict(original)

    apkFile=ROOT/'NANO-POS-Mobile-v1.3.7.apk'
    if not apkFile.exists():
        with urllib.request.urlopen(urllib.request.Request(APK_URL, headers={'User-Agent':'NANO-POS-v158-builder'}),timeout=100) as response:
            apkFile.write_bytes(response.read())
    apk=apkFile.read_bytes()
    assert sha(apk)==APK_SHA256 and apk[:2]==b'PK', "Unrecognized or corrupted Android APK"
    with zipfile.ZipFile(apkFile) as z:
        assert z.testzip() is None
        assert 'AndroidManifest.xml' in z.namelist()
        assert 'classes.dex' in z.namelist()
    assert APK_ASAR_PATH not in files, 'APK already bundled, unexpected upstream'
    files[APK_ASAR_PATH]=({},apk)

    def get(name):
        assert name in original, 'Missing '+name
        return original[name][1].decode('utf8')
    def put(name, content):
        files[name]=(original.get(name,({},b''))[0],content.encode('utf8'))
    def replace_once(name, old, new):
        content=get(name)
        assert content.count(old)==1, ('Unexpected anchor',name,old,content.count(old))
        put(name,content.replace(old,new,1))

    helper=(ROOT/'nano-embedded-apk.cjs').read_text('utf8')
    ui=(ROOT/'nano-mobile-offline-ui.js').read_text('utf8')
    assert APK_SHA256 in helper and 'readVerifiedApk' in helper
    assert "RELEASE_MANIFEST" not in ui and "https://raw.githubusercontent.com" not in ui
    files['nano-embedded-apk.cjs']=({},helper.encode('utf8'))
    files['nano-mobile-offline-ui.js']=({},ui.encode('utf8'))

    # Electron's embedded 127.0.0.1 webserver and LAN mobile-sync server
    # serve the same static APK stored in app.asar.
    replace_once('electron-main.cjs',
      "const { createMobileSyncServer } = require('./mobile-sync-server.cjs');",
      "const { createMobileSyncServer } = require('./mobile-sync-server.cjs');\nconst { serve: serveEmbeddedApk, registerIpc: registerEmbeddedApkIpc } = require('./nano-embedded-apk.cjs');")
    content=files['electron-main.cjs'][1].decode('utf8')
    anchor="registerUpdaterIpc(ipcMain);"
    assert content.count(anchor)==1
    put('electron-main.cjs',content.replace(anchor, anchor+"\nregisterEmbeddedApkIpc({ ipcMain, dialog, app, getWindow: () => mainWindow });",1))
    content=files['electron-main.cjs'][1].decode('utf8')
    anchor="localServer = http.createServer((req, res) => {"
    assert content.count(anchor)==1
    put('electron-main.cjs',content.replace(anchor,anchor+"\n      if (serveEmbeddedApk(req, res)) return;",1))

    replace_once('electron-native-preload.cjs',
      "  appVersion: APP_VERSION,",
      "  appVersion: APP_VERSION,\n  getEmbeddedMobileApkStatus: () => ipcRenderer.invoke('nano-embedded-mobile-apk-status'),\n  saveEmbeddedMobileApk: () => ipcRenderer.invoke('nano-save-embedded-mobile-apk'),")

    replace_once('mobile-sync-server.cjs',
      "const { resolveCustomerRows } = require('./nano-customer-contract.cjs');",
      "const { resolveCustomerRows } = require('./nano-customer-contract.cjs');\nconst { serve: serveEmbeddedApk } = require('./nano-embedded-apk.cjs');")
    content=files['mobile-sync-server.cjs'][1].decode('utf8')
    anchor="  async function handler(req, res) {"
    assert content.count(anchor)==1
    put('mobile-sync-server.cjs',content.replace(anchor,anchor+"\n    if (serveEmbeddedApk(req, res)) return;",1))

    replace_once('server.cjs',
      "const { trialState } = require('./trial-state.cjs');",
      "const { trialState } = require('./trial-state.cjs');\nconst { serve: serveEmbeddedApk } = require('./nano-embedded-apk.cjs');")
    content=files['server.cjs'][1].decode('utf8')
    anchor="const server = http.createServer((req, res) => {"
    assert content.count(anchor)==1
    put('server.cjs',content.replace(anchor,anchor+"\n  if (serveEmbeddedApk(req, res)) return;",1))

    # Replace the old Internet-dependent panel script with bundled-only UI.
    replace_once('index.html',
      '<script defer src="nano-mobile-download.js"></script>',
      '<script defer src="nano-mobile-offline-ui.js"></script>')

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.57', 'Unexpected previous version'
    pkg['version']='1.0.58'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in files:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.57'
        lock['version']='1.0.58'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.58'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in files:
        config=get('app-config.js')
        newer=config.replace("|| '1.0.57'","|| '1.0.58'")
        assert newer!=config, 'App fallback version not found'
        put('app-config.js',newer)

    features={
      'ar':[
       'تضمين ملف NANO POS Mobile v1.3.7 بصيغة APK داخل تطبيق الكمبيوتر دون الحاجة إلى الإنترنت.',
       'زر لحفظ APK من برنامج الكمبيوتر مباشرة مع اختيار مجلد الحفظ.',
       'رابط تنزيل محلي للهاتف عبر الشبكة المحلية أو Tailscale من الكمبيوتر الرئيسي.',
       'التحقق من بصمة SHA-256 للتطبيق قبل تقديمه، مع الحفاظ على المبيعات والديون والمزامنة والبيانات والتفعيل.'
      ],
      'fr':[
       'APK NANO POS Mobile v1.3.7 intégré au programme PC, hors ligne.',
       'Bouton pour enregistrer directement l’APK depuis le logiciel Windows.',
       'Adresse locale de téléchargement depuis le PC sur le LAN ou via Tailscale.',
       'Vérification SHA-256, sans toucher aux ventes, dettes, synchronisation, données et activation.'
      ],
      'en':[
       'Bundle NANO POS Mobile v1.3.7 APK directly inside the Windows desktop app for offline use.',
       'Save the bundled APK to disk using the built-in Windows save dialog.',
       'LAN/Tailscale URL to download the Android APK directly from the PC.',
       'SHA-256 integrity verification; leave sales, debts, sync, stored data and activation unchanged.'
      ]
    }
    if 'release-notes.js' in files:
        notes=get('release-notes.js'); a=notes.find('const F=');b=notes.find(';',a)
        assert a>=0 and b>a, 'Unexpected release-notes template'
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[name for name in files if name not in original or files[name][1]!=original[name][1]]
    allowed={
      APK_ASAR_PATH,'nano-embedded-apk.cjs','nano-mobile-offline-ui.js',
      'electron-main.cjs','electron-native-preload.cjs','mobile-sync-server.cjs',
      'server.cjs','index.html','package.json','package-lock.json','app-config.js','release-notes.js'
    }
    assert set(changed).issubset(allowed),changed
    assert {'electron-main.cjs','electron-native-preload.cjs','mobile-sync-server.cjs','server.cjs',
            'nano-mobile-offline-ui.js','nano-embedded-apk.cjs',APK_ASAR_PATH,'index.html'}.issubset(set(changed))

    # Check all changed JavaScript in both their original and packaged forms.
    for n in ['electron-main.cjs','electron-native-preload.cjs','mobile-sync-server.cjs',
              'server.cjs','nano-embedded-apk.cjs','nano-mobile-offline-ui.js']:
        path=ROOT/('check-'+n)
        path.write_bytes(files[n][1])
        subprocess.run(['node','--check',str(path)],check=True,timeout=25)

    asar=pack(files)
    rebuilt=unpack(asar)
    assert set(rebuilt)==set(files)
    assert all(rebuilt[k][1]==v[1] for k,v in files.items())
    assert sha(rebuilt[APK_ASAR_PATH][1])==APK_SHA256
    assert b'RELEASE_MANIFEST' not in rebuilt['nano-mobile-offline-ui.js'][1]
    result_path=ROOT/ASSET
    with zipfile.ZipFile(result_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(result_path) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={
      'fileName':ASSET,'sha256':sha(result_path.read_bytes()),'appAsarSha256':sha(asar),
      'sizeBytes':result_path.stat().st_size,'fromVersion':'1.0.57','toVersion':'1.0.58',
      'apkVersion':'1.3.7','apkSha256':APK_SHA256,'apkBytes':len(apk),
      'changedFiles':changed,'dataFilesModified':False
    }
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.57' and manifest['published'] is True
    previous=manifest.get('patches',[])
    fromVersions=list(dict.fromkeys((previous[0].get('fromVersions',[]) if previous else [])+['1.0.57']))
    manifest['version']='1.0.58'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.58']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{
       'id':'nano-pos-v1.0.58-bundled-mobile-apk',
       'fromVersions':fromVersions,
       'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.58/'+ASSET,
       'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.58',
       'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
       'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'
    }]
    manifest['notes']={
       'ar':'إدراج تطبيق الهاتف APK داخل NANO POS للكمبيوتر مع تحميل محلي دون إنترنت وعبر شبكة الكمبيوتر.',
       'fr':'APK Android intégré au programme PC, accessible hors ligne et sur le réseau local.',
       'en':'Android APK embedded in the desktop application, with offline extraction and LAN download.'
    }
    (ROOT/'nano-pos-update-v158.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
