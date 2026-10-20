#!/usr/bin/env python3
"""Publish v1.1.0 Multi-Commerce Phase 1 only after both release assets exist."""
import datetime as dt
import hashlib,json,os,sys,zipfile
from pathlib import Path
exe,patch=map(Path,sys.argv[1:3])
assert exe.name=='NANO-POS-Setup-1.1.0-x64.exe' and exe.stat().st_size>20_000_000
assert patch.name=='NANO-POS-Patch-1.0.91-to-1.1.0-MULTI-COMMERCE-PHASE1.zip'
with zipfile.ZipFile(patch) as z:
 assert z.namelist()==['payload/app.asar']
 asarsha=hashlib.sha256(z.read('payload/app.asar')).hexdigest()
manifest=Path('nano-pos-update.json')
d=json.loads(manifest.read_text(encoding='utf-8'))
assert d['version']=='1.0.91' and d['published'],'Unexpected currently published version'
repo=os.environ['GITHUB_REPOSITORY']
page=f'https://github.com/{repo}/releases/tag/v1.1.0'
base=f'https://github.com/{repo}/releases/download/v1.1.0/'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
features={
 'ar':[
  'المرحلة الأولى من NANO POS Multi-Commerce: شاشة اختيار نشاط المتجر عند الإعداد الأول فقط، ثم الدخول مباشرة للرئيسية.',
  'ثمانية أنشطة: المواد الغذائية، الهواتف والإلكترونيات، الملابس والأحذية، العطور والتجميل، الخردوات، قطع الغيار، السيارات، والتجارة المتعددة.',
  'إظهار النشاط المختار في الرئيسية وزر تغيير النشاط للمدير.',
  'حفظ اختيار النشاط والوحدات والحقول المقترحة ضمن إعدادات المتجر والتحقق من نجاح الحفظ.',
  'لا تتغير قواعد حساب المبيعات والمخزون أو طرق البيع الحالية في هذه المرحلة التأسيسية؛ ستضاف الخصائص القطاعية بعد اختبارها.'
 ],
 'fr':[
  'Première phase Multi-Commerce: sélection du secteur au premier paramétrage, accès direct au tableau de bord ensuite.',
  'Huit activités commerciales, notamment alimentation, électronique, mode, cosmétique, quincaillerie, pièces auto et véhicules.',
  'Activité affichée sur l’accueil et modification réservée à l’administrateur.',
  'Enregistrement du secteur, des unités et des champs recommandés dans les paramètres du magasin.',
  'Les règles de vente et de stock ne changent pas dans cette phase de préparation.'
 ],
 'en':[
  'Multi-Commerce Phase 1: select business sector at first setup only, then open the dashboard directly.',
  'Eight sector templates including groceries, electronics, apparel, beauty, hardware, parts, cars and mixed retail.',
  'Display the current activity on Home, with admin-only change control.',
  'Persist sector, recommended units and fields in store settings and verify save.',
  'Existing inventory, sales accounting and installments are unchanged in this foundation release.'
 ]}
date=dt.datetime.now(dt.timezone.utc).date().isoformat()
d.update(version='1.1.0',published=True,mandatory=False,importance='high',releaseDate=date,features=features)
d.setdefault('releaseHistory',{})['1.1.0']={'releaseDate':date,'features':features}
d['download']={'directUrl':base+exe.name,'pageUrl':page,'sha256':sha(exe),'fileName':exe.name,'sizeBytes':exe.stat().st_size}
d['patches']=[{'id':'nano-pos-v1.1.0-multi-commerce-phase1','fromVersions':['1.0.91'],'directUrl':base+patch.name,'pageUrl':page,'sha256':sha(patch),'appAsarSha256':asarsha,'fileName':patch.name,'sizeBytes':patch.stat().st_size,'payloadType':'app-asar'}]
d['notes']={
 'ar':'المرحلة الأولى لنظام متعدد الأنشطة: شاشة اختيار أولية، ثم دخول مباشر إلى الرئيسية مع زر تغيير النشاط. وظائف البيع القطاعية تأتي في إصدارات لاحقة.',
 'fr':'Multi-Commerce Phase 1: choix initial d’activité, accès direct au tableau de bord, sans modification du moteur de vente.',
 'en':'Multi-Commerce Phase 1: initial activity selection with direct dashboard entry thereafter, existing sales engine preserved.'}
manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Published v1.1.0 EXE SHA256',d['download']['sha256'],'ZIP SHA256',d['patches'][0]['sha256'])
