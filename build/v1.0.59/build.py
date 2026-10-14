#!/usr/bin/env python3
"""Build NANO POS v1.0.59 single offline APK button alongside barcode scanner."""
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
ASSET = "NANO-POS-Patch-1.0.58-to-1.0.59-ONE-LOCAL-MOBILE-BUTTON.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.58/NANO-POS-Patch-1.0.57-to-1.0.58-EMBEDDED-APK.zip"
BASE_SHA = "d0425eac64239ddc25c6e9a6a52b04baa666d6c8b9c96463fad6707c6bec0ced"
BASE_ASAR_SHA = "a99626b1b8fc73465e195774dc56b7ce4957fc6b240a6cdbe0f28b475a7f027e"

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

APK_SHA256 = '49503c07f39d941e308005df40b7de3243e1a379704b042ef1f7bd7e2bd6174c'
APK_ASAR_PATH = 'downloads/NANO-POS-Mobile-v1.3.7.apk'

def main():
    source = ROOT / 'published-v158.zip'
    if not source.exists():
        with urllib.request.urlopen(
            urllib.request.Request(BASE_URL, headers={'User-Agent': 'NANO-POS-v159-builder'}),
            timeout=180
        ) as response:
            source.write_bytes(response.read())
    assert sha(source.read_bytes()) == BASE_SHA, 'Base update v1.0.58 checksum mismatch'
    with zipfile.ZipFile(source) as archive:
        assert archive.testzip() is None
        orig = archive.read('payload/app.asar')
    assert sha(orig) == BASE_ASAR_SHA, 'Base v1.0.58 ASAR checksum mismatch'
    original = unpack(orig)
    files = dict(original)

    def get(name):
        assert name in original, 'Missing previous ASAR entry: '+name
        return original[name][1].decode('utf8')

    def put(name, content):
        files[name] = (original.get(name, ({}, b''))[0], content.encode('utf8'))

    # Remove the outdated MediaFire URL and connect the ORIGINAL center button
    # to the existing local APK API. Keep the original scanner download button.
    ui = get('desktop-sync-ui.js')
    source_url = "const MOBILE_APP_DOWNLOAD_URL = 'https://www.mediafire.com/file/fw5ktfst7kntw7f/NANO-POS-Mobile-v1.3.6.apk/file';"
    assert ui.count(source_url) == 1, 'MediaFire button changed upstream'
    ui = ui.replace(source_url, "const MOBILE_APP_DOWNLOAD_PATH = '/nano-mobile.apk';")

    handler_before = "if(target.dataset.downloadMobile!==undefined){window.open(MOBILE_APP_DOWNLOAD_URL,'_blank','noopener,noreferrer');return;}"
    handler_after = """if(target.dataset.downloadMobile!==undefined){
      if (typeof window.nanoNative?.saveEmbeddedMobileApk === 'function') {
        const saved = await window.nanoNative.saveEmbeddedMobileApk();
        if (saved?.success === false && !saved?.cancelled) {
          throw new Error(saved.error || 'Cannot save local Android APK');
        }
      } else {
        const localOrigin = /^https?:$/.test(location.protocol)
          ? location.origin
          : ('http://127.0.0.1:' + Number(lastInfo?.port || 4177));
        window.open(localOrigin + MOBILE_APP_DOWNLOAD_PATH, '_blank', 'noopener,noreferrer');
      }
      return;
    }"""
    assert ui.count(handler_before) == 1, 'Cannot locate old MediaFire event handler'
    ui = ui.replace(handler_before, handler_after)
    assert ui.count('data-download-scanner') == 1, 'Barcode reader button changed upstream'
    assert ui.count('data-download-mobile') == 1, 'Mobile download button changed upstream'
    assert ui.count('WIRELESS_SCANNER_DOWNLOAD_PATH') == 2, 'Barcode download handler changed upstream'
    assert 'mediafire' not in ui.lower()

    # Keep existing two download controls but display them SIDE BY SIDE.
    # The mobile one now downloads the embedded APK, and the scanner is untouched.
    cards_pattern = (
        r'(?P<app><section class="rounded-2xl border border-emerald-200\b.*?'
        r'<button data-download-mobile\b.*?</button></section>)\s*'
        r'(?P<scanner><section class="rounded-2xl border border-violet-200\b.*?'
        r'<button data-download-scanner\b.*?</button></section>)'
    )
    matches = list(re.finditer(cards_pattern, ui, re.S))
    assert len(matches) == 1, f'Expected exactly one adjacent mobile/scanner layout, found {len(matches)}'
    m = matches[0]
    replacement = (
        '<div id="nano-local-app-scanner-downloads" class="grid grid-cols-1 lg:grid-cols-2 gap-3">'
        + m.group('app') + '\n' + m.group('scanner') + '</div>'
    )
    ui = ui[:m.start()] + replacement + ui[m.end():]
    ui = ui.replace('NANO POS Mobile v1.3.6', 'NANO POS Mobile v1.3.7')
    assert 'v1.3.6' not in ui
    assert ui.count('data-download-mobile') == 1
    assert ui.count('data-download-scanner') == 1
    assert ui.count('nano-local-app-scanner-downloads') == 1
    put('desktop-sync-ui.js', ui)

    # Delete the duplicate UI at the bottom of the Settings mobile tab
    # WITHOUT removing its APK from the app or altering download/IPC endpoints.
    html = get('index.html')
    old_script = '<script defer src="nano-mobile-offline-ui.js"></script>'
    assert html.count(old_script) == 1
    html = html.replace(old_script, '')
    assert html.count('desktop-sync-ui.js') >= 1
    put('index.html', html)

    pkg=json.loads(get('package.json'))
    assert pkg['version'] == '1.0.58'
    pkg['version']='1.0.59'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in files:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.58'
        lock['version']='1.0.59'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.59'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in files:
        config=get('app-config.js')
        new=config.replace("|| '1.0.58'","|| '1.0.59'")
        assert new != config, 'Missing app version fallback'
        put('app-config.js',new)

    features={
      'ar':[
        'إزالة زر MediaFire القديم لتنزيل تطبيق الهاتف من مركز الأجهزة.',
        'الإبقاء على زر تحميل محلي واحد لتطبيق NANO POS Mobile المضمّن بجوار قارئ الباركود.',
        'حفظ APK محليًا من الكمبيوتر دون إنترنت، مع الإبقاء على خدمة تنزيله عبر الشبكة المحلية.',
        'عدم تغيير بيانات المتجر والتفعيل والمبيعات والديون والمزامنة وقارئ الباركود.'
      ],
      'fr':[
        'Suppression du bouton de téléchargement MediaFire obsolète.',
        'Un seul bouton local pour l’APK NANO POS Mobile, à côté du lecteur de codes-barres.',
        'Enregistrement hors ligne depuis Windows; lien LAN de téléchargement conservé.',
        'Données, activation, ventes, dettes, synchronisation et lecteur de codes-barres inchangés.'
      ],
      'en':[
        'Remove the outdated MediaFire mobile download action.',
        'Place the single local NANO POS Mobile APK download next to Barcode Scanner.',
        'Save the bundled APK without Internet; retain local network download functionality.',
        'Preserve business data, activation, sales, debts, sync and scanner.'
      ]
    }
    if 'release-notes.js' in files:
        notes=get('release-notes.js')
        a=notes.find('const F=')
        b=notes.find(';',a)
        assert a>=0 and b>a,'Expected release notes template'
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allowed={'desktop-sync-ui.js','index.html','package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allowed),changed
    assert {'desktop-sync-ui.js','index.html','package.json'}.issubset(changed)
    assert sha(original[APK_ASAR_PATH][1])==APK_SHA256,'APK checksum unexpectedly changed'
    assert files[APK_ASAR_PATH][1]==original[APK_ASAR_PATH][1], 'Bundled APK must remain unchanged'
    assert files['mobile-sync-server.cjs'][1]==original['mobile-sync-server.cjs'][1], 'Scanner server changed unexpectedly'
    assert files['nano-embedded-apk.cjs'][1]==original['nano-embedded-apk.cjs'][1], 'Offline APK provider changed unexpectedly'

    test_file=ROOT/'check-desktop-sync-ui.js'
    test_file.write_text(ui,encoding='utf8')
    subprocess.run(['node','--check',str(test_file)],check=True,timeout=30)

    asar=pack(files)
    rebuilt=unpack(asar)
    assert set(rebuilt)==set(files)
    assert all(rebuilt[k][1]==v[1] for k,v in files.items()), 'Repacked ASAR failed integrity check'
    assert b'nano-local-app-scanner-downloads' in rebuilt['desktop-sync-ui.js'][1]
    assert b'mediafire' not in rebuilt['desktop-sync-ui.js'][1].lower()
    assert b'nano-mobile-offline-ui.js"></script>' not in rebuilt['index.html'][1]
    assert sha(rebuilt[APK_ASAR_PATH][1])==APK_SHA256

    output=ROOT/ASSET
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={
      'fileName':ASSET,'sha256':sha(output.read_bytes()),'appAsarSha256':sha(asar),
      'sizeBytes':output.stat().st_size,'fromVersion':'1.0.58','toVersion':'1.0.59',
      'apkVersion':'1.3.7','apkSha256':APK_SHA256,'changedFiles':changed,
      'dataFilesModified':False,'downloadButtonCount':1,'scannerButtonCount':1
    }
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.58' and manifest.get('published') is True
    old=manifest.get('patches',[])
    from_versions=list(dict.fromkeys((old[0].get('fromVersions',[]) if old else [])+['1.0.58']))
    manifest['version']='1.0.59'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.59']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{
       'id':'nano-pos-v1.0.59-one-local-mobile-button',
       'fromVersions':from_versions,
       'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.59/'+ASSET,
       'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.59',
       'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
       'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'
    }]
    manifest['notes']={
       'ar':'إزالة تحميل الهاتف من MediaFire والاكتفاء بتحميل APK المحلي بجوار زر قارئ الباركود.',
       'fr':'Suppression du bouton MediaFire; téléchargement APK local à côté du lecteur code-barres.',
       'en':'Remove MediaFire button; keep only offline mobile APK download alongside the barcode scanner.'
    }
    (ROOT/'nano-pos-update-v159.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
