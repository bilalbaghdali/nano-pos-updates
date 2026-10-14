#!/usr/bin/env python3
"""Build v1.0.60: remove only the sidebar logo beside the merchant/store heading."""
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
ASSET = "NANO-POS-Patch-1.0.59-to-1.0.60-SIDEBAR-LOGO-REMOVAL.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.59/NANO-POS-Patch-1.0.58-to-1.0.59-ONE-LOCAL-MOBILE-BUTTON.zip"
BASE_SHA = "1826b7e4ce852610a732336a09e1981c66fbbb148cad82b907f00ac7295395ab"
BASE_ASAR_SHA = "4ea2b86e928adf3a4e4b90d21660ddf1f05358537b2b047e3541cbc7cde6bb26"

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
    source=ROOT/'published-v159.zip'
    if not source.exists():
        with urllib.request.urlopen(
            urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v160-builder'}),
            timeout=180
        ) as response:
            source.write_bytes(response.read())
    assert sha(source.read_bytes())==BASE_SHA,'Unexpected v1.0.59 release'
    with zipfile.ZipFile(source) as archive:
        assert archive.testzip() is None
        original_asar=archive.read('payload/app.asar')
    assert sha(original_asar)==BASE_ASAR_SHA,'Unexpected v1.0.59 ASAR'
    original=unpack(original_asar)
    files=dict(original)

    def get(name):
        assert name in original, 'Missing ASAR entry: '+name
        return original[name][1].decode('utf8')

    def put(name,content):
        files[name]=(original.get(name,({},b''))[0],content.encode('utf8'))

    for name in ['index.html','mobile/www/index.html']:
        before=get(name)
        assert '<!-- Sidebar -->' in before,'Cannot identify sidebar '+name
        assert before.count('data-i18n="app_title"')>=1
        # Restrict deletion to the exact single sidebar icon, not shop logos elsewhere.
        matches=list(SIDEBAR_LOGO.finditer(before))
        assert len(matches)==1, f'Expected one sidebar logo in {name}, got {len(matches)}'
        m=matches[0]
        sidebar=before.index('<!-- Sidebar -->')
        nav=before.index('<nav class="flex-1 overflow-y-auto',sidebar)
        assert sidebar<m.start()<m.end()<nav, 'Icon not inside sidebar heading'
        after=before[:m.start()] + before[m.end():]
        assert before.count('<span data-nano-app-brand>')==after.count('<span data-nano-app-brand>')
        assert before.count('id="sidebarToggleIcon"')==after.count('id="sidebarToggleIcon"')
        assert after.count('data-i18n="app_title"')==before.count('data-i18n="app_title"')
        assert after.count('id="appDownloadSection"')==before.count('id="appDownloadSection"')
        assert after.count('settingsTab-mobileapp')==before.count('settingsTab-mobileapp')
        assert len(before)-len(after)==len(m.group(0))
        assert not SIDEBAR_LOGO.search(after)
        put(name,after)

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.59'
    pkg['version']='1.0.60'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.59'
        lock['version']='1.0.60'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.60'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        conf=get('app-config.js')
        updated=conf.replace("|| '1.0.59'","|| '1.0.60'")
        assert updated!=conf
        put('app-config.js',updated)

    features={
      'ar':[
        'حذف الأيقونة الزرقاء بجانب اسم المتجر في رأس القائمة الجانبية للكمبيوتر.',
        'إزالة الأيقونة نفسها من واجهة القائمة الجانبية التي تُفتح من المتصفح المحلي.',
        'الإبقاء على اسم المتجر ونص العنوان والقوائم كما هي دون تغيير.',
        'عدم تعديل شعار المتجر في الإعدادات والفواتير والطباعة أو بيانات البيع والتفعيل والمزامنة.'
      ],
      'fr':[
        'Suppression de l’icône bleue à côté du nom du magasin dans la barre latérale.',
        'Même correction dans la barre latérale de l’interface locale.',
        'Nom du magasin et menu inchangés.',
        'Conservation des logos sur les factures et dans les paramètres, des données et de la synchronisation.'
      ],
      'en':[
        'Remove the blue icon directly beside the store heading in the desktop sidebar.',
        'Apply the same change to the local browser sidebar.',
        'Preserve store name, heading text and navigation.',
        'Keep business logos in settings/receipts, sales data, activation and synchronization intact.'
      ]
    }
    if 'release-notes.js' in original:
        notes=get('release-notes.js')
        a=notes.find('const F=');b=notes.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allowed={'index.html','mobile/www/index.html','package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allowed),changed
    assert {'index.html','mobile/www/index.html','package.json'}.issubset(set(changed))
    for n in ['desktop-sync-ui.js','renderer.js','electron-main.cjs','nano-embedded-apk.cjs','mobile-sync-server.cjs']:
        assert files[n][1]==original[n][1],'Unexpected change to '+n
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA
    assert files[BUNDLED_APK][1]==original[BUNDLED_APK][1]

    asar=pack(files)
    rebuilt=unpack(asar)
    assert set(rebuilt)==set(files)
    assert all(rebuilt[n][1]==v[1] for n,v in files.items())
    for n in ['index.html','mobile/www/index.html']:
        contents=rebuilt[n][1].decode('utf8')
        assert not SIDEBAR_LOGO.search(contents)
        assert 'data-i18n="app_title"' in contents
        assert '<!-- Sidebar -->' in contents
    assert b'nano-local-app-scanner-downloads' in rebuilt['desktop-sync-ui.js'][1]
    assert sha(rebuilt[BUNDLED_APK][1])==BUNDLED_APK_SHA

    result_path=ROOT/ASSET
    with zipfile.ZipFile(result_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as zipout:
        zipout.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(result_path) as zipin:
        assert zipin.testzip() is None and zipin.namelist()==['payload/app.asar']
    meta={
      'fileName':ASSET,'sha256':sha(result_path.read_bytes()),
      'appAsarSha256':sha(asar),'sizeBytes':result_path.stat().st_size,
      'fromVersion':'1.0.59','toVersion':'1.0.60',
      'changedFiles':changed,'dataFilesModified':False,
      'removedLogoFrom':['index.html','mobile/www/index.html'],
      'mobileApkVersion':'1.3.7','mobileApkSha256':BUNDLED_APK_SHA
    }
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.59' and manifest.get('published') is True
    old=manifest.get('patches',[])
    from_versions=list(dict.fromkeys((old[0].get('fromVersions',[]) if old else [])+['1.0.59']))
    manifest['version']='1.0.60'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.60']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{
      'id':'nano-pos-v1.0.60-sidebar-logo-only',
      'fromVersions':from_versions,
      'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.60/'+ASSET,
      'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.60',
      'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
      'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'
    }]
    manifest['notes']={
      'ar':'إزالة الشعار الأزرق بجانب اسم المتجر داخل رأس القائمة الجانبية فقط.',
      'fr':'Suppression de l’icône à côté du nom du magasin dans la barre latérale.',
      'en':'Remove only the blue sidebar logo beside the shop heading.'
    }
    (ROOT/'nano-pos-update-v160.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
