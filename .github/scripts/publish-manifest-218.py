import datetime, hashlib, json, zipfile
from pathlib import Path

path = Path("NANO-POS-Patch-2.0.17-to-2.0.18-LICENSE-LABEL-FIX.zip")
with zipfile.ZipFile(path) as z:
    assert z.namelist() == ["payload/app.asar"], z.namelist()
    asar = z.read("payload/app.asar")
data = json.loads(Path("nano-pos-update.json").read_text(encoding="utf-8"))
assert data.get("version") == "2.0.17" and data.get("published"), "Manifest must start from published v2.0.17"
date = datetime.date.today().isoformat()
features = {
    "ar": ["تغيير عبارة زر الترخيص إلى «ازل الترخيص من البرنامج» بدلًا من «ازل الترخيص من المتصفح»، دون تغيير منطق التفعيل أو معرّف الجهاز."],
    "fr": ["Remplace le libellé arabe « retirer la licence du navigateur » par « retirer la licence du programme », sans modifier la logique d’activation ni l’identifiant de l’appareil."],
    "en": ["Changes the Arabic license-button label from removing the license from the browser to removing it from the program; activation logic and device identification are unchanged."]
}
filename = path.name
versions = set()
for version in data.get("releaseHistory", {}):
    try:
        if tuple(map(int, version.split("."))) >= (1, 0, 34):
            versions.add(version)
    except (TypeError, ValueError):
        pass
versions.update(["1.0.118"] + [f"2.0.{i}" for i in range(18)])
entry = {
    "id": "nano-pos-v118-license-label-program-v218",
    "fromVersions": sorted(versions, key=lambda v: tuple(map(int, v.split(".")))),
    "directUrl": f"https://raw.githubusercontent.com/bilalbaghdali/nano-pos-updates/main/downloads/{filename}",
    "pageUrl": "https://github.com/bilalbaghdali/nano-pos-updates/blob/main/downloads/NANO-POS-Patch-2.0.17-to-2.0.18-LICENSE-LABEL-FIX.zip",
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "appAsarSha256": hashlib.sha256(asar).hexdigest(),
    "fileName": filename,
    "sizeBytes": path.stat().st_size,
    "payloadType": "app-asar"
}
data["version"] = "2.0.18"
data["releaseDate"] = date
data["published"] = True
data["mandatory"] = False
data["importance"] = "normal"
data["features"] = features
data.setdefault("releaseHistory", {})["2.0.18"] = {"releaseDate": date, "features": features, "label": "تعديل عبارة الترخيص"}
data["patches"] = [entry] + [old for old in data.get("patches", []) if old.get("id") != entry["id"]]
Path("nano-pos-update.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Prepared v2.0.18 manifest with verified patch and ASAR hashes.")
