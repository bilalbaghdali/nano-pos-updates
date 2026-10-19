#!/usr/bin/env python3
import os,json,hashlib,base64,subprocess
from pathlib import Path
repo=os.environ['GITHUB_REPOSITORY']
version='1.0.86'
name='NANO-POS-Patch-1.0.85-to-1.0.86-FAITH-AFTER-LOGIN.zip'
archive=Path('/tmp/release')/name
asar=Path('/tmp/release/payload/app.asar')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gh(*args):return json.loads(subprocess.check_output(['gh','api',*args],text=True))
key=f'repos/{repo}/contents/nano-pos-update.json'
original=gh(key);doc=json.loads(base64.b64decode(original['content']))
if doc['version']!='1.0.85':raise RuntimeError('Unexpected current version, not publishing')
if not archive.is_file() or not asar.is_file():raise RuntimeError('Missing verified archive or application')
features={
 'ar':['إظهار نافذة الآية أو الحديث فور تسجيل الدخول الناجح واكتمال تأثير الدخول.',
       'عدم إظهار النافذة قبل تسجيل الدخول أو عند فشله أو عند بدء جلسة محفوظة أو فك القفل.',
       'الإبقاء على 100 رسالة موثقة مختلفة مع الشرح والمصدر والتناوب المحفوظ دون المساس بالبيانات.'],
 'fr':['Fenêtre sourcée seulement après connexion réussie et animation terminée.',
       'Ne pas afficher avant connexion, en cas d’échec, en reprise de session ou au déverrouillage.',
       '100 messages sourcés et rotation enregistrée préservés.'],
 'en':['Show sourced reminder only after confirmed successful login and completed transition.',
       'Never display before login, on failed login, startup resume or unlock.',
       'Keep 100 verified messages, explanations, citations and persistent rotation.']}
base=f'https://github.com/{repo}/releases'
doc.update(version=version,published=True,releaseDate='2026-10-19',features=features,
 notes={'ar':'نافذة الآية والحديث تظهر فقط بعد تسجيل الدخول الناجح مع الحفاظ على 100 رسالة موثقة.',
        'fr':'Rappel uniquement après authentification réussie.',
        'en':'Reminder appears only after successful login.'})
doc.setdefault('releaseHistory',{})[version]={'releaseDate':'2026-10-19','features':features}
doc['patches']=[{'id':'nano-pos-v1.0.86-faith-after-login',
  'fromVersions':[f'1.0.{i}' for i in range(34,86)],
  'directUrl':f'{base}/download/v{version}/{name}','pageUrl':f'{base}/tag/v{version}',
  'sha256':digest(archive),'appAsarSha256':digest(asar),
  'fileName':name,'sizeBytes':archive.stat().st_size,'payloadType':'app-asar'}]
encoded=base64.b64encode((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()).decode()
result=gh('-X','PUT',key,'-f','message=Publish NANO POS v1.0.86 strict post-login faith reminder',
 '-f',f'content={encoded}','-f',f"sha={original['sha']}")
if not result.get('commit',{}).get('sha'):raise RuntimeError('Manifest update failed')
confirmed=json.loads(base64.b64decode(gh(key)['content']))
assert confirmed['version']==version and confirmed['patches'][0]['sha256']==digest(archive)
print('PASS: v1.0.86 patch published in autoupdate manifest')
