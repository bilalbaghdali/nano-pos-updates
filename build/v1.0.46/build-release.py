#!/usr/bin/env python3
"""Build NANO POS v1.0.46 from verified public 1.0.45 artifact.

Only changes the scoped-search UI, existing product suggestion global-search hook,
version display, and release highlights; never touches business data or security.
"""
import hashlib,json,pathlib,re,struct,subprocess,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_URL='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.45/NANO-POS-Patch-1.0.44-to-1.0.45-ACTUAL-LOGIN-FIX.zip'
BASE_ZIP_SHA='d78ced6ff90b8df547bf44aaf5e7c5863a3abc62fa0f37f8bd855e0d6f7ac708'
BASE_ASAR_SHA='9496a1382a8db8bddaa7cb24fd43bcf1ef5b577a50bab44c0c40844882386c03'
SEARCH_SHA='312c16d058c30a3ac39e5ac192d902617c5c38ad8275ff25afd0df10ed44a2b8'
ASSET='NANO-POS-Patch-1.0.45-to-1.0.46-SECTION-SEARCH.zip'
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(raw):
    length=struct.unpack_from('<I',raw,12)[0]
    header=json.loads(raw[16:16+length]);start=8+struct.unpack_from('<I',raw,4)[0];out={}
    def walk(node,path=''):
        for name,meta in node.get('files',{}).items():
            rel=path+name
            if 'files' in meta:walk(meta,rel+'/')
            else:
                pos=start+int(meta['offset']);size=meta['size'];blob=raw[pos:pos+size]
                assert len(blob)==size,'Corrupt original ASAR '+rel
                out[rel]=(meta,blob)
    walk(header);return out
def pack(files):
    header={'files':{}};blobs=[];offset=0
    for path,(old,blob) in files.items():
        node=header;parts=path.split('/')
        for part in parts[:-1]:node=node['files'].setdefault(part,{'files':{}})
        meta={'size':len(blob),'offset':str(offset)}
        if 'integrity' in old:
            bs=old['integrity'].get('blockSize',4194304)
            meta['integrity']={'algorithm':'SHA256','hash':sha(blob),'blockSize':bs,'blocks':[sha(blob[i:i+bs]) for i in range(0,len(blob),bs)]}
        node['files'][parts[-1]]=meta;blobs.append(blob);offset+=len(blob)
    s=json.dumps(header,ensure_ascii=False,separators=(',',':')).encode();pad=(len(s)+3)&~3
    return struct.pack('<IIII',4,pad+8,pad+4,len(s))+s+b'\0'*(pad-len(s))+b''.join(blobs)
def main():
    base=pathlib.Path('base-v145.zip')
    if not base.exists():
        req=urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-1.0.46-build'})
        with urllib.request.urlopen(req,timeout=180) as response:base.write_bytes(response.read())
    assert sha(base.read_bytes())==BASE_ZIP_SHA,'Wrong predecessor ZIP SHA-256'
    with zipfile.ZipFile(base) as z:asar=z.read('payload/app.asar')
    assert sha(asar)==BASE_ASAR_SHA,'Wrong predecessor app.asar SHA-256'
    files=parse(asar);before={k:b for k,(_,b) in files.items()}
    required={'index.html','nano-v140-smart-lookup.js','package.json','app-config.js','release-notes.js','renderer.js','browser-ui.js','electron-main.cjs'}
    assert required<=set(files), f'Missing predecessor module(s): {required-set(files)}'
    content=(ROOT/'nano-v146-section-search.js').read_bytes()
    assert sha(content)==SEARCH_SHA,'Search logic not reviewed/verified'
    subprocess.run(['node','--check',str(ROOT/'nano-v146-section-search.js')],check=True,timeout=25)
    html=before['index.html'].decode('utf8')
    assert html.count('id="globalSearch"')==1,'Unexpected global search markup'
    assert html.count('</body>')==1 and 'nano-v146-section-search.js' not in html
    html=html.replace('</body>','<script src="nano-v146-section-search.js"></script>\n</body>',1)
    auto=before['nano-v140-smart-lookup.js'].decode('utf8')
    assert "'posProductSearchInput','globalSearch','inventorySearch'" in auto,'Unexpected product suggestion source'
    auto=auto.replace("'posProductSearchInput','globalSearch','inventorySearch'","'posProductSearchInput','inventorySearch'",1)
    pkg=json.loads(before['package.json']);assert pkg['version']=='1.0.45','Expected source 1.0.45'
    pkg['version']='1.0.46'
    config=before['app-config.js'].decode('utf8')
    assert "'1.0.45'" in config,'Version fallback marker missing'
    config=config.replace("'1.0.45'","'1.0.46'")
    notes=before['release-notes.js'].decode('utf8')
    features={
      'ar':['البحث في القسم المفتوح بدل البحث عن المنتجات في جميع الأقسام.','تصفية الموردين والزبائن والمنتجات مباشرة من شريط البحث العلوي.','البحث داخل السجلات المعروضة للفواتير والطلبيات والحزم والعروض والتقارير والمستخدمين.','البحث داخل خيارات الأقسام الأخرى، مع إعادة ضبط البحث تلقائيًا عند الانتقال إلى قسم مختلف.'],
      'fr':['La recherche principale cible désormais la rubrique ouverte.','Recherche directe parmi les fournisseurs, clients et articles de la rubrique courante.','Filtrage des lignes affichées pour les factures, commandes, lots, promotions, rapports et utilisateurs.','Recherche des options dans les autres rubriques, réinitialisée au changement de page.'],
      'en':['Top search is scoped to the currently open section.','Search suppliers, customers and products directly from the top search bar.','Filter displayed records in invoices, orders, bundles, promotions, reports and users.','Find settings and options within other sections; reset search when switching sections.']}
    replacement='const F='+json.dumps(features,ensure_ascii=False,separators=(',',':'))+';let R='
    notes,n=re.subn(r'const F=\{.*?\};let R=',lambda _:replacement,notes,count=1,flags=re.S)
    assert n==1,'Unsupported release note shape'
    update={
      'index.html':html.encode(), 'nano-v140-smart-lookup.js':auto.encode(),
      'nano-v146-section-search.js':content,
      'package.json':(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(),
      'app-config.js':config.encode(), 'release-notes.js':notes.encode()
    }
    for path,payload in update.items():
        if path in files:files[path]=(files[path][0],payload)
        else:files[path]=({},payload)
    for name in ['nano-v140-smart-lookup.js','app-config.js','release-notes.js']:
        p=ROOT/('check-'+name);p.write_bytes(update[name]);subprocess.run(['node','--check',str(p)],check=True,timeout=25)
    rebuilt=pack(files);verified=parse(rebuilt)
    for key,b in update.items():assert verified[key][1]==b, 'Patch file content mismatch '+key
    for key in ['renderer.js','browser-ui.js','electron-main.cjs','license-access.js','mega-cloud-backup.cjs']:
        if key in before:assert verified[key][1]==before[key], 'Sensitive file modified: '+key
    assert 'node_modules/megajs/package.json' in verified,'MEGA backup dependencies lost'
    with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',rebuilt)
    with zipfile.ZipFile(ASSET) as z:assert z.testzip() is None and z.namelist()==['payload/app.asar']
    output={'version':'1.0.46','fromVersion':'1.0.45','fileName':ASSET,'sha256':sha(pathlib.Path(ASSET).read_bytes()),'appAsarSha256':sha(rebuilt),'sizeBytes':pathlib.Path(ASSET).stat().st_size,'changedFiles':sorted(update)}
    pathlib.Path('build-result.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=='__main__':main()