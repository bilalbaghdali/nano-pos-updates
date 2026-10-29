#!/usr/bin/env python3
"""Build NANO POS 2.0.19 with a motherboard-derived ID and same-hardware activation recovery."""
import hashlib, json, re, struct, sys, zipfile
from pathlib import Path

BASE_PATCH_SHA256 = "6848c73648740e7503aa4ef248e0deb79512367f5a0b0f0a3dd308e27e4351d6"
BASE_ASAR_SHA256 = "b1fc5bceadfe4ae42cfdd145d7fef9fe3f45a4d18e182d598516c9d3d0e0987d"
NEW_VERSION = "2.0.19"
MARKER = "__NANO_POS_HARDWARE_ID_V219"
NEW_ID_FN = r"""function installationId() {
    let id = localStorage.getItem(installationKey);
    const hasSavedLicense = Boolean(localStorage.getItem(tokenKey) || localStorage.getItem(serverKey));
    if (id) {
      // Do not invalidate a legacy signed license during an in-place update.
      if (hasSavedLicense || /^NANO-HW1-[A-F0-9]{64}$/i.test(id)) return id;
      const hardwareId = hardwareInstallationId();
      if (/^NANO-HW1-[A-F0-9]{64}$/i.test(hardwareId)) {
        id = hardwareId.toUpperCase();
        localStorage.setItem(installationKey, id);
        return id;
      }
      return id;
    }
    id = hardwareInstallationId();
    if (!/^NANO-HW1-[A-F0-9]{64}$/i.test(id)) id = 'NANO-' + crypto.randomUUID();
    else id = id.toUpperCase();
    localStorage.setItem(installationKey, id);
    return id;
  }"""

MAIN_BLOCK = r"""
// __NANO_POS_HARDWARE_ID_V219: stable Windows computer identity; raw hardware serials never leave the PC.
function nanoPosNormalizeHardwareValue(value) {
  const raw = String(value || '').replace(/[\u0000-\u001f\u007f]/g, '').trim().toUpperCase();
  const compact = raw.replace(/[^A-Z0-9]/g, '');
  if (compact.length < 4) return '';
  if (/^(TOBEFILLEDBYOEM|DEFAULTSTRING|SYSTEMSERIALNUMBER|UNKNOWN|NONE|NA|NOTAPPLICABLE|123456789|0+|F+)$/.test(compact)) return '';
  if (/^F{8}-F{4}-F{4}-F{4}-F{12}$/.test(raw)) return '';
  return raw;
}
function nanoPosHardwareInstallationId() {
  if (process.platform !== 'win32') return '';
  try {
    const child = require('node:child_process');
    const crypto = require('node:crypto');
    const query = function (expression) {
      return child.execFileSync('powershell.exe', [
        '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-Command', "$ErrorActionPreference='Stop'; " + expression
      ], { encoding: 'utf8', windowsHide: true, timeout: 5000, maxBuffer: 65536, stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    };
    let value = '';
    let source = 'baseboard-serial';
    try {
      value = nanoPosNormalizeHardwareValue(query("(Get-CimInstance -ClassName Win32_BaseBoard -ErrorAction Stop | Select-Object -First 1 -ExpandProperty SerialNumber)"));
    } catch (_) {}
    if (!value) {
      source = 'system-uuid';
      try {
        value = nanoPosNormalizeHardwareValue(query("(Get-CimInstance -ClassName Win32_ComputerSystemProduct -ErrorAction Stop | Select-Object -First 1 -ExpandProperty UUID)"));
      } catch (_) {}
    }
    if (!value) return '';
    const digest = crypto.createHash('sha256').update('NANO-POS-HARDWARE-ID-V1|' + source + '|' + value, 'utf8').digest('hex').toUpperCase();
    return 'NANO-HW1-' + digest;
  } catch (_) {
    return '';
  }
}
if (!ipcMain.listenerCount('nano-license-hardware-id-sync')) {
  ipcMain.on('nano-license-hardware-id-sync', (event) => {
    event.returnValue = nanoPosHardwareInstallationId();
  });
}
"""

RECOVERY_API = r"""
  function hardwareInstallationId() {
    try {
      const value = String(window.nanoNative?.getHardwareInstallationId?.() || '').trim().toUpperCase();
      return /^NANO-HW1-[A-F0-9]{64}$/.test(value) ? value : '';
    } catch (_) { return ''; }
  }
  async function exportRecovery() {
    const hardwareId = hardwareInstallationId();
    if (!hardwareId) throw new Error('لا يمكن إنشاء نسخة استرداد على المتصفح؛ افتح NANO POS على الكمبيوتر الذي تريد ربط التفعيل به.');
    const token = localStorage.getItem(tokenKey);
    let server = null;
    try { server = JSON.parse(localStorage.getItem(serverKey) || 'null'); } catch (_) {}
    if (!token && !server) throw new Error('لا يوجد تفعيل محفوظ لإنشاء نسخة احتياطية منه.');
    const current = await status(true);
    if (!current || current.state !== 'active') throw new Error((current && current.message) || 'تعذر التحقق من التفعيل؛ لا يمكن إنشاء نسخة استرداد موثوقة.');
    return JSON.stringify({
      format: 'NANO-POS-ACTIVATION-RECOVERY',
      schema: 1,
      product: 'NANO POS',
      hardwareId,
      installationId: installationId(),
      token: token || null,
      server: server || null,
      exportedAt: new Date().toISOString()
    }, null, 2);
  }
  async function restoreRecovery(source) {
    let recovery;
    try { recovery = JSON.parse(String(source || '')); } catch (_) { throw new Error('ملف الاسترداد غير صالح أو تالف.'); }
    if (!recovery || recovery.format !== 'NANO-POS-ACTIVATION-RECOVERY' || recovery.schema !== 1 || recovery.product !== 'NANO POS') throw new Error('هذا ليس ملف استرداد تفعيل NANO POS صالحاً.');
    const hardwareId = hardwareInstallationId();
    if (!hardwareId) throw new Error('تعذر قراءة معرف اللوحة الأم لهذا الكمبيوتر.');
    if (String(recovery.hardwareId || '').toUpperCase() !== hardwareId) throw new Error('ملف الاسترداد مرتبط بلوحة أم أخرى. يلزم إصدار تفعيل جديد لهذا الجهاز.');
    const id = String(recovery.installationId || '');
    if (!id || id.length > 300 || !/^NANO-[A-Za-z0-9-]+$/.test(id)) throw new Error('معرف التفعيل داخل ملف الاسترداد غير صالح.');
    let license;
    if (recovery.server && typeof recovery.server === 'object') {
      const server = recovery.server;
      if (typeof server.url !== 'string' || typeof server.token !== 'string' || typeof server.licenseId !== 'string' || !server.publicKey) throw new Error('بيانات تفعيل الخادم داخل ملف الاسترداد غير مكتملة.');
      license = await verify(server.token, server.publicKey, id);
      if (license.source !== 'server' || license.id !== server.licenseId) throw new Error('بيانات الترخيص المستعادة لا تتطابق مع ترخيص الخادم.');
      localStorage.setItem(installationKey, id);
      localStorage.setItem(serverKey, JSON.stringify(server));
      localStorage.removeItem(tokenKey);
    } else {
      const token = String(recovery.token || '').trim();
      if (token.startsWith('NANO4.')) license = await verifyNano4(token, id);
      else if (token.startsWith('NANO2.')) license = await verifySimple(token, id);
      else if (token.startsWith('NANO1.')) license = await verify(token, await publicKey(), id);
      else throw new Error('ملف الاسترداد لا يحتوي على رمز تفعيل مدعوم.');
      localStorage.setItem(installationKey, id);
      localStorage.setItem(tokenKey, token);
      localStorage.removeItem(serverKey);
    }
    window.dispatchEvent?.(new Event('nano-license-updated'));
    return license;
  }
"""

def sha(data):
    return hashlib.sha256(data).hexdigest()

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

def patch_license_client(src):
    if MARKER in src:
        raise AssertionError("v2.0.19 hardware-ID marker already exists in license-client.js")
    pattern = re.compile(r"function installationId\(\)\s*\{\s*let id = localStorage\.getItem\(installationKey\);\s*if \(!id\) \{\s*id = 'NANO-' \+ crypto\.randomUUID\(\);\s*localStorage\.setItem\(installationKey, id\);\s*\}\s*return id;\s*\}")
    match = pattern.search(src)
    if not match:
        start = src.find("function installationId")
        raise AssertionError("Could not match installationId() safely; context=" + repr(src[max(0,start-100):start+900]))
    src = src[:match.start()] + NEW_ID_FN + src[match.end():]
    anchor = "  window.nanoLicense = { installationId, verify, verifyNano4, verifySimple, activate, status, trial, access, remove:"
    if anchor not in src:
        raise AssertionError("Could not safely attach recovery API to window.nanoLicense")
    if "function exportRecovery()" in src:
        raise AssertionError("Recovery API already present")
    src = src.replace(anchor, RECOVERY_API + "\n" + anchor, 1)
    src = src.replace("window.nanoLicense = { installationId, verify, verifyNano4, verifySimple, activate, status, trial, access, remove:", "window.nanoLicense = { installationId, hardwareInstallationId, exportRecovery, restoreRecovery, verify, verifyNano4, verifySimple, activate, status, trial, access, remove:", 1)
    # The hardware ID helper is also used by installationId() before any license is active.
    src = src.replace("function installationId() {", "function installationId() {", 1)
    # Ensure the helper is defined before installationId().
    src = src.replace(NEW_ID_FN, NEW_ID_FN, 1)
    helper = "  function hardwareInstallationId() {"
    if helper not in src:
        raise AssertionError("Hardware-ID helper did not install")
    # Move helper definition before installationId so calls are clear and easy to audit.
    start = src.index(helper)
    end = src.index("\n  async function exportRecovery()", start)
    hardware_fn = src[start:end]
    src = src[:start] + src[end:]
    point = src.index("function installationId()")
    src = src[:point] + hardware_fn + "\n  " + src[point:]
    return src

def patch_license_ui(src):
    if "nano-license-recovery-export" in src:
        raise AssertionError("v2.0.19 recovery button already exists")
    marker = "id=\"nano-license-export\" class=\"nano-license-secondary\"></button></div><p id=\"nano-license-install-note\""
    repl = "id=\"nano-license-export\" class=\"nano-license-secondary\"></button></div><div class=\"nano-license-actions\"><button type=\"button\" id=\"nano-license-recovery-export\" class=\"nano-license-secondary\"></button></div><p id=\"nano-license-install-note\""
    if marker not in src:
        raise AssertionError("Could not add the recovery button in license-ui.js")
    src = src.replace(marker, repl, 1)
    lang_anchor = "  const x=()=>T[language()];"
    lang_block = r"""
  const recoveryText = () => ({
    ar: { button: 'حفظ نسخة احتياطية للتفعيل', exported: 'تم حفظ نسخة الاسترداد. احتفظ بها خارج الكمبيوتر قبل تهيئة Windows.', restored: 'تم استرداد التفعيل بنجاح على الكمبيوتر نفسه.' },
    fr: { button: 'Sauvegarder la licence', exported: 'Sauvegarde créée. Conservez-la hors du PC avant de réinstaller Windows.', restored: 'Licence restaurée sur le même ordinateur.' },
    en: { button: 'Back up activation', exported: 'Recovery file saved. Keep it off this PC before reinstalling Windows.', restored: 'Activation restored on the same computer.' }
  })[language()] || { button: 'Back up activation', exported: 'Recovery file saved.', restored: 'Activation restored.' };
"""
    if lang_anchor not in src:
        raise AssertionError("Could not locate language helper in license-ui.js")
    src = src.replace(lang_anchor, lang_anchor + "\n" + lang_block, 1)
    paint_anchor = "$('export').textContent=a.export;"
    if paint_anchor not in src:
        raise AssertionError("Could not locate static button paint logic")
    src = src.replace(paint_anchor, paint_anchor + "$('recovery-export').textContent=recoveryText().button;", 1)
    src = src.replace('accept=\".nano-license,.txt\"', 'accept=\".nano-license,.txt,.nano-recovery,.json\"', 1)
    old_change = "$('file').addEventListener('change',async()=>{const file=$('file').files[0];if(!file)return;try{if(file.size>32768)throw new Error(x().fileBig);$('token').value=(await file.text()).trim();message(x().loaded);$('submit').focus();}catch(error){message(error.message,true);}finally{$('file').value='';}});"
    new_change = r"""$('file').addEventListener('change',async()=>{const file=$('file').files[0];if(!file)return;try{if(file.size>32768)throw new Error(x().fileBig);const content=await file.text();if(file.name.toLowerCase().endsWith('.nano-recovery')){await window.nanoLicense.restoreRecovery(content);$('token').value='';await refresh(true);message(recoveryText().restored);return;}$('token').value=content.trim();message(x().loaded);$('submit').focus();}catch(error){message(error.message,true);}finally{$('file').value='';}});"""
    if old_change not in src:
        raise AssertionError("Could not safely update the license import handler")
    src = src.replace(old_change, new_change, 1)
    export_anchor = "$('export').addEventListener('click',()=>{const id=window.nanoLicense.installationId(),url=URL.createObjectURL(new Blob([id+'\\n'],{type:'text/plain'})),link=document.createElement('a');link.href=url;link.download='nano-program-id.nano-id';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message(x().exported);});"
    if export_anchor not in src:
        raise AssertionError("Could not locate program-ID export handler")
    recovery_handler = r"""$('recovery-export').addEventListener('click',async()=>{try{const text=await window.nanoLicense.exportRecovery();const url=URL.createObjectURL(new Blob([text],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='NANO-POS-activation-recovery.nano-recovery';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message(recoveryText().exported);}catch(error){message(error.message||'تعذر حفظ نسخة الاسترداد.',true);}});"""
    src = src.replace(export_anchor, export_anchor + "\n  " + recovery_handler, 1)
    return src

def main():
    if len(sys.argv) != 4:
        raise SystemExit("build-hardware-id-219.py BASE_PATCH.zip OUTPUT_PATCH.zip WORKDIR")
    base, output, workdir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    assert sha(base.read_bytes()) == BASE_PATCH_SHA256, "Official v2.0.18 patch SHA-256 mismatch"
    with zipfile.ZipFile(base) as z:
        assert z.namelist() == ["payload/app.asar"], "Unexpected base patch contents"
        raw = z.read("payload/app.asar")
    assert sha(raw) == BASE_ASAR_SHA256, "Official v2.0.18 app.asar SHA-256 mismatch"
    tree, entries = read_asar(raw)
    out_data = bytearray()
    modified, written = [], {}
    for path, ent, blob in entries:
        changed = False
        if path == "package.json":
            package = json.loads(blob.decode("utf-8"))
            assert package.get("version") == "2.0.18", "Expected package.json version 2.0.18"
            package["version"] = NEW_VERSION
            blob = (json.dumps(package, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            changed = True
        elif path.endswith("/license-client.js") or path == "license-client.js":
            blob = patch_license_client(blob.decode("utf-8")).encode("utf-8")
            changed = True
        elif path.endswith("/license-ui.js") or path == "license-ui.js":
            blob = patch_license_ui(blob.decode("utf-8")).encode("utf-8")
            changed = True
        elif path.endswith("/electron-main.cjs") or path == "electron-main.cjs":
            src = blob.decode("utf-8")
            if MARKER in src:
                raise AssertionError("Hardware-ID marker already exists in electron-main.cjs")
            imp = re.search(r"const\s*\{[^}]*\bipcMain\b[^}]*\}\s*=\s*require\(['\"]electron['\"]\)\s*;", src, re.S)
            if not imp:
                raise AssertionError("Could not find the Electron ipcMain import safely; main prefix=" + repr(src[:900]))
            src = src[:imp.end()] + "\n" + MAIN_BLOCK + "\n" + src[imp.end():]
            blob = src.encode("utf-8")
            changed = True
        elif path.endswith("/electron-native-preload.cjs") or path == "electron-native-preload.cjs":
            src = blob.decode("utf-8")
            if "getHardwareInstallationId" in src:
                raise AssertionError("Hardware-ID API already exists in the native preload")
            pat = re.compile(r"(contextBridge\.exposeInMainWorld\(\s*['\"]nanoNative['\"]\s*,\s*\{)")
            match = pat.search(src)
            if not match:
                raise AssertionError("Could not find nanoNative exposed object safely; preload prefix=" + repr(src[:1400]))
            prop = "getHardwareInstallationId: () => { try { return String(ipcRenderer.sendSync('nano-license-hardware-id-sync') || ''); } catch (_) { return ''; } },\n  "
            src = src[:match.end()] + "\n  " + prop + src[match.end():]
            blob = src.encode("utf-8")
            changed = True
        if changed:
            modified.append(path)
            written[path] = blob
            if path.endswith((".js", ".cjs", ".mjs")):
                target = workdir / Path(path).name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(blob)
        ent["offset"] = str(len(out_data))
        ent["size"] = len(blob)
        if changed and "integrity" in ent:
            ent["integrity"]["hash"] = sha(blob)
            integrity = ent["integrity"]
            block_size = int(integrity.get("blockSize", 4 * 1024 * 1024))
            integrity["blocks"] = [sha(blob[i:i+block_size]) for i in range(0, len(blob), block_size)]
        out_data.extend(blob)
    required = {"package.json", "license-client.js", "license-ui.js", "electron-main.cjs", "electron-native-preload.cjs", "renderer.js"}
    present = {p for p, _, _ in entries}
    missing = required - present
    assert not missing, "Required ASAR files missing: " + ", ".join(sorted(missing))
    header = json.dumps(tree, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    padded = (len(header) + 7) & ~3
    final_asar = struct.pack("<4I", 4, padded + 4, padded, len(header)) + header + b"\0" * (padded - 4 - len(header)) + out_data
    _, check_entries = read_asar(final_asar)
    files = {p: b for p, _, b in check_entries}
    package = json.loads(files["package.json"].decode("utf-8"))
    assert package.get("version") == NEW_VERSION
    lc = files["license-client.js"].decode("utf-8")
    ui = files["license-ui.js"].decode("utf-8")
    main_src = files["electron-main.cjs"].decode("utf-8")
    preload = files["electron-native-preload.cjs"].decode("utf-8")
    renderer = files["renderer.js"].decode("utf-8", "ignore")
    all_text = "\n".join(v.decode("utf-8", "ignore") for v in files.values())
    assert MARKER in main_src and "Win32_BaseBoard" in main_src and "Win32_ComputerSystemProduct" in main_src
    assert "getHardwareInstallationId" in preload and "nano-license-hardware-id-sync" in preload
    assert "NANO-HW1-" in lc and "hasSavedLicense" in lc and "restoreRecovery" in lc and "exportRecovery" in lc
    assert "NANO-POS-ACTIVATION-RECOVERY" in lc and "nano-license-recovery-export" in ui
    assert "window.nanoLicense.restoreRecovery" in ui and "NANO-POS-activation-recovery.nano-recovery" in ui
    assert "__nanoCartSpeechV202" in renderer and "__nanoOperationalAnalyticsV217" in renderer
    assert "ازل الترخيص من البرنامج" in all_text
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("payload/app.asar", final_asar)
    with zipfile.ZipFile(output) as z:
        assert z.namelist() == ["payload/app.asar"]
        assert sha(z.read("payload/app.asar")) == sha(final_asar)
    print(json.dumps({
        "fromVersion": "2.0.18", "version": NEW_VERSION,
        "modifiedFiles": modified, "asarFiles": len(files),
        "appAsarSha256": sha(final_asar), "patchSha256": sha(output.read_bytes()),
        "sizeBytes": output.stat().st_size,
        "checks": ["motherboard serial queried first", "system UUID fallback", "legacy active IDs preserved",
                   "same-hardware recovery export/import", "license signature checks retained",
                   "price speech and operational analytics retained"]
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
