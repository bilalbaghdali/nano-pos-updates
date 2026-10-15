#!/usr/bin/env python3
"""Build v1.0.63: read-only unified operations and alert center."""
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
ASSET = "NANO-POS-Patch-1.0.62-to-1.0.63-OPERATIONS-ALERTS.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.62/NANO-POS-Patch-1.0.61-to-1.0.62-RESTOCK-BARCODE.zip"
BASE_SHA = "65257db69c30c20f6bc2b6bad0b958e67ff7a47f7b3b371de456b339c5fc7c94"
BASE_ASAR_SHA = "01fc230ec74b948aa7b95fc7fdc20648d3626cfd4be3fd2ee01b7b5ad050d01c"

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




import re

BUNDLED_APK = 'downloads/NANO-POS-Mobile-v1.3.7.apk'
BUNDLED_APK_SHA = '49503c07f39d941e308005df40b7de3243e1a379704b042ef1f7bd7e2bd6174c'

# Exact logo element in the sidebar beside the brand/store heading.
SIDEBAR_LOGO = re.compile(
    r'<div\s+class="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center '
    r'text-white shrink-0 shadow-lg shadow-blue-200 dark:shadow-none">\s*'
    r'<span class="material-symbols-outlined"\s*'
    r'style="font-variation-settings: \x27FILL\x27 1;">deployed_code</span>\s*</div>'
)

def main():
    source=ROOT/'published-v162.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v163-builder'}),timeout=180) as r:
            source.write_bytes(r.read())
    assert sha(source.read_bytes())==BASE_SHA,'v1.0.62 patch SHA-256 mismatch'
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR_SHA,'v1.0.62 app.asar SHA-256 mismatch'
    original=unpack(raw)
    files=dict(original)
    def get(name):
        assert name in original,'Missing app file: '+name
        return original[name][1].decode('utf8')
    def put(name,value):
        files[name]=(original[name][0],value.encode('utf8'))

    addon=(ROOT/'nano-operations-center.js').read_bytes()
    assert b'getProducts' in addon and b'getNotifications' in addon
    assert b"module.exports=API" in addon
    files['nano-operations-center.js']=({},addon)
    files['mobile/www/nano-operations-center.js']=({},addon)
    for path in ('index.html','mobile/www/index.html'):
        body=get(path)
        assert body.count('</body>')==1 and body.count('id="notificationToggle"')==1
        assert 'nano-restock-assistant.js' in body
        assert 'nano-operations-center.js' not in body
        put(path,body.replace('</body>','  <script defer src="nano-operations-center.js"></script>\n</body>',1))

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.62'
    pkg['version']='1.0.63'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.62'
        lock['version']='1.0.63'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.63'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        config=get('app-config.js')
        updated=config.replace("|| '1.0.62'","|| '1.0.63'")
        assert updated!=config
        put('app-config.js',updated)
    features={
      'ar':[
        'إضافة مركز موحد للعمليات والتنبيهات، يعرض تنبيهات المخزون والصلاحية من بيانات المنتجات الأصلية.',
        'إضافة وصول سريع للأقسام الموجودة: الصندوق والمناوبات، الفواتير والمرتجعات، الجرد، العروض، البيع بالجملة والتقارير.',
        'إظهار التنبيهات المتاحة من واجهة البرنامج دون إنشاء سجل بديل للمعاملات أو إجراء أي تعديلات مالية.',
        'الحفاظ على المزامنة وقاعدة البيانات ونظام التفعيل. إصلاحات المرتجعات ومحاسبة صافي الربح وسجل التدقيق المؤكد لم تكتمل بعد.'
      ],
      'fr':[
        'Centre centralisé en lecture seule pour les alertes de stock et péremption.',
        'Accès rapide aux modules existants de caisse, retours, inventaire, promotions et rapports.',
        'Lecture des alertes existantes sans écritures comptables.',
        'Données et licences inchangées; contrôles financiers approfondis restant à vérifier.'
      ],
      'en':[
        'Add a read-only operations and unified inventory/expiration alert center.',
        'Quick access to existing shifts, returns, stocktake, promotions, wholesale and report sections.',
        'Display existing application notifications without creating new financial transactions.',
        'Preserve data, activation and sync; full financial reconciliation and audit logs remain separate work.'
      ]
    }
    if 'release-notes.js' in original:
        notes=get('release-notes.js')
        a=notes.find('const F=');b=notes.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allow={'nano-operations-center.js','mobile/www/nano-operations-center.js',
           'index.html','mobile/www/index.html','package.json',
           'package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allow),changed
    assert {'nano-operations-center.js','mobile/www/nano-operations-center.js',
            'index.html','mobile/www/index.html','package.json'}.issubset(set(changed))
    protected=[
        'electron-main.cjs','electron-native-preload.cjs','renderer.js','mobile/www/renderer.js',
        'mobile-sync-server.cjs','pc-sync-service.cjs','mega-cloud-backup.cjs','mega-restore-safety.cjs',
        'nano-debt-stats-fix.js','print-engine.js','document-print-preview.js',
        'nano-restock-assistant.js','mobile/www/nano-restock-assistant.js',
        'nano-v136-shortcuts.js'
    ]
    for name in protected:
        assert files[name][1]==original[name][1],('Protected system mutated',name)
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA
    subprocess.run(['node','--check',str(ROOT/'nano-operations-center.js')],check=True,timeout=30)
    subprocess.run(['node',str(ROOT/'test-operations.cjs')],check=True,timeout=30,cwd=ROOT)
    subprocess.run(['node',str(ROOT.parent/'v1.0.62/test-restock.cjs')],check=True,timeout=30)
    asar=pack(files)
    verified=unpack(asar)
    assert set(verified)==set(files)
    assert all(verified[n][1]==data for n,(meta,data) in files.items())
    assert sha(verified[BUNDLED_APK][1])==BUNDLED_APK_SHA
    for html in ['index.html','mobile/www/index.html']:
        assert b'<script defer src="nano-operations-center.js"></script>' in verified[html][1]
    output=ROOT/ASSET
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={'fileName':ASSET,'sha256':sha(output.read_bytes()),
          'appAsarSha256':sha(asar),'sizeBytes':output.stat().st_size,
          'fromVersion':'1.0.62','toVersion':'1.0.63',
          'changedFiles':changed,'dataFilesModified':False,'mobileApkSha256':BUNDLED_APK_SHA}
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.62' and manifest.get('published') is True
    old=manifest.get('patches',[])
    from_versions=list(dict.fromkeys((old[0].get('fromVersions',[]) if old else [])+['1.0.62']))
    manifest['version']='1.0.63'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.63']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{'id':'nano-pos-v1.0.63-operations-alerts',
       'fromVersions':from_versions,
       'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.63/'+ASSET,
       'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.63',
       'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
       'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'}]
    manifest['notes']={'ar':'مركز تنبيهات للمخزون والصلاحية وروابط للأقسام التشغيلية الحالية دون تعديل البيانات.',
                       'fr':'Centre des alertes et raccourcis opérationnels en lecture seule.',
                       'en':'Read-only operations shortcuts and unified stock and expiry alerts.'}
    (ROOT/'nano-pos-update-v163.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
