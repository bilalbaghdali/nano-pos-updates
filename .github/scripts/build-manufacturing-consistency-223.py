import hashlib, json, os, struct, sys, zipfile
from pathlib import Path

SOURCE = Path(sys.argv[1])
OUT_ZIP = Path("NANO-POS-Patch-2.0.22-to-2.0.23-MANUFACTURING-UI-CONSISTENCY.zip")
OUT_ASAR = Path("app-2.0.23.asar")
MANIFEST = Path("nano-pos-update.json")
VERSION = "2.0.23"
PATCH_NAME = OUT_ZIP.name
PATCH_ID = "nano-pos-v223-manufacturing-ui-consistency"
CSS = r"""
<style id="nano-mfg-consistency-v223">
/* NANO POS 2.0.23 — manufacturing screen visual consistency only */
#manufacturingSection { color: #0f172a; }
#manufacturingSection #mfgRoot { min-width: 0; gap: 1rem; }
#manufacturingSection #mfgRoot h1,
#manufacturingSection #mfgRoot h2,
#manufacturingSection #mfgRoot h3 { color: #0f172a; letter-spacing: -0.015em; line-height: 1.35; }
#manufacturingSection #mfgRoot h1 { font-size: clamp(1.35rem, 2vw, 1.75rem); font-weight: 800; }
#manufacturingSection #mfgRoot h2 { font-size: clamp(1.05rem, 1.5vw, 1.25rem); font-weight: 750; }
#manufacturingSection #mfgRoot h3 { font-weight: 700; }
#manufacturingSection #mfgRoot .bg-white,
#manufacturingSection #mfgRoot [class*="bg-white"] { border-color: #e2e8f0; }
#manufacturingSection #mfgRoot .rounded-xl,
#manufacturingSection #mfgRoot .rounded-2xl,
#manufacturingSection #mfgRoot .rounded-3xl { border-radius: 0.9rem; }
#manufacturingSection #mfgRoot .shadow,
#manufacturingSection #mfgRoot .shadow-md,
#manufacturingSection #mfgRoot .shadow-lg,
#manufacturingSection #mfgRoot .shadow-xl { box-shadow: 0 4px 16px rgba(15,23,42,.055); }
#manufacturingSection #mfgRoot input:not([type="checkbox"]):not([type="radio"]),
#manufacturingSection #mfgRoot select,
#manufacturingSection #mfgRoot textarea { min-width: 0; max-width: 100%; border: 1px solid #cbd5e1; border-radius: .65rem; background-color: #fff; color: #0f172a; padding: .55rem .75rem; transition: border-color .15s ease, box-shadow .15s ease; }
#manufacturingSection #mfgRoot input:focus,
#manufacturingSection #mfgRoot select:focus,
#manufacturingSection #mfgRoot textarea:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,.13); }
#manufacturingSection #mfgRoot button { border-radius: .65rem; font-weight: 650; transition: filter .15s ease, box-shadow .15s ease, transform .15s ease; }
#manufacturingSection #mfgRoot button:hover { filter: brightness(.98); }
#manufacturingSection #mfgRoot button:focus-visible { outline: 3px solid rgba(37,99,235,.28); outline-offset: 2px; }
#manufacturingSection #mfgRoot table { width: 100%; border-collapse: separate; border-spacing: 0; }
#manufacturingSection #mfgRoot th { color: #475569; font-weight: 750; background: #f8fafc; }
#manufacturingSection #mfgRoot th,
#manufacturingSection #mfgRoot td { padding: .7rem .8rem; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
#manufacturingSection #mfgRoot .overflow-x-auto { max-width: 100%; overscroll-behavior-x: contain; }
#manufacturingSection #mfgRoot img,
#manufacturingSection #mfgRoot svg { max-width: 100%; }
@media (max-width: 768px) {
  #manufacturingSection { padding: 1rem !important; }
  #manufacturingSection #mfgRoot { gap: .75rem; }
  #manufacturingSection #mfgRoot .grid { grid-template-columns: minmax(0, 1fr) !important; }
  #manufacturingSection #mfgRoot .flex { min-width: 0; }
  #manufacturingSection #mfgRoot button { min-height: 2.5rem; }
  #manufacturingSection #mfgRoot th,
  #manufacturingSection #mfgRoot td { padding: .55rem .6rem; }
}
</style>
"""

def read_asar(raw):
    header_size = struct.unpack_from("<I", raw, 4)[0]
    json_size = struct.unpack_from("<I", raw, 12)[0]
    tree = json.loads(raw[16:16 + json_size])
    return tree, raw, 8 + header_size

def extract_tree(node, raw, data_base, root):
    for name, entry in node.get("files", {}).items():
        if "files" in entry:
            extract_tree(entry, raw, data_base, root / name)
        elif "offset" in entry:
            start = data_base + int(entry["offset"])
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw[start:start + entry["size"]])

def walk_repack(node, root, chunks):
    for name, entry in node.get("files", {}).items():
        if "files" in entry:
            walk_repack(entry, root / name, chunks)
        elif "offset" in entry:
            payload = (root / name).read_bytes()
            entry["size"] = len(payload)
            entry["offset"] = str(sum(map(len, chunks)))
            chunks.append(payload)

def main():
    with zipfile.ZipFile(SOURCE) as z:
        member = "payload/app.asar" if "payload/app.asar" in z.namelist() else "app.asar"
        assert z.namelist() == [member], "Unexpected source ZIP structure"
        original = z.read(member)
    tree, raw, base = read_asar(original)
    work = Path("work-asar")
    if work.exists():
        import shutil
        shutil.rmtree(work)
    work.mkdir()
    extract_tree(tree, raw, base, work)
    html_path = work / "index.html"
    html = html_path.read_text(encoding="utf-8")
    if "nano-mfg-consistency-v223" not in html:
        if "</head>" not in html:
            raise RuntimeError("Could not find </head> in index.html")
        html = html.replace("</head>", CSS + "\n</head>", 1)
        html_path.write_text(html, encoding="utf-8")
    package_path = work / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["version"] = VERSION
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    chunks = []
    walk_repack(tree, work, chunks)
    header_json = json.dumps(tree, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    header_size = len(header_json) + 10
    with OUT_ASAR.open("wb") as f:
        f.write(struct.pack("<IIII", 4, header_size, len(header_json), len(header_json)))
        f.write(header_json)
        f.write(b'\\x00\\x00')  # ASAR header requires two padding bytes before payload data.
        for chunk in chunks:
            f.write(chunk)
    # Read back the ASAR header and verify the actual modified files.
    rebuilt = OUT_ASAR.read_bytes()
    rebuilt_tree, _, rebuilt_base = read_asar(rebuilt)
    def entry_at(parts):
        node = rebuilt_tree
        for part in parts:
            node = node["files"][part]
        return node
    e = entry_at(["index.html"])
    html_check = rebuilt[rebuilt_base + int(e["offset"]):rebuilt_base + int(e["offset"]) + e["size"]].decode("utf-8")
    assert "nano-mfg-consistency-v223" in html_check
    e = entry_at(["package.json"])
    package_check = json.loads(rebuilt[rebuilt_base + int(e["offset"]):rebuilt_base + int(e["offset"]) + e["size"]])
    assert package_check["version"] == VERSION
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.write(OUT_ASAR, "payload/app.asar")
    zip_hash = hashlib.sha256(OUT_ZIP.read_bytes()).hexdigest()
    asar_hash = hashlib.sha256(OUT_ASAR.read_bytes()).hexdigest()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    previous = next(p for p in manifest["patches"] if p.get("id") == "nano-pos-v222-manufacturing-activation")
    from_versions = list(dict.fromkeys(previous.get("fromVersions", []) + ["2.0.22"]))
    features = {
        "ar": ["توحيد ألوان وتنسيق نافذة التصنيع مع واجهة NANO POS.", "تحسين تناسق الحقول والأزرار والجداول والاستجابة للشاشات الصغيرة مع الحفاظ على وظائف التصنيع."],
        "fr": ["Harmonisation des couleurs et de la présentation de la fenêtre de fabrication avec NANO POS.", "Amélioration de la cohérence des champs, boutons, tableaux et de l’affichage sur petits écrans, sans modifier les fonctions de fabrication."],
        "en": ["Aligned manufacturing-window colors and styling with the NANO POS interface.", "Improved consistency of fields, buttons, tables, and small-screen layout while preserving manufacturing behavior."]
    }
    manifest["version"] = VERSION
    manifest["releaseDate"] = "2026-10-29"
    manifest["published"] = True
    manifest["features"] = features
    manifest.setdefault("releaseHistory", {})[VERSION] = {"releaseDate": "2026-10-29", "features": features}
    patch = {
        "id": PATCH_ID,
        "fromVersions": from_versions,
        "directUrl": "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v2.0.23/" + PATCH_NAME,
        "pageUrl": "https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v2.0.23",
        "sha256": zip_hash,
        "appAsarSha256": asar_hash,
        "fileName": PATCH_NAME,
        "sizeBytes": OUT_ZIP.stat().st_size,
        "payloadType": "app-asar"
    }
    manifest["patches"] = [patch] + [p for p in manifest["patches"] if p.get("id") != PATCH_ID]
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ZIP_SHA256=" + zip_hash)
    print("ASAR_SHA256=" + asar_hash)
    print("ZIP_SIZE=" + str(OUT_ZIP.stat().st_size))
    print("PASS: ASAR header, app version, CSS injection, ZIP layout, and manifest prepared.")

if __name__ == "__main__":
    main()
