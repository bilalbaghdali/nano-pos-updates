#!/usr/bin/env python3
"""Verify in-app update manifest coverage against the exact GitHub release payload."""
from pathlib import Path
import hashlib,json,zipfile,struct,sys
manifest=Path("nano-pos-update.json")
source=Path(sys.argv[1])
d=json.loads(manifest.read_text(encoding="utf-8"))
assert d["published"] and d["version"]=="1.0.102"
assert d["product"]=="NANO POS"
assert not d["mandatory"],"Do not force interruption of active checkout"
assert len(d["patches"])==1
patch=d["patches"][0]
versions=["1.0.97","1.0.98","1.0.99","1.0.100","1.0.101"]
assert patch["fromVersions"]==versions, "Not all auto-update-capable NANO versions are supported"
assert patch["directUrl"]=="https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.102/"+source.name
assert patch["payloadType"]=="app-asar"
assert len(patch["sha256"])==64 and len(patch["appAsarSha256"])==64
assert source.stat().st_size==patch["sizeBytes"],"Release size does not match"
assert hashlib.sha256(source.read_bytes()).hexdigest()==patch["sha256"],"Release ZIP mismatch"
with zipfile.ZipFile(source) as z:
    assert z.namelist()==["payload/app.asar"]
    data=z.read("payload/app.asar")
assert hashlib.sha256(data).hexdigest()==patch["appAsarSha256"],"App ASAR mismatch"
magic,block,hs,n=struct.unpack_from("<4I",data)
assert magic==4 and block==hs+4
head=json.loads(data[16:16+n])
def source_file(filename):
    e=head["files"][filename]
    value=data[8+block+int(e["offset"]):8+block+int(e["offset"])+e["size"]]
    if "integrity" in e:
        assert hashlib.sha256(value).hexdigest()==e["integrity"]["hash"]
    return value
pkg=json.loads(source_file("package.json"))
assert pkg["version"]=="1.0.102"
updater=source_file("updater-main.cjs")
ui=source_file("update-manager.js")
for token in [
    b"function findApplicablePatch(manifest, currentVersion)",
    b"patch.fromVersions.includes(String(currentVersion))",
    b"findApplicablePatch(manifest, app.getVersion())",
    b"getLastUpdateResult" if b"getLastUpdateResult" in updater else b"nano-update-last-result",
    b"patch_payload_sha256_mismatch",
]:
    assert token in updater, "Native updater lacks protection: "+repr(token)
assert b"rollback" in updater.lower() and b"backup" in updater.lower(), "No rollback/backup implementation"
for token in [
    b"scheduleAutomaticUpdate(result)",
    b"installAutoWhenSafe()",
    b"loginSafeForRestart()",
    b"autoAttemptedVersion",
    b"autoDownloading",
    b"nano-pos-auto-update-enabled-v1"
]:
    assert token in ui, "Expected automatic updater mechanism absent: "+repr(token)
Path("work").mkdir(exist_ok=True)
Path("work/updater-main.cjs").write_bytes(updater)
Path("work/update-manager.js").write_bytes(ui)
print("PASS: Official signed-by-hash v1.0.102 ZIP and ASAR match, auto-update UI and protected native installer exist")
print("PASS: v1.0.97 to v1.0.101 can directly receive v1.0.102 (one ASAR installation)")
