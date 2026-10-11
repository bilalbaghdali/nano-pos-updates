#!/usr/bin/env python3
"""Rebuild NANO POS 1.0.35's verified app.asar from 1.0.34 + delta."""
import base64
import hashlib
import json
import os
import pathlib
import struct
import sys
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
BASE_URL = "https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.34/NANO-POS-Patch-1.0.33-to-1.0.34-PRINT-SYNC-CURRENCY.zip"
BASE_SHA = "2ea92ed65a3964f3fedb24593c9553630f0ae93c5acb1b49d58457b72b15ea1c"
DELTA_SHA = "2d5655503849c47c305c644ceba53c3a14b33473037f2c4e41f1d0ef258b531b"
ASAR_SHA = "485d5662f9e53cbbbc52fb22a72a9616950224d7aea34a07dab23c42ee73d73c"
ASSET = "NANO-POS-Patch-1.0.34-to-1.0.35-AUTO.zip"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def files_table(raw):
    header_length = struct.unpack("<I", raw[12:16])[0]
    meta = json.loads(raw[16:16+header_length])
    base = 8 + struct.unpack("<I", raw[4:8])[0]
    files = {}
    def walk(node, parent=""):
        for name, meta in node.get("files", {}).items():
            path = parent + name
            if "files" in meta:
                walk(meta, path + "/")
            elif "offset" in meta:
                files[path] = (base + int(meta["offset"]), meta["size"])
    walk(meta)
    return files

def main():
    downloaded = pathlib.Path("build-1.0.34.zip")
    if not downloaded.exists():
        req = urllib.request.Request(BASE_URL, headers={"User-Agent": "NANO-POS-release-builder"})
        with urllib.request.urlopen(req, timeout=120) as response:
            downloaded.write_bytes(response.read())
    source_bytes = downloaded.read_bytes()
    assert digest(source_bytes) == BASE_SHA, "Base release hash mismatch!"
    with zipfile.ZipFile(downloaded) as z:
        old_asar = z.read("payload/app.asar")
    parts = sorted(ROOT.glob("delta-part-*.b64"))
    assert len(parts) == 4, "Missing delta chunks"
    encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    delta_bytes = base64.b64decode(encoded, validate=True)
    assert digest(delta_bytes) == DELTA_SHA, "Delta integrity mismatch!"
    delta_path = pathlib.Path("delta-1.0.35.zip")
    delta_path.write_bytes(delta_bytes)
    with zipfile.ZipFile(delta_path) as z:
        new_header = z.read("header.bin")
        changes = {n[len("modified/"):]: z.read(n)
                   for n in z.namelist() if n.startswith("modified/") and not n.endswith("/")}
    old_files = files_table(old_asar)
    new_files = files_table(new_header)
    rebuilt = bytearray(new_header)
    for path, (offset, size) in sorted(new_files.items(), key=lambda p: p[1][0]):
        if path in changes:
            data = changes[path]
        else:
            old_pos, old_size = old_files[path]
            assert old_size == size, "Unexpected original file size: " + path
            data = old_asar[old_pos:old_pos+old_size]
        assert len(data) == size and len(rebuilt) == offset, "ASAR layout mismatch: " + path
        rebuilt.extend(data)
    assert digest(rebuilt) == ASAR_SHA, "Rebuilt app.asar doesn't match tested candidate!"
    with zipfile.ZipFile(ASSET, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("payload/app.asar", rebuilt)
    with zipfile.ZipFile(ASSET) as z:
        assert z.testzip() is None
        assert z.namelist() == ["payload/app.asar"]
    result = {"asset": ASSET, "sha256": digest(pathlib.Path(ASSET).read_bytes()),
              "appAsarSha256": ASAR_SHA, "sizeBytes": pathlib.Path(ASSET).stat().st_size}
    pathlib.Path("build-result.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
