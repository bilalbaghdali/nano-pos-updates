#!/usr/bin/env python3
"""Build v1.0.66: implement verified ledger-safe sale return posting."""
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
ASSET = "NANO-POS-Patch-1.0.65-to-1.0.66-SALE-RETURNS.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.65/NANO-POS-Patch-1.0.64-to-1.0.65-FINANCE-SAFETY.zip"
BASE_SHA = "4b0109bbf5de2a9fff3c3080a0aab132e4a3f4e9456c78a8e677bbb03372afbf"
BASE_ASAR_SHA = "a13c00f987b324decbb356c2949e7c3ef3f81cfa6cd285e0f41b9c374a524489"

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
    source=ROOT/'published-v165.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v166-builder'}),timeout=180) as r:
            source.write_bytes(r.read())
    assert sha(source.read_bytes())==BASE_SHA,'Unexpected v1.0.65 patch checksum'
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR_SHA,'Unexpected app.asar checksum'
    original=unpack(raw)
    files=dict(original)
    def get(n):
        assert n in original,'Required application entry missing: '+n
        return original[n][1].decode('utf8')
    def put(n,v):
        files[n]=(original[n][0],v.encode('utf8'))

    addon=(ROOT/'nano-return-plan.js').read_bytes()
    assert b'NANO_RETURN_PLAN_166' in addon and b'function post(' in addon
    files['nano-return-plan.js']=({},addon)
    files['mobile/www/nano-return-plan.js']=({},addon)
    ui=(ROOT/'nano-return-ui.js').read_bytes()
    files['nano-return-ui.js']=({},ui)
    files['mobile/www/nano-return-ui.js']=({},ui)
    for path in ('index.html','mobile/www/index.html'):
        html=get(path)
        assert html.count('src="browser-bridge.js"')==1
        assert 'nano-return-plan.js' not in html
        html=html.replace('src="browser-bridge.js"',
                          'src="nano-return-plan.js"></script>\n  <script src="browser-bridge.js"',1)
        assert html.index('src="nano-return-plan.js"')<html.index('src="browser-bridge.js"')
        assert html.count('</body>')==1
        html=html.replace('</body>','<script defer src="nano-return-ui.js"></script>\n</body>',1)
        put(path,html)

    for path in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        src=get(path)
        old="if (channel === 'issue-credit-note') return fail('لا يمكن إصدار مرتجع مالي دون تحديث الفاتورة والمخزون ورصيد الزبون. استخدم الإجراء المعتمد بعد تفعيله.');"
        assert src.count(old)==1,('Credit-note handler changed',path)
        handler="""if (channel === 'issue-credit-note') {
     const payload=args[0] || {};
     let logged=null;
     try { logged=JSON.parse(localStorage.getItem('pos_current_user') || 'null'); } catch {}
     if (!logged || String(logged.id) !== String(payload.userId)) return fail('يجب تسجيل الدخول بالحساب المخول لاعتماد المرتجع');
     try {
       const prepared=window.NANO_RETURN_PLAN_166.post(db,payload,logged.id);
       if (prepared.result.alreadyProcessed) return clone(prepared.result);
       const previous=db;
       db=prepared.next;
       save();
       const persisted=JSON.parse(localStorage.getItem(KEY) || '{}');
       if (!(persisted.sales_returns || []).some(r=>r.request_id===payload.requestId)) {
         db=previous;
         return fail('فشل الحفظ الذري للمرتجع؛ لم يتم اعتماد العملية');
       }
       return clone(prepared.result);
     } catch (error) {
       return fail(error?.message || 'تعذر تسجيل المرتجع');
     }
   }
   if (channel === 'get-sales-returns') {
     const saleId=args[0]?.saleId ?? args[0] ?? null;
     return clone((db.sales_returns || []).filter(x=>saleId==null||String(x.sale_id)===String(saleId)));
   }"""
        src=src.replace(old,handler,1)
        # The purchase/sales authorization check must include credit-note writes.
        oldrx="(add-|update-|delete-|save-|process-|create-|confirm-|reverse-|set-|toggle-|import-|reset-|open-caisse|close-caisse)"
        if oldrx in src:
            src=src.replace(oldrx,"(issue-credit-note|add-|update-|delete-|save-|process-|create-|confirm-|reverse-|set-|toggle-|import-|reset-|open-caisse|close-caisse)",1)
        else:
            assert path.startswith('mobile/'),('License write guard changed',path)

        originalCost="const cogs = rounded(sales.reduce((sum, v) => sum + (v.items || []).reduce((n, i) => n + Number(i.cost_price || 0) * Number(i.quantity || 0), 0), 0));"
        updatedCost="const cogs = rounded(sales.reduce((sum, v) => sum + (v.items || []).reduce((n, i, index) => n + Number(i.cost_price || 0) * Math.max(0, Number(i.quantity || 0)-Number(v.returned_by_index?.[index] || 0)), 0), 0));"
        assert src.count(originalCost)==1,('Analytics cost calculation changed',path)
        src=src.replace(originalCost,updatedCost,1)
        originalStats="sales: { revenue, net_revenue: revenue, returns_value: 0, returns_count: 0, total_sales_count: sales.length }"
        updatedStats="""sales: { revenue, net_revenue: revenue,
         returns_value: rounded((db.sales_returns || []).filter(r=>inDateRange(r.created_at,f)).reduce((n,r)=>n+Number(r.credit_amount||0),0)),
         returns_count: (db.sales_returns || []).filter(r=>inDateRange(r.created_at,f)).length,
         total_sales_count: sales.length }"""
        assert src.count(originalStats)==1,('Returns analytics anchor changed',path)
        src=src.replace(originalStats,updatedStats,1)
        details="payments: clone(s.payments || []), customer: db.customers.find(v => v.id == s.customer_id) || null"
        assert src.count(details)==1,('Sale details missing',path)
        src=src.replace(details,"payments: clone(s.payments || []), returns: clone((db.sales_returns || []).filter(r=>String(r.sale_id)===String(s.id))), customer: db.customers.find(v => v.id == s.customer_id) || null",1)
        put(path,src)

    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.65'
    pkg['version']='1.0.66'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.65'
        lock['version']='1.0.66'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.66'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        config=get('app-config.js')
        updated=config.replace("|| '1.0.65'","|| '1.0.66'")
        assert updated!=config
        put('app-config.js',updated)
    features={
       'ar':[
         'تسجيل مرتجعات البيع جزئيًا أو كليًا مع ربط الفاتورة والدفعة الأصلية.',
         'تخفيض دين الزبون أولاً ثم رد المبلغ المتبقي نقدًا من المناوبة المفتوحة للمستخدم المخوّل.',
         'منع تكرار المرتجع باستعمال معرّف العملية ومنع استرجاع كمية أكبر من الكمية المباعة.',
         'تعديل تكلفة البضاعة المباعة وإظهار قيمة وعدد المرتجعات في التحليلات.',
         'الإبقاء على البيانات والتفعيل والمزامنة دون تغيير؛ إجراءات الاستبدال والعروض والجرد المعتمد للهاتف ما زالت تحتاج اختبارًا مستقلاً.'
       ],
       'fr':['Retours de vente tracés par facture, ligne et lot, y compris les remboursements partiels.',
             'Réduction de la dette puis remboursement en caisse avec identifiant anti-doublon.',
             'Statistiques et coût des marchandises ajustés pour les quantités retournées.',
             'Données et licences conservées; échanges et inventaires mobile encore à valider.'],
       'en':['Post sale returns by original invoice and stock batch with idempotent request identifiers.',
             'Apply debt reduction before cash refunds, requiring an active authorized cashier shift.',
             'Recalculate cost of sold goods after returned quantities and show return totals.',
             'Data and licensing preserved; exchanges, complex promotions and APK stocktake approval pending.']
    }
    if 'release-notes.js' in original:
        note=get('release-notes.js')
        a=note.find('const F=');b=note.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',note[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+note[b:])

    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allowed={'nano-return-plan.js','mobile/www/nano-return-plan.js','nano-return-ui.js','mobile/www/nano-return-ui.js',
             'browser-bridge.js','mobile/www/browser-bridge.js','index.html','mobile/www/index.html',
             'package.json','package-lock.json','app-config.js','release-notes.js'}
    assert set(changed).issubset(allowed),changed
    assert {'nano-return-plan.js','mobile/www/nano-return-plan.js','browser-bridge.js','mobile/www/browser-bridge.js','index.html','mobile/www/index.html','package.json'}.issubset(set(changed))
    for n in ('electron-main.cjs','electron-native-preload.cjs','renderer.js','mobile/www/renderer.js',
              'mobile-sync-server.cjs','pc-sync-service.cjs','mega-cloud-backup.cjs','mega-restore-safety.cjs',
              'nano-debt-stats-fix.js','print-engine.js','nano-transaction-guards.js','mobile/www/nano-transaction-guards.js'):
        assert original[n][1]==files[n][1],('Protected subsystem unexpectedly modified',n)
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA
    for name in ('browser-bridge.js','mobile/www/browser-bridge.js','nano-return-plan.js','nano-return-ui.js'):
        t=ROOT/('check-'+name.replace('/','-'))
        t.write_bytes(files[name][1])
        subprocess.run(['node','--check',str(t)],check=True,timeout=30)
    subprocess.run(['node',str(ROOT/'test-return-plan.cjs')],check=True,timeout=30,cwd=ROOT)
    for name in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        t=ROOT/('integration-'+name.replace('/','-'))
        t.write_bytes(files[name][1])
        subprocess.run(['node',str(ROOT/'test-return-bridge.cjs'),str(t),
                        str(ROOT.parent/'v1.0.65/nano-transaction-guards.js'),
                        str(ROOT/'nano-return-plan.js')],check=True,timeout=45,cwd=ROOT)
    asar=pack(files)
    verified=unpack(asar)
    assert set(verified)==set(files)
    assert all(verified[k][1]==v for k,(m,v) in files.items())
    assert sha(verified[BUNDLED_APK][1])==BUNDLED_APK_SHA
    archive=ROOT/ASSET
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={'fileName':ASSET,'sha256':sha(archive.read_bytes()),'appAsarSha256':sha(asar),
          'sizeBytes':archive.stat().st_size,'fromVersion':'1.0.65','toVersion':'1.0.66',
          'changedFiles':changed,'dataFilesModified':False,'mobileApkSha256':BUNDLED_APK_SHA}
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    base=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert base['version']=='1.0.65' and base.get('published') is True
    previous=base.get('patches',[])
    sources=list(dict.fromkeys((previous[0].get('fromVersions',[]) if previous else [])+['1.0.65']))
    base['version']='1.0.66'
    base['releaseDate']=date.today().isoformat()
    base['features']=features
    base.setdefault('releaseHistory',{})['1.0.66']={'releaseDate':base['releaseDate'],'features':features}
    base['patches']=[{'id':'nano-pos-v1.0.66-sale-returns',
        'fromVersions':sources,
        'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.66/'+ASSET,
        'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.66',
        'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
        'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'}]
    base['notes']={'ar':'مرتجعات البيع الموثقة مع تصحيح الديون والمخزون وتكلفة المبيعات.',
                   'fr':'Retours clients contrôlés avec gestion des dettes et du stock.',
                   'en':'Controlled partial or full returns with accounting and inventory entries.'}
    (ROOT/'nano-pos-update-v166.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
