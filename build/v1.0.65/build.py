#!/usr/bin/env python3
"""Build v1.0.65: financial write validations and removal of false credit-note success."""
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
ASSET = "NANO-POS-Patch-1.0.64-to-1.0.65-FINANCE-SAFETY.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.64/NANO-POS-Patch-1.0.63-to-1.0.64-FINANCIAL-REVIEW.zip"
BASE_SHA = "d2ded1ff6c0fbd08f8396d3ffda04b1e43596d7438037878c6b9de4cb4202457"
BASE_ASAR_SHA = "3bdf3730bf94de9c7235d4cb6bddc89b84d0e4c1644140b1aa1df655bf8e4473"

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
    source=ROOT/'published-v164.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v165-builder'}),timeout=180) as r:
            source.write_bytes(r.read())
    assert sha(source.read_bytes())==BASE_SHA,'Unrecognized NANO POS v1.0.64 archive'
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR_SHA,'Unrecognized v1.0.64 app.asar'
    original=unpack(raw)
    files=dict(original)
    def get(name):
        assert name in original,'Missing file: '+name
        return original[name][1].decode('utf8')
    def put(name,content):
        files[name]=(original[name][0],content.encode('utf8'))

    addon=(ROOT/'nano-transaction-guards.js').read_bytes()
    assert b'NANO_TX_GUARD_165' in addon and b'module.exports=api' in addon
    files['nano-transaction-guards.js']=({},addon)
    files['mobile/www/nano-transaction-guards.js']=({},addon)

    for html in ('index.html','mobile/www/index.html'):
        doc=get(html)
        assert doc.count('src="browser-bridge.js"')==1,html
        assert 'nano-transaction-guards.js' not in doc
        doc=doc.replace('src="browser-bridge.js"',
                        'src="nano-transaction-guards.js"></script>\n  <script src="browser-bridge.js"',1)
        assert doc.index('src="nano-transaction-guards.js"')<doc.index('src="browser-bridge.js"')
        put(html,doc)

    for path in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        src=get(path)
        guard='window.NANO_TX_GUARD_165'
        assert src.count("if (channel === 'issue-credit-note') return { success: true, credit_note_id: ids(), date: new Date().toISOString() };")==1
        src=src.replace("if (channel === 'issue-credit-note') return { success: true, credit_note_id: ids(), date: new Date().toISOString() };",
           "if (channel === 'issue-credit-note') return fail('لا يمكن إصدار مرتجع مالي دون تحديث الفاتورة والمخزون ورصيد الزبون. استخدم الإجراء المعتمد بعد تفعيله.');",1)

        shift_old="""     const summary = caisseSessionSummary(s);
     const closingBalance = rounded(payload.closingBalance ?? payload.closing_balance ?? 0);"""
        shift_new="""     let closingBalance;
     try { closingBalance = window.NANO_TX_GUARD_165.close(s, payload.closingBalance ?? payload.closing_balance); }
     catch (error) { return fail(error.message || 'مبلغ الإغلاق غير صالح'); }
     const summary = caisseSessionSummary(s);"""
        assert src.count(shift_old)==1,('Shift close anchor changed',path)
        src=src.replace(shift_old,shift_new,1)

        stock_anchor="""     if (!rows.length) return fail('لا توجد أصناف للجرد');
     let net = 0, increases = 0, decreases = 0, changedRows = 0;"""
        stock_new="""     if (!rows.length) return fail('لا توجد أصناف للجرد');
     try { window.NANO_TX_GUARD_165.stocktake(db.products, rows); }
     catch (error) { return fail(error.message || 'الجرد يحتوي معلومات غير متزامنة'); }
     let net = 0, increases = 0, decreases = 0, changedRows = 0;"""
        assert src.count(stock_anchor)==1,('Stocktake anchor changed',path)
        src=src.replace(stock_anchor,stock_new,1)

        # The new price quote uses existing recorded retail/wholesale values.
        # It never changes a sale or offers unverified discount/promotion rules.
        price_anchor="""   if (channel === 'get-products') {"""
        quote="""   if (channel === 'nano-quote-product-price') {
     const payload = args[0] || {};
     const p = db.products.find(p => String(p.id) === String(payload.productId));
     try {
       return { success: true, productId: p?.id || null,
         tier: payload.tier === 'wholesale' ? 'wholesale' : 'retail',
         price: window.NANO_TX_GUARD_165.price(p, payload.tier) };
     } catch (error) { return fail(error.message || 'سعر غير صالح'); }
   }
"""
        assert src.count(price_anchor)==1,('Price lookup anchor changed',path)
        src=src.replace(price_anchor,quote+price_anchor,1)

        # Do not call this an immutable audit trail: record reliable shift closure
        # and stocktake posting metadata in the same synchronized business store.
        close_tail="""     s.close_note = payload.closeNote || payload.close_note || '';
     save();"""
        close_audit="""     s.close_note = payload.closeNote || payload.close_note || '';
     db.audit_log = Array.isArray(db.audit_log) ? db.audit_log : [];
     db.audit_log.push({ id: ids(), at: new Date().toISOString(),
       operation: 'close-caisse-session', record_id: s.id, user_id: s.user_id,
       before: {status: 'open', expected_balance: s.expected_balance},
       after: {status: 'closed', closing_balance: s.closing_balance, difference: s.difference} });
     save();"""
        assert src.count(close_tail)==1,('Shift audit anchor missing',path)
        src=src.replace(close_tail,close_audit,1)
        stock_tail="""     db.stocktakes.unshift(st);
     save();"""
        stock_audit="""     db.stocktakes.unshift(st);
     db.audit_log = Array.isArray(db.audit_log) ? db.audit_log : [];
     db.audit_log.push({id: ids(), at: new Date().toISOString(),
       operation: 'create-stocktake', record_id: st.id,
       after: { changed_rows: changedRows, net_difference: rounded(net) }});
     save();"""
        assert src.count(stock_tail)==1,('Stocktake audit anchor missing',path)
        src=src.replace(stock_tail,stock_audit,1)
        audit_anchor="""   if (channel === 'get-stocktakes') return clone(db.stocktakes || []);"""
        assert src.count(audit_anchor)==1
        src=src.replace(audit_anchor,
            "   if (channel === 'nano-get-financial-action-log') return clone((db.audit_log || []).slice(-500));\n"+audit_anchor,1)
        put(path,src)

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.64'
    pkg['version']='1.0.65'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.64'
        lock['version']='1.0.65'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.65'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        config=get('app-config.js')
        changed=config.replace("|| '1.0.64'","|| '1.0.65'")
        assert changed!=config
        put('app-config.js',changed)
    features={
      'ar':[
        'التحقق من إغلاق المناوبة: منع إغلاق مناوبة مغلقة ورفض المبالغ السالبة أو غير الصالحة.',
        'فحص اختلاف كميات الجرد عن المخزون الحالي قبل تطبيق أي تسوية، مع رفض الدفعات المكررة.',
        'إلغاء رسالة النجاح الوهمية عند إنشاء إشعار دائن دون حفظ أثره المالي الفعلي.',
        'إضافة عرض سعر جملة/تجزئة من البيانات المسجلة دون تغيير أسعار الفواتير.',
        'تسجيل بيانات إغلاق المناوبات والجرد الجديد في سجل عمليات محلي؛ لا يُعد سجلًا غير قابل للتعديل.'
      ],
      'fr':[
        'Contrôle de fermeture des caisses et rejet des montants incorrects.',
        'Validation de cohérence et doublons des lots lors de l’inventaire.',
        'Suppression du faux succès des avoirs non enregistrés.',
        'Devis prix de gros/détail en lecture seule et journal local de clôture/inventaire.'
      ],
      'en':[
        'Validate cash shift close status and amounts.',
        'Reject stale inventory counts and duplicate stocktake batches.',
        'Never falsely report unrecorded credit notes as successfully posted.',
        'Read-only wholesale/retail price quotes plus local shift and stocktake events.'
      ]
    }
    if 'release-notes.js' in original:
        notes=get('release-notes.js')
        a=notes.find('const F=');b=notes.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])

    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allow={'nano-transaction-guards.js','mobile/www/nano-transaction-guards.js',
           'browser-bridge.js','mobile/www/browser-bridge.js','index.html','mobile/www/index.html',
           'package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allow),changed
    assert {'nano-transaction-guards.js','mobile/www/nano-transaction-guards.js',
            'browser-bridge.js','mobile/www/browser-bridge.js','index.html','mobile/www/index.html',
            'package.json'}.issubset(set(changed))
    for p in ('electron-main.cjs','electron-native-preload.cjs','renderer.js','mobile/www/renderer.js',
              'mobile-sync-server.cjs','pc-sync-service.cjs','mega-cloud-backup.cjs',
              'mega-restore-safety.cjs','print-engine.js','nano-debt-stats-fix.js'):
        assert files[p][1]==original[p][1],('Protected file changed',p)
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA,'Android APK changed'
    for name in ('browser-bridge.js','mobile/www/browser-bridge.js','nano-transaction-guards.js'):
        temp=ROOT/('syntax-'+name.replace('/','-'))
        temp.write_bytes(files[name][1])
        subprocess.run(['node','--check',str(temp)],check=True,timeout=30)
    subprocess.run(['node',str(ROOT/'test-transaction-guards.cjs')],check=True,timeout=30,cwd=ROOT)
    for path in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        module=ROOT/('integration-'+path.replace('/','-'))
        module.write_bytes(files[path][1])
        subprocess.run(['node',str(ROOT/'test-bridge-live.cjs'),str(module),str(ROOT/'nano-transaction-guards.js')],check=True,timeout=30,cwd=ROOT)
    asar=pack(files)
    check=unpack(asar)
    assert set(check)==set(files)
    assert all(check[name][1]==data for name,(meta,data) in files.items())
    assert sha(check[BUNDLED_APK][1])==BUNDLED_APK_SHA
    archive=ROOT/ASSET
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={'fileName':ASSET,'sha256':sha(archive.read_bytes()),'appAsarSha256':sha(asar),
          'sizeBytes':archive.stat().st_size,'fromVersion':'1.0.64','toVersion':'1.0.65',
          'changedFiles':changed,'dataFilesModified':False,'mobileApkSha256':BUNDLED_APK_SHA}
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.64' and manifest.get('published') is True
    old=manifest.get('patches',[])
    from_versions=list(dict.fromkeys((old[0].get('fromVersions',[]) if old else [])+['1.0.64']))
    manifest['version']='1.0.65'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.65']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{'id':'nano-pos-v1.0.65-finance-safety',
       'fromVersions':from_versions,
       'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.65/'+ASSET,
       'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.65',
       'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
       'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'}]
    manifest['notes']={'ar':'تحقق أكثر أمانًا من إغلاق المناوبات والجرد وأسعار الجملة، مع منع نتيجة مرتجع مالية وهمية.',
                       'fr':'Protections de caisse et inventaire, rejet de fausses confirmations de remboursement.',
                       'en':'Cash/stocktake safety validations and fail-closed unposted credit notes.'}
    (ROOT/'nano-pos-update-v165.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
