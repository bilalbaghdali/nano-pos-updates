#!/usr/bin/env python3
import base64,hashlib,json,os,subprocess
from pathlib import Path
repo=os.environ['GITHUB_REPOSITORY']
version='1.0.84'
filename='NANO-POS-Patch-1.0.83-to-1.0.84-FAITH-ROTATION.zip'
zipfile=Path('/tmp/release')/filename
asar=Path('/tmp/release/payload/app.asar')
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def gh(*args):return json.loads(subprocess.check_output(['gh','api',*args],text=True))
target=f'repos/{repo}/contents/nano-pos-update.json'
response=gh(target)
data=json.loads(base64.b64decode(response['content']))
if data.get('version')!='1.0.83':raise RuntimeError('Refusing to overwrite an unexpected release')
if not zipfile.is_file() or not asar.is_file():raise RuntimeError('Missing verified build artifacts')
features={
 'ar':['تغيير الآية أو الحديث تلقائيًا بعد كل تسجيل دخول ناجح، حتى بعد إغلاق البرنامج وإعادة فتحه.',
       'إضافة ست رسائل موثقة من القرآن الكريم وصحيحي البخاري ومسلم، بالتناوب دون تكرار قبل انتهاء الدورة.',
       'الإبقاء على شرح كل رسالة ومصدرها ورابطها وإمكانية إغلاقها للمتابعة.'],
 'fr':['Un verset ou hadith différent après chaque connexion, même après redémarrage.',
       'Six citations vérifiées alternent sans répétition avant la fin du cycle.',
       'Sources, explications et fermeture conservées.'],
 'en':['Show a different Quran verse or authentic hadith at every successful login, even after restarting.',
       'Six verified reminders rotate without repetition until the full set has been shown.',
       'Keep source links, brief explanations and dismiss action.']
}
base=f'https://github.com/{repo}/releases'
data.update(version=version,published=True,releaseDate='2026-10-19',features=features,notes={
 'ar':'تغيير الآية والحديث بعد كل تسجيل دخول وحفظ ترتيب النصوص بين تشغيلات NANO POS.',
 'fr':'Rotation persistante des rappels sourcés après chaque connexion.',
 'en':'Persistent rotation of sourced reminders after each login.'})
data.setdefault('releaseHistory',{})[version]={'releaseDate':'2026-10-19','features':features}
data['patches']=[{'id':'nano-pos-v1.0.84-faith-rotation',
 'fromVersions':[f'1.0.{n}' for n in range(34,84)],
 'directUrl':f'{base}/download/v{version}/{filename}',
 'pageUrl':f'{base}/tag/v{version}', 'sha256':digest(zipfile),
 'appAsarSha256':digest(asar),'fileName':filename,
 'sizeBytes':zipfile.stat().st_size,'payloadType':'app-asar'}]
blob=base64.b64encode((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()).decode()
result=gh('-X','PUT',target,'-f','message=Publish verified NANO POS 1.0.84 persistent faith reminders',
 '-f',f'content={blob}','-f',f"sha={response['sha']}")
if not result.get('commit',{}).get('sha'):raise RuntimeError('Manifest update failed')
check=gh(target);updated=json.loads(base64.b64decode(check['content']))
if updated.get('version')!=version or updated['patches'][0]['sha256']!=digest(zipfile):
 raise RuntimeError('Manifest verification failed')
print('PASS: v1.0.84 automatic update activated and checksum verified')
