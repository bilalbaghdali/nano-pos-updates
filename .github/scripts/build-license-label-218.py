#!/usr/bin/env python3
"""Create NANO POS v2.0.18 from the SHA-verified v2.0.17 app.asar; change only the Arabic license-button label."""
import hashlib, json, re, struct, sys, zipfile
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXPECTED_BASE_PATCH_SHA256 = "24ca28ed073d9a0a90f638080116e6c82214bb4d4e4997c632151b3f63ee86b5"
EXPECTED_BASE_ASAR_SHA256 = "ae06246d24a9f28257f6bfe17a3e4b3dbf5e9dc836201de9255ab9021cecaf21"
OLD_LABEL = re.compile(r"(?:إزالة|ازالة|أزل|ازل|أزالة|ازاله)\s+الترخيص\s+من\s+(?:هذا\s+)?المتصفح")
NEW_LABEL = "ازل الترخيص من البرنامج"

def sha(b): return hashlib.sha256(b).hexdigest()

def read_asar(raw):
    magic, block, header_size, json_size = struct.unpack_from("<4I", raw)
    assert magic == 4 and block == header_size + 4, "Invalid ASAR header"
    tree = json.loads(raw[16:16+json_size].decode("utf-8"))
    data_start = 8 + block
    entries = []
    def walk(node, prefix=""):
        for name, ent in node.get("files", {}).items():
            path = prefix + name
            if "files" in ent:
                walk(ent, path + "/")
            elif "offset" in ent and "size" in ent:
                start = data_start + int(ent["offset"])
                blob = raw[start:start+int(ent["size"])]
                assert len(blob) == int(ent["size"]), "Truncated ASAR entry: " + path
                entries.append((path, ent, blob))
    walk(tree)
    entries.sort(key=lambda item: int(item[1]["offset"]))
    return tree, entries

def main():
    if len(sys.argv) != 4:
        raise SystemExit("build-license-label-218.py BASE.zip OUTPUT.zip WORKDIR")
    base, output, workdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    assert sha(base.read_bytes()) == EXPECTED_BASE_PATCH_SHA256, "Official v2.0.17 patch SHA-256 mismatch"
    with zipfile.ZipFile(base) as z:
        assert z.namelist() == ["payload/app.asar"], "Unexpected base patch contents"
        raw = z.read("payload/app.asar")
    assert sha(raw) == EXPECTED_BASE_ASAR_SHA256, "Official v2.0.17 ASAR SHA-256 mismatch"
    tree, entries = read_asar(raw)

    out_data = bytearray()
    found_label = 0
    found_package = False
    edited_paths = []
    for path, ent, blob in entries:
        changed = False
        if path == "package.json":
            package = json.loads(blob.decode("utf-8"))
            assert package.get("version") == "2.0.17", "Expected package version 2.0.17"
            package["version"] = "2.0.18"
            blob = (json.dumps(package, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            found_package = True
            changed = True
        else:
            try:
                src = blob.decode("utf-8")
            except UnicodeDecodeError:
                src = None
            if src is not None:
                replacement, count = OLD_LABEL.subn(NEW_LABEL, src)
                if count:
                    blob = replacement.encode("utf-8")
                    found_label += count
                    changed = True
        ent["offset"] = str(len(out_data))
        ent["size"] = len(blob)
        if changed and "integrity" in ent:
            ent["integrity"]["hash"] = sha(blob)
            integrity = ent["integrity"]
            block_size = int(integrity.get("blockSize", 4 * 1024 * 1024))
            integrity["blocks"] = [sha(blob[i:i+block_size]) for i in range(0, len(blob), block_size)]
        out_data.extend(blob)
        if changed:
            edited_paths.append(path)
            if path.endswith((".js", ".cjs", ".mjs")):
                target = workdir / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(blob)

    assert found_package, "package.json was not found"
    if found_label == 0:
        candidates = []
        for path, ent, blob in entries:
            try:
                src = blob.decode("utf-8")
            except UnicodeDecodeError:
                continue
            snippets = []
            for needle in ("الترخيص", "ترخيص", "المتصفح", "license", "browser", "التفعيل"):
                pos = 0
                while len(snippets) < 8:
                    pos = src.lower().find(needle.lower(), pos)
                    if pos < 0:
                        break
                    snippets.append(src[max(0, pos-160):min(len(src), pos+240)].replace("\\r", " ").replace("\\n", " "))
                    pos += len(needle)
            if snippets:
                candidates.append({"path": path, "snippets": snippets[:8]})
        print("LICENSE_LABEL_DISCOVERY=" + json.dumps(candidates[:80], ensure_ascii=False))
    assert found_label > 0, "The expected Arabic label was not found; see LICENSE_LABEL_DISCOVERY above; refusing to publish an unchanged app"
    header = json.dumps(tree, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    padded = (len(header) + 7) & ~3
    final_asar = struct.pack("<4I", 4, padded + 4, padded, len(header)) + header + b"\0" * (padded - 4 - len(header)) + out_data
    # Re-open and verify the exact output before writing the ZIP.
    check_tree, check_entries = read_asar(final_asar)
    files = {p: b for p, _, b in check_entries}
    package = json.loads(files["package.json"].decode("utf-8"))
    assert package.get("version") == "2.0.18"
    joined = "\n".join(b.decode("utf-8", "ignore") for p, b in files.items())
    assert NEW_LABEL in joined, "Target label missing from final ASAR"
    assert not OLD_LABEL.search(joined), "Old label remains in final ASAR"
    renderer = files.get("renderer.js", b"").decode("utf-8", "ignore")
    assert "__nanoCartSpeechV202" in renderer and "SpeechSynthesisUtterance" in renderer, "Base cart-price speech feature was lost"
    assert "__nanoOperationalAnalyticsV217" in renderer and "nanoChartSalesPurchases" in renderer, "Base analytics charts were lost"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("payload/app.asar", final_asar)
    with zipfile.ZipFile(output) as z:
        assert z.namelist() == ["payload/app.asar"]
        assert sha(z.read("payload/app.asar")) == sha(final_asar)
    print(json.dumps({
        "fromVersion": "2.0.17", "version": "2.0.18",
        "newLabel": NEW_LABEL, "oldLabelOccurrencesReplaced": found_label,
        "modifiedFiles": edited_paths, "appAsarSha256": sha(final_asar),
        "patchSha256": sha(output.read_bytes()), "sizeBytes": output.stat().st_size
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
