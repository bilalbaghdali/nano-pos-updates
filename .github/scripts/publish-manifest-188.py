#!/usr/bin/env python3
"""Update the stable channel only after the complete 1.0.88 EXE is published."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys

exe = Path(sys.argv[1])
assert exe.name == "NANO-POS-Setup-1.0.88-x64.exe" and exe.stat().st_size > 20_000_000
manifest_file = Path("nano-pos-update.json")
d = json.loads(manifest_file.read_text(encoding="utf-8"))
assert d["version"] == "1.0.87" and d["published"], "Release base changed; refusing to overwrite"
version = "1.0.88"
tag = "v"+version
repo = os.environ["GITHUB_REPOSITORY"]
release_url = f"https://github.com/{repo}/releases/tag/{tag}"
binary_url = f"https://github.com/{repo}/releases/download/{tag}/{exe.name}"
sha = hashlib.sha256(exe.read_bytes()).hexdigest()
features = {
  "ar": [
    "اعتماد أيقونة N مع واجهة متجر لأيقونة NANO POS على سطح المكتب وقائمة ابدأ.",
    "تضمين الأيقونة في ملف NANO POS.exe ومثبت Windows الجديد 64 بت.",
    "تحديث اختصار البرنامج دون تعديل بيانات المبيعات أو المخزون أو التفعيل."
  ],
  "fr": [
    "Nouvelle icône N et boutique sur le bureau et dans le menu Démarrer.",
    "Icône intégrée dans NANO POS.exe et dans l'installateur Windows 64 bits.",
    "Mise à jour des raccourcis sans toucher aux données ni à la licence."
  ],
  "en": [
    "New N storefront icon for desktop and Start menu shortcuts.",
    "Icon embedded in NANO POS.exe and the Windows 64-bit installer.",
    "Updated shortcuts without modifying store records or activation."
  ],
}
d["version"] = version
d["releaseDate"] = dt.datetime.now(dt.timezone.utc).date().isoformat()
d["features"] = features
d["releaseHistory"][version] = {"releaseDate": d["releaseDate"], "features": features}
d["download"] = {"directUrl": binary_url, "pageUrl": release_url, "sha256": sha, "fileName": exe.name, "sizeBytes": exe.stat().st_size}
# Icon modifications affect resources outside app.asar: no patch-only upgrade.
d["patches"] = []
d["notes"] = {"ar": "مثبت Windows كامل لتحديث أيقونة البرنامج واختصاراته.", "fr": "Installateur complet Windows avec nouvelle icône.", "en": "Full Windows installer for the new desktop icon."}
d["published"] = True
manifest_file.write_text(json.dumps(d, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print("Version:", version)
print("Installer SHA256:", sha)
print("Installer size:", exe.stat().st_size)
