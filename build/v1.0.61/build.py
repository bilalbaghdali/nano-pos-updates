#!/usr/bin/env python3
"""Build v1.0.61: remove only lower floating devices button and validate partial payment input."""
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
ASSET = "NANO-POS-Patch-1.0.60-to-1.0.61-UI-PAYMENT-GUARDS.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.60/NANO-POS-Patch-1.0.59-to-1.0.60-SIDEBAR-LOGO-REMOVAL.zip"
BASE_SHA = "3cc83f02536ff92eed93004d7e2bc2fa1db6520265811a958fe7ed6ecdb832c9"
BASE_ASAR_SHA = "dc52c487cd99c1e5b86f3726211e063f5c75dc5b4b71a2e809dab66217fe8d70"

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
    source=ROOT/'published-v160.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v161-builder'}),timeout=180) as response:
            source.write_bytes(response.read())
    assert sha(source.read_bytes())==BASE_SHA,'Unrecognized v1.0.60 patch'
    with zipfile.ZipFile(source) as archive:
        assert archive.testzip() is None
        original_asar=archive.read('payload/app.asar')
    assert sha(original_asar)==BASE_ASAR_SHA,'Unrecognized v1.0.60 ASAR'
    original=unpack(original_asar)
    files=dict(original)

    def get(name):
        assert name in original, 'Missing entry: '+name
        return original[name][1].decode('utf8')
    def put(name,value):
        files[name]=(original[name][0],value.encode('utf8'))

    # Remove only the redundant FLOATING bottom-left mobile device/status button.
    # The top-header connected-devices badge and Settings > Mobile remain intact.
    ui=get('desktop-sync-ui.js')
    chip_func=re.compile(r'  function ensureGlobalStatusChip\(\)\{\n.*?\n  \}\n(?=  function updateGlobalStatus\()',re.S)
    assert len(chip_func.findall(ui))==1,'Floating status control function changed'
    ui=chip_func.sub('',ui,count=1)
    old_line=re.compile(r"    const chip=ensureGlobalStatusChip\(\),dot=chip.querySelector\('\[data-dot\]'\),text=chip.querySelector\('\[data-text\]'\);[^\n]*\n")
    assert len(old_line.findall(ui))==1,'Floating badge update changed upstream'
    ui=old_line.sub("    document.getElementById('nanoMobileSyncGlobalStatus')?.remove();\n",ui,count=1)
    assert 'ensureGlobalStatusChip' not in ui
    assert 'ensureHeaderDevicesBadge' in ui and 'openConnectedDevices' in ui
    assert 'saveEmbeddedMobileApk' in ui and 'data-download-scanner' in ui
    put('desktop-sync-ui.js',ui)

    # Avoid accidental negative quantities of paid money in the purchase invoice
    # without changing the checkout accounting or credit mode at all.
    for path in ('index.html','mobile/www/index.html'):
        body=get(path)
        before='id="invPaid" value="0"'
        after='id="invPaid" value="0" min="0" step="0.01" inputmode="decimal"'
        assert body.count(before)==1,('Invoice paid input anchor changed',path)
        body=body.replace(before,after,1)
        # Keyboard focus visibility for accessibility and quicker checkout.
        assert body.count('</head>')==1,('HTML head anchor changed',path)
        focus_css=('<!-- NANO POS v1.0.61 keyboard focus -->\n'
                   '<style>#salesSection :is(button,input,select):focus-visible,'
                   '#nanoHomeSection :is(button,input,select):focus-visible,'
                   '#invoiceSection :is(button,input,select):focus-visible'
                   '{outline:2px solid #2563eb;outline-offset:2px}</style>\n')
        body=body.replace('</head>',focus_css+'</head>',1)
        assert 'id="connectedDevicesBadge"' in body
        put(path,body)

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.60'
    pkg['version']='1.0.61'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.60'
        lock['version']='1.0.61'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.61'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        config=get('app-config.js')
        updated=config.replace("|| '1.0.60'","|| '1.0.61'")
        assert updated!=config,'Version fallback changed'
        put('app-config.js',updated)

    features={
      'ar':[
        'إزالة زر حالة الأجهزة والمزامنة العائم من أسفل واجهة الكمبيوتر دون تعطيل المزامنة.',
        'الإبقاء على مؤشر الأجهزة المرتبطة في الأعلى وعلى مركز إدارة الأجهزة داخل الإعدادات.',
        'تحسين إدخال المبلغ المدفوع في فاتورة الشراء ومنع الأرقام السالبة عبر خصائص حقل الإدخال.',
        'إبراز التركيز بلوحة المفاتيح في شاشات البيع والرئيسية والفواتير دون تغيير بيانات التفعيل أو الأرصدة.'
      ],
      'fr':[
        'Suppression du bouton flottant inférieur des appareils, sans désactiver la synchronisation.',
        'Indicateur supérieur et gestion des appareils dans les paramètres conservés.',
        'Champ montant payé de facture: minimum zéro et précision de 0,01.',
        'Amélioration de la navigation au clavier sans modifier les données ni les licences.'
      ],
      'en':[
        'Remove the redundant bottom floating connected-devices button without disabling sync.',
        'Preserve the header devices badge and Settings device center.',
        'Add nonnegative and decimal input hints to the purchase invoice amount-paid field.',
        'Make keyboard focus visible in sales, home and invoices; preserve existing data and activation.'
      ]
    }
    if 'release-notes.js' in original:
        notes=get('release-notes.js')
        a=notes.find('const F=');b=notes.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allowed={'desktop-sync-ui.js','index.html','mobile/www/index.html','package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allowed),changed
    assert {'desktop-sync-ui.js','index.html','mobile/www/index.html','package.json'}.issubset(set(changed))
    for protected in ('electron-main.cjs','electron-native-preload.cjs','renderer.js','mobile/www/renderer.js',
                      'mobile-sync-server.cjs','pc-sync-service.cjs','mega-cloud-backup.cjs','mega-restore-safety.cjs',
                      'nano-debt-stats-fix.js','print-engine.js','document-print-preview.js'):
        assert files[protected][1]==original[protected][1],('Protected subsystem modified',protected)
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA
    for name in ('desktop-sync-ui.js',):
        check=ROOT/('check-'+name)
        check.write_bytes(files[name][1])
        subprocess.run(['node','--check',str(check)],check=True,timeout=25)

    asar=pack(files)
    rebuilt=unpack(asar)
    assert set(rebuilt)==set(original)
    assert all(rebuilt[k][1]==data for k,(meta,data) in files.items())
    assert b'ensureGlobalStatusChip' not in rebuilt['desktop-sync-ui.js'][1]
    assert b'ensureHeaderDevicesBadge' in rebuilt['desktop-sync-ui.js'][1]
    assert sha(rebuilt[BUNDLED_APK][1])==BUNDLED_APK_SHA
    output=ROOT/ASSET
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={'fileName':ASSET,'sha256':sha(output.read_bytes()),'appAsarSha256':sha(asar),
          'sizeBytes':output.stat().st_size,'fromVersion':'1.0.60','toVersion':'1.0.61',
          'changedFiles':changed,'dataFilesModified':False,'mobileApkSha256':BUNDLED_APK_SHA}
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.60' and manifest.get('published') is True
    previous=manifest.get('patches',[])
    from_versions=list(dict.fromkeys((previous[0].get('fromVersions',[]) if previous else [])+['1.0.60']))
    manifest['version']='1.0.61'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.61']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{'id':'nano-pos-v1.0.61-ui-payment-guard',
        'fromVersions':from_versions,
        'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.61/'+ASSET,
        'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.61',
        'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
        'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'}]
    manifest['notes']={'ar':'تحسين واجهة الأجهزة وإدخال المبلغ المدفوع دون تغيير قواعد البيانات.',
        'fr':'Amélioration de l’interface et du champ de paiement, sans modification des données.',
        'en':'Improve device UI and amount-paid input without changing stored data.'}
    (ROOT/'nano-pos-update-v161.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
