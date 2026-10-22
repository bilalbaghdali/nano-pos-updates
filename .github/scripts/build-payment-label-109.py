#!/usr/bin/env python3
"""NANO POS 1.0.109: fix untranslated payment amount label, preserving all sales code."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda x:hashlib.sha256(x).hexdigest()
SOURCE_ASAR="16ad741ad25e13a766d060d3990e04a17ca50de21147f4c11272032228952907"
OLD='data-i18n="nano_received_amount_108">المبلغ الذي قدمه الزبون (د.ج)</label>'
NEW='>المبلغ المدفوع</label>'
def only(s,needle,repl):
    assert s.count(needle)==1,("unexpected_source_version_or_count",needle,s.count(needle))
    return s.replace(needle,repl)
def change_notes(s):
    s=only(s,"const FALLBACK_VERSION = '1.0.108';","const FALLBACK_VERSION = '1.0.109';")
    a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
    return s[:a]+"""  const OFFLINE = {
    ar:['تحسينات: تصحيح عنوان مبلغ الدفع إلى «المبلغ المدفوع» في شاشة البيع.',
        'إزالة مفتاح الترجمة غير المعرف nano_received_amount_108 حتى لا يظهر مكان النص.',
        'الحفاظ على الكريدي الجزئي والصرف النقدي والفواتير والبيانات دون أي تغيير في الحسابات.'],
    fr:['Correction du libellé du montant versé à la caisse.',
        'Suppression d’une clé de traduction non définie visible à l’écran.',
        'Paiements partiels, monnaie à rendre, factures et données conservés.'],
    en:['Fix checkout payment amount label instead of displaying a missing translation key.',
        'Remove undefined nano_received_amount_108 translation marker.',
        'Preserve existing partial credit, change calculations and transaction records.']
  };
"""+s[b:]
def build(source,output,work):
    with zipfile.ZipFile(source) as z:
        assert z.namelist()==['payload/app.asar']
        original=z.read('payload/app.asar')
    assert sha(original)==SOURCE_ASAR,'This must be based on official v1.0.108'
    magic,block,headsize,n=struct.unpack_from('<4I',original)
    assert magic==4 and block==headsize+4
    header=json.loads(original[16:16+n])
    entries=[]
    def scan(node,prefix=''):
        for name,e in node.get('files',{}).items():
            if 'files' in e: scan(e,prefix+name+'/')
            elif 'offset' in e: entries.append((prefix+name,e))
    scan(header);assert len(entries)>200
    entries.sort(key=lambda v:int(v[1]['offset']))
    start=8+block;payload=bytearray();modified=set()
    for name,e in entries:
        raw=original[start+int(e['offset']):start+int(e['offset'])+e['size']]
        assert len(raw)==e['size']
        updated=raw
        if name=='index.html':
            text=raw.decode('utf-8')
            text=only(text,OLD,NEW)
            assert 'nano_received_amount_108' not in text
            assert 'id="nanoTenderAmount108"' in text
            assert 'id="nanoFlexibleSummary108"' in text
            updated=text.encode('utf-8');modified.add(name)
        elif name=='package.json':
            text=raw.decode('utf-8')
            assert json.loads(text)['version']=='1.0.108'
            updated=only(text,'"version": "1.0.108"','"version": "1.0.109"').encode('utf-8');modified.add(name)
        elif name=='release-notes.js':
            updated=change_notes(raw.decode('utf-8')).encode('utf-8');modified.add(name)
        e['offset']=str(len(payload));e['size']=len(updated)
        if name in modified and 'integrity' in e:
            integrity=e['integrity'];integrity['hash']=sha(updated)
            stride=int(integrity.get('blockSize',4194304))
            integrity['blocks']=[sha(updated[i:i+stride]) for i in range(0,len(updated),stride)]
        payload.extend(updated)
        if name in modified or name in ['browser-bridge.js','nano-flex-core-108.js','nano-flex-payment-108.js','nano-cash-plan-106.js','nano-payment-ledger-102.js','nano-payment-quality-105.js','nano-credit-picker-107.js']:
            p=work/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(updated)
    assert modified=={'index.html','package.json','release-notes.js'}
    metadata=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    padded=(len(metadata)+7)&~3
    final=struct.pack('<4I',4,padded+4,padded,len(metadata))+metadata+b'\0'*(padded-4-len(metadata))+payload
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('payload/app.asar',final)
    with zipfile.ZipFile(output) as z:assert sha(z.read('payload/app.asar'))==sha(final)
    print(json.dumps({'version':'1.0.109','changed':sorted(modified),'asar_sha256':sha(final),'zip_sha256':sha(output.read_bytes())}))
if __name__=='__main__':
    source,output,work=map(Path,sys.argv[1:4]);work.mkdir(parents=True,exist_ok=True);build(source,output,work)
