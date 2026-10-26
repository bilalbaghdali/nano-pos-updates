import json,hashlib,zipfile,datetime
from pathlib import Path

path=Path('NANO-POS-Patch-1.0.118-to-2.0.16-GENERAL-IMPROVEMENTS-NO-PRAYER.zip')
with zipfile.ZipFile(path) as z:
    assert z.namelist()==['payload/app.asar'], z.namelist()
    asar=z.read('payload/app.asar')
data=json.loads(Path('nano-pos-update.json').read_text(encoding='utf-8'))
date=datetime.date.today().isoformat()
features={
 'ar':[
  'إلغاء ميزة مواقيت الصلاة وإزالة شيفرتها من الحزمة الجديدة.',
  'الحفاظ على نطق سعر المنتج عند إضافته إلى السلة باللغة المختارة.',
  'الاعتماد على أساس NANO POS المستقر 1.0.118 للحفاظ على وظائف البيع والمخزون والفواتير والديون والطباعة والنسخ الاحتياطي.',
  'عدم تعديل قاعدة بيانات المتجر أو ملفات النسخ الاحتياطي.'
 ],
 'fr':[
  'Suppression de la fonctionnalité des horaires de prière et de son code dans le nouveau paquet.',
  'Conservation de la lecture vocale du prix du produit lors de son ajout au panier.',
  'Conservation de la base stable NANO POS 1.0.118 et de ses fonctions de vente, stock, factures, dettes, impression et sauvegarde.',
  'Aucune modification de la base de données du magasin ni des sauvegardes.'
 ],
 'en':[
  'Removes the prayer-times feature and its code from the new package.',
  'Keeps spoken product prices when items are added to the cart.',
  'Uses the stable NANO POS 1.0.118 base to preserve sales, inventory, invoices, debts, printing, and backup functions.',
  'Does not modify the store database or backup files.'
 ]
}
filename=path.name
versions=set()
for version in data.get('releaseHistory',{}):
    try:
        if tuple(map(int,version.split('.'))) >= (1,0,34):
            versions.add(version)
    except (TypeError,ValueError):
        pass
versions.update(['1.0.118']+[f'2.0.{i}' for i in range(16)])
entry={
 'id':'nano-pos-v118-general-improvements-no-prayer-v216',
 'fromVersions':sorted(versions,key=lambda v:tuple(map(int,v.split('.')))),
 'directUrl':f'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.16/{filename}',
 'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.16',
 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'appAsarSha256':hashlib.sha256(asar).hexdigest(),
 'fileName':filename,
 'sizeBytes':path.stat().st_size,
 'payloadType':'app-asar'
}
data['version']='2.0.16'
data['releaseDate']=date
data['published']=True
data['mandatory']=False
data['importance']='normal'
data['features']=features
data.setdefault('releaseHistory',{})['2.0.16']={'releaseDate':date,'features':features,'label':'تحسينات عامة'}
# The new universal patch supersedes all prayer-time patches and is based on stable v1.0.118.
kept=[]
for old in data.get('patches',[]):
    marker=(str(old.get('id',''))+' '+str(old.get('fileName',''))).lower()
    if 'prayer' not in marker and old.get('id')!='nano-pos-v118-general-improvements-no-prayer-v216':
        kept.append(old)
data['patches']=[entry]+kept
Path('nano-pos-update.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared a universal v2.0.16 manifest entry with exact ZIP and ASAR hashes.')
