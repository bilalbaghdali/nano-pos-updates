#!/usr/bin/env python3
"""Build NANO POS desktop v1.0.57 from SHA-pinned v1.0.56; APK download link only."""
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
ASSET = "NANO-POS-Patch-1.0.56-to-1.0.57-MOBILE-DOWNLOAD.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.56/NANO-POS-Patch-1.0.55-to-1.0.56-DEBT-STATS-SYNC.zip"
BASE_SHA = "00eef6932622feb3d7821fb2e81f284d3f7c36608b61af627b625771d8100e80"
BASE_ASAR_SHA = "71e08afb9d579118af990f1c90a97ac35710c7c2416d768c8c816c13aad5b0a4"

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

def main():
    source=ROOT/'published-v156.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v157-builder'}),timeout=180) as response:
            source.write_bytes(response.read())
    assert sha(source.read_bytes()) == BASE_SHA, 'Unexpected v1.0.56 release archive'
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        assert 'payload/app.asar' in z.namelist()
        orig = z.read('payload/app.asar')
    assert sha(orig)==BASE_ASAR_SHA, 'Unexpected v1.0.56 ASAR'
    original=unpack(orig)
    files=dict(original)

    def get(name):
        assert name in original, 'Missing ASAR file: ' + name
        return original[name][1].decode('utf8')
    def put(name,text):
        files[name]=(original.get(name,({},b''))[0],text.encode('utf8'))

    index=get('index.html')
    assert index.count('id="settingsTab-mobileapp"')==1
    assert index.count('id="appDownloadSection"')==1
    assert 'nano-mobile-download.js' not in index
    assert index.count('</body>')==1, 'Unexpected HTML layout'
    index=index.replace('</body>','<script defer src="nano-mobile-download.js"></script>\n</body>',1)
    assert index.count('nano-mobile-download.js')==1
    put('index.html',index)

    helper=(ROOT/'nano-mobile-download.js').read_text('utf8')
    assert 'nano-pos-updates/main/mobile-latest.json' in helper
    assert 'nanoOfficialApkCard' in helper
    assert 'lumina.fikradevs.com' not in helper
    subprocess.run(['node','--check',str(ROOT/'nano-mobile-download.js')],check=True,timeout=25)
    put('nano-mobile-download.js', helper)

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.56', 'Unexpected previous app version'
    pkg['version']='1.0.57'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')

    if 'package-lock.json' in files:
        lock=json.loads(get('package-lock.json'))
        assert lock.get('version')=='1.0.56'
        lock['version']='1.0.57'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.57'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')

    if 'app-config.js' in files:
        appconfig=get('app-config.js')
        newer=appconfig.replace("|| '1.0.56'","|| '1.0.57'")
        assert newer!=appconfig, 'Missing version fallback'
        put('app-config.js',newer)

    features={
        'ar':[
            'إضافة تنبيه بجوار رابط تطبيق الهاتف في الإعدادات، مع رقم أحدث إصدار APK منشور.',
            'ربط أيقونة التحميل مباشرة بآخر نسخة رسمية منشورة من NANO POS Mobile على GitHub.',
            'إضافة نسخ رابط التحميل وتحديث حالة الإصدار، مع رسالة عند تعذر الوصول للملف.',
            'الإبقاء على وظائف البيع، الديون، المزامنة، البيانات والتفعيل دون تعديل.'
        ],
        'fr':[
            'Notification et numéro de version de la dernière application Android dans les paramètres.',
            'Téléchargement de l’APK NANO POS Mobile publié sur GitHub depuis le bouton dédié.',
            'Copie du lien et actualisation du statut, avec message si le fichier est indisponible.',
            'Aucune modification des ventes, dettes, synchronisation, données ou activation.'
        ],
        'en':[
            'Show an Android download notice and the latest published APK version.',
            'Connect the download icon to the newest verified NANO POS Mobile GitHub release.',
            'Copyable download link and refreshable availability status.',
            'Preserve sales, debts, synchronization, stored data, and licensing.'
        ]
    }
    if 'release-notes.js' in files:
        notes=get('release-notes.js')
        a=notes.find('const F=')
        b=notes.find(';',a)
        assert a>=0 and b>a, 'Unexpected release-notes template'
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[name for name in files if name not in original or files[name][1]!=original[name][1]]
    allowed={'index.html','nano-mobile-download.js','package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allowed),changed
    assert {'index.html','nano-mobile-download.js','package.json'}.issubset(set(changed))
    asar=pack(files)
    check=unpack(asar)
    assert set(check)==set(files)
    assert all(check[k][1]==v[1] for k,v in files.items()),'ASAR data integrity failed'
    assert check['index.html'][1].decode('utf8').count('nano-mobile-download.js')==1

    output=ROOT/ASSET
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={
        'fileName':ASSET, 'sha256':sha(output.read_bytes()), 'appAsarSha256':sha(asar),
        'sizeBytes':output.stat().st_size, 'fromVersion':'1.0.56', 'toVersion':'1.0.57',
        'changedFiles':changed, 'sourceVersionSha256':BASE_SHA, 'dataFilesModified':False,
        'apkVersion':'1.3.7'
    }
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

    manifestPath=REPO/'nano-pos-update.json'
    manifest=json.loads(manifestPath.read_text('utf8'))
    assert manifest['version']=='1.0.56'
    assert manifest['published'] is True
    prev=manifest.get('patches',[])
    fromVersions=prev[0].get('fromVersions',[]) if prev else []
    fromVersions=list(dict.fromkeys(fromVersions+['1.0.56']))
    manifest['version']='1.0.57'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.57']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{
        'id':'nano-pos-v1.0.57-mobile-download',
        'fromVersions':fromVersions,
        'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.57/'+ASSET,
        'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.57',
        'sha256':meta['sha256'], 'appAsarSha256':meta['appAsarSha256'],
        'fileName':ASSET, 'sizeBytes':meta['sizeBytes'], 'payloadType':'app-asar'
    }]
    manifest['notes']={
        'ar':'تحديث رابط تنزيل تطبيق NANO POS Mobile والإشعار بآخر نسخة منشورة؛ بدون تغيير بيانات المتجر أو الفواتير.',
        'fr':'Mise à jour du téléchargement mobile et de la notification; sans modification des données du magasin.',
        'en':'Mobile APK download link and release notification update; no store-data changes.'
    }
    (ROOT/'nano-pos-update-v157.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
