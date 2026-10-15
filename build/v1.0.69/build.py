#!/usr/bin/env python3
"""Build v1.0.69: primary-authoritative multi-phone count sessions and operator conflict locks."""
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
ASSET = "NANO-POS-Patch-1.0.68-to-1.0.69-MULTIPHONE-COUNT.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.68/NANO-POS-Patch-1.0.67-to-1.0.68-PRICING-OFFERS.zip"
BASE_SHA = "64a3a0a7564dc8d8ea0408ff6282e1f453f28ff54d7154b1c67e0a1b94d556fc"
BASE_ASAR_SHA = "c0302905634d3bd358f79ee1ffd5f4d25e5626d894f6c60bd6178e06d73ea9f6"

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
    source=ROOT/'published-v168.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v169-builder'}),timeout=180) as r:
            source.write_bytes(r.read())
    assert sha(source.read_bytes())==BASE_SHA,'Unknown NANO POS v1.0.68 ZIP; refusing to continue'
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR_SHA,'Unknown v1.0.68 ASAR; refusing to mutate'
    original=unpack(raw)
    files=dict(original)
    def get(n):
        assert n in original,('Missing file',n)
        return original[n][1].decode('utf8')
    def put(n,s):files[n]=(original[n][0],s.encode('utf8'))

    for name in ('nano-multi-count.js','nano-multi-count-ui.js'):
        blob=(ROOT/name).read_bytes()
        assert b'NANO_MULTI_COUNT_' in blob
        files[name]=({},blob)
        files['mobile/www/'+name]=({},blob)
    for path in ('index.html','mobile/www/index.html'):
        html=get(path)
        assert html.count('src="browser-bridge.js"')==1 and html.count('</body>')==1
        assert 'nano-multi-count.js' not in html
        html=html.replace('src="browser-bridge.js"',
          'src="nano-multi-count.js"></script>\n  <script src="browser-bridge.js"',1)
        html=html.replace('</body>','<script defer src="nano-multi-count-ui.js"></script>\n</body>',1)
        put(path,html)

    for path in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        s=get(path)
        anchor="   if (channel === 'get-stocktake-drafts') {"
        assert s.count(anchor)==1,('Multi-count insertion point changed',path)
        handlers="""   if (channel === 'nano-count-active') {
     return clone(window.NANO_MULTI_COUNT_169.present(window.NANO_MULTI_COUNT_169.active(db)));
   }
   if (['nano-count-start','nano-count-claim','nano-count-record','nano-count-release','nano-count-finish'].includes(channel)) {
     const payload=args[0] || {};
     const engine=window.NANO_MULTI_COUNT_169;
     const user=(()=>{try{return JSON.parse(localStorage.getItem('pos_current_user')||'null')}catch{return null}})();
     try {
       const trusted=payload.__nanoCountOrigin;
       if (channel!=='nano-count-start'&&channel!=='nano-count-finish'&&trusted?.origin!=='mobile')
          return fail('جرد الهاتف يتطلب هاتفًا مربوطًا ومصادقًا عليه من الكمبيوتر الرئيسي');
       if (['nano-count-start','nano-count-finish'].includes(channel)&&!user?.id)
          return fail('تسجيل الدخول بحساب مدير على الكمبيوتر الرئيسي مطلوب');
       const data=channel==='nano-count-start'
         ?engine.start(db,payload,user.id)
         :channel==='nano-count-claim'
         ?engine.claim(db,payload,trusted)
         :channel==='nano-count-record'
         ?engine.record(db,payload,trusted)
         :channel==='nano-count-release'
         ?engine.release(db,payload,trusted)
         :engine.finish(db,payload,user.id,window.NANO_STOCKTAKE_APPROVAL_167);
       if(data.next!==db){
         const previous=db;db=data.next;save();
         const persisted=JSON.parse(localStorage.getItem(KEY)||'{}');
         const persistedSession=(persisted.nano_multi_count_sessions||[]).find(v=>v.id===String(payload.sessionId||data.result?.session?.id));
         if(!persistedSession){db=previous;return fail('فشل حفظ حالة الجرد؛ لم يتم تسجيل العملية');}
       }
       return clone(data.result);
     }catch(error){return fail(error?.message||'تعذر تحديث الجرد الجماعي');}
   }
"""
        s=s.replace(anchor,handlers+anchor,1)
        writeguard="(approve-stocktake-draft|reject-stocktake-draft|issue-credit-note|"
        assert s.count(writeguard)==1,('Business write protection anchor changed',path)
        s=s.replace(writeguard,"(nano-count-(start|claim|record|release|finish)|"+writeguard[1:],1)
        put(path,s)

    ms=get('mobile-sync-server.cjs')
    permission="  if (c.startsWith('delete-')"
    assert ms.count(permission)==1
    ms=ms.replace(permission,"  if (c.startsWith('nano-count-')) return 'inventory';\n"+permission,1)
    previous="if (channel === 'approve-stocktake-draft' || channel === 'reject-stocktake-draft') return send(res, 403, { success: false, error: 'primary_pc_only', message: 'اعتماد الجرد يقتصر على الكمبيوتر الرئيسي.' });"
    assert ms.count(previous)==1
    ms=ms.replace(previous,previous+"""
        if (channel==='nano-count-start'||channel==='nano-count-finish')
          return send(res,403,{success:false,error:'primary_pc_only',message:'فتح وإغلاق الجرد الجماعي من الكمبيوتر الرئيسي فقط'});
        if (channel.startsWith('nano-count-')&&device.permissions?.inventory===false)
          return send(res,403,{success:false,error:'permission_denied',message:'الهاتف غير مخول للجرد'});""",1)
    origin="""        const rpcContext = { ip: req.socket.remoteAddress || '', deviceId: device.id, deviceName: device.name, operationId };
        const result = channel === 'get-customers'
          ? await resolveCustomerRows(dispatchRpc, args, rpcContext)
          : await dispatchRpc(channel, args, rpcContext);"""
    newOrigin="""        const rpcContext = { ip: req.socket.remoteAddress || '', deviceId: device.id, deviceName: device.name, operationId };
        const authenticatedArgs = channel.startsWith('nano-count-')
          ? [{...(args[0]||{}),__nanoCountOrigin:{origin:'mobile',deviceId:device.id,deviceName:device.name}}]
          : args;
        const result = channel === 'get-customers'
          ? await resolveCustomerRows(dispatchRpc, args, rpcContext)
          : await dispatchRpc(channel, authenticatedArgs, rpcContext);"""
    assert ms.count(origin)==1,('Authenticated RPC dispatch changed',)
    ms=ms.replace(origin,newOrigin,1)
    put('mobile-sync-server.cjs',ms)

    pc=get('pc-sync-service.cjs')
    web="if (channel === 'approve-stocktake-draft' || channel === 'reject-stocktake-draft') return webJson(res, 403, { success: false, error: 'primary_pc_only', message: 'اعتماد الجرد أو رفضه يجب أن يتم من الكمبيوتر الرئيسي.' });"
    assert pc.count(web)==1
    pc=pc.replace(web,web+"""
          if (['nano-count-start','nano-count-finish','nano-count-claim','nano-count-record','nano-count-release'].includes(channel))
            return webJson(res,403,{success:false,error:'primary_pc_only',message:'الجرد الجماعي من جهاز مرتبط معتمد فقط'});""",1)
    dev="if (channel === 'approve-stocktake-draft' || channel === 'reject-stocktake-draft') return json(res, 403, { success: false, error: 'primary_pc_only', message: 'يجب اعتماد الجرد من الكمبيوتر الرئيسي.' });"
    assert pc.count(dev)==1
    pc=pc.replace(dev,dev+"""
        if (['nano-count-start','nano-count-finish','nano-count-claim','nano-count-record','nano-count-release'].includes(channel))
          return json(res,403,{success:false,error:'primary_pc_only',message:'جرد الهواتف يمر عبر خادم مزامنة الهاتف فقط'});""",1)
    put('pc-sync-service.cjs',pc)

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.68'
    pkg['version']='1.0.69'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.68'
        lock['version']='1.0.69'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.69'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        conf=get('app-config.js')
        changed=conf.replace("|| '1.0.68'","|| '1.0.69'")
        assert changed!=conf
        put('app-config.js',changed)
    features={
       'ar':[
         'فتح جرد جماعي من الكمبيوتر الرئيسي وإظهار الجلسة تلقائيًا على الهواتف المتصلة.',
         'إدخال اسم الجارد لكل هاتف وعرض الكمية المسجلة مباشرة عند مسح باركود المنتج.',
         'حجز المنتج لهاتف واحد مؤقتًا لمنع تضارب عدّ نفس المنتج من هواتف متعددة.',
         'إظهار رسالة تم جرده عند إعادة المسح، مع اسم الجارد والهاتف والكميات المسجلة.',
         'عرض تقدم الجرد حسب كل هاتف وتجميع النتائج في مسودة للمراجعة والاعتماد من الكمبيوتر الرئيسي دون تغيير المخزون أثناء العدّ.'
       ],
       'fr':['Inventaire collectif ouvert depuis le PC principal et affiché automatiquement sur les téléphones.',
             'Nom du compteur par téléphone; scan montre le stock théorique et la saisie des quantités.',
             'Verrou temporaire au niveau du produit, historique par opérateur et refus des doublons.',
             'Envoi des comptages vers un brouillon pour approbation sur PC principal.'],
       'en':['Primary PC starts a shared count; connected phones automatically display the count.',
             'Each phone enters the counter name, scans barcodes and records physical quantities.',
             'Exclusive per-product short leases prevent concurrent handset edits or duplicate counts.',
             'All handset counts are attributed and merged into a draft pending primary PC approval.']
    }
    if 'release-notes.js' in original:
        note=get('release-notes.js')
        a=note.find('const F=');b=note.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',note[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+note[b:])
    changes=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allow={'nano-multi-count.js','mobile/www/nano-multi-count.js',
           'nano-multi-count-ui.js','mobile/www/nano-multi-count-ui.js',
           'browser-bridge.js','mobile/www/browser-bridge.js','mobile-sync-server.cjs','pc-sync-service.cjs',
           'index.html','mobile/www/index.html','package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changes).issubset(allow),changes
    assert {'nano-multi-count.js','mobile/www/nano-multi-count.js','nano-multi-count-ui.js',
            'mobile/www/nano-multi-count-ui.js','browser-bridge.js','mobile/www/browser-bridge.js',
            'mobile-sync-server.cjs','pc-sync-service.cjs'}.issubset(set(changes))
    for n in ('electron-main.cjs','electron-native-preload.cjs','renderer.js','mobile/www/renderer.js',
              'mega-cloud-backup.cjs','mega-restore-safety.cjs','nano-debt-stats-fix.js','print-engine.js',
              'nano-pricing-offers-168.js','nano-return-plan.js','mobile/www/nano-return-plan.js',
              'nano-transaction-guards.js','nano-stocktake-approval.js','mobile/www/nano-stocktake-approval.js'):
        if n in files and n in original:
            assert files[n][1]==original[n][1],('Protected subsystem mutated',n)
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA
    for n in ('browser-bridge.js','mobile/www/browser-bridge.js','mobile-sync-server.cjs',
              'pc-sync-service.cjs','nano-multi-count.js','nano-multi-count-ui.js'):
        temp=ROOT/('syntax-'+n.replace('/','-'))
        temp.write_bytes(files[n][1])
        subprocess.run(['node','--check',str(temp)],check=True,timeout=30)
    subprocess.run(['node',str(ROOT/'test-multi-count.cjs')],check=True,timeout=30,cwd=ROOT)
    for name in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        tested=ROOT/('integration-'+name.replace('/','-'))
        tested.write_bytes(files[name][1])
        subprocess.run(['node',str(ROOT/'test-multi-bridge.cjs'),
            str(ROOT.parent/'v1.0.65/nano-transaction-guards.js'),
            str(ROOT.parent/'v1.0.66/nano-return-plan.js'),
            str(ROOT.parent/'v1.0.67/nano-stocktake-approval.js'),
            str(ROOT/'nano-multi-count.js'),str(tested)],check=True,timeout=40,cwd=ROOT)
    asar=pack(files)
    verified=unpack(asar)
    assert set(verified)==set(files)
    assert all(verified[k][1]==v for k,(m,v) in files.items())
    assert sha(verified[BUNDLED_APK][1])==BUNDLED_APK_SHA
    with zipfile.ZipFile(ROOT/ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(ROOT/ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={'fileName':ASSET,'sha256':sha((ROOT/ASSET).read_bytes()),'appAsarSha256':sha(asar),
          'sizeBytes':(ROOT/ASSET).stat().st_size,'fromVersion':'1.0.68','toVersion':'1.0.69',
          'changedFiles':changes,'dataFilesModified':False,'mobileApkSha256':BUNDLED_APK_SHA}
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    base=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert base['version']=='1.0.68' and base.get('published') is True
    old=base.get('patches',[])
    from_versions=list(dict.fromkeys((old[0].get('fromVersions',[]) if old else [])+['1.0.68']))
    base['version']='1.0.69'
    base['releaseDate']=date.today().isoformat()
    base['features']=features
    base.setdefault('releaseHistory',{})['1.0.69']={'releaseDate':base['releaseDate'],'features':features}
    base['patches']=[{'id':'nano-pos-v1.0.69-multi-phone-count',
       'fromVersions':from_versions,
       'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.69/'+ASSET,
       'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.69',
       'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
       'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'}]
    base['notes']={'ar':'جرد متزامن من عدة هواتف دون ازدواج المنتجات مع توثيق اسم الجارد لكل جهاز.',
       'fr':'Inventaire simultané multi-téléphones avec attribution par opérateur.',
       'en':'Shared multi-phone count, exclusive product claims and operator audit details.'}
    (ROOT/'nano-pos-update-v169.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
