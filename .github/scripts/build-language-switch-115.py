#!/usr/bin/env python3
"""Build the NANO POS 1.0.115 language-switch visual refinement patch."""
import hashlib, json, struct, sys, zipfile
from pathlib import Path

sha = lambda b: hashlib.sha256(b).hexdigest()

def one(text, old, new):
    count = text.count(old)
    assert count == 1, (old[:100], count)
    return text.replace(old, new, 1)

def update_notes(text):
    text = one(text, "const FALLBACK_VERSION = '1.0.114';", "const FALLBACK_VERSION = '1.0.115';")
    start = text.index('  const OFFLINE = {')
    end = text.index('  const TITLES = {', start)
    offline = """  const OFFLINE = {
    ar:['وضع زر تغيير اللغة بين التنبيهات وزر اقتران الهاتف على نفس المستوى.',
        'الحفاظ على عرض اللغة الحالية والقائمة المنسقة.',
        'ضبط المحاذاة الأفقية مع عناصر شريط الأدوات على الكمبيوتر والهاتف.',
        'الحفاظ على وظائف البرنامج وبياناته ولغة طباعة الفواتير المستقلة.'],
    fr:['Placement du bouton de langue entre les notifications et l’association du téléphone, sur la même ligne.',
        'Conservation de l’affichage de la langue active et du menu soigné.',
        'Alignement horizontal dans la barre d’outils sur ordinateur et mobile.',
        'Conservation des fonctions, des données et de la langue d’impression indépendante.'],
    en:['Placed the language button between notifications and phone pairing on the same toolbar row.',
        'Preserved the active-language display and refined menu.',
        'Aligned the control horizontally with toolbar items on desktop and mobile.',
        'Preserves app functionality, data, and the independent print-language setting.']
  };
"""
    return text[:start] + offline + text[end:]

def build(source, dest, work):
    source, dest, work = Path(source), Path(dest), Path(work)
    with zipfile.ZipFile(source) as z:
        assert z.namelist() == ['payload/app.asar'], 'Unexpected base patch contents'
        raw = z.read('payload/app.asar')
    magic, block, header_size, header_len = struct.unpack_from('<4I', raw)
    assert magic == 4 and block == header_size + 4, 'Invalid ASAR header'
    tree = json.loads(raw[16:16+header_len])
    data_start = 8 + block
    entries = []
    def walk(node, prefix=''):
        for name, entry in node.get('files', {}).items():
            path = prefix + name
            if 'files' in entry:
                walk(entry, path + '/')
            elif 'offset' in entry and 'size' in entry:
                entries.append((path, entry))
    walk(tree)
    entries.sort(key=lambda pair: int(pair[1]['offset']))
    buffer = bytearray()
    changed = set()
    found = set()
    for name, entry in entries:
        begin = data_start + int(entry['offset'])
        blob = raw[begin:begin+int(entry['size'])]
        assert len(blob) == int(entry['size']), name
        if name == 'package.json':
            pkg = json.loads(blob.decode('utf-8'))
            assert pkg.get('version') == '1.0.114', ('Expected v1.0.114 base', pkg.get('version'))
            pkg['version'] = '1.0.115'
            blob = (json.dumps(pkg, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            changed.add(name)
        elif name == 'release-notes.js':
            blob = update_notes(blob.decode('utf-8')).encode('utf-8')
            changed.add(name)
        elif name == 'nano-language-switch-113.js':
            replacement = (Path('.github/assets') / name).read_bytes()
            assert b'nano-language-switch-113-trigger' in replacement
            assert b'1.0.115' in replacement
            blob = replacement
            changed.add(name)
            found.add(name)
        entry['offset'] = str(len(buffer))
        entry['size'] = len(blob)
        if name in changed and 'integrity' in entry:
            integrity = entry['integrity']
            integrity['hash'] = sha(blob)
            size = int(integrity.get('blockSize', 4194304))
            integrity['blocks'] = [sha(blob[i:i+size]) for i in range(0, len(blob), size)]
        buffer.extend(blob)
        if name in changed:
            (work/name).parent.mkdir(parents=True, exist_ok=True)
            (work/name).write_bytes(blob)
    assert found == {'nano-language-switch-113.js'}, 'Existing language switch script not found'
    assert changed == {'package.json', 'release-notes.js', 'nano-language-switch-113.js'}, changed
    header = json.dumps(tree, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    padded = (len(header) + 7) & ~3
    asar = struct.pack('<4I', 4, padded+4, padded, len(header)) + header + b'\0'*(padded-4-len(header)) + buffer
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('payload/app.asar', asar)
    with zipfile.ZipFile(dest) as z:
        check = z.read('payload/app.asar')
    assert sha(check) == sha(asar)
    _, b2, _, n2 = struct.unpack_from('<4I', check)
    final_tree = json.loads(check[16:16+n2])
    start2 = 8+b2
    files = final_tree['files']
    assert 'nano-operations-center.js' not in files and 'nano-financial-review.js' not in files
    assert 'nano-language-switch-113.js' in files
    for name in ('package.json', 'release-notes.js', 'nano-language-switch-113.js'):
        e = files[name]
        payload = check[start2+int(e['offset']):start2+int(e['offset'])+e['size']]
        if 'integrity' in e:
            assert sha(payload) == e['integrity']['hash'], name
    e = files['package.json']
    pkg = json.loads(check[start2+int(e['offset']):start2+int(e['offset'])+e['size']])
    assert pkg['version'] == '1.0.115'
    (work/'app.asar').write_bytes(check)
    print(json.dumps({'version':'1.0.115','changed':sorted(changed),
        'appAsarSha256':sha(check),'patchSha256':sha(dest.read_bytes()),
        'patchSize':dest.stat().st_size}))

if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit('usage: build-language-switch-115.py base.zip output.zip workdir')
    build(*sys.argv[1:])
