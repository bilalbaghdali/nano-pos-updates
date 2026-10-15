#!/usr/bin/env python3
"""Build v1.0.68: opt-in authoritative promotion and wholesale pricing."""
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
ASSET = "NANO-POS-Patch-1.0.67-to-1.0.68-PRICING-OFFERS.zip"
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.67/NANO-POS-Patch-1.0.66-to-1.0.67-STOCKTAKE-APPROVAL.zip"
BASE_SHA = "8b9ac5da6be3c5eca003fe86de3ae5236cc05368db1f8a0ceeb40659d73dd63a"
BASE_ASAR_SHA = "67bcfdbff2c73ed99a0dd69d6885a6fc6c9e8fd6308bff18623a809364ace0fb"

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
    source=ROOT/'published-v167.zip'
    if not source.exists():
        with urllib.request.urlopen(urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-v168-builder'}),timeout=180) as r:
            source.write_bytes(r.read())
    assert sha(source.read_bytes())==BASE_SHA,'Unknown NANO POS v1.0.67 patch archive'
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR_SHA,'Unknown NANO POS v1.0.67 app.asar'
    original=unpack(raw)
    files=dict(original)
    def get(n):
        assert n in original,'Missing entry: '+n
        return original[n][1].decode('utf8')
    def put(n,s):files[n]=(original[n][0],s.encode('utf8'))
    pricing=(ROOT/'nano-pricing.js').read_bytes()
    ui=(ROOT/'nano-pricing-ui.js').read_bytes()
    assert b'NANO_PRICING_168' in pricing and b'module.exports' in pricing
    files['nano-pricing.js']=({},pricing)
    files['mobile/www/nano-pricing.js']=({},pricing)
    files['nano-pricing-ui.js']=({},ui)
    files['mobile/www/nano-pricing-ui.js']=({},ui)
    for path in ('index.html','mobile/www/index.html'):
        s=get(path)
        assert s.count('src="browser-bridge.js"')==1
        s=s.replace('src="browser-bridge.js"',
            'src="nano-pricing.js"></script>\n  <script src="browser-bridge.js"',1)
        assert s.count('</body>')==1
        s=s.replace('</body>','  <script defer src="nano-pricing-ui.js"></script>\n</body>',1)
        assert s.index('src="nano-pricing.js"')<s.index('src="browser-bridge.js"')
        put(path,s)
    for path in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        s=get(path)
        start="const api = async (channel, ...args) => {"
        assert s.count(start)==1,('API initialization missing',path)
        preRoute="""const api = async (channel, ...args) => {
   if (channel === 'process-sale' && args[0] && document.getElementById('nanoApplyOffersToggle')?.checked) {
     args[0]={...args[0],checkout:{...(args[0].checkout||{}),applyOffers:true}};
   }"""
        s=s.replace(start,preRoute,1)
        process="if (channel === 'process-sale') {"
        assert s.count(process)==1,('Checkout anchor changed',path)
        apply="""if (channel === 'process-sale') {
     if (args[0]?.checkout?.applyOffers === true) {
       try {
         const out=window.NANO_PRICING_168.reprice(args[0],db.products,db.promotions||[]);
         args[0]=out.payload;
       } catch(error) { return fail(error.message || 'تعذر تطبيق العروض'); }
     }"""
        s=s.replace(process,apply,1)
        priceAnchor="""   if (channel === 'get-products') {"""
        quote="""   if (channel === 'nano-quote-active-price') {
     const payload=args[0] || {};
     const p=db.products.find(x=>String(x.id)===String(payload.productId));
     try {
       return { success:true, quote:window.NANO_PRICING_168.quote(p,
         payload.quantity,db.promotions||[],payload.tier||'auto') };
     } catch(error){ return fail(error.message || 'تعذر عرض السعر'); }
   }
"""
        assert s.count(priceAnchor)==1,('Pricing lookup anchor changed',path)
        s=s.replace(priceAnchor,quote+priceAnchor,1)
        put(path,s)
    pkg=json.loads(get('package.json'))
    assert pkg['version']=='1.0.67'
    pkg['version']='1.0.68'
    put('package.json',json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    if 'package-lock.json' in original:
        lock=json.loads(get('package-lock.json'))
        assert lock['version']=='1.0.67'
        lock['version']='1.0.68'
        if isinstance(lock.get('packages'),dict) and isinstance(lock['packages'].get(''),dict):
            lock['packages']['']['version']='1.0.68'
        put('package-lock.json',json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    if 'app-config.js' in original:
        cfg=get('app-config.js')
        updated=cfg.replace("|| '1.0.67'","|| '1.0.68'")
        assert updated!=cfg
        put('app-config.js',updated)
    features={
      'ar':[
        'إضافة خيار واضح لتطبيق العروض والسعر بالجملة أثناء البيع عند اختياره فقط.',
        'إعادة حساب إجمالي الفاتورة من أسعار المنتجات والعروض السارية على الكمبيوتر الرئيسي.',
        'التحقق من تاريخ العرض والكمية، واختيار أفضل تخفيض واحد دون جمع تخفيضات متعددة على المنتج.',
        'الإبقاء على طريقة التسعير السابقة دون تغيير عند عدم تفعيل الخيار.'
      ],
      'fr':['Application optionnelle des promotions et prix de gros à la caisse.',
            'Calcul du total sur le PC principal, validation des périodes et quantités, sans cumul des remises.',
            'Comportement de caisse inchangé tant que le mode est désactivé.'],
      'en':['Add explicit opt-in to calculate current promotions and wholesale prices at checkout.',
            'Recompute totals on the authoritative main PC with date and quantity guards.',
            'Use the best promotion only and preserve default legacy pricing unless enabled.']
    }
    if 'release-notes.js' in original:
        notes=get('release-notes.js')
        a=notes.find('const F=');b=notes.find(';',a)
        assert a>=0 and b>a
        put('release-notes.js',notes[:a]+'const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+notes[b:])
    changed=[n for n in files if n not in original or files[n][1]!=original[n][1]]
    allowed={'nano-pricing.js','mobile/www/nano-pricing.js','nano-pricing-ui.js',
             'mobile/www/nano-pricing-ui.js','browser-bridge.js','mobile/www/browser-bridge.js',
             'index.html','mobile/www/index.html','package.json','package-lock.json',
             'app-config.js','release-notes.js'}
    assert set(changed).issubset(allowed),changed
    assert {'nano-pricing.js','mobile/www/nano-pricing.js','nano-pricing-ui.js','mobile/www/nano-pricing-ui.js',
            'browser-bridge.js','mobile/www/browser-bridge.js','index.html','mobile/www/index.html',
            'package.json'}.issubset(set(changed))
    for n in ('electron-main.cjs','electron-native-preload.cjs','pc-sync-service.cjs',
              'mobile-sync-server.cjs','renderer.js','mobile/www/renderer.js','mega-cloud-backup.cjs',
              'mega-restore-safety.cjs','nano-debt-stats-fix.js','print-engine.js',
              'nano-return-plan.js','mobile/www/nano-return-plan.js',
              'nano-stocktake-approval.js','mobile/www/nano-stocktake-approval.js'):
        assert files[n][1]==original[n][1],('Protected subsystem changed',n)
    assert sha(files[BUNDLED_APK][1])==BUNDLED_APK_SHA
    for n in ('browser-bridge.js','mobile/www/browser-bridge.js','nano-pricing.js','nano-pricing-ui.js'):
        dest=ROOT/('check-'+n.replace('/','-'))
        dest.write_bytes(files[n][1])
        subprocess.run(['node','--check',str(dest)],check=True,timeout=30)
    subprocess.run(['node',str(ROOT/'test-pricing.cjs')],check=True,timeout=30)
    for name in ('browser-bridge.js','mobile/www/browser-bridge.js'):
        t=ROOT/('integration-'+name.replace('/','-'))
        t.write_bytes(files[name][1])
        subprocess.run(['node',str(ROOT/'test-pricing-bridge.cjs'),str(t),
                        str(ROOT.parent/'v1.0.65/nano-transaction-guards.js'),
                        str(ROOT.parent/'v1.0.66/nano-return-plan.js'),
                        str(ROOT.parent/'v1.0.67/nano-stocktake-approval.js'),
                        str(ROOT/'nano-pricing.js')],check=True,timeout=45,cwd=ROOT)
    asar=pack(files)
    verified=unpack(asar)
    assert set(verified)==set(files)
    assert all(verified[n][1]==v for n,(meta,v) in files.items())
    assert sha(verified[BUNDLED_APK][1])==BUNDLED_APK_SHA
    out=ROOT/ASSET
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',asar)
    with zipfile.ZipFile(out) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    meta={'fileName':ASSET,'sha256':sha(out.read_bytes()),'appAsarSha256':sha(asar),
          'sizeBytes':out.stat().st_size,'fromVersion':'1.0.67','toVersion':'1.0.68',
          'changedFiles':changed,'dataFilesModified':False,'mobileApkSha256':BUNDLED_APK_SHA}
    (ROOT/'build-result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    manifest=json.loads((REPO/'nano-pos-update.json').read_text('utf8'))
    assert manifest['version']=='1.0.67' and manifest.get('published') is True
    old=manifest.get('patches',[])
    from_versions=list(dict.fromkeys((old[0].get('fromVersions',[]) if old else [])+['1.0.67']))
    manifest['version']='1.0.68'
    manifest['releaseDate']=date.today().isoformat()
    manifest['features']=features
    manifest.setdefault('releaseHistory',{})['1.0.68']={'releaseDate':manifest['releaseDate'],'features':features}
    manifest['patches']=[{'id':'nano-pos-v1.0.68-pricing-offers',
       'fromVersions': from_versions,
       'directUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.68/'+ASSET,
       'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.68',
       'sha256':meta['sha256'],'appAsarSha256':meta['appAsarSha256'],
       'fileName':ASSET,'sizeBytes':meta['sizeBytes'],'payloadType':'app-asar'}]
    manifest['notes']={'ar':'قواعد جملة وعروض اختيارية في البيع مع إعادة حساب الإجمالي على الكمبيوتر الرئيسي.',
       'fr':'Prix de gros et promotions optionnels validés sur le PC principal.',
       'en':'Opt-in promotion and wholesale pricing checked on primary PC.'}
    (ROOT/'nano-pos-update-v168.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
