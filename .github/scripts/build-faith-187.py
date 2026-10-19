import hashlib, json, struct, sys, zipfile
from pathlib import Path

OLD_ZIP_SHA = "a1d8a39cddf695f977b2bdb78a0e72e68c1580102ee00cc8f93e2838febb1e9c"
OLD_ASAR_SHA = "6cebbec3b230fff98cc7169eba45e2996c968def334c0ea9e8d80edace3cebe8"
EXPECTED_JS_SHA = "0554c1a1b3c838d2772a35897b84248ecdf874e2b550c7b85dbd6090126a5c24"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def once(s, old, new):
    assert s.count(old) == 1, ("Expected exactly one match:", old, s.count(old))
    return s.replace(old, new, 1)

def build(source):
    assert sha(source.read_bytes()) == OLD_ZIP_SHA, "Unexpected v1.0.86 ZIP SHA"
    with zipfile.ZipFile(source) as z:
        assert z.namelist() == ["payload/app.asar"]
        data = bytearray(z.read("payload/app.asar"))
    assert sha(data) == OLD_ASAR_SHA, "Unexpected v1.0.86 ASAR SHA"
    a, n, c, d = struct.unpack_from("<4I", data)
    header = json.loads(data[16:16+d])
    base = 8 + n
    def read(path):
        entry = header["files"][path]
        start = base + int(entry["offset"])
        return entry, start, bytes(data[start:start+entry["size"]])
    entry, start, old_js = read("nano-faith-login.js")
    js = old_js.decode("utf-8")
    js = once(js, """ // This event is dispatched only from the successful loginUser branch, after
 // the NANOLoginSuccessEffect finishes and the session has been established.
 // Merely opening the app, resuming a session, or unlocking does NOT trigger it.""", """ // Only the authenticated login branch may request this dialog.""")
    js = once(js, """   // The original login screen is hidden by a 500ms transition. Wait for it,
   // rather than showing a reminder below the still-visible login overlay.""", """   // Check both overlays after the login transition. Do not drop a
   // confirmed successful login after the old twelve-second timeout.""")
    js = once(js, "if(++attempts<=60)", "if(++attempts<600)")
    js = once(js, "console.warn('[NANO Reminder] Login overlay never closed after successful authentication');", "console.error('[NANO Reminder] Login overlay still visible after authentication');")
    js = once(js, "console.error('[NANO Reminder] Popup failed after successful login',error);", "console.error('[NANO Reminder] Popup failed',error);")
    js = once(js, "w.setTimeout(displayAfterLogin,100);", "w.setTimeout(displayAfterLogin,650);")
    js = once(js, "\nfunction init(){", "\n\nfunction init(){")
    fixed = (js + " " * (len(old_js)-len(js.encode("utf-8")))).encode("utf-8")
    assert len(fixed) == len(old_js) and sha(fixed) == EXPECTED_JS_SHA, "Fix differs from supplied patch"
    data[start:start+len(old_js)] = fixed
    entry["integrity"]["hash"] = sha(fixed)
    entry["integrity"]["blocks"] = [sha(fixed)]
    pkg_entry, pkg_start, pkg = read("package.json")
    pkg = once(pkg, b'"version": "1.0.86"', b'"version": "1.0.87"')
    assert len(pkg) == pkg_entry["size"] and json.loads(pkg)["version"] == "1.0.87"
    data[pkg_start:pkg_start+len(pkg)] = pkg
    pkg_entry["integrity"]["hash"] = sha(pkg)
    pkg_entry["integrity"]["blocks"] = [sha(pkg)]
    new_header = json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    assert len(new_header) == d, "Header layout must remain unchanged"
    data[16:16+d] = new_header
    assert data[:16] == struct.pack("<4I", a, n, c, d)
    return bytes(data)

if __name__ == "__main__":
    source, output = map(Path, sys.argv[1:3])
    result = build(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("payload/app.asar", result)
    with zipfile.ZipFile(output) as z:
        assert z.namelist() == ["payload/app.asar"] and sha(z.read("payload/app.asar")) == sha(result)
    print("Built v1.0.87 ZIP SHA256:", sha(output.read_bytes()))
    print("Built v1.0.87 ASAR SHA256:", sha(result))
