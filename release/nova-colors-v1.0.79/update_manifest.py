#!/usr/bin/env python3
"""Publish metadata for a verified v1.0.79 release artifact. Only after release succeeds."""
import base64
import json
import os
import subprocess
from pathlib import Path

REPO = os.environ['GITHUB_REPOSITORY']
TARGET = '1.0.79'
ZIP_NAME = 'NANO-POS-Patch-1.0.78-to-1.0.79-NOVA-COLORS.zip'
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
    'تطبيق ألوان Nomad POS Nova v1.2.18 على NANO POS للكمبيوتر',
    'الهوية الجديدة: أخضر داكن وعاجي وبرتقالي دافئ في تسجيل الدخول والشريط الجانبي والرئيسية.',
    'توحيد ألوان شاشة البيع وحقول البحث والسلة وأزرار الدفع ولوحة السعر الرقمية.',
    'تنسيق ألوان البطاقات والنوافذ وعناصر التحكم مع الحفاظ على جميع الوظائف والأبعاد الحالية.',
    'الحفاظ على بيانات المتجر والمبيعات والمخزون والمزامنة والطباعة دون تعديل.',
]
fr = [
    'Couleurs de Nomad POS Nova 1.2.18 appliquées à NANO POS Desktop.',
    'Palette vert profond, ivoire et orange chaleureux pour la connexion, le menu et l’accueil.',
    'Vente, recherche, panier, encaissement et afficheur numérique harmonisés.',
    'Toutes les fonctions, tailles de fenêtres et données restent inchangées.',
]
en = [
    'Nomad POS Nova 1.2.18 palette applied to NANO POS Desktop.',
    'Deep green, ivory and warm orange across login, sidebar and dashboard.',
    'Sales, barcode search, cart, checkout and digital total match the new palette.',
    'All workflows, layouts, settings and business data are preserved.',
]

path = f'repos/{REPO}/contents/nano-pos-update.json'
current_response = json.loads(gh(path))
current = json.loads(base64.b64decode(current_response['content']).decode('utf8'))
if current.get('version') != '1.0.78':
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
    'id': 'nano-pos-v1.0.79-nomad-nova-palette',
    'fromVersions': [f'1.0.{n}' for n in range(34, 79)],
    'directUrl': f'{BASE}/download/v{TARGET}/{ZIP_NAME}',
    'pageUrl': f'{BASE}/tag/v{TARGET}',
    'sha256': sha256(ZIP),
    'appAsarSha256': sha256(ASAR),
    'fileName': ZIP_NAME,
    'sizeBytes': ZIP.stat().st_size,
    'payloadType': 'app-asar',
}]
current['notes'] = {
    'ar': 'تحديث ألوان NANO POS بهوية Nomad POS Nova: أخضر داكن، برتقالي وعاجي دون تعديل وظائف البرنامج.',
    'fr': 'Palette Nomad Nova vert foncé, orange et ivoire, sans changement fonctionnel.',
    'en': 'Nomad Nova deep-green, orange and ivory colors, with no functional changes.',
}

serialized = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
encoded = base64.b64encode(serialized.encode('utf8')).decode('ascii')
response = json.loads(gh('-X', 'PUT', path,
                         '-f', 'message=Release NANO POS 1.0.79 Nomad Nova palette',
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