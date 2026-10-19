#!/usr/bin/env python3
"""Enable v1.0.85 only after verified release publication."""
import os,hashlib,json,base64,subprocess
from pathlib import Path
repo=os.environ["GITHUB_REPOSITORY"]
version="1.0.85"
name="NANO-POS-Patch-1.0.84-to-1.0.85-FAITH-100-LOGIN-FIX.zip"
archive=Path("/tmp/release")/name
asar=Path("/tmp/release/payload/app.asar")
def checksum(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def api(*args):return json.loads(subprocess.check_output(["gh","api",*args],text=True))
f=f"repos/{repo}/contents/nano-pos-update.json"
original=api(f)
data=json.loads(base64.b64decode(original["content"]))
if data.get("version")!="1.0.84":raise RuntimeError("Refusing update on unexpected version")
if not archive.is_file() or not asar.is_file():raise RuntimeError("Release artifacts missing")
features={
 "ar":["إصلاح عدم ظهور نافذة الآية أو الحديث بربطها بنجاح تسجيل الدخول الفعلي، ودعم استئناف الجلسة.",
       "زيادة المحتوى إلى 100 رسالة مختلفة: 80 آية من القرآن الكريم بتفسير الميسر و20 حديثًا صحيحًا من البخاري ومسلم.",
       "حفظ ترتيب الرسائل بين تشغيلات التطبيق وتجنب التكرار حتى اكتمال دورة المئة.",
       "عرض نص كل آية أو حديث وشرح مختصر ومصدر موثق ورابط للمراجعة، دون تغيير وظائف البيع."],
 "fr":["Correction de la fenêtre après l’authentification, y compris la reprise de session.",
       "100 citations vérifiées: 80 versets avec Tafsir Muyassar et 20 hadiths Sahih.",
       "Rotation persistante sans doublon avant les 100 messages."],
 "en":["Fix missing reminder after real login, including session resume.",
       "100 unique verified messages: 80 Quran verses with Muyassar tafsir and 20 Sahih hadith.",
       "Persistent, nonrepeating 100-message rotation and source links."]}
base=f"https://github.com/{repo}/releases"
data.update(version=version,published=True,releaseDate="2026-10-19",features=features,
 notes={"ar":"إصلاح ظهور نافذة الآية والحديث وزيادة المحتوى إلى 100 رسالة موثقة.",
        "fr":"Fenêtre de rappel fonctionnelle et 100 textes sourcés.",
        "en":"Reliable post-login reminder and 100 verified items."})
data.setdefault("releaseHistory",{})[version]={"releaseDate":"2026-10-19","features":features}
data["patches"]=[dict(id="nano-pos-v1.0.85-faith-100-login-fix",
 fromVersions=[f"1.0.{n}" for n in range(34,85)],
 directUrl=f"{base}/download/v{version}/{name}",pageUrl=f"{base}/tag/v{version}",
 sha256=checksum(archive),appAsarSha256=checksum(asar),
 fileName=name,sizeBytes=archive.stat().st_size,payloadType="app-asar")]
blob=base64.b64encode((json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode()).decode()
written=api("-X","PUT",f,"-f","message=Publish NANO POS v1.0.85 100-message login reminder fix",
 "-f",f"content={blob}","-f",f"sha={original['sha']}")
if not written.get("commit",{}).get("sha"):raise RuntimeError("Manifest update failed")
latest=json.loads(base64.b64decode(api(f)["content"]))
if latest.get("version")!=version or latest["patches"][0]["sha256"]!=checksum(archive):
 raise RuntimeError("Manifest verification failed")
print("PASS: 1.0.85 automatic update active with verified checksum")
