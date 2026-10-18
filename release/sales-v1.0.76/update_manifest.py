#!/usr/bin/env python3
"""Publish metadata for a verified v1.0.76 release artifact. Only after release succeeds."""
import base64
import json
import os
import subprocess
from pathlib import Path

REPO = os.environ['GITHUB_REPOSITORY']
TARGET = '1.0.76'
ZIP_NAME = 'NANO-POS-Patch-1.0.75-to-1.0.76-SALES-WORKSPACE.zip'
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
    'إعادة تنظيم شاشة البيع بالكامل',
    'توزيع متناسق بين المنتجات والسلة وأزرار الدفع مع احترام العرض المخصص يدويًا.',
    'إبراز حقلي البحث بالمنتجات والباركود وتحسين شريط أدوات البيع.',
    'ضبط شاشة الإجمالي الرقمي لتبقى واضحة وتتناسب تلقائيًا مع مساحة النافذة.',
    'تخطيط رأسي مرن للشاشات الضيقة مع الحفاظ على جميع أدوات البيع.',
]
fr = [
    'Réorganisation complète de l’écran de vente',
    'Disposition équilibrée du catalogue, du panier et des boutons de paiement.',
    'Meilleure lisibilité de la recherche par produit et code-barres.',
    'Affichage numérique du total adapté automatiquement à la fenêtre.',
    'Mise en page verticale sur les fenêtres étroites, sans changer les calculs.',
]
en = [
    'Complete sales screen reorganization',
    'Balanced product, cart and checkout controls with preserved manual resizing.',
    'Improved visibility of product and barcode search.',
    'Digital total scales to the available space.',
    'Adaptive stacked layout on narrower screens without sales logic changes.',
]

path = f'repos/{REPO}/contents/nano-pos-update.json'
current_response = json.loads(gh(path))
current = json.loads(base64.b64decode(current_response['content']).decode('utf8'))
if current.get('version') != '1.0.75':
    raise SystemExit(f"Refusing to overwrite unexpected update manifest version: {current.get('version')!r}")
if not ZIP.exists() or not ASAR.exists():
    raise SystemExit('Missing verified release archive or app.asar')

features = {'ar': ar, 'fr': fr, 'en': en}
current['version'] = TARGET
current['releaseDate'] = '2026-10-18'
current['published'] = True
current['features'] = features
current.setdefault('releaseHistory', {})[TARGET] = {'releaseDate': '2026-10-18', 'features': features}
current['patches'] = [{
    'id': 'nano-pos-v1.0.76-responsive-sales-workspace',
    'fromVersions': [f'1.0.{n}' for n in range(34, 76)],
    'directUrl': f'{BASE}/download/v{TARGET}/{ZIP_NAME}',
    'pageUrl': f'{BASE}/tag/v{TARGET}',
    'sha256': sha256(ZIP),
    'appAsarSha256': sha256(ASAR),
    'fileName': ZIP_NAME,
    'sizeBytes': ZIP.stat().st_size,
    'payloadType': 'app-asar',
}]
current['notes'] = {
    'ar': 'إعادة تنظيم شاشة البيع — البحث بالباركود والمنتجات والسلة والإجمالي الرقمي وأزرار الدفع بتخطيط متجاوب.',
    'fr': 'Écran de vente réorganisé : recherche, panier, total numérique et actions adaptés à la fenêtre.',
    'en': 'Responsive sales layout for barcode search, products, cart, digital total and checkout.',
}

serialized = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
encoded = base64.b64encode(serialized.encode('utf8')).decode('ascii')
response = json.loads(gh('-X', 'PUT', path,
                         '-f', 'message=Release NANO POS 1.0.76 desktop-only stocktake',
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