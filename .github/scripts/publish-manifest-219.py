import datetime, hashlib, json, zipfile
from pathlib import Path

PATCH = Path("NANO-POS-Patch-2.0.18-to-2.0.19-MOTHERBOARD-ID-RECOVERY.zip")
with zipfile.ZipFile(PATCH) as archive:
    assert archive.namelist() == ["payload/app.asar"], archive.namelist()
    asar = archive.read("payload/app.asar")
data = json.loads(Path("nano-pos-update.json").read_text(encoding="utf-8"))
assert data.get("version") == "2.0.18" and data.get("published"), "Manifest must start from published v2.0.18"
date = datetime.date.today().isoformat()
features = {
    "ar": [
        "معرف جديد ثابت مشتق من الرقم التسلسلي للوحة الأم، مع استخدام UUID النظام كبديل عندما لا يتوفر رقم صالح.",
        "الحفاظ على معرفات وتفعيلات الإصدارات الحالية وعدم تغيير بيانات المتجر أو النسخ الاحتياطية.",
        "إضافة حفظ واستعادة ملف التفعيل على الكمبيوتر نفسه بعد إعادة تثبيت Windows؛ يجب حفظ الملف خارج الكمبيوتر."
    ],
    "fr": [
        "Nouvel identifiant stable dérivé du numéro de série de la carte mère, avec l’UUID système comme solution de secours.",
        "Conserve les identifiants et activations déjà présents sans modifier les données ni les sauvegardes du magasin.",
        "Ajout d’une sauvegarde/restauration de licence sur le même ordinateur après réinstallation de Windows ; gardez le fichier hors du PC."
    ],
    "en": [
        "New stable device ID derived from the motherboard serial number, with the system UUID as a fallback.",
        "Preserves existing activation IDs and licenses without changing store data or backups.",
        "Adds activation recovery on the same computer after reinstalling Windows; keep the recovery file off the PC."
    ]
}
versions = set()
for value in data.get("releaseHistory", {}):
    try:
        parts = tuple(int(x) for x in value.split("."))
        if parts >= (1, 0, 34) and len(parts) == 3:
            versions.add(value)
    except (ValueError, TypeError):
        pass
versions.update(["1.0.118"] + [f"2.0.{i}" for i in range(20)])
entry = {
    "id": "nano-pos-v118-motherboard-id-recovery-v219",
    "fromVersions": sorted(versions, key=lambda v: tuple(int(x) for x in v.split("."))),
    "directUrl": "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.19/" + PATCH.name,
    "pageUrl": "https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.19",
    "sha256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
    "appAsarSha256": hashlib.sha256(asar).hexdigest(),
    "fileName": PATCH.name,
    "sizeBytes": PATCH.stat().st_size,
    "payloadType": "app-asar"
}
data["version"] = "2.0.19"
data["releaseDate"] = date
data["published"] = True
data["mandatory"] = False
data["importance"] = "normal"
data["features"] = features
data.setdefault("releaseHistory", {})["2.0.19"] = {
    "releaseDate": date, "features": features, "label": "تحسينات عامة"
}
data["patches"] = [entry] + [old for old in data.get("patches", []) if old.get("id") != entry["id"]]
Path("nano-pos-update.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"version":"2.0.19","patch":PATCH.name,"patchSha256":entry["sha256"],"appAsarSha256":entry["appAsarSha256"],"sizeBytes":entry["sizeBytes"],"fromVersionCount":len(entry["fromVersions"]),"features":features["ar"]},ensure_ascii=True))
