#!/usr/bin/env python3
import datetime, hashlib, json, zipfile
from pathlib import Path

PATCH = Path("NANO-POS-Patch-2.0.20-to-2.0.21-MANUFACTURING-CENTER.zip")
BASE_VERSION = "2.0.20"
NEW_VERSION = "2.0.21"

with zipfile.ZipFile(PATCH) as archive:
    assert archive.namelist() == ["payload/app.asar"], archive.namelist()
    asar = archive.read("payload/app.asar")

data = json.loads(Path("nano-pos-update.json").read_text(encoding="utf-8"))
assert data.get("version") == BASE_VERSION and data.get("published"), "Manifest must start from published v2.0.20"
date = datetime.date.today().isoformat()
features = {
    "ar": [
        "تطوير شاشة التصنيع إلى مركز تشغيل واضح مع اختصارات للتركيبات وأوامر الإنتاج والمكونات والدفعات.",
        "إضافة بحث فوري داخل جداول التصنيع مع مؤشرات للصفوف المعروضة والتنبيهات التي تحتاج مراجعة.",
        "إضافة قائمة تحقق قبل تأكيد الإنتاج وتصميم متجاوب مع واجهة الكمبيوتر والهاتف؛ مع الحفاظ على منطق المخزون والتفعيل والنسخ الاحتياطي."
    ],
    "fr": [
        "Amélioration de l’écran de fabrication avec des raccourcis vers les recettes, les ordres de production, les composants et les lots.",
        "Ajout d’une recherche instantanée dans les tableaux et d’indicateurs sur les lignes affichées et à vérifier.",
        "Ajout d’une liste de contrôle avant confirmation et d’une interface adaptative, tout en conservant la logique de stock, l’activation et les sauvegardes."
    ],
    "en": [
        "Improved manufacturing screen with quick access to recipes, production orders, components, and batches.",
        "Added live search across manufacturing tables and indicators for displayed rows that need review.",
        "Added a pre-confirmation checklist and responsive layout while preserving inventory logic, activation, and backups."
    ]
}

versions = set()
for patch in data.get("patches", []):
    for value in patch.get("fromVersions", []):
        if isinstance(value, str) and value.count(".") == 2:
            versions.add(value)
for value in data.get("releaseHistory", {}):
    if isinstance(value, str) and value.count(".") == 2:
        versions.add(value)
versions.add("1.0.118")
versions.add(BASE_VERSION)
def version_key(value):
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError:
        return (0, 0, 0)
versions = sorted(versions, key=version_key)

filename = PATCH.name
entry = {
    "id": "nano-pos-v221-manufacturing-center",
    "fromVersions": versions,
    "directUrl": "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.21/" + filename,
    "pageUrl": "https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.21",
    "sha256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
    "appAsarSha256": hashlib.sha256(asar).hexdigest(),
    "fileName": filename,
    "sizeBytes": PATCH.stat().st_size,
    "payloadType": "app-asar"
}
data["version"] = NEW_VERSION
data["releaseDate"] = date
data["published"] = True
data["mandatory"] = False
data["importance"] = "normal"
data["features"] = features
data.setdefault("releaseHistory", {})[NEW_VERSION] = {
    "releaseDate": date,
    "features": features,
    "label": "تحسينات عامة"
}
data["patches"] = [entry] + [
    patch for patch in data.get("patches", [])
    if patch.get("id") != entry["id"]
]
Path("nano-pos-update.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "version": NEW_VERSION,
    "patch": filename,
    "patchSha256": entry["sha256"],
    "appAsarSha256": entry["appAsarSha256"],
    "sizeBytes": entry["sizeBytes"],
    "supportedSourceVersions": len(versions),
    "featuresAr": features["ar"]
}, ensure_ascii=True))
