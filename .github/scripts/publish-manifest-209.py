import json,hashlib,zipfile,datetime
from pathlib import Path
path=Path('NANO-POS-Patch-1.0.118-to-2.0.9-PRAYER-CARD-PLACEMENT-FIX.zip')
with zipfile.ZipFile(path) as z: asar=z.read('payload/app.asar')
data=json.loads(Path('nano-pos-update.json').read_text(encoding='utf-8'))
date=datetime.date.today().isoformat()
features={
 'ar':['إصلاح عرض بطاقة مواقيت الصلاة بجانب المدير العام، مع جعل التحديث متاحًا من الإصدارات السابقة المدعومة.','اختيار المدينة والدولة وحفظ الموقع المختار.','تنبيه مرئي قبل كل صلاة بعشر دقائق مع تحديث المواقيت يوميًا.','الإبقاء على ميزة نطق سعر المنتج السابقة.'],
 'fr':['Correction de l’affichage des horaires de prière à côté du profil Directeur général et mise à jour depuis les versions précédentes prises en charge.','Sélection et mémorisation de la ville et du pays.','Alerte visuelle dix minutes avant chaque prière et mise à jour quotidienne.','Conservation de la lecture vocale du prix des produits.'],
 'en':['Fixes the prayer-times card beside the General Manager profile and enables updating from previously supported installed versions.','Choose and save the city and country with a location button.','Visual alert ten minutes before each prayer; refreshes daily.','Keeps the existing cart-price speech feature.']
}
fn=path.name
entry={'id':'nano-pos-v118-prayer-card-fix-v209','fromVersions':sorted(set([v for v in data.get('releaseHistory',{}) if tuple(map(int,v.split('.'))) >= (1,0,34)] + ['1.0.118'] + [f'2.0.{i}' for i in range(0,9)], key=lambda v:tuple(map(int,v.split('.')))),'directUrl':f'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.9/{fn}','pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.9','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'appAsarSha256':hashlib.sha256(asar).hexdigest(),'fileName':fn,'sizeBytes':path.stat().st_size,'payloadType':'app-asar'}
data['version']='2.0.9'; data['releaseDate']=date; data['published']=True; data['mandatory']=False; data['importance']='normal'; data['features']=features
data.setdefault('releaseHistory',{})['2.0.9']={'releaseDate':date,'features':features,'label':'إصلاحات'}
data['patches']=[entry]+[p for p in data.get('patches',[]) if p.get('id') not in ('nano-pos-v118-prayer-sidebar-v209','nano-pos-v118-prayer-card-fix-v209')]
Path('nano-pos-update.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Manifest prepared with verified patch hashes.')
