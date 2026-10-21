#!/usr/bin/env python3
"""Patch official 1.0.92 ASAR, fixing only release-notes.js and package.json."""
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

BASE_ASAR_SHA = 'f25a6c0ca6aaded38f7984b6bcf9edc3b1829c7846148bc0f6ad0a0c080b03e1'
BASE_NOTES_SHA = '42227b88769a6059e2fb03846afc8acc7ca69b333b54378bbdf1209cf0ab0c5d'

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def patch_asar(data, replacement):
    magic, block, content_size, n = struct.unpack_from('<4I', data)
    assert magic == 4 and block == content_size + 4, 'Invalid ASAR format'
    header = json.loads(data[16:16+n])
    start = 8 + block
    entries = []
    def collect(directory, prefix=''):
        for key, entry in directory.get('files', {}).items():
            path = prefix + key
            if 'files' in entry:
                collect(entry, path+'/')
            elif 'offset' in entry:
                entries.append((path, entry))
    collect(header)
    entries.sort(key=lambda item: int(item[1]['offset']))
    assert len(entries) > 100 and header['files']['release-notes.js']['size'] > 5000
    rebuilt = bytearray()
    changed = set()
    for path, entry in entries:
        offset = start + int(entry['offset'])
        part = data[offset:offset + entry['size']]
        assert len(part) == entry['size'], 'ASAR truncated: ' + path
        if path == 'release-notes.js':
            assert sha(part) == BASE_NOTES_SHA, 'Unknown release-notes source'
            part = replacement
            changed.add(path)
        elif path == 'package.json':
            old = part.decode('utf-8')
            assert json.loads(old)['version'] == '1.0.92'
            assert old.count('"version": "1.0.92"') == 1
            part = old.replace('"version": "1.0.92"', '"version": "1.0.93"').encode('utf-8')
            changed.add(path)
        entry['offset'] = str(len(rebuilt))
        entry['size'] = len(part)
        if path in changed and 'integrity' in entry:
            entry['integrity']['hash'] = sha(part)
            entry['integrity']['blocks'] = [sha(part[i:i+4194304]) for i in range(0,len(part),4194304)]
        rebuilt.extend(part)
    assert changed == {'release-notes.js','package.json'}
    packed = json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    new_content_size = (len(packed) + 7) & ~3
    assert new_content_size - 4 >= len(packed)
    new_block = new_content_size + 4
    new_data = struct.pack('<4I',4,new_block,new_content_size,len(packed))
    return new_data + packed + b'\0'*(new_content_size-4-len(packed)) + rebuilt

def main(source, destination, js_path):
    with zipfile.ZipFile(source) as z:
        assert z.namelist() == ['payload/app.asar']
        data = z.read('payload/app.asar')
    assert sha(data) == BASE_ASAR_SHA, 'Wrong 1.0.92 ASAR SHA; no release made'
    js = Path(js_path).read_bytes()
    assert len(js) >= 1000 and b'currentReleaseFeatures' in js and b'getCurrentAppVersion' in js
    patched = patch_asar(data, js)
    destination = Path(destination)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('payload/app.asar',patched)
    with zipfile.ZipFile(destination) as z:
        assert sha(z.read('payload/app.asar')) == sha(patched)
    print('PATCH_SHA256='+sha(destination.read_bytes()))
    print('ASAR_SHA256='+sha(patched))
if __name__=='__main__':
    main(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
