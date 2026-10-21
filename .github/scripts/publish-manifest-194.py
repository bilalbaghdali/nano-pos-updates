#!/usr/bin/env python3
"""NANO POS 1.0.94 official manifest; run only after tests and release upload."""
import datetime,hashlib,json,zipfile,sys
from pathlib import Path
meta=Path('nano-pos-update.json')
data=json.loads(meta.read_text(encoding='utf8'))
assert data['published'] and data['version']=='1.0.93'
patch=Path('NANO-POS-Patch-1.0.93-to-1.0.94-STABILITY-PROTECTION.zip')
assert patch.is_file()
build=json.loads(Path('incoming/build-194.json').read_text())
sha=hashlib.sha256(patch.read_bytes()).hexdigest()
assert sha==build['sha256']
with zipfile.ZipFile(patch) as z:
 assert z.namelist()==['payload/app.asar']
 assert hashlib.sha256(z.read('payload/app.asar')).hexdigest()==build['asarSha256']
features={
'ar':['تعزيز أمان التحديثات بإعادة فحص SHA-256 قبل تثبيتها ومنع الرجوع إلى نسخة أقدم.',
      'تطبيق استبدال ذري لملفات البرنامج على Windows مع نسخة احتياطية متحقق منها للتراجع عند الفشل.',
      'تحسين التحقق من سلامة النسخ الاحتياطية ورفض النسخ غير المكتملة، مع الحفاظ على بيانات المتجر والتفعيل.',
      'الاحتفاظ بإصلاح البحث داخل الأقسام وعرض مميزات الإصدار الحالي.'],
'fr':['Vérification SHA-256 juste avant installation et refus des versions plus anciennes.',
      'Remplacement atomique sur Windows avec sauvegarde de retour arrière vérifiée.',
      'Détection des sauvegardes incomplètes, sans toucher aux données ni à la licence.',
      'Correctifs de recherche et des nouveautés conservés.'],
'en':['Recheck update SHA-256 immediately before installation and reject downgrades.',
      'Atomically replace the Windows app with a retained verified rollback copy.',
      'Reject incomplete backup files while preserving store data and activation.',
      'Preserve the previous scoped-search and release-highlights fixes.']}
day=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
page='https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.94'
direct='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.94/'+patch.name
data.update(version='1.0.94',releaseDate=day,published=True,mandatory=False,
            importance='high',features=features)
data.setdefault('releaseHistory',{})['1.0.94']={'releaseDate':day,'features':features}
data['patches']=[{'id':'nano-pos-v1.0.94-stability-protection',
  'fromVersions':['1.0.91','1.0.92','1.0.93'],
  'directUrl':direct,'pageUrl':page,'sha256':sha,'appAsarSha256':build['asarSha256'],
  'fileName':patch.name,'sizeBytes':patch.stat().st_size,'payloadType':'app-asar'}]
data['download']={'directUrl':'','pageUrl':page,'sha256':'','fileName':''}
data['notes']={
'ar':'تحسينات عامة: الاستقرار وحماية التحديثات والنسخ الاحتياطية.',
'fr':'Améliorations générales : stabilité, mises à jour et sauvegardes.',
'en':'General improvements: stability, rollback and backup verification.'}
meta.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Updated NANO POS official manifest to v1.0.94:',sha)
