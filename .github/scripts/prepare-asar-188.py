#!/usr/bin/env python3
"""Prepare NANO POS 1.0.88 Windows app.asar from verified 1.0.87 release."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

source = Path(sys.argv[1])
target = Path(sys.argv[2])
manifest = json.loads(Path("nano-pos-update.json").read_text(encoding="utf-8"))
assert manifest["version"] == "1.0.87" and manifest["published"]
prev = manifest["patches"][0]
assert hashlib.sha256(source.read_bytes()).hexdigest() == prev["sha256"], "Source ZIP digest mismatch"
with zipfile.ZipFile(source) as z:
    assert z.namelist() == ["payload/app.asar"], "Unexpected ZIP contents"
    data = bytearray(z.read("payload/app.asar"))
assert hashlib.sha256(data).hexdigest() == prev["appAsarSha256"], "Source ASAR digest mismatch"
a, n, c, d = struct.unpack_from("<4I", data)
header = json.loads(data[16:16+d])
entry = header["files"]["package.json"]
start = 8+n+int(entry["offset"])
end = start + entry["size"]
pkg = bytes(data[start:end])
assert pkg.count(b'"version": "1.0.87"') == 1
fixed = pkg.replace(b'"version": "1.0.87"', b'"version": "1.0.88"')
assert len(fixed) == len(pkg)
assert json.loads(fixed)["version"] == "1.0.88"
data[start:end] = fixed
assert "integrity" in entry
entry["integrity"]["hash"] = hashlib.sha256(fixed).hexdigest()
entry["integrity"]["blocks"] = [hashlib.sha256(fixed).hexdigest()]
packed = json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
assert len(packed) == d, "ASAR header length changed unexpectedly"
data[16:16+d] = packed
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(data)
print("Verified app.asar 1.0.88 SHA256:", hashlib.sha256(data).hexdigest())
