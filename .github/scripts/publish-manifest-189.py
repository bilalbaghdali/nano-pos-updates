#!/usr/bin/env python3
"""Activate v1.0.89 only after GitHub published the patch AND the full EXE."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

exe,patch=map(Path,sys.argv[1:3])
assert exe.name=='NANO-POS-Setup-1.0.89-x64.exe' and exe.stat().st_size>20_000_000
assert patch.name=='NANO-POS-Patch-1.0.88-to-1.0.89-HOME-FAITH-BANNER.zip'
with zipfile.ZipFile(patch) as z:
    assert z.namelist()==['payload/app.asar']
    app_sha=hashlib.sha256(z.read('payload/app.asar')).hexdigest()
data=json.loads(Path('nano-pos-update.json').read_text(encoding='utf-8'))
assert data['published'] and data['version']=='1.0.88','Unexpected published version'
repo=os.environ['GITHUB_REPOSITORY']
version='1.0.89'
tag='v'+version
page=f'https://github.com/{repo}/releases/tag/{tag}'
download=f'https://github.com/{repo}/releases/download/{tag}/'
file_hash=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
features={
 'ar':[
  'تحديث مهم للغاية: عرض آية كريمة أو حديث صحيح داخل البانر العلوي للصفحة الرئيسية بدل النافذة المنبثقة.',
  'تتغير الرسالة عند كل رجوع فعلي من أحد الأقسام إلى الصفحة الرئيسية، دون تكرارها عند تحديث الإحصائيات.',
  'الإبقاء على 100 رسالة موثقة مختلفة مع شرحها والمصدر ورابط الاطلاع.',
  'الحفاظ على أيقونة N الجديدة وعلى المبيعات والمخزون والتفعيل والنسخ الاحتياطية.'
 ],
 'fr':[
  'Mise à jour très importante : verset ou hadith dans la bannière supérieure de l’accueil, sans fenêtre modale.',
  'La citation change à chaque retour réel à l’accueil, pas à chaque actualisation des statistiques.',
  '100 messages sourcés avec explication et lien de référence.',
  'Préservation de l’icône N et des données, licences et sauvegardes.'
 ],
 'en':[
  'High-priority update: Quran verse or authentic hadith displayed in the Home header banner, not a popup.',
  'Message changes on every return to Home, not on background statistics refresh.',
  '100 sourced messages with explanation and reference link.',
  'Keeps the new N icon, all store records, licenses, and backups.'
 ]}
date=dt.datetime.now(dt.timezone.utc).date().isoformat()
data.update(version=version,published=True,releaseDate=date,importance='critical',mandatory=False,features=features)
data.setdefault('releaseHistory',{})[version]={'releaseDate':date,'features':features}
data['download']={'directUrl':download+exe.name,'pageUrl':page,'sha256':file_hash(exe),'fileName':exe.name,'sizeBytes':exe.stat().st_size}
data['patches']=[{
 'id':'nano-pos-v1.0.89-faith-home-banner',
 'fromVersions':['1.0.88'],
 'directUrl':download+patch.name,
 'pageUrl':page,
 'sha256':file_hash(patch),
 'appAsarSha256':app_sha,
 'fileName':patch.name,
 'sizeBytes':patch.stat().st_size,
 'payloadType':'app-asar'
}]
data['notes']={
'ar':'تحديث ذو أولوية عالية: الآيات والأحاديث في بانر الرئيسية وتتغير عند الرجوع إليها.',
'fr':'Priorité élevée : citations dans la bannière d’accueil, actualisées à chaque retour.',
'en':'High priority: sourced Home-banner reminders rotate on each return.'}
Path('nano-pos-update.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Version',version,'EXE sha256',data['download']['sha256'],'ZIP sha256',data['patches'][0]['sha256'],'ASAR sha256',app_sha)
