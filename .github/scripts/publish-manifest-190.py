#!/usr/bin/env python3
"""Publish verified full installer and patch metadata for v1.0.90."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

exe,patch=map(Path,sys.argv[1:3])
assert exe.name=="NANO-POS-Setup-1.0.90-x64.exe" and exe.stat().st_size>20_000_000
assert patch.name=="NANO-POS-Patch-1.0.89-to-1.0.90-SECONDARY-LOGIN.zip"
with zipfile.ZipFile(patch) as z:
 assert z.namelist()==["payload/app.asar"]
 asar_sha=hashlib.sha256(z.read("payload/app.asar")).hexdigest()
p=Path("nano-pos-update.json")
d=json.loads(p.read_text(encoding="utf-8"))
assert d["version"]=="1.0.89" and d["published"],"Release base changed"
repo=os.environ["GITHUB_REPOSITORY"]
page=f"https://github.com/{repo}/releases/tag/v1.0.90"
url=f"https://github.com/{repo}/releases/download/v1.0.90/"
hashfile=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
features={
"ar":["إضافة خيار «الدخول ككمبيوتر ثانوي» مباشرة في صفحة تسجيل الدخول.",
"إمكانية إدخال IP الكمبيوتر الرئيسي عبر LAN أو Tailscale ورمز الاقتران واسم الكمبيوتر الثانوي.",
"اختبار الاتصال ومزامنة البيانات قبل السماح بالدخول، مع منع الدخول المحلي إذا تعذر الاتصال بالرئيسي.",
"إعادة استخدام الربط المحفوظ، مع بقاء الدخول العادي للكمبيوتر الرئيسي دون تغيير.",
"الحفاظ على بيانات البرنامج والتفعيل والنسخ الاحتياطية وأيقونة N."],
"fr":["Ajouter le mode PC secondaire à l'écran de connexion NANO POS.",
"Configurer l'adresse LAN/Tailscale, le code d'appairage et le nom du PC.",
"Vérifier l'hôte et synchroniser les données avant la connexion; refuser le repli local si l'hôte est inaccessible.",
"Réutiliser les connexions appairées tout en préservant le mode principal.",
"Conserver les données, licences, sauvegardes et la nouvelle icône N."],
"en":["Secondary computer sign-in option on the NANO POS login screen.",
"Configure primary PC IP over LAN/Tailscale, pairing code and secondary device name.",
"Verify host reachability and synchronize before login; block local fallback on connection failure.",
"Reuse saved pairing while preserving normal primary-PC login.",
"Preserve store records, licenses, backups and the new N icon."]}
date=dt.datetime.now(dt.timezone.utc).date().isoformat()
d.update(version="1.0.90",releaseDate=date,published=True,mandatory=False,importance="high",features=features)
d.setdefault("releaseHistory",{})["1.0.90"]={"releaseDate":date,"features":features}
d["download"]={"directUrl":url+exe.name,"pageUrl":page,"sha256":hashfile(exe),"fileName":exe.name,"sizeBytes":exe.stat().st_size}
d["patches"]=[{"id":"nano-pos-v1.0.90-secondary-login","fromVersions":["1.0.89"],"directUrl":url+patch.name,"pageUrl":page,"sha256":hashfile(patch),"appAsarSha256":asar_sha,"fileName":patch.name,"sizeBytes":patch.stat().st_size,"payloadType":"app-asar"}]
d["notes"]={"ar":"الدخول ككمبيوتر ثانوي من شاشة تسجيل الدخول، مع التحقق من اتصال الكمبيوتر الرئيسي قبل السماح بالدخول.","fr":"Connexion secondaire et vérification du PC principal depuis l'écran de connexion.","en":"Secondary PC login with primary connectivity check on sign-in."}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Published metadata v1.0.90","ZIP",d["patches"][0]["sha256"],"EXE",d["download"]["sha256"])
