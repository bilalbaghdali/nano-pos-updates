import json,hashlib,zipfile,datetime
from pathlib import Path
path=Path('NANO-POS-Patch-1.0.118-to-2.0.14-PRAYER-TIMES-FIXED-OVERLAY-VISIBILITY-FIX.zip')
with zipfile.ZipFile(path) as z: asar=z.read('payload/app.asar')
data=json.loads(Path('nano-pos-update.json').read_text(encoding='utf-8'))
date=datetime.date.today().isoformat()
features={
 'ar':['إصلاح ظهور بطاقة مواقيت الصلاة بجانب المدير العام، مع مواقيت الصلاة والتاريخين الهجري والميلادي والعد التنازلي.','اختيار المدينة والدولة وحفظ الموقع المختار.','تصحيح تحليل أوقات الصلاة وإظهار العد التنازلي مع تحديث المواقيت يوميًا.','الإبقاء على ميزة نطق سعر المنتج السابقة.'],
 'fr':['Correction de la visibilité de la carte des prières près du profil Directeur général, avec horaires, dates hégirienne et grégorienne et compte à rebours.','Sélection et mémorisation de la ville et du pays.','Compte à rebours corrigé et mise à jour quotidienne des horaires.','Conservation de la lecture vocale du prix des produits.'],
 'en':['Fixes the visibility and placement of the prayer card beside the General Manager profile, including prayer times, Hijri/Gregorian dates, and countdown.','Choose and save the city and country with a location button.','Corrected countdown and daily prayer-time refresh.','Keeps the existing cart-price speech feature.']
}
fn=path.name
entry={'id':'nano-pos-v118-prayer-card-visibility-v214','fromVersions':sorted(set([v for v in data.get('releaseHistory',{}) if tuple(map(int,v.split('.'))) >= (1,0,34)] + ['1.0.118'] + [f'2.0.{i}' for i in range(0,14)]), key=lambda v:tuple(map(int,v.split('.')))),'directUrl':f'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.14/{fn}','pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.14','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'appAsarSha256':hashlib.sha256(asar).hexdigest(),'fileName':fn,'sizeBytes':path.stat().st_size,'payloadType':'app-asar'}
data['version']='2.0.14'; data['releaseDate']=date; data['published']=True; data['mandatory']=False; data['importance']='normal'; data['features']=features
data.setdefault('releaseHistory',{})['2.0.14']={'releaseDate':date,'features':features,'label':'إصلاحات'}
data['patches']=[entry]+[p for p in data.get('patches',[]) if p.get('id') not in ('nano-pos-v118-prayer-sidebar-v214','nano-pos-v118-prayer-card-visibility-v214')]
Path('nano-pos-update.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Manifest prepared with verified patch hashes.')
