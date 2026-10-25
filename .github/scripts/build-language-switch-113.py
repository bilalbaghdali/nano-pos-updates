#!/usr/bin/env python3
"""Build NANO POS 1.0.113 from the checksum-verified 1.0.112 ASAR."""
import hashlib, json, re, struct, sys, zipfile
from pathlib import Path
sha = lambda b: hashlib.sha256(b).hexdigest()
BASE_ZIP_SHA = 'b8811644f4f51548b2a03aafe93123c2434035ddedec3bc2004440adfdd646ee'
BASE_ASAR_SHA = '5cb8bb257734fc16980468c14f91b0d12a83f4ca45fa1dd5dcc0860fa1c8fee5'
REMOVE = {'nano-operations-center.js', 'nano-financial-review.js'}
def one(text, old, new):
    count = text.count(old)
    assert count == 1, (old[:120], count)
    return text.replace(old, new, 1)
def update_notes(text):
    text = one(text, "const FALLBACK_VERSION = '1.0.112';", "const FALLBACK_VERSION = '1.0.113';")
    start = text.index('  const OFFLINE = {')
    end = text.index('  const TITLES = {', start)
    offline = """  const OFFLINE = {
    ar:['إزالة زري مركز العمليات والمراجعة المالية من الواجهة الرئيسية.',
        'استبدالهما بزر موحد لتغيير لغة واجهة البرنامج إلى العربية أو الفرنسية أو الإنجليزية.',
        'حفظ لغة الواجهة المختارة باستخدام إعدادات البرنامج الأصلية، مع إبقاء لغة طباعة الفواتير مستقلة.',
        'الحفاظ على البيع والمخزون والفواتير والديون والتفعيل والنسخ الاحتياطية دون تعديل بيانات المتجر.'],
    fr:['Suppression des boutons Centre des opérations et Revue financière de l’accueil.',
        'Remplacement par un bouton unique pour changer l’interface en arabe, français ou anglais.',
        'Enregistrement de la langue choisie via les paramètres existants, sans modifier la langue d’impression.',
        'Conservation des ventes, du stock, des factures, des dettes, de l’activation et des sauvegardes.'],
    en:['Removed the Operations Center and Financial Review buttons from the main interface.',
        'Replaced them with one global interface-language button for Arabic, French, and English.',
        'Persists the selected interface language through existing settings; print language remains separate.',
        'Preserves sales, inventory, invoices, debts, activation, backups, and store data.']
  };
"""
    return text[:start] + offline + text[end:]
def build(source, dest, work):
    source, dest, work = Path(source), Path(dest), Path(work)
    assert sha(source.read_bytes()) == BASE_ZIP_SHA, 'Base patch ZIP SHA256 mismatch'
    with zipfile.ZipFile(source) as z:
        assert z.namelist() == ['payload/app.asar']
        raw = z.read('payload/app.asar')
    assert sha(raw) == BASE_ASAR_SHA, 'Base app.asar SHA256 mismatch'
    magic, block, header_size, header_len = struct.unpack_from('<4I', raw)
    assert magic == 4 and block == header_size + 4
    tree = json.loads(raw[16:16+header_len]); data_start = 8 + block
    all_items = []
    def walk(node, prefix=''):
        for name, entry in node.get('files', {}).items():
            path = prefix + name
            if 'files' in entry: walk(entry, path + '/')
            elif 'offset' in entry and 'size' in entry: all_items.append((path, entry))
    walk(tree)
    items = sorted(all_items, key=lambda item: int(item[1]['offset']))
    buffer = bytearray(); changed = set(); removed = set()
    for name, entry in items:
        if name in REMOVE:
            removed.add(name); continue
        blob = raw[data_start+int(entry['offset']):data_start+int(entry['offset'])+int(entry['size'])]
        assert len(blob) == entry['size'], name
        if name == 'index.html':
            text = blob.decode('utf-8')
            for removed_script in REMOVE:
                pattern = r'<script\s+defer\s+src=["\']' + re.escape(removed_script) + r'["\']\s*>\s*</script>'
                text, count = re.subn(pattern, '', text, count=1, flags=re.I)
                assert count == 1, ('Expected exactly one script tag', removed_script, count)
            marker = '<script defer src="nano-purchase-order-ui.js"></script>'
            text = one(text, marker, marker + '\n  <script defer src="nano-language-switch-113.js"></script>')
            assert all(x not in text for x in REMOVE)
            blob = text.encode('utf-8'); changed.add(name)
        elif name == 'package.json':
            text = blob.decode('utf-8')
            pkg = json.loads(text); assert pkg.get('version') == '1.0.112'
            blob = one(text, '"version": "1.0.112"', '"version": "1.0.113"').encode('utf-8')
            changed.add(name)
        elif name == 'release-notes.js':
            blob = update_notes(blob.decode('utf-8')).encode('utf-8'); changed.add(name)
        entry['offset'] = str(len(buffer)); entry['size'] = len(blob)
        if name in changed and 'integrity' in entry:
            integrity = entry['integrity']; integrity['hash'] = sha(blob)
            size = int(integrity.get('blockSize', 4194304))
            integrity['blocks'] = [sha(blob[i:i+size]) for i in range(0, len(blob), size)]
        buffer.extend(blob)
        if name in changed:
            (work/name).parent.mkdir(parents=True, exist_ok=True); (work/name).write_bytes(blob)
    assert removed == REMOVE, ('Missing expected legacy scripts', removed)
    for name in REMOVE: tree['files'].pop(name, None)
    script_name = 'nano-language-switch-113.js'
    blob = (Path('.github/assets') / script_name).read_bytes()
    tree['files'][script_name] = {'size': len(blob), 'offset': str(len(buffer)),
        'integrity': {'algorithm':'SHA256','hash':sha(blob),'blockSize':4194304,
        'blocks':[sha(blob[i:i+4194304]) for i in range(0,len(blob),4194304)]}}
    buffer.extend(blob); (work/script_name).write_bytes(blob)
    assert changed == {'index.html','package.json','release-notes.js'}, changed
    header = json.dumps(tree, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    padded = (len(header) + 7) & ~3
    asar = struct.pack('<4I', 4, padded+4, padded, len(header)) + header + b'\0'*(padded-4-len(header)) + buffer
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('payload/app.asar', asar)
    with zipfile.ZipFile(dest) as z: check = z.read('payload/app.asar')
    assert sha(check) == sha(asar)
    _, b2, _, n2 = struct.unpack_from('<4I', check)
    final_tree = json.loads(check[16:16+n2]); start2 = 8+b2; files = final_tree['files']
    assert all(x not in files for x in REMOVE)
    assert 'nano-language-switch-113.js' in files
    for name in ('index.html','package.json','release-notes.js','nano-language-switch-113.js'):
        e=files[name]; payload=check[start2+int(e['offset']):start2+int(e['offset'])+e['size']]
        if 'integrity' in e: assert sha(payload)==e['integrity']['hash'], name
    e=files['package.json']; pkg=json.loads(check[start2+int(e['offset']):start2+int(e['offset'])+e['size']])
    assert pkg['version']=='1.0.113'
    (work/'app.asar').write_bytes(check)
    print(json.dumps({'version':'1.0.113','removed':sorted(removed),'changed':sorted(changed),'appAsarSha256':sha(check),'patchSha256':sha(dest.read_bytes()),'patchSize':dest.stat().st_size}))
if __name__ == '__main__':
    if len(sys.argv) != 4: raise SystemExit('usage: build-language-switch-113.py base.zip output.zip workdir')
    build(*sys.argv[1:])
