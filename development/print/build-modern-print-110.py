#!/usr/bin/env python3
"""Build v1.0.110 NANO POS unified invoice/receipt design on verified official 1.0.109.
Only print-center, index loader, release notes and version change; user data untouched.
"""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
H=lambda v:hashlib.sha256(v).hexdigest()
BASE="5f4d6fcd36fa1dee73297e808e4133ceededbf0aa32921a0323fffee9ac0017a"
def once(src,old,new):
    count=src.count(old)
    assert count==1,("source_drift",old[:160],count)
    return src.replace(old,new)
def patch_center(src):
    src=once(src,"const PAPER={A4:{label:'A4',width:210,height:297},A5:{label:'A5',width:148,height:210},R80:{label:'80mm',width:80,height:297},R58:{label:'58mm',width:58,height:297}};",
             "const PAPER={A4:{label:'A4',width:210,height:297},A5:{label:'A5',width:148,height:210},R80:{label:'80mm',width:80,height:297},R80D:{label:'80mm مفصل',width:80,height:297},R58:{label:'58mm',width:58,height:297}};")
    src=once(src,"const prefKey=k=>'nano.print.center.v135.'+k;",
             "PF.ar.blue='تصميم NANO POS الأزرق';PF.fr.blue='NANO POS bleu moderne';PF.en.blue='NANO POS Modern Blue';\nconst prefKey=k=>'nano.print.center.v135.'+k;")
    src=once(src,"template:localStorage.getItem(prefKey(kind+'.template'))||'classic'",
             "template:localStorage.getItem(prefKey(kind+'.skin110'))?(localStorage.getItem(prefKey(kind+'.template'))||'blue110'):(kind==='p'?'classic':'blue110')")
    src=once(src,"template:'classic',footer:''","template:kind==='p'?'classic':'blue110',footer:''")
    src=once(src,"localStorage.setItem(prefKey(kind+'.template'),p.template||'classic');",
             "localStorage.setItem(prefKey(kind+'.template'),p.template||'blue110');localStorage.setItem(prefKey(kind+'.skin110'),'1');")
    src=once(src,"function decorate(h,l,paper,color,template='classic',footer=''){",
             "function decorate(h,l,paper,color,template='classic',footer='',scope='other'){")
    src=once(src," h=applyPaper(h,paper,color);",
             """ if(template==='blue110'&&(scope==='sale'||scope==='receipt')){
   if(!window.NANO_BLUE_PRINT_110?.render)throw Error('NANO POS 110 print layout is missing');
   h=window.NANO_BLUE_PRINT_110.render(h,{paper:paper,language:l,color:color,scope:scope});
 }
 h=applyPaper(h,paper,color);""")
    src=once(src,"function show({html,kind='i',language,onLanguageChange,print,pdf}){",
             "function show({html,kind='i',language,onLanguageChange,print,pdf,scope=null}){")
    src=once(src,"let L=lang(html,language),raw=String(html||''),t=0;close();",
             """let L=lang(html,language),raw=String(html||''),t=0;
  scope=scope||(kind==='r'?'receipt':kind==='i'&&/فاتورة بيع|facture de vente|sales invoice/i.test(raw)?'sale':'other');
  close();""")
    src=once(src,"[['classic',styleText.classic],['modern',styleText.modern],['compact',styleText.compact]]",
             "[['blue110',styleText.blue],['classic',styleText.classic],['modern',styleText.modern],['compact',styleText.compact]]")
    src=once(src,"frame.srcdoc=decorate(raw,L,p.paper,p.color,p.template,p.footer)",
             "frame.srcdoc=decorate(raw,L,p.paper,p.color,p.template,p.footer,scope)")
    # Fix previous pre-v1.0.110 divergence: preview used selected template/footer,
    # print/PDF dropped both and sent undecorated styles.
    old="const p=state(),H=decorate(raw,L,p.paper,p.color),size=PAPER[p.paper]||PAPER.A4;"
    new="const p=state(),H=decorate(raw,L,p.paper,p.color,p.template,p.footer,scope),size=PAPER[p.paper]||PAPER.A4;"
    assert src.count(old)==2,("unexpected_preview_print_pdf_paths",src.count(old))
    src=src.replace(old,new)
    src=once(src,"return show({html:h,kind:k,language:l,onLanguageChange:",
             "return show({html:h,kind:k,scope:k==='r'?'receipt':a[0]==='sale'?'sale':'other',language:l,onLanguageChange:")
    assert "R80D:{label:" in src
    return src
def patch_notes(src):
    src=once(src,"const FALLBACK_VERSION = '1.0.109';","const FALLBACK_VERSION = '1.0.110';")
    a=src.index("  const OFFLINE = {")
    b=src.index("  const TITLES = {",a)
    return src[:a]+"""  const OFFLINE = {
    ar:['اعتماد تصميم أزرق وأبيض عصري متناسق للفواتير والوصول على 58 مم و80 مم و80 مم مفصل وA4 وA5.',
        'ألوان NANO POS مع إبراز المجموع والمبلغ المدفوع والصرف والدين بحسب المستند الأصلي.',
        'الاحتفاظ ببيانات البائع والزبون والمنتجات والمبالغ والباركود/QR، مع إزالة صور المنتجات.',
        'توحيد تصميم معاينة الطباعة والمخرجات الفعلية للطابعة وPDF، مع الحفاظ على اختيار اللغة.'],
    fr:['Nouvelle présentation bleue NANO POS pour factures et tickets : 58, 80, 80 détaillé, A4 et A5.',
        'Totaux mis en valeur et QR/code-barres conservés, sans photos des produits.',
        'Aperçu identique au document imprimé et au PDF, avec choix de langue.'],
    en:['Adopt NANO POS blue and white invoice/receipt look for 58mm, 80mm, 80mm detailed, A4 and A5.',
        'Highlight totals while preserving product lines, barcodes and QR, without product photos.',
        'Use the same layout in preview, print and PDF with the existing language selector.']
  };
"""+src[b:]
def build(source,out,work):
    with zipfile.ZipFile(source) as z:
        assert z.namelist()==['payload/app.asar']
        original=z.read('payload/app.asar')
    assert H(original)==BASE,'Base v1.0.109 ASAR mismatch'
    magic,block,hs,n=struct.unpack_from('<4I',original)
    assert magic==4 and block==hs+4
    tree=json.loads(original[16:16+n]);start=8+block
    assert 'nano-blue-print-110.js' not in tree['files']
    members=[]
    def walk(node,prefix=''):
        for name,e in node.get('files',{}).items():
            if 'files' in e:walk(e,prefix+name+'/')
            elif 'offset' in e:members.append((prefix+name,e))
    walk(tree);assert len(members)>200
    members.sort(key=lambda x:int(x[1]['offset']))
    data=bytearray();changed=set()
    for name,e in members:
        blob=original[start+int(e['offset']):start+int(e['offset'])+e['size']]
        assert len(blob)==e['size']
        if name=='index.html':
            s=blob.decode('utf8')
            s=once(s,'<script src="document-print-preview.js"></script>',
                   '<script src="nano-blue-print-110.js"></script>\\n    <script src="document-print-preview.js"></script>')
            # Ensure actual line break in output, rather than literal escaped newline.
            s=s.replace('src="nano-blue-print-110.js"></script>\\n    <script',
                        'src="nano-blue-print-110.js"></script>\n    <script')
            blob=s.encode('utf8');changed.add(name)
        elif name=='document-print-preview.js':
            blob=patch_center(blob.decode('utf8')).encode('utf8');changed.add(name)
        elif name=='release-notes.js':
            blob=patch_notes(blob.decode('utf8')).encode('utf8');changed.add(name)
        elif name=='package.json':
            s=blob.decode('utf8');assert json.loads(s)['version']=='1.0.109'
            blob=once(s,'"version": "1.0.109"','"version": "1.0.110"').encode('utf8');changed.add(name)
        e['offset']=str(len(data));e['size']=len(blob)
        if name in changed and 'integrity' in e:
            integrity=e['integrity'];integrity['hash']=H(blob)
            size=int(integrity.get('blockSize',4194304))
            integrity['blocks']=[H(blob[i:i+size]) for i in range(0,len(blob),size)]
        data.extend(blob)
        if name in changed or name in ('invoice_template_modern.html','receipt_template_1.html','receipt_template_2.html','invoice_thermal_modern_80.html','browser-bridge.js'):
            dst=work/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(blob)
    assert changed=={'index.html','document-print-preview.js','release-notes.js','package.json'}
    name='nano-blue-print-110.js'
    blob=Path('development/print/'+name).read_bytes()
    tree['files'][name]={'size':len(blob),'offset':str(len(data)),
        'integrity':{'algorithm':'SHA256','hash':H(blob),'blockSize':4194304,'blocks':[H(blob)]}}
    data.extend(blob);(work/name).write_bytes(blob)
    header=json.dumps(tree,separators=(',',':'),ensure_ascii=False).encode('utf8')
    pad=(len(header)+7)&~3
    result=struct.pack('<4I',4,pad+4,pad,len(header))+header+b'\0'*(pad-4-len(header))+data
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('payload/app.asar',result)
    with zipfile.ZipFile(out) as z: assert H(z.read('payload/app.asar'))==H(result)
    print(json.dumps({'version':'1.0.110','changed':sorted(changed),'added':name,'asar_sha256':H(result),'zip_sha256':H(out.read_bytes())}))
if __name__=='__main__':
    a,b,c=map(Path,sys.argv[1:4]);c.mkdir(parents=True,exist_ok=True);build(a,b,c)
