#!/usr/bin/env python3
"""Build v1.0.62: read-only restock and expiry assistant + repair POS F2 barcode focus."""
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
ASSET = "NANO-POS-Patch-1.0.61-to-1.0.62-RESTOCK-BARCODE.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.61/NANO-POS-Patch-1.0.60-to-1.0.61-UI-PAYMENT-GUARDS.zip"
BASE_SHA = "4682c80470c7a8412e23d875167ddf4a1a7b30b53c94c7bd4e38ff4552976b9e"
BASE_ASAR_SHA = "ba12baef2a1678f681e5796ac5fc4a3ed38d52634a54a854a1ac98c7beace9b5"

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
    source=ROOT/'published-v161.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v162-builder'}),timeout=180) as r:
            source.write_bytes(r.read())
    assert sha(source.read_bytes())==BASE_SHA,'v1.0.61 archive checksum mismatch'
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR_SHA,'v1.0.61 app.asar integrity mismatch'
    original=unpack(raw)
    files=dict(original)
    def get(name):
        assert name in original,'Missing application entry: '+name
        return original[name][1].decode('utf8')
    def put(name,content):
        files[name]=(original[name][0],content.encode('utf8'))

    # Read-only inventory assistant. The application must already authenticate
    # product read requests using its current window.api.getProducts bridge.
    addon=(ROOT/'nano-restock-assistant.js').read_bytes()
    files['nano-restock-assistant.js']=({},addon)
    files['mobile/www/nano-restock-assistant.js']=({},addon)
    assert b'root.api.getProducts' in addon
    assert b"module.exports=API" in addon
    for html in ['index.html','mobile/www/index.html']:
        body=get(html)
        assert body.count('</body>')==1
        assert 'id="productsSection"' in body
        assert 'nano-restock-assistant.js' not in body
        body=body.replace('</body>', '  <script defer src="nano-restock-assistant.js"></script>\n</body>',1)
        put(html,body)

    # Fix the old F2 shortcut search selector: current POS search input is
    # #posProductSearchInput, not the selectors from older POS versions.
    oldSelector='#posSearchInput,#posProductSearch,#posSearchWrapper input[type="text"],#salesSection input[type="search"]'
    newSelector='#posProductSearchInput,'+oldSelector
    shortcuts=get('nano-v136-shortcuts.js')
    assert shortcuts.count(oldSelector)==1,'Cannot locate old F2 search selector'
    shortcuts=shortcuts.replace(oldSelector,newSelector,1)
    assert shortcuts.count('window.navigate')>=1
    put('nano-v136-shortcuts.js',shortcuts)

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.61'
    pkg['version']='1.0.62'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.61'
        lock['version']='1.0.62'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.62'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        config=get('app-config.js')
        updated=config.replace("|| '1.0.61'","|| '1.0.62'")
        assert updated!=config,'Version config anchor missing'
        put('app-config.js',updated)

    features={
      'ar':[
        'إصلاح اختصار F2 ليركز على حقل البحث بالاسم والباركود الفعلي في شاشة البيع.',
        'إضافة مساعد إعادة الطلب في قسم المنتجات باستخدام حد المخزون الأدنى والكمية المتوفرة.',
        'عرض تنبيهات انتهاء الصلاحية حسب تواريخ دفعات المنتجات المسجلة، دون اختلاق تواريخ للمنتجات غير المسجلة.',
        'الحسابات للقراءة فقط: لا تُنشأ أوامر شراء تلقائية ولا تتغير البيانات أو التفعيل أو المزامنة.'
      ],
      'fr':[
        'Correction de F2 pour activer la recherche de produits et codes-barres du point de vente.',
        'Assistant de réapprovisionnement basé sur les stocks et les seuils existants.',
        'Alertes de péremption selon les dates de lots enregistrés.',
        'Calculs en lecture seule; aucune écriture dans les stocks, données ou licences.'
      ],
      'en':[
        'Fix F2 shortcut to focus the current POS product/barcode search field.',
        'Add a read-only reorder suggestion tool using existing inventory thresholds.',
        'Show recorded batch expiry warnings without inferring missing expiration dates.',
        'No automatic purchases, stock edits, activation changes, or synchronization changes.'
      ]
    }
    if 'release-notes.js' in original:
        notes=get('release-notes.js')
        a=notes.find('const F=');b=notes.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allowed={'nano-restock-assistant.js','mobile/www/nano-restock-assistant.js',
             'nano-v136-shortcuts.js','index.html','mobile/www/index.html',
             'package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allowed),changed
    assert {'nano-restock-assistant.js','mobile/www/nano-restock-assistant.js',
            'nano-v136-shortcuts.js','index.html','mobile/www/index.html','package.json'}.issubset(set(changed))
    for protected in ('electron-main.cjs','electron-native-preload.cjs','renderer.js','mobile/www/renderer.js',
                      'mobile-sync-server.cjs','pc-sync-service.cjs','mega-cloud-backup.cjs','mega-restore-safety.cjs',
                      'nano-debt-stats-fix.js','print-engine.js','document-print-preview.js'):
        assert original[protected][1]==files[protected][1],('Protected subsystem modified',protected)
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA,'Mobile APK unexpectedly changed'
    for name in ['nano-restock-assistant.js','nano-v136-shortcuts.js']:
        path=ROOT/('check-'+name)
        path.write_bytes(files[name][1])
        subprocess.run(['node','--check',str(path)],check=True,timeout=30)
    subprocess.run(['node',str(ROOT/'test-restock.cjs')],check=True,timeout=30,cwd=ROOT)

    asar=pack(files)
    rebuilt=unpack(asar)
    assert set(rebuilt)==set(files)
    assert all(rebuilt[k][1]==data for k,(meta,data) in files.items())
    assert sha(rebuilt[BUNDLED_APK][1])==BUNDLED_APK_SHA
    assert b'#posProductSearchInput' in rebuilt['nano-v136-shortcuts.js'][1]
    for html in ['index.html','mobile/www/index.html']:
        assert b'<script defer src="nano-restock-assistant.js"></script>' in rebuilt[html][1]

    output=ROOT/ASSET
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={'fileName':ASSET,'sha256':sha(output.read_bytes()),'appAsarSha256':sha(asar),
          'sizeBytes':output.stat().st_size,'fromVersion':'1.0.61','toVersion':'1.0.62',
          'changedFiles':changed,'dataFilesModified':False,'mobileApkSha256':BUNDLED_APK_SHA}
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.61' and manifest.get('published') is True
    previous=manifest.get('patches',[])
    from_versions=list(dict.fromkeys((previous[0].get('fromVersions',[]) if previous else [])+['1.0.61']))
    manifest['version']='1.0.62'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.62']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{'id':'nano-pos-v1.0.62-restock-barcode',
       'fromVersions':from_versions,
       'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.62/'+ASSET,
       'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.62',
       'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
       'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'}]
    manifest['notes']={'ar':'مساعد إعادة الطلب بالاعتماد على البيانات المسجلة وإصلاح اختصار الباركود F2، دون تغيير قاعدة البيانات.',
                       'fr':'Réapprovisionnement en lecture seule et raccourci F2 corrigé, données préservées.',
                       'en':'Read-only restock assistant and repaired F2 barcode focus, stored data preserved.'}
    (ROOT/'nano-pos-update-v162.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
