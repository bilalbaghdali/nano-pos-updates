#!/usr/bin/env python3
"""Publish metadata for a verified v1.0.73 release artifact. Only after release succeeds."""
import base64
import json
import os
import subprocess
from pathlib import Path

REPO = os.environ['GITHUB_REPOSITORY']
TARGET = '1.0.73'
ZIP_NAME = 'NANO-POS-Patch-1.0.72-to-1.0.73-SALES-RESPONSIVE.zip'
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
    'تحسينات عامة على تناسق شاشة البيع',
    'إعادة ضبط عرض لوحات المنتجات والسلة لتناسب المساحات المتاحة بدون تداخل.',
    'تصغير ارتفاع شاشة السعر الرقمية وتنسيق الرقم والعملة والعنوان في بطاقة متوازنة.',
    'تحسين المسافات بين أزرار البيع والتسديد وتوافق أوضاع العرض الثلاثة.',
    'الاحتفاظ بجميع حسابات البيع وميزات التسعير من الإصدار السابق دون تغيير.',
]
fr = [
    'Améliorations générales de la mise en page de vente',
    'Panneaux produits et panier mieux adaptés aux différentes tailles.',
    'Afficheur numérique du prix plus compact avec montant et devise alignés.',
    'Boutons de vente et validation mieux espacés dans les trois modes.',
    'Aucun changement de calcul des ventes ou de tarification.',
]
en = [
    'General sales screen layout improvements',
    'Product and cart panels better fit available width without overlaps.',
    'A compact digital total with aligned amount, label and currency.',
    'More balanced checkout buttons in all three POS display modes.',
    'Sales calculation and pricing behavior unchanged.',
]

path = f'repos/{REPO}/contents/nano-pos-update.json'
current_response = json.loads(gh(path))
current = json.loads(base64.b64decode(current_response['content']).decode('utf8'))
if current.get('version') != '1.0.72':
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
    'id': 'nano-pos-v1.0.73-responsive-sales-layout',
    'fromVersions': [f'1.0.{n}' for n in range(34, 73)],
    'directUrl': f'{BASE}/download/v{TARGET}/{ZIP_NAME}',
    'pageUrl': f'{BASE}/tag/v{TARGET}',
    'sha256': sha256(ZIP),
    'appAsarSha256': sha256(ASAR),
    'fileName': ZIP_NAME,
    'sizeBytes': ZIP.stat().st_size,
    'payloadType': 'app-asar',
}]
current['notes'] = {
    'ar': 'تحسينات عامة — تنسيق أبعاد شاشة البيع وشاشة السعر الرقمية بما يتناسب مع عرض الصفحة، دون تغيير حسابات البيع.',
    'fr': 'Améliorations générales — écran de vente et afficheur numérique adaptatifs, sans changer les calculs.',
    'en': 'General improvements — responsive sales screen and digital total, without sales logic changes.',
}

serialized = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
encoded = base64.b64encode(serialized.encode('utf8')).decode('ascii')
response = json.loads(gh('-X', 'PUT', path,
                         '-f', 'message=Release NANO POS 1.0.73 desktop-only stocktake',
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