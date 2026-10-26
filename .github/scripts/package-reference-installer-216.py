#!/usr/bin/env python3
"""Validate and extract the official NANO POS v2.0.16 ASAR for Windows packaging."""
import hashlib, json, struct, sys, zipfile
from pathlib import Path

EXPECTED_PATCH_SHA256 = "c1de6142d92b6d41bc4767c8c1feb1d946687e39b0d6c74a264bc81367b49630"
EXPECTED_ASAR_SHA256 = "09ca5848787cff21b6bd99c5a0d718d39586085290b97f8b5eb366317277b439"
EXPECTED_VERSION = "2.0.16"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def extract_files(raw: bytes):
    magic, block, header_size, n = struct.unpack_from("<4I", raw)
    assert magic == 4 and block == header_size + 4, "Invalid ASAR header"
    tree = json.loads(raw[16:16+n].decode("utf-8"))
    start = 8 + block
    files = {}
    def walk(node, prefix=""):
        for name, entry in node.get("files", {}).items():
            path = prefix + name
            if "files" in entry:
                walk(entry, path + "/")
            elif "offset" in entry and "size" in entry:
                a = start + int(entry["offset"])
                files[path] = raw[a:a+int(entry["size"])]
    walk(tree)
    return tree, files

def main():
    if len(sys.argv) != 4:
        raise SystemExit("package-reference-installer-216.py PATCH.zip OUTPUT.asar WORKDIR")
    zip_path, out_path, work = map(Path, sys.argv[1:4])
    assert sha(zip_path.read_bytes()) == EXPECTED_PATCH_SHA256, "v2.0.16 patch SHA-256 mismatch"
    with zipfile.ZipFile(zip_path) as z:
        assert z.namelist() == ["payload/app.asar"], "Unexpected patch contents"
        raw = z.read("payload/app.asar")
    assert sha(raw) == EXPECTED_ASAR_SHA256, "v2.0.16 ASAR SHA-256 mismatch"
    _, files = extract_files(raw)
    assert "package.json" in files and "renderer.js" in files, "Required ASAR files missing"
    package = json.loads(files["package.json"].decode("utf-8"))
    assert package.get("version") == EXPECTED_VERSION, package.get("version")
    main_file = package.get("main", "index.js")
    assert main_file in files, "Package entry point is absent: " + main_file
    renderer = files["renderer.js"].decode("utf-8")
    assert "__nanoCartSpeechV202" in renderer and "SpeechSynthesisUtterance" in renderer, "Cart price speech is missing"
    for forbidden in ("__nanoPrayer", "api.aladhan.com", "مواقيت الصلاة"):
        assert forbidden not in renderer, "Prayer feature unexpectedly present: " + forbidden
    work.mkdir(parents=True, exist_ok=True)
    (work / "renderer.js").write_bytes(files["renderer.js"])
    if "electron-main.cjs" in files:
        (work / "electron-main.cjs").write_bytes(files["electron-main.cjs"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    print(json.dumps({
        "version": package["version"],
        "main": main_file,
        "asarSha256": sha(raw),
        "patchSha256": sha(zip_path.read_bytes()),
        "asarFiles": len(files),
        "prayerFeature": False,
        "cartPriceSpeech": True
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
