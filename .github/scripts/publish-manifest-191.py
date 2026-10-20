#!/usr/bin/env python3
"""Publish NANO POS 1.0.91 only after both Windows installer and ZIP are released."""
import datetime as dt
import hashlib,json,os,sys,zipfile
from pathlib import Path
exe,patch=map(Path,sys.argv[1:3])
assert exe.name=="NANO-POS-Setup-1.0.91-x64.exe" and exe.stat().st_size>20_000_000
assert patch.name=="NANO-POS-Patch-1.0.90-to-1.0.91-VISIBLE-SECONDARY-LOGIN.zip"
with zipfile.ZipFile(patch) as z:
 assert z.namelist()==["payload/app.asar"]
 asarsha=hashlib.sha256(z.read("payload/app.asar")).hexdigest()
path=Path("nano-pos-update.json")
d=json.loads(path.read_text(encoding="utf-8"))
assert d["version"]=="1.0.90" and d["published"]
owner=os.environ["GITHUB_REPOSITORY"]
url=f"https://github.com/{owner}/releases/download/v1.0.91/"
page=f"https://github.com/{owner}/releases/tag/v1.0.91"
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
features={
 "ar":["إصلاح عدم ظهور خيارات الكمبيوتر الرئيسي والثانوي داخل شاشة تسجيل الدخول.","عرض خيار نوع الكمبيوتر مباشرة في واجهة الدخول حتى لو تأخر تحميل JavaScript.","إظهار IP الكمبيوتر الرئيسي ورمز الاقتران واسم الكمبيوتر عند اختيار الدخول الثانوي.","ضمان قابلية تمرير نافذة الدخول على الشاشات الصغيرة مع الحفاظ على شرط الاتصال بالرئيسي.","الحفاظ على بيانات البيع والمخزون والتفعيل وأيقونة N."],
 "fr":["Corrige les options de connexion PC principal/secondaire manquantes.","Le choix du mode est directement intégré à l'écran de connexion.","Champs d'adresse IP, de code de liaison et de nom d'appareil en mode secondaire.","Défilement corrigé pour petits écrans et blocage de connexion si l'hôte est indisponible.","Aucune modification des données, des licences ou de l'icône N."],
 "en":["Fixed missing primary/secondary computer options on the login screen.","Role selection is embedded directly in the login layout, independent of JavaScript initialization.","Host IP, pairing code and device name appear when secondary login is selected.","Scrollable login on small screens; host-connection safety check preserved.","Sales data, inventory, activation and N icon retained."]
}
date=dt.datetime.now(dt.timezone.utc).date().isoformat()
d.update(version="1.0.91",published=True,mandatory=False,importance="high",releaseDate=date,features=features)
d.setdefault("releaseHistory",{})["1.0.91"]={"releaseDate":date,"features":features}
d["download"]={"directUrl":url+exe.name,"pageUrl":page,"sha256":sha(exe),"fileName":exe.name,"sizeBytes":exe.stat().st_size}
d["patches"]=[{"id":"nano-pos-v1.0.91-visible-secondary-login","fromVersions":["1.0.90"],"directUrl":url+patch.name,"pageUrl":page,"sha256":sha(patch),"appAsarSha256":asarsha,"fileName":patch.name,"sizeBytes":patch.stat().st_size,"payloadType":"app-asar"}]
d["notes"]={"ar":"إصلاح ظهور خيارات الدخول على صفحة تسجيل الدخول واستمرار الربط الآمن بالرئيسي.","fr":"Correction de l'affichage du mode de connexion principal/secondaire.","en":"Fixed primary/secondary login selection visibility."}
path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("v1.0.91 EXE",d["download"]["sha256"],"ZIP",d["patches"][0]["sha256"])
