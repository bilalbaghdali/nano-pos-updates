#!/usr/bin/env python3
import os, json, hashlib, base64, subprocess
from pathlib import Path
repo=os.environ["GITHUB_REPOSITORY"]
name="NANO-POS-Patch-1.0.81-to-1.0.82-NOTIFICATIONS-FIX.zip"
zipfile=Path("/tmp/release")/name
asar=Path("/tmp/release/payload/app.asar")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def api(*args): return json.loads(subprocess.check_output(["gh","api",*args],text=True))
path=f"repos/{repo}/contents/nano-pos-update.json"
response=api(path)
data=json.loads(base64.b64decode(response["content"]))
if data.get("version")!="1.0.81": raise RuntimeError("Unexpected previous release")
if not zipfile.is_file() or not asar.is_file(): raise RuntimeError("Missing verified package")
ar=["تنبيهات حقيقية لنفاد المخزون ونقص الكميات واقتراب انتهاء الصلاحية والعروض.","عرض عدد التنبيهات على الجرس وفتح المنتج المتأثر مباشرة.","تحديث تلقائي مع حفظ البيانات والمزامنة دون تعديل آلية البيع."]
fr=["Alertes réelles de stocks bas, ruptures et dates de péremption.","Compteur sur la cloche et navigation vers les produits.","Mise à jour après modifications et synchronisation."]
en=["Real inventory, expiry and promotion alerts.","Notification count and affected-product navigation.","Automatic refresh after stock changes and synchronization."]
features={"ar":ar,"fr":fr,"en":en}
target="1.0.82"
data.update(version=target,releaseDate="2026-10-19",published=True,features=features,
 notes={"ar":"إصلاح نظام التنبيهات والجرس وعدّاد التنبيهات.","fr":"Correction des alertes et du compteur.","en":"Fixed live notification system and badge."})
data.setdefault("releaseHistory",{})[target]={"releaseDate":"2026-10-19","features":features}
base=f"https://github.com/{repo}/releases"
data["patches"]=[dict(id="nano-pos-v1.0.82-notifications",fromVersions=[f"1.0.{i}" for i in range(34,82)],
 directUrl=f"{base}/download/v{target}/{name}",pageUrl=f"{base}/tag/v{target}",sha256=sha(zipfile),
 appAsarSha256=sha(asar),fileName=name,sizeBytes=zipfile.stat().st_size,payloadType="app-asar")]
encoded=base64.b64encode((json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode()).decode()
result=api("-X","PUT",path,"-f","message=Publish 1.0.82 live notifications",
 "-f",f"content={encoded}","-f",f"sha={response['sha']}")
if not result.get("commit",{}).get("sha"): raise RuntimeError("Manifest commit failed")
verify=api(path)
check=json.loads(base64.b64decode(verify["content"]))
assert check["version"]==target and check["patches"][0]["sha256"]==sha(zipfile)
print("Published and checked manifest 1.0.82")
