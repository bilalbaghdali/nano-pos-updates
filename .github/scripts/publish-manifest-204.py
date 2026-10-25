import json,hashlib,zipfile,datetime
from pathlib import Path
path=Path('NANO-POS-Patch-1.0.118-to-2.0.4-PRAYER-SIDEBAR.zip')
with zipfile.ZipFile(path) as z: asar=z.read('payload/app.asar')
data=json.loads(Path('nano-pos-update.json').read_text(encoding='utf-8'))
date=datetime.date.today().isoformat()
features={
 'ar':['لوحة جانبية قابلة للفتح والإغلاق لمواقيت الصلاة، لا تظهر فوق واجهة البرنامج عند الإغلاق.','زر لاختيار المدينة والدولة وحفظ الموقع المختار.','تنبيه مرئي قبل كل صلاة بعشر دقائق، مع تحديث المواقيت يوميًا.','الإبقاء على ميزة نطق سعر المنتج السابقة.'],
 'fr':['Panneau latéral repliable pour les horaires de prière, masqué lorsqu’il n’est pas utilisé.','Bouton de sélection et mémorisation de la ville et du pays.','Alerte visuelle dix minutes avant chaque prière et mise à jour quotidienne.','Conservation de la lecture vocale du prix des produits.'],
 'en':['Adds a collapsible side panel for prayer times, hidden when not in use.','Choose and save the city and country with a location button.','Visual alert ten minutes before each prayer; refreshes daily.','Keeps the existing cart-price speech feature.']
}
fn=path.name
entry={'id':'nano-pos-v118-prayer-sidebar-v204','fromVersions':['1.0.118','2.0.0','2.0.1','2.0.2','2.0.3'],'directUrl':f'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.4/{fn}','pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.4','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'appAsarSha256':hashlib.sha256(asar).hexdigest(),'fileName':fn,'sizeBytes':path.stat().st_size,'payloadType':'app-asar'}
data['version']='2.0.4'; data['releaseDate']=date; data['published']=True; data['mandatory']=False; data['importance']='normal'; data['features']=features
data.setdefault('releaseHistory',{})['2.0.4']={'releaseDate':date,'features':features}
data['patches']=[p for p in data.get('patches',[]) if p.get('id')!='nano-pos-v118-prayer-sidebar-v204']+[entry]
Path('nano-pos-update.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Manifest prepared with verified patch hashes.')
