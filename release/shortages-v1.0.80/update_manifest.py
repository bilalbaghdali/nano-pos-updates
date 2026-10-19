#!/usr/bin/env python3
"""Publish metadata for a verified v1.0.80 release artifact. Only after release succeeds."""
import base64
import json
import os
import subprocess
from pathlib import Path

REPO = os.environ['GITHUB_REPOSITORY']
TARGET = '1.0.80'
ZIP_NAME = 'NANO-POS-Patch-1.0.79-to-1.0.80-INVENTORY-SHORTAGES.zip'
BASE = f'https://github.com/{REPO}/releases'
ZIP = Path('/tmp/release') / ZIP_NAME
ASAR = Path('/tmp/release/payload/app.asar')


def gh(*args):
    return subprocess.check_output(['gh', 'api', *args], text=True)


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


ar = [
    'إظهار قائمة اقتراح المنتجات الناقصة من المخزون في واجهة إدارة المخزون.',
    'زر ثابت في شريط المخزون العلوي قرب إضافة منتج جديد وقائمة الأسعار.',
    'عرض المخزون الحالي والحد الأدنى وكمية شراء مقترحة مع تمييز المنتجات النافدة.',
    'طباعة القائمة وتصديرها CSV والنسخ ومشاركتها أو إرسالها عبر البريد وواتساب.',
    'عدم تعديل أرصدة المنتجات أو إنشاء فواتير شراء تلقائيًا.',
]
fr = [
    'Bouton de réapprovisionnement visible dans la barre des stocks.',
    'Liste des produits épuisés ou sous le seuil avec quantités d’achat suggérées.',
    'Impression, export CSV, copie et partage par e-mail ou WhatsApp.',
    'Aucune modification des stocks ni création de commandes.',
]
en = [
    'Prominent restock suggestion button in the inventory toolbar.',
    'Out-of-stock and low-stock items with suggested replenishment quantities.',
    'Print, CSV export, copy and sharing via email or WhatsApp.',
    'Inventory and purchase invoices remain unchanged.',
]

path = f'repos/{REPO}/contents/nano-pos-update.json'
current_response = json.loads(gh(path))
current = json.loads(base64.b64decode(current_response['content']).decode('utf8'))
if current.get('version') != '1.0.79':
    raise SystemExit(f"Refusing to overwrite unexpected update manifest version: {current.get('version')!r}")
if not ZIP.exists() or not ASAR.exists():
    raise SystemExit('Missing verified release archive or app.asar')

features = {'ar': ar, 'fr': fr, 'en': en}
current['version'] = TARGET
current['releaseDate'] = '2026-10-19'
current['published'] = True
current['features'] = features
current.setdefault('releaseHistory', {})[TARGET] = {'releaseDate': '2026-10-19', 'features': features}
current['patches'] = [{
    'id': 'nano-pos-v1.0.80-inventory-shortages-print-share',
    'fromVersions': [f'1.0.{n}' for n in range(34, 80)],
    'directUrl': f'{BASE}/download/v{TARGET}/{ZIP_NAME}',
    'pageUrl': f'{BASE}/tag/v{TARGET}',
    'sha256': sha256(ZIP),
    'appAsarSha256': sha256(ASAR),
    'fileName': ZIP_NAME,
    'sizeBytes': ZIP.stat().st_size,
    'payloadType': 'app-asar',
}]
current['notes'] = {
    'ar': 'زر المنتجات الناقصة في المخزون مع القائمة والطباعة وتصدير CSV والإرسال.',
    'fr': 'Suggestions de réapprovisionnement depuis la barre des stocks, impression et partage.',
    'en': 'Inventory low-stock suggestion list with print, CSV and sharing.',
}

serialized = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
encoded = base64.b64encode(serialized.encode('utf8')).decode('ascii')
response = json.loads(gh('-X', 'PUT', path,
                         '-f', 'message=Release NANO POS 1.0.80 inventory shortages list',
                         '-f', f'content={encoded}',
                         '-f', f"sha={current_response['sha']}"))
if not response.get('commit', {}).get('sha'):
    raise SystemExit('Manifest update was not acknowledged by GitHub')
confirm = json.loads(gh(path))
check = json.loads(base64.b64decode(confirm['content']).decode('utf8'))
assert check['version'] == TARGET
assert check['patches'][0]['sha256'] == sha256(ZIP)
assert check['patches'][0]['appAsarSha256'] == sha256(ASAR)
print(f"Published manifest {TARGET}: commit {response['commit']['sha']}")