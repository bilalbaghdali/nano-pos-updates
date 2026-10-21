#!/usr/bin/env python3
"""Build NANO POS 1.0.97 only from verified, official v1.0.96 ASAR."""
import hashlib, json, struct, sys, zipfile
from pathlib import Path
SHA=lambda b:hashlib.sha256(b).hexdigest()
OFFICIAL='a09b0fdffb6c9e2ce75011bda51ed315467ae68e6003e9eea7a62288c4b2fbfe'
ORIGINAL_UPDATER='57f576363c70ad32a69f1374cd3cb204cc31e1a0c8fea69ebbda1223b05c4979'

def once(s,a,b):
    assert s.count(a)==1,('unexpected_original_source',a[:110],s.count(a))
    return s.replace(a,b)

def patch_manager(s):
    s=once(s,"  let progressUnsub = null;","""  let progressUnsub = null;
  let autoAttemptedVersion = '';
  let autoDownloading = false;
  let autoInstalling = false;
  let autoLoginObserver = null;
  // Automatic download is enabled; installation only happens at the sign-in screen.
  // This avoids shutting down a cashier in the middle of a sale.
  const AUTO_UPDATE_SETTING = 'nano-pos-auto-update-enabled-v1';""")
    s=once(s,"      checksumError: 'فشل التحقق من سلامة ملف التحديث. لم يتم تشغيله.',",
             "      autoReady: 'اكتمل تحميل التحديث. سيُثبّت تلقائيًا عند الرجوع لشاشة الدخول.', autoDownloading: 'يُحمّل التحديث تلقائيًا…',\n      checksumError: 'فشل التحقق من سلامة ملف التحديث. لم يتم تشغيله.',")
    s=once(s,"      checksumError: \"Échec de la vérification d'intégrité. Le fichier n'a pas été exécuté.\",",
             "      autoReady: 'Mise à jour téléchargée. Installation automatique au prochain écran de connexion.', autoDownloading: 'Téléchargement automatique…',\n      checksumError: \"Échec de la vérification d'intégrité. Le fichier n'a pas été exécuté.\",")
    s=once(s,"      checksumError: 'Update integrity verification failed. The file was not launched.',",
             "      autoReady: 'Update downloaded; it will install automatically at the sign-in screen.', autoDownloading: 'Automatically downloading update…',\n      checksumError: 'Update integrity verification failed. The file was not launched.',")
    s=once(s,"    currentManifest = manifest;\n    downloadedUpdate = null;",
             "    if (currentManifest?.version !== manifest.version) downloadedUpdate = null;\n    currentManifest = manifest;")
    s=once(s,"        openModal(result.manifest);\n      } else {",
             "        openModal(result.manifest);\n        scheduleAutomaticUpdate(result);\n      } else {")
    start="  function bindProgress() {"
    assert s.count(start)==1
    helper="""  function autoEnabled() {
    try { return localStorage.getItem(AUTO_UPDATE_SETTING) !== 'false'; }
    catch { return true; }
  }
  function loginSafeForRestart() {
    const login = el('loginOverlay');
    return !!(login && !login.classList.contains('hidden')
      && !(window.NANO_SALE_SAFE_195?.isPending?.()));
  }
  function installAutoWhenSafe() {
    if (!autoEnabled() || !downloadedUpdate || autoInstalling || !loginSafeForRestart()) return;
    if (downloadedUpdate.version !== currentManifest?.version) return;
    autoInstalling = true;
    installDownloadedUpdate(downloadedUpdate).then(success => {
      if (!success) autoInstalling = false; // Manual retry stays available.
    }).catch(error => {
      autoInstalling = false;
      console.error('[NANO auto update] install failed:', error);
      showToastSafe(error?.message || 'Automatic update failed', 'error');
    });
  }
  function observeLoginSafety() {
    if (autoLoginObserver || typeof MutationObserver === 'undefined') return;
    const login = el('loginOverlay');
    if (!login) return;
    autoLoginObserver = new MutationObserver(installAutoWhenSafe);
    autoLoginObserver.observe(login, {attributes: true, attributeFilter: ['class']});
  }
  function validAutomaticSource(result) {
    const manifest = result?.manifest;
    if (!result?.success || !result.available || !manifest?.published) return false;
    if (typeof window.nanoNative?.downloadUpdate !== 'function' ||
        typeof window.nanoNative?.installUpdate !== 'function' ||
        typeof window.nanoNative?.getCurrentAppVersion !== 'function') return false;
    const prefix = 'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/';
    if (result.selectedUpdateType === 'patch') return Array.isArray(manifest.patches)
      && manifest.patches.some(p => p.fromVersions?.includes(result.currentVersion)
        && p.directUrl?.startsWith(prefix) && /^[a-f0-9]{64}$/i.test(p.sha256 || '')
        && /^[a-f0-9]{64}$/i.test(p.appAsarSha256 || ''));
    return !!(manifest.download?.directUrl?.startsWith(prefix)
      && /^[a-f0-9]{64}$/i.test(manifest.download.sha256 || ''));
  }
  function scheduleAutomaticUpdate(result) {
    if (!autoEnabled() || !validAutomaticSource(result) || autoDownloading) return;
    if (autoAttemptedVersion === result.manifest.version) {
      installAutoWhenSafe();
      return;
    }
    autoAttemptedVersion = result.manifest.version;
    autoDownloading = true;
    observeLoginSafety();
    bindProgress();
    const btn = el('updateModalDownloadBtn');
    if (btn) {
      btn.disabled = true;
      const label = btn.querySelector('[data-i18n="download_update"]') || btn.querySelector('span:last-child');
      if (label) label.textContent = s('autoDownloading');
    }
    updateStatus(s('autoDownloading'), 'cloud_download');
    Promise.resolve().then(async () => {
      const downloaded = await window.nanoNative.downloadUpdate(result.manifest);
      if (!downloaded?.success || !downloaded.filePath) {
        throw new Error(downloaded?.error || 'auto_download_failed');
      }
      // Still on the same release? A later check must not apply stale downloads.
      if (currentManifest?.version !== result.manifest.version) return;
      downloadedUpdate = {...downloaded,version:result.manifest.version};
      updateStatus(s('autoReady'), 'verified');
      if (btn) {
        btn.disabled = false;
        const label = btn.querySelector('[data-i18n="download_update"]') || btn.querySelector('span:last-child');
        if (label) label.textContent = s('install');
      }
      installAutoWhenSafe();
    }).catch(error => {
      console.error('[NANO auto update] Download failed:', error);
      updateStatus(s('failed'), 'cloud_off');
      if (btn) {
        btn.disabled = false;
        const label = btn.querySelector('[data-i18n="download_update"]') || btn.querySelector('span:last-child');
        if (label) label.textContent = s('retry');
      }
      showToastSafe(error?.message || s('failed'), 'error');
    }).finally(() => { autoDownloading = false; });
  }

"""
    s=once(s,start,helper+start)
    s=once(s,"    if (!btn || !currentManifest) return;\n    if (downloadedUpdate) {",
             "    if (!btn || !currentManifest || autoDownloading || autoInstalling) return;\n    if (downloadedUpdate) {")
    s=once(s,"    window.closeUpdateModal = closeModal;\n    renderUpdateMeta();",
             "    window.closeUpdateModal = closeModal;\n    window.setNanoAutoUpdates = enabled => {\n      localStorage.setItem(AUTO_UPDATE_SETTING, enabled === false ? 'false' : 'true');\n      if (enabled !== false) installAutoWhenSafe();\n    };\n    renderUpdateMeta();")
    return s

def patch_release_notes(s):
    assert "const FALLBACK_VERSION = '1.0.94';" in s
    s=once(s,"const FALLBACK_VERSION = '1.0.94';","const FALLBACK_VERSION = '1.0.97';")
    start=s.index("  const OFFLINE = {")
    end=s.index("  const TITLES = {",start)
    notes="""  const OFFLINE = {
    ar: [
      'البحث تلقائيًا عن تحديثات NANO POS عند فتح البرنامج وبصورة دورية.',
      'تنزيل حزمة التحديث الموثقة والتحقق من سلامتها دون الحاجة إلى تنزيل ZIP يدويًا.',
      'تثبيت التحديث وإعادة التشغيل تلقائيًا عند شاشة الدخول، وتأجيله أثناء العمل لحماية الفواتير.'
    ],
    fr: [
      'Vérification automatique au démarrage et régulièrement.',
      'Téléchargement et vérification automatiques des mises à jour officielles.',
      'Installation au moment de la connexion, sans interrompre les ventes.'
    ],
    en: [
      'Automatically check for updates at startup and periodically.',
      'Automatically download and verify official update packages in the app.',
      'Install and restart at the sign-in screen, deferring during active sales.'
    ]
  };
"""
    return s[:start]+notes+s[end:]

def make(source,output,tests):
    with zipfile.ZipFile(source) as z:
        assert z.namelist()==['payload/app.asar']
        data=z.read('payload/app.asar')
    assert SHA(data)==OFFICIAL, 'Not official 1.0.96 ASAR'
    magic,block,hs,n=struct.unpack_from('<4I',data)
    assert magic==4 and block==hs+4
    header=json.loads(data[16:16+n]); start=8+block;files=[]
    def visit(node,prefix=''):
        for name,entry in node.get('files',{}).items():
            if 'files' in entry:visit(entry,prefix+name+'/')
            elif 'offset' in entry: files.append((prefix+name,entry))
    visit(header);assert len(files)>200
    files.sort(key=lambda x:int(x[1]['offset']))
    new=bytearray();changed=set()
    for name,entry in files:
        blob=data[start+int(entry['offset']):start+int(entry['offset'])+entry['size']]
        assert len(blob)==entry['size']
        if name=='update-manager.js':
            assert SHA(blob)==ORIGINAL_UPDATER, 'Update manager source changed'
            patched=patch_manager(blob.decode('utf8')).encode('utf8');changed.add(name)
        elif name=='release-notes.js':
            patched=patch_release_notes(blob.decode('utf8')).encode('utf8');changed.add(name)
        elif name=='package.json':
            src=blob.decode('utf8')
            assert json.loads(src)['version']=='1.0.96'
            patched=once(src,'"version": "1.0.96"','"version": "1.0.97"').encode('utf8');changed.add(name)
        else:patched=blob
        entry['offset']=str(len(new));entry['size']=len(patched)
        if name in changed and 'integrity' in entry:
            item=entry['integrity'];item['hash']=SHA(patched)
            step=int(item.get('blockSize',4194304))
            item['blocks']=[SHA(patched[i:i+step]) for i in range(0,len(patched),step)]
        new.extend(patched)
        if name in changed:
            (tests/name).parent.mkdir(parents=True,exist_ok=True)
            (tests/name).write_bytes(patched)
    assert changed=={'package.json','update-manager.js','release-notes.js'}
    h=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8'); padded=(len(h)+7)&~3
    final=struct.pack('<4I',4,padded+4,padded,len(h))+h+b'\0'*(padded-4-len(h))+new
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',final)
    with zipfile.ZipFile(output) as z:assert SHA(z.read('payload/app.asar'))==SHA(final)
    print(json.dumps({'version':'1.0.97','modified':sorted(changed),'asar_sha256':SHA(final),'zip_sha256':SHA(output.read_bytes())}))
if __name__=='__main__':
    source,output,testdir=map(Path,sys.argv[1:4]);testdir.mkdir(parents=True,exist_ok=True)
    make(source,output,testdir)
