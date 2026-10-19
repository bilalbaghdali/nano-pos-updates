#!/usr/bin/env python3
"""Publish metadata for a verified v1.0.81 release artifact. Only after release succeeds."""
import base64
import json
import os
import subprocess
from pathlib import Path

REPO = os.environ['GITHUB_REPOSITORY']
TARGET = '1.0.81'
ZIP_NAME = 'NANO-POS-Patch-1.0.80-to-1.0.81-LOCAL-STORAGE-FOLDER.zip'
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
    'إضافة اختيار مجلد التخزين المحلي في الإعدادات ← استيراد وتصدير.',
    'حفظ المسار المختار على الكمبيوتر واستخدامه في النسخ الاحتياطية المحلية اليدوية والتلقائية ونسخة إغلاق البرنامج.',
    'فتح نافذة حفظ التصديرات وPDF افتراضيًا داخل المجلد المختار، مع السماح باختيار مكان آخر وقت الحفظ.',
    'إضافة زري إعادة الوضع الافتراضي وتحديث حالة المجلد، مع مسار آمن بديل إذا أصبح المجلد غير متاح.',
    'عدم نقل قاعدة البيانات الحية أو تغيير البيانات والنسخ السابقة أو إعدادات النسخ إلى MEGA.',
]
fr = [
    'Choix du dossier de stockage local dans Paramètres > Importer/Exporter.',
    'Sauvegardes locales automatiques/manuelles et à la fermeture au dossier sélectionné.',
    'Exports et PDF suggérés dans le dossier choisi, modifiable au moment de sauvegarder.',
    'Réinitialisation et bascule sûre si le dossier devient indisponible.',
    'Aucune migration de base active ni modification des sauvegardes MEGA.',
]
en = [
    'Local storage folder picker in Settings > Import / Export.',
    'Persistent chosen location for native manual/hourly/shutdown backups.',
    'Default export and PDF save path uses the chosen folder, still overridable.',
    'Reset and safe fallback if selected storage is unavailable.',
    'Live database and existing backup files are never moved.',
]

path = f'repos/{REPO}/contents/nano-pos-update.json'
current_response = json.loads(gh(path))
current = json.loads(base64.b64decode(current_response['content']).decode('utf8'))
if current.get('version') != '1.0.80':
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
    'id': 'nano-pos-v1.0.81-local-storage-folder',
    'fromVersions': [f'1.0.{n}' for n in range(34, 81)],
    'directUrl': f'{BASE}/download/v{TARGET}/{ZIP_NAME}',
    'pageUrl': f'{BASE}/tag/v{TARGET}',
    'sha256': sha256(ZIP),
    'appAsarSha256': sha256(ASAR),
    'fileName': ZIP_NAME,
    'sizeBytes': ZIP.stat().st_size,
    'payloadType': 'app-asar',
}]
current['notes'] = {
    'ar': 'اختيار مجلد التخزين المحلي للنسخ الاحتياطية والتصدير مع حفظ الاختيار وإعادة الضبط الآمنة.',
    'fr': 'Sélection du dossier local pour les sauvegardes et exports, avec repli sécurisé.',
    'en': 'Select persistent local backup/export folder with safe fallback.',
}

serialized = json.dumps(current, ensure_ascii=False, indent=2) + '\n'
encoded = base64.b64encode(serialized.encode('utf8')).decode('ascii')
response = json.loads(gh('-X', 'PUT', path,
                         '-f', 'message=Release NANO POS 1.0.81 local storage folder',
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