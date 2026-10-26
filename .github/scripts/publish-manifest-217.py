import json,hashlib,zipfile,datetime
from pathlib import Path
path=Path('NANO-POS-Patch-1.0.118-to-2.0.17-STATISTICS-CHARTS-AUTOMATIC.zip')
with zipfile.ZipFile(path) as z:
    assert z.namelist()==['payload/app.asar'], z.namelist()
    asar=z.read('payload/app.asar')
data=json.loads(Path('nano-pos-update.json').read_text(encoding='utf-8'))
date=datetime.date.today().isoformat()
features={
 'ar':[
  'ترقية قسم الرسوم البيانية بمخططات دائرية وأعمدة مترابطة مع المبيعات والمشتريات والمصاريف والمخزون.',
  'مقارنة البيع والشراء عبر الزمن؛ يعرض البيانات يوميًا أو شهريًا أو ربع سنويًا وفق الفترة المختارة.',
  'مخطط حركة الصندوق للجلسة المفتوحة، مع عرض حركة الفترة المحددة عند عدم وجود جلسة مفتوحة.',
  'توزيع وحدات المخزون حسب الفئة ومقارنة قيمة المخزون بالتكلفة وقيمته المحتملة بسعر البيع.',
  'تحديث الرسوم تلقائيًا بعد حفظ عمليات البيع والشراء والمخزون، وكذلك بعد المزامنة، دون تعديل بيانات المتجر.',
  'الحفاظ على نطق سعر المنتج وإزالة مواقيت الصلاة.'
 ],
 'fr':[
  'Ajout de graphiques circulaires et en barres liés aux ventes, achats, dépenses et au stock.',
  'Comparaison des ventes et achats dans le temps, par jour, mois ou trimestre selon la période choisie.',
  'Graphique de la caisse pour la session ouverte, ou des flux de la période sélectionnée en l’absence de session.',
  'Répartition des unités en stock par catégorie et comparaison de la valeur au coût avec la valeur de vente potentielle.',
  'Actualisation automatique après les opérations et la synchronisation, sans modifier les données du magasin.',
  'Conservation de la lecture vocale du prix et suppression des horaires de prière.'
 ],
 'en':[
  'Adds connected pie and bar charts for sales, purchases, expenses, cash-register activity, and inventory.',
  'Compares sales and purchases over time, grouped daily, monthly, or quarterly according to the selected period.',
  'Shows movements for the open cash session, or selected-period cash flows when no session is open.',
  'Breaks down stocked units by category and compares inventory cost with potential sale value.',
  'Automatically refreshes charts after saved transactions and synchronization without modifying store data.',
  'Retains spoken product prices and removes the prayer-times feature.'
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
versions.update(['1.0.118']+[f'2.0.{i}' for i in range(17)])
entry={
 'id':'nano-pos-v118-automatic-operational-charts-v217',
 'fromVersions':sorted(versions,key=lambda v:tuple(map(int,v.split('.')))),
 'directUrl':f'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.17/{filename}',
 'pageUrl':'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.17',
 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'appAsarSha256':hashlib.sha256(asar).hexdigest(),
 'fileName':filename,
 'sizeBytes':path.stat().st_size,
 'payloadType':'app-asar'
}
data['version']='2.0.17'
data['releaseDate']=date
data['published']=True
data['mandatory']=False
data['importance']='normal'
data['features']=features
data.setdefault('releaseHistory',{})['2.0.17']={'releaseDate':date,'features':features,'label':'إحصائيات ذكية'}
old_prayer_tokens=('prayer-times','prayer-card','prayer-sidebar','prayer-home','prayer-popover','prayer-icon','prayer-banner')
kept=[]
for old in data.get('patches',[]):
    marker=(str(old.get('id',''))+' '+str(old.get('fileName',''))).lower()
    if old.get('id')=='nano-pos-v118-automatic-operational-charts-v217':
        continue
    if any(token in marker for token in old_prayer_tokens):
        continue
    kept.append(old)
data['patches']=[entry]+kept
Path('nano-pos-update.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared v2.0.17 manifest with verified ZIP and ASAR hashes.')
