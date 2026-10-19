#!/usr/bin/env python3
import os, json, base64, hashlib, subprocess
from pathlib import Path
repo=os.environ['GITHUB_REPOSITORY']
target='1.0.83'
name='NANO-POS-Patch-1.0.82-to-1.0.83-SALES-ANALYTICS-FAITH.zip'
zipfile=Path('/tmp/release')/name
asar=Path('/tmp/release/payload/app.asar')
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
def api(*args):return json.loads(subprocess.check_output(['gh','api',*args],text=True))
path=f'repos/{repo}/contents/nano-pos-update.json'
old=api(path)
data=json.loads(base64.b64decode(old['content']))
if data['version']!='1.0.82':raise RuntimeError('Unexpected current version')
if not zipfile.is_file() or not asar.is_file():raise RuntimeError('Release file missing')
features={
'ar':['إصلاح تعديل الفاتورة الأصلية دون تسجيل بيع جديد أو تكرار خصم المخزون.','إصلاح تحليلات المنتج.','نافذة آية أو حديث موثق بعد تسجيل الدخول.'],
'fr':['Modification de la facture originale sans nouvelle vente.','Analyse de produit corrigée.','Verset ou hadith référencé après connexion.'],
'en':['Edit the original sale without creating a new one.','Repair product analytics.','Show a sourced verse or hadith after login.']}
data['version']=target;data['published']=True;data['releaseDate']='2026-10-19';data['features']=features
data.setdefault('releaseHistory',{})[target]={'releaseDate':'2026-10-19','features':features}
base=f'https://github.com/{repo}/releases'
data['patches']=[{'id':'nano-pos-v1.0.83','fromVersions':[f'1.0.{x}' for x in range(34,83)],'directUrl':f'{base}/download/v{target}/{name}','pageUrl':f'{base}/tag/v{target}','sha256':sha(zipfile),'appAsarSha256':sha(asar),'fileName':name,'sizeBytes':zipfile.stat().st_size,'payloadType':'app-asar'}]
data['notes']={'ar':'إصلاح تعديل الفواتير وتحليلات المنتج وإضافة النافذة الدينية الموثقة.','fr':'Factures, analyses et citations.','en':'Invoice editing, analytics and sourced reminder.'}
encoded=base64.b64encode((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()).decode()
result=api('-X','PUT',path,'-f','message=Publish 1.0.83 verified fixes','-f',f'content={encoded}','-f',f"sha={old['sha']}")
assert result.get('commit',{}).get('sha')
check=api(path);updated=json.loads(base64.b64decode(check['content']))
assert updated['version']==target and updated['patches'][0]['sha256']==sha(zipfile)
print('Published v1.0.83 auto-update')
