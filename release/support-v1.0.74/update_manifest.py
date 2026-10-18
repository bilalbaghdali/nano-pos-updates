#!/usr/bin/env python3
"""Publish metadata for a verified v1.0.74 release artifact. Only after release succeeds."""
import base64
import json
import os
import subprocess
from pathlib import Path

REPO = os.environ['GITHUB_REPOSITORY']
TARGET = '1.0.74'
ZIP_NAME = 'NANO-POS-Patch-1.0.73-to-1.0.74-SUPPORT-TOOLS.zip'
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
    'تحسينات عامة على الدعم التقني',
    'إضافة زري فتح AnyDesk وTailscale داخل نافذة الاتصال بالدعم.',
    'فتح التطبيق المثبت على Windows عند الضغط؛ وإذا لم يكن مثبتًا يظهر رابط التنزيل الرسمي.',
    'لا تُفتح أي جلسة دعم أو اتصال عن بعد دون إجراء من المستخدم.',
]
fr = [
    'Améliorations générales du support technique',
    'Ajout des boutons AnyDesk et Tailscale dans la fenêtre de contact du support.',
    'Ouverture des applications Windows installées et lien officiel de téléchargement à défaut.',
    'Aucune session distante n’est ouverte sans intervention de l’utilisateur.',
]
en = [
    'General technical support improvements',
    'Added AnyDesk and Tailscale buttons to the Contact Support window.',
    'Launch installed Windows apps or show their official download links if missing.',
    'No remote-control session is started automatically.',
]

path = f'repos/{REPO}/contents/nano-pos-update.json'
current_response = json.loads(gh(path))
current = json.loads(base64.b64decode(current_response['content']).decode('utf8'))
if current.get('version') != '1.0.73':
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
    'id': 'nano-pos-v1.0.74-remote-support-tools',
    'fromVersions': [f'1.0.{n}' for n in range(34, 74)],
    'directUrl': f'{BASE}/download/v{TARGET}/{ZIP_NAME}',
    'pageUrl': f'{BASE}/tag/v{TARGET}',
    'sha256': sha256(ZIP),
    'appAsarSha256': sha256(ASAR),
    'fileName': ZIP_NAME,
    'sizeBytes': ZIP.stat().st_size,
    'payloadType': 'app-asar',
}]
current['notes'] = {
    'ar': 'تحسينات عامة — فتح AnyDesk وTailscale من نافذة الدعم التقني مع رابط تنزيل رسمي عند عدم التثبيت.',
    'fr': 'Améliorations générales — ouverture d’AnyDesk et de Tailscale depuis l’assistance.',
    'en': 'General improvements — launch AnyDesk and Tailscale from Contact Support.',
}

serialized = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
encoded = base64.b64encode(serialized.encode('utf8')).decode('ascii')
response = json.loads(gh('-X', 'PUT', path,
                         '-f', 'message=Release NANO POS 1.0.74 desktop-only stocktake',
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