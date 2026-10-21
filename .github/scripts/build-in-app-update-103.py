#!/usr/bin/env python3
"""Patch the verified official NANO POS v1.0.102 to keep updates INSIDE the app.
A release is blocked if native or UI source drift is detected. No data files touched."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
BASE_ASAR='fefbdd4eb0e7517639d28e19df6a15b3c30a30f41b8169985ebc0cb519464c59'
def once(s,a,b):
    assert s.count(a)==1,('source_marker_changed',a[:140],s.count(a))
    return s.replace(a,b)
def patch_ui(s):
    # A real ZIP patch should be selected based on the native version, not on a page link.
    s=once(s,
      "      const hasPatch = manifest.selectedUpdateType === 'patch' && Array.isArray(manifest.patches) && manifest.patches.some(p => p?.directUrl);",
      """      const hasPatch = Array.isArray(manifest.patches) && manifest.patches.some(p =>
        p?.directUrl && p?.appAsarSha256 && p?.sha256 &&
        Array.isArray(p.fromVersions) && p.fromVersions.includes(String(manifest.currentVersion || '')));""")
    s=once(s,
      "      btn.dataset.mode = (hasPatch || manifest.download?.directUrl) ? 'download' : manifest.download?.pageUrl ? 'manual' : 'none';",
      """      // Never turn an in-app update control into a GitHub browser redirect.
      // If this device cannot install an authenticated package, explain it in the app.
      btn.dataset.mode = (hasPatch || (manifest.download?.directUrl && manifest.download?.sha256)) ? 'download' : 'none';""")
    s=once(s,
      "      if (label) label.textContent = btn.dataset.mode === 'manual' ? s('manual') : s('download');",
      "      if (label) label.textContent = btn.dataset.mode === 'none' ? s('noLink') : s('download');")
    s=once(s,
      "        openModal(result.manifest);\n        scheduleAutomaticUpdate(result);",
      """        result.manifest.currentVersion = result.currentVersion;
        openModal(result.manifest);
        scheduleAutomaticUpdate(result);""")
    s=once(s,
      """    if (mode === 'manual') {
      await window.nanoNative.openUpdatePage(currentManifest.download.pageUrl);
      return;
    }
    if (mode === 'none') { showToastSafe(s('noLink'), 'warning'); return; }""",
      """    if (mode === 'manual' || mode === 'none') {
      updateStatus(s('noLink'), 'error');
      showToastSafe(s('noLink'), 'warning');
      return;
    }""")
    s=once(s,
      """        if (result?.manual && result.pageUrl) {
          btn.disabled = false; btn.dataset.mode = 'manual';
          const label = btn.querySelector('[data-i18n="download_update"]') || btn.querySelector('span:last-child');
          if (label) label.textContent = s('manual');
          return;
        }""",
      """        if (result?.manual) {
          // Do not silently switch to opening GitHub if direct download failed.
          throw new Error(result?.patchError || result?.error || 'direct_download_unavailable');
        }""")
    # No manual external-page action, anywhere in this update control.
    assert "openUpdatePage(" not in s
    assert "btn.dataset.mode = 'manual'" not in s
    return s
def notes(s):
    s=once(s,"const FALLBACK_VERSION = '1.0.102';","const FALLBACK_VERSION = '1.0.103';")
    a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
    return s[:a]+"""  const OFFLINE = {
    ar:['إصلاح زر التحديث ليحمّل الحزمة الموثقة ويثبتها من داخل NANO POS دون فتح GitHub.',
        'إتاحة التحديث المباشر إلى أحدث إصدار من النسخ القديمة ذات آلية التثبيت الداخلية المدعومة.',
        'الإبقاء على التحقق من سلامة الحزمة ونسخة الاسترجاع وتأجيل إعادة التشغيل أثناء البيع.',
        'إذا تعذر تنزيل تحديث معتمد، تظهر رسالة داخل البرنامج بدل الانتقال إلى صفحة خارجية.'],
    fr:['Télécharger et installer les mises à jour dans NANO POS sans ouvrir de navigateur.',
        'Mises à niveau directes depuis les anciennes versions dotées du moteur interne.',
        'Vérification SHA-256, restauration et installation sans interruption de caisse.',
        'Afficher l’erreur dans l’application au lieu d’ouvrir GitHub.'],
    en:['Download and install updates within NANO POS, without opening the browser.',
        'Direct upgrade from supported older releases with a native patch installer.',
        'SHA-256 verification, rollback and safe restart outside an active checkout.',
        'Show any unsupported download as an in-app error, never an external page.']
  };
"""+s[b:]
def build(source,target,folder):
    with zipfile.ZipFile(source) as z:
        assert z.namelist()==['payload/app.asar']
        raw=z.read('payload/app.asar')
    assert sha(raw)==BASE_ASAR,'Official v1.0.102 ASAR hash changed!'
    magic,block,hs,n=struct.unpack_from('<4I',raw)
    assert magic==4 and block==hs+4
    header=json.loads(raw[16:16+n]);start=8+block
    files=[]
    def walk(node,prefix=''):
        for name,entry in node.get('files',{}).items():
            if 'files' in entry: walk(entry,prefix+name+'/')
            elif 'offset' in entry:files.append((prefix+name,entry))
    walk(header);assert len(files)>200
    files.sort(key=lambda item:int(item[1]['offset']))
    output=bytearray();changed=set()
    for name,entry in files:
        old=raw[start+int(entry['offset']):start+int(entry['offset'])+entry['size']]
        assert len(old)==entry['size']
        if name=='update-manager.js':
            new=patch_ui(old.decode('utf8')).encode('utf8');changed.add(name)
        elif name=='release-notes.js':
            new=notes(old.decode('utf8')).encode('utf8');changed.add(name)
        elif name=='package.json':
            src=old.decode('utf8');assert json.loads(src)['version']=='1.0.102'
            new=once(src,'"version": "1.0.102"','"version": "1.0.103"').encode('utf8');changed.add(name)
        else:new=old
        entry['offset']=str(len(output));entry['size']=len(new)
        if name in changed and 'integrity' in entry:
            integ=entry['integrity'];integ['hash']=sha(new)
            length=int(integ.get('blockSize',4194304))
            integ['blocks']=[sha(new[i:i+length]) for i in range(0,len(new),length)]
        output.extend(new)
        if name in changed:
            (folder/name).parent.mkdir(parents=True,exist_ok=True)
            (folder/name).write_bytes(new)
    assert changed=={'update-manager.js','release-notes.js','package.json'}
    head=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8')
    padded=(len(head)+7)&~3
    final=struct.pack('<4I',4,padded+4,padded,len(head))+head+b'\0'*(padded-4-len(head))+output
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',final)
    with zipfile.ZipFile(target) as z:assert sha(z.read('payload/app.asar'))==sha(final)
    print(json.dumps({'version':'1.0.103','files_modified':sorted(changed),
       'asar_sha256':sha(final),'zip_sha256':sha(target.read_bytes())}))
if __name__=='__main__':
    source,target,folder=map(Path,sys.argv[1:4]);folder.mkdir(parents=True,exist_ok=True)
    build(source,target,folder)
