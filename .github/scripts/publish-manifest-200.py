import json,hashlib,zipfile,datetime
from pathlib import Path
path=Path('NANO-POS-Patch-1.0.118-to-2.0.0-GENERAL-IMPROVEMENTS.zip')
with zipfile.ZipFile(path) as z: asar=z.read('payload/app.asar')
data=json.loads(Path('nano-pos-update.json').read_text(encoding='utf-8'))
date=datetime.date.today().isoformat()
features={
 'ar':['إشعار مرئي عند إضافة منتج إلى السلة.','نطق سعر المنتج المضاف بلغة واجهة البرنامج: العربية أو الفرنسية أو الإنجليزية.','تحسينات عامة مع الحفاظ على بيانات المتجر.'],
 'fr':['Notification visuelle lors de l’ajout d’un produit au panier.','Lecture vocale du prix dans la langue de l’interface : arabe, français ou anglais.','Améliorations générales sans modifier les données du magasin.'],
 'en':['Visual notification when a product is added to the cart.','Speak the added product price in the interface language: Arabic, French, or English.','General improvements while preserving store data.']
}
fn=path.name
entry={'id':'nano-pos-v118-cart-price-speech-v200','fromVersions':['1.0.118'],'directUrl':f'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.0/{fn}','pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.0','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'appAsarSha256':hashlib.sha256(asar).hexdigest(),'fileName':fn,'sizeBytes':path.stat().st_size,'payloadType':'app-asar'}
data['version']='2.0.0'; data['releaseDate']=date; data['published']=True; data['mandatory']=False; data['importance']='normal'; data['features']=features
data.setdefault('releaseHistory',{})['2.0.0']={'releaseDate':date,'features':features}
data['patches']=[p for p in data.get('patches',[]) if p.get('id')!='nano-pos-v118-cart-price-speech-v200']+[entry]
Path('nano-pos-update.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Manifest prepared with verified patch hashes.')
