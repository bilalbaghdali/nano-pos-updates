import json,hashlib,zipfile,datetime
from pathlib import Path
path=Path('NANO-POS-Patch-1.0.118-to-2.0.15-PRAYER-BANNER-PLACEMENT-AND-TIMING-FIX.zip')
with zipfile.ZipFile(path) as z: asar=z.read('payload/app.asar')
data=json.loads(Path('nano-pos-update.json').read_text(encoding='utf-8'))
date=datetime.date.today().isoformat()
features={
 'ar':['إصلاح تثبيت بطاقة مواقيت الصلاة داخل البنر الرئيسي بجانب المدير العام ومنع انتقالها بين العناصر.','إصلاح تحليل أوقات الصلاة وعرض الصلوات الست بما فيها الشروق مع التاريخين والعد التنازلي.','حفظ المنطقة المختارة وتحديث المواقيت يوميًا دون تغيير بيانات المتجر.','الإبقاء على ميزة نطق سعر المنتج السابقة.'],
 'fr':['Maintient la carte des horaires de prière dans la bannière principale, à côté du Directeur général, sans déplacement intempestif.','Corrige l’analyse des horaires et affiche les six horaires, lever du soleil inclus, avec les dates et le compte à rebours.','Conserve la région choisie et actualise les horaires chaque jour sans modifier les données du magasin.','Conserve la lecture vocale du prix des produits.'],
 'en':['Keeps the prayer card in the main banner beside the General Manager and prevents it moving between elements.','Fixes prayer-time parsing and shows all six times, including sunrise, dates, and countdown.','Preserves the selected region and refreshes timings daily without changing store data.','Keeps the existing cart-price speech feature.']
}
fn=path.name
entry={'id':'nano-pos-v118-prayer-card-visibility-v215','fromVersions':sorted(set([v for v in data.get('releaseHistory',{}) if tuple(map(int,v.split('.'))) >= (1,0,34)] + ['1.0.118'] + [f'2.0.{i}' for i in range(0,15)]), key=lambda v:tuple(map(int,v.split('.')))),'directUrl':f'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.15/{fn}','pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.15','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'appAsarSha256':hashlib.sha256(asar).hexdigest(),'fileName':fn,'sizeBytes':path.stat().st_size,'payloadType':'app-asar'}
data['version']='2.0.15'; data['releaseDate']=date; data['published']=True; data['mandatory']=False; data['importance']='normal'; data['features']=features
data.setdefault('releaseHistory',{})['2.0.15']={'releaseDate':date,'features':features,'label':'إصلاحات'}
data['patches']=[entry]+[p for p in data.get('patches',[]) if p.get('id') not in ('nano-pos-v118-prayer-sidebar-v215','nano-pos-v118-prayer-card-visibility-v215')]
Path('nano-pos-update.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Manifest prepared with verified patch hashes.')
