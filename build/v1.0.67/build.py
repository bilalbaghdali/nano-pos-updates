#!/usr/bin/env python3
"""Build v1.0.67: reviewed stocktake drafts on authoritative primary PC."""
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
ASSET = "NANO-POS-Patch-1.0.66-to-1.0.67-STOCKTAKE-APPROVAL.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.66/NANO-POS-Patch-1.0.65-to-1.0.66-SALE-RETURNS.zip"
BASE_SHA = "b9e8c9d8f533c6149b3e7f230e870d62dd1e5e95991c3f85c3013a25101398be"
BASE_ASAR_SHA = "82a8cf1011e78ac13f4983a4491dfde159bbf88124b775427d6969988ade95a7"

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
    source=ROOT/'published-v166.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v167-builder'}),timeout=180) as r:
            source.write_bytes(r.read())
    assert sha(source.read_bytes())==BASE_SHA,'Unknown v1.0.66 release archive'
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR_SHA,'Unknown v1.0.66 app package'
    original=unpack(raw)
    files=dict(original)
    def get(n):
        assert n in original,'Missing required entry: '+n
        return original[n][1].decode('utf8')
    def put(n,v):files[n]=(original[n][0],v.encode('utf8'))
    module=(ROOT/'nano-stocktake-approval.js').read_bytes()
    assert b'NANO_STOCKTAKE_APPROVAL_167' in module
    files['nano-stocktake-approval.js']=({},module)
    files['mobile/www/nano-stocktake-approval.js']=({},module)
    ui=(ROOT/'nano-stocktake-drafts-ui.js').read_bytes()
    files['nano-stocktake-drafts-ui.js']=({},ui)
    files['mobile/www/nano-stocktake-drafts-ui.js']=({},ui)
    for path in ('index.html','mobile/www/index.html'):
        doc=get(path)
        assert doc.count('src="browser-bridge.js"')==1
        assert 'nano-stocktake-approval.js' not in doc
        doc=doc.replace('src="browser-bridge.js"',
            'src="nano-stocktake-approval.js"></script>\n  <script src="browser-bridge.js"',1)
        assert doc.index('src="nano-stocktake-approval.js"')<doc.index('src="browser-bridge.js"')
        assert doc.count('</body>')==1
        doc=doc.replace('</body>','<script defer src="nano-stocktake-drafts-ui.js"></script>\n</body>',1)
        put(path,doc)

    for path in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        src=get(path)
        anchor="""   if (channel === 'get-stocktakes') return clone(db.stocktakes || []);"""
        assert src.count(anchor)==1,('Stocktake handler missing',path)
        calls="""   if (channel === 'get-stocktake-drafts') {
     const filter=args[0] || {};
     return clone((db.stocktake_drafts || []).filter(d=>!filter.status||d.status===filter.status));
   }
   if (['create-stocktake-draft','approve-stocktake-draft','reject-stocktake-draft'].includes(channel)) {
     const payload=args[0] || {};
     let user=null;
     try { user=JSON.parse(localStorage.getItem('pos_current_user') || 'null'); } catch {}
     if(!user?.id)return fail('يلزم تسجيل الدخول للمستخدم المخول');
     try {
       const gate=window.NANO_STOCKTAKE_APPROVAL_167,stock=window.NANO_TX_GUARD_165;
       const outcome=channel==='create-stocktake-draft'
         ?gate.submit(db,payload,user.id,stock)
         :channel==='approve-stocktake-draft'
         ?gate.approve(db,payload,user.id,stock)
         :gate.reject(db,payload,user.id);
       if (outcome.result.alreadyProcessed||outcome.result.alreadyApproved||outcome.result.alreadyRejected) return clone(outcome.result);
       const old=db;
       db=outcome.next;
       save();
       const stored=JSON.parse(localStorage.getItem(KEY) || '{}');
       const check=(stored.stocktake_drafts || []).find(x=>x.id===String(payload.draftId||payload.requestId));
       if (!check || (channel==='create-stocktake-draft'&&check.status!=='pending')||
            (channel==='approve-stocktake-draft'&&check.status!=='approved')||
            (channel==='reject-stocktake-draft'&&check.status!=='rejected')) {
         db=old;return fail('تعذر حفظ عملية الجرد بشكل متسق');
       }
       return clone(outcome.result);
     } catch(error) { return fail(error?.message || 'فشلت مراجعة الجرد'); }
   }
"""
        src=src.replace(anchor,calls+anchor,1)
        # Treat approve and reject as license-protected write operations
        oldrx='(issue-credit-note|add-|update-|delete-|save-|process-|create-|confirm-|reverse-|set-|toggle-|import-|reset-|open-caisse|close-caisse)'
        assert src.count(oldrx)==1,('Write license gate missing',path)
        src=src.replace(oldrx,'(approve-stocktake-draft|reject-stocktake-draft|issue-credit-note|add-|update-|delete-|save-|process-|create-|confirm-|reverse-|set-|toggle-|import-|reset-|open-caisse|close-caisse)',1)
        put(path,src)

    pc=get('pc-sync-service.cjs')
    webbad="if (!channel || channel.startsWith('__nano-pc-') || channel === 'login-user') return webJson(res, 400, { success: false, error: 'invalid_channel' });"
    pcdeny="if (channel === 'approve-stocktake-draft' || channel === 'reject-stocktake-draft') return webJson(res, 403, { success: false, error: 'primary_pc_only', message: 'اعتماد الجرد أو رفضه يجب أن يتم من الكمبيوتر الرئيسي.' });"
    assert pc.count(webbad)==1
    pc=pc.replace(webbad,webbad+'\n          '+pcdeny,1)
    devbad="if (!channel || channel.startsWith('__nano-pc-')) return json(res, 400, { success: false, error: 'invalid_channel' });"
    pcdev="if (channel === 'approve-stocktake-draft' || channel === 'reject-stocktake-draft') return json(res, 403, { success: false, error: 'primary_pc_only', message: 'يجب اعتماد الجرد من الكمبيوتر الرئيسي.' });"
    assert pc.count(devbad)==1
    pc=pc.replace(devbad,devbad+'\n        '+pcdev,1)
    put('pc-sync-service.cjs',pc)

    mobile=get('mobile-sync-server.cjs')
    mobbad="if (!channel || channel.length > 120) return send(res, 400, { success: false, error: 'invalid_channel' });"
    mobdeny="if (channel === 'approve-stocktake-draft' || channel === 'reject-stocktake-draft') return send(res, 403, { success: false, error: 'primary_pc_only', message: 'اعتماد الجرد يقتصر على الكمبيوتر الرئيسي.' });"
    assert mobile.count(mobbad)==1
    mobile=mobile.replace(mobbad,mobbad+'\n        '+mobdeny,1)
    put('mobile-sync-server.cjs',mobile)

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.66'
    pkg['version']='1.0.67'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.66'
        lock['version']='1.0.67'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.67'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        config=get('app-config.js')
        updated=config.replace("|| '1.0.66'","|| '1.0.67'")
        assert updated!=config
        put('app-config.js',updated)
    features={
      'ar':[
        'إنشاء مسودات جرد من الهاتف أو المتصفح دون تعديل كميات المخزون.',
        'اعتماد الجرد أو رفضه من الكمبيوتر الرئيسي فقط، والتحقق من الكميات الحالية قبل الموافقة.',
        'منع الاعتماد المكرر وتسجيل معلومات المستخدم والدفعات والفرق في سجل الجرد.',
        'حظر أوامر اعتماد الجرد من أجهزة العميل والمتصفح البعيد على مستوى الخادم.'
      ],
      'fr':['Création des projets de comptage sans modification du stock.',
            'Validation ou rejet exclusivement sur le PC principal après contrôle du stock courant.',
            'Anti-doublon et journal des opérations de stocktake, refus des validations à distance.'],
      'en':['Submit stocktake count drafts without changing inventory.',
            'Require primary-PC approval or rejection with current stock consistency checks.',
            'Prevent repeated approvals and deny remote approval at sync endpoints.']
    }
    if 'release-notes.js' in original:
        notes=get('release-notes.js')
        a=notes.find('const F=');b=notes.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allowed={'nano-stocktake-approval.js','mobile/www/nano-stocktake-approval.js',
             'nano-stocktake-drafts-ui.js','mobile/www/nano-stocktake-drafts-ui.js',
             'browser-bridge.js','mobile/www/browser-bridge.js','pc-sync-service.cjs','mobile-sync-server.cjs',
             'index.html','mobile/www/index.html','package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allowed),changed
    assert {'nano-stocktake-approval.js','mobile/www/nano-stocktake-approval.js','browser-bridge.js',
            'mobile/www/browser-bridge.js','pc-sync-service.cjs','mobile-sync-server.cjs',
            'index.html','mobile/www/index.html','package.json'}.issubset(set(changed))
    for n in ('electron-main.cjs','electron-native-preload.cjs','renderer.js','mobile/www/renderer.js',
              'mega-cloud-backup.cjs','mega-restore-safety.cjs','nano-debt-stats-fix.js','print-engine.js',
              'nano-return-plan.js','mobile/www/nano-return-plan.js','nano-transaction-guards.js'):
        assert files[n][1]==original[n][1],('Protected file modified',n)
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA
    for n in ('browser-bridge.js','mobile/www/browser-bridge.js','pc-sync-service.cjs',
              'mobile-sync-server.cjs','nano-stocktake-approval.js','nano-stocktake-drafts-ui.js'):
        temp=ROOT/('syntax-'+n.replace('/','-'))
        temp.write_bytes(files[n][1])
        subprocess.run(['node','--check',str(temp)],check=True,timeout=30)
    subprocess.run(['node',str(ROOT/'test-stocktake-approval.cjs')],check=True,timeout=30,cwd=ROOT)
    for name in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        t=ROOT/('integration-'+name.replace('/','-'))
        t.write_bytes(files[name][1])
        subprocess.run(['node',str(ROOT/'test-stocktake-bridge.cjs'),str(t),
                       str(ROOT.parent/'v1.0.65/nano-transaction-guards.js'),
                       str(ROOT.parent/'v1.0.66/nano-return-plan.js'),
                       str(ROOT/'nano-stocktake-approval.js')],check=True,timeout=40,cwd=ROOT)
    asar=pack(files)
    verify=unpack(asar)
    assert set(verify)==set(files)
    assert all(verify[k][1]==v for k,(meta,v) in files.items())
    assert sha(verify[BUNDLED_APK][1])==BUNDLED_APK_SHA
    out=ROOT/ASSET
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(out) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={'fileName':ASSET,'sha256':sha(out.read_bytes()),'appAsarSha256':sha(asar),
          'sizeBytes':out.stat().st_size,'fromVersion':'1.0.66','toVersion':'1.0.67',
          'changedFiles':changed,'dataFilesModified':False,'mobileApkSha256':BUNDLED_APK_SHA}
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.66' and manifest.get('published') is True
    old=manifest.get('patches',[])
    from_versions=list(dict.fromkeys((old[0].get('fromVersions',[]) if old else [])+['1.0.66']))
    manifest['version']='1.0.67'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.67']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{'id':'nano-pos-v1.0.67-stocktake-approval',
       'fromVersions':from_versions,
       'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.67/'+ASSET,
       'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.67',
       'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
       'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'}]
    manifest['notes']={'ar':'مسودات جرد من الهاتف مع اعتماد آمن على الكمبيوتر الرئيسي بعد تحقق كميات المخزون.',
       'fr':'Brouillons d’inventaire avec approbation sur ordinateur principal.',
       'en':'Stocktake count drafts requiring primary PC approval.'}
    (ROOT/'nano-pos-update-v167.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
