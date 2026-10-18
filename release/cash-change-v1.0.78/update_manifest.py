#!/usr/bin/env python3
"""Publish metadata for a verified v1.0.78 release artifact. Only after release succeeds."""
import base64
import json
import os
import subprocess
from pathlib import Path

REPO = os.environ['GITHUB_REPOSITORY']
TARGET = '1.0.78'
ZIP_NAME = 'NANO-POS-Patch-1.0.77-to-1.0.78-CASH-CHANGE-AUDIT.zip'
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
    'حساب الصرف النقدي وتوثيقه عند البيع',
    'إدخال المبلغ النقدي الذي سلّمه الزبون وعرض الصرف الواجب إرجاعه بشكل مباشر وواضح.',
    'حفظ المبلغ المستلم والصرف المحسوب ورقم الفاتورة والبائع والمناوبة في سجل مستقل دائم.',
    'ربط سجل الصرف بالفاتورة وإتاحته للمراجعة من شاشة المبيعات حتى عند حذف الفاتورة.',
    'حساب النقد المحتسب بالصندوق منفصلًا عن إجمالي المبلغ المستلم لحماية أرصدة النقد والكريدي.',
]
fr = [
    'Calcul de la monnaie et journal des encaissements',
    'Saisie de la somme remise et calcul immédiat de la monnaie à rendre.',
    'Conservation du montant reçu, monnaie, facture, caissier et session dans un journal distinct.',
    'Consultation du journal même après suppression d’une vente.',
    'Seule la somme nette imputée à la vente affecte la caisse et le crédit.',
]
en = [
    'Cash tender and expected-change audit',
    'Enter customer cash handed and calculate change immediately.',
    'Persist cash received, calculated change, sale reference, cashier and shift separately.',
    'Read the persistent audit history even after a sale is deleted.',
    'Only net cash applied to the invoice affects cashbox and customer credit.',
]

path = f'repos/{REPO}/contents/nano-pos-update.json'
current_response = json.loads(gh(path))
current = json.loads(base64.b64decode(current_response['content']).decode('utf8'))
if current.get('version') != '1.0.77':
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
    'id': 'nano-pos-v1.0.78-cash-change-audit',
    'fromVersions': [f'1.0.{n}' for n in range(34, 78)],
    'directUrl': f'{BASE}/download/v{TARGET}/{ZIP_NAME}',
    'pageUrl': f'{BASE}/tag/v{TARGET}',
    'sha256': sha256(ZIP),
    'appAsarSha256': sha256(ASAR),
    'fileName': ZIP_NAME,
    'sizeBytes': ZIP.stat().st_size,
    'payloadType': 'app-asar',
}]
current['notes'] = {
    'ar': 'إضافة المبلغ المستلم من الزبون وحساب الصرف الواجب إرجاعه مع سجل مرجعي دائم لكل عملية بيع نقدي.',
    'fr': 'Saisie des espèces reçues, calcul de la monnaie et journal de référence par vente.',
    'en': 'Record cash tender, calculate change and keep a permanent reference log per sale.',
}

serialized = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
encoded = base64.b64encode(serialized.encode('utf8')).decode('ascii')
response = json.loads(gh('-X', 'PUT', path,
                         '-f', 'message=Release NANO POS 1.0.78 desktop-only stocktake',
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