#!/usr/bin/env python3
"""Build verified NANO POS app.asar-only update, based on released v1.0.58."""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

OLD = '1.0.58'
NEW = '1.0.59'
SRC_FILE = 'NANO-POS-Patch-1.0.57-to-1.0.58-EMBEDDED-APK.zip'
OUT_FILE = 'NANO-POS-Patch-1.0.58-to-1.0.59-MOBILE-BUTTONS-FIX.zip'
REPO = 'bilalbaghdali/nano-pos-updates'
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'nano-pos-update.json'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def unpack(data):
    if len(data) < 24:
        raise ValueError('Invalid app.asar')
    a, b, c, d = struct.unpack_from('<4I', data)
    if a != 4 or b != d + 8 or c != d + 4 or d <= 0:
        raise ValueError('Unrecognized ASAR header format')
    start = 8 + b
    header = json.loads(data[16:16+d])
    def read(path):
        info = header['files'][path]
        if info.get('unpacked') or 'offset' not in info:
            raise ValueError('Unsupported ASAR entry: ' + path)
        offset = start + int(info['offset'])
        length = int(info['size'])
        if length < 1 or offset + length > len(data):
            raise ValueError('Invalid ASAR entry bounds: ' + path)
        return data[offset:offset+length]
    return header, start, read

def patch_asar(original, modifications):
    header, payload_start, read = unpack(original)
    payload = bytearray(original[payload_start:])
    for name, value in modifications.items():
        assert value != read(name), 'No actual change in ' + name
        entry = header['files'][name]
        entry['offset'] = str(len(payload))
        entry['size'] = len(value)
        if 'integrity' in entry:
            integrity = entry['integrity']
            integrity['algorithm'] = 'SHA256'
            integrity['hash'] = digest(value)
            block = int(integrity.get('blockSize') or 4194304)
            integrity['blocks'] = [digest(value[i:i+block]) for i in range(0, len(value), block)]
        payload.extend(value)
    encoded = json.dumps(header, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    encoded += b' ' * (-len(encoded) % 4)
    updated = struct.pack('<4I', 4, len(encoded)+8, len(encoded)+4, len(encoded)) + encoded + payload
    check_header, _, check_read = unpack(updated)
    for name, value in modifications.items():
        if check_read(name) != value:
            raise ValueError('ASAR data validation failed: ' + name)
        if 'integrity' in check_header['files'][name] and check_header['files'][name]['integrity']['hash'] != digest(value):
            raise ValueError('ASAR hash mismatch: ' + name)
    return updated

def main(source_zip):
    meta = json.loads(MANIFEST.read_text(encoding='utf8'))
    if meta['version'] != OLD or meta.get('published') is not True:
        raise SystemExit('Expected published v1.0.58 manifest, refusing stale update')
    matches = [p for p in meta['patches'] if p.get('fileName') == SRC_FILE]
    if len(matches) != 1:
        raise SystemExit('Could not uniquely identify source v1.0.58 patch')
    with zipfile.ZipFile(source_zip) as z:
        if 'payload/app.asar' not in z.namelist():
            raise SystemExit('v1.0.58 patch is missing payload/app.asar')
        original = z.read('payload/app.asar')
    if digest(original) != matches[0]['appAsarSha256']:
        raise SystemExit('v1.0.58 ASAR hash mismatch, refusing publication')
    header, _, read = unpack(original)
    html = read('index.html').decode('utf8')
    ui = read('desktop-sync-ui.js').decode('utf8')
    package = json.loads(read('package.json').decode('utf8'))
    if package.get('version') != OLD:
        raise SystemExit('Source NANO POS package version was not 1.0.58')
    if not all(s in html for s in ('settingsTab-mobileapp', 'appDownloadSection', '</body>')):
        raise SystemExit('Desktop interface structure unrecognized')
    if not all(s in ui for s in ('data-download-mobile', 'data-download-scanner')):
        raise SystemExit('Existing phone/scanner buttons unrecognized')
    mobile_meta = json.loads((ROOT / 'mobile-latest.json').read_text(encoding='utf8'))
    latest_ids = ('mobileApkDownloadButton', 'mobileApkSaveButton', 'nanoMobileDownloadLatest', 'downloadLatestMobileApk', 'saveMobileApkButton')
    if mobile_meta.get('version') != '1.3.7' or mobile_meta.get('published') is not True:
        raise SystemExit('Stable mobile 1.3.7 release is not published')
    if not any(s in html for s in latest_ids) and '1.3.7' not in html and '1.3.7' not in ui:
        raise SystemExit('Latest Mobile download button not found; refusing to remove old button')
    script = (ROOT / '.github/pos-fixes/mobile-buttons-fix.js').read_text(encoding='utf8')
    if '__nanoMobileButtonsFixInstalled' in html:
        raise SystemExit('Hotfix already embedded; refusing duplicate update')
    html = re.sub('</body>', lambda m: '<script id="nano-mobile-buttons-fix">\n' + script + '\n</script>\n' + m.group(), html, count=1, flags=re.I)
    package['version'] = NEW
    config = read('app-config.js').decode('utf8')
    if "'"+OLD+"'" not in config:
        raise SystemExit('Source app-config.js does not have the expected version')
    config = config.replace("'"+OLD+"'", "'"+NEW+"'")
    new_asar = patch_asar(original, {
      'index.html': html.encode('utf8'),
      'package.json': (json.dumps(package, ensure_ascii=False, indent=2) + '\n').encode('utf8'),
      'app-config.js': config.encode('utf8')
    })
    out = ROOT / '_release_build' / OUT_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr('payload/app.asar', new_asar)
    with zipfile.ZipFile(out) as z:
        assert z.namelist() == ['payload/app.asar']
        assert digest(z.read('payload/app.asar')) == digest(new_asar)
    features = {
      'ar': ['إزالة زر تنزيل نسخة تطبيق الهاتف القديمة 1.3.6 والإبقاء على زر 1.3.7.', 'نقل زر تنزيل تطبيق الهاتف إلى جانب زر تطبيق قارئ الباركود.', 'الحفاظ على روابط التنزيل وقاعدة البيانات والتفعيل والمزامنة.'],
      'fr': ["Suppression du bouton Mobile 1.3.6, conservation de 1.3.7.", "Placement du bouton Mobile près du lecteur code-barres.", "Conservation des téléchargements, des données et de la synchronisation."],
      'en': ['Removed Mobile 1.3.6 download button; preserved 1.3.7.', 'Placed Mobile download beside barcode scanner.', 'Preserved download handlers, data, activation, and sync.']
    }
    meta['version'] = NEW
    meta['releaseDate'] = '2026-10-14'
    meta['features'] = features
    meta.setdefault('releaseHistory', {})[NEW] = {'releaseDate':'2026-10-14', 'features':features}
    meta['patches'] = [{
      'id': 'nano-pos-v1.0.59-mobile-buttons-fix',
      'fromVersions': ['1.0.' + str(i) for i in range(34,59)],
      'directUrl': 'https://github.com/' + REPO + '/releases/download/v' + NEW + '/' + OUT_FILE,
      'pageUrl': 'https://github.com/' + REPO + '/releases/tag/v' + NEW,
      'sha256': digest(out.read_bytes()),
      'appAsarSha256': digest(new_asar),
      'fileName': OUT_FILE,
      'sizeBytes': out.stat().st_size,
      'payloadType': 'app-asar'
    }]
    meta['notes'] = {
      'ar': 'ترتيب زري تطبيق الهاتف وقارئ الباركود وإزالة تنزيل نسخة الهاتف القديمة.',
      'fr': 'Correction de doublon des boutons de téléchargement mobile.',
      'en': 'Removed duplicate mobile app download button.'
    }
    MANIFEST.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    (ROOT / '_release_build' / 'RELEASE_NOTES.md').write_text(
       '# NANO POS v1.0.59\n\n- Remove old v1.3.6 Mobile download button.\n'
       '- Keep v1.3.7 Mobile download beside Wireless Barcode Scanner.\n'
       '- No changes to sales, purchases, database, activation, or sync.\n',
       encoding='utf8'
    )
    print('Build verified:', out, 'ZIP SHA:', meta['patches'][0]['sha256'], 'ASAR SHA:', meta['patches'][0]['appAsarSha256'])

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: build-mobile-buttons-release.py <existing-v1.0.58-zip>')
    main(Path(sys.argv[1]))
