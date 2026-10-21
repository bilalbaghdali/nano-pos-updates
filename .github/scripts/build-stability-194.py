#!/usr/bin/env python3
"""Fail-closed NANO POS 1.0.94 ASAR patch; aborts on unexpected official base."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
SHA=lambda b:hashlib.sha256(b).hexdigest()
ORIGINAL={
 'updater-main.cjs':'0a977713744ed5b738b00e3cdb5a07f914a9bb1902ebf719c5b080fed2971a9a',
 'backup-safety.cjs':'4c4acd363758abe31134ad01ae163bf43195031479ebdf1c3c328c7e20fbae30'}
BASE_ASAR='74725370d317031683794312bcfebd3b131c8ec64e1e4db7c4e2083814f5d269'
def replace(s,old,new):
 assert s.count(old)==1,('marker_not_unique',old[:100],s.count(old))
 return s.replace(old,new)
def between(s,start,end,new):
 assert s.count(start)==1 and s.count(end)==1,('boundary_not_unique',start)
 i=s.index(start);j=s.index(end,i)
 return s[:i]+new+s[j:]
def patch_updater(s):
 s=replace(s,
 """  const updateDir = path.join(app.getPath('userData'), 'updates');
  const filePath = path.join(updateDir, manifest.download.fileName);""",
 """  if (!manifest.download.sha256) return { success: false, error: 'installer_checksum_required', ...extra };
  const updateDir = path.join(app.getPath('userData'), 'updates');
  const filePath = path.join(updateDir, manifest.download.fileName);""")
 s=replace(s,
 """$backup = Join-Path $BackupDir 'app.asar'
$log = Join-Path $BackupDir 'patch.log'""",
 """$backup = Join-Path $BackupDir 'app.asar'
$targetOld = Join-Path $ResourcesPath ('app.asar.nano-prev-' + [guid]::NewGuid().ToString('N'))
$log = Join-Path $BackupDir 'patch.log'""")
 s=replace(s,
 """  Copy-Item -LiteralPath $target -Destination $backup -Force
  $backupMade = $true
  Write-Log 'Backup created.'""",
 """  $originalHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
  Copy-Item -LiteralPath $target -Destination $backup -Force
  if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $originalHash) { throw 'rollback_backup_verification_failed' }
  $backupMade = $true
  Write-Log ('Rollback backup verified: ' + $originalHash)""")
 s=between(s,"  $replaced = $false\n  $lastError = ''\n  for ($i = 0; $i -lt 60;",
 """  Remove-Item -LiteralPath $targetNew -Force -ErrorAction SilentlyContinue
  Set-Content -LiteralPath (Join-Path $BackupDir 'applied.txt')""",
 """  # Atomic replacement avoids a half-written app.asar on interruption.
  $replaced = $false
  $lastError = ''
  for ($i = 0; $i -lt 60; $i++) {
    try {
      [System.IO.File]::Replace($targetNew, $target, $targetOld, $true)
      $replaced = $true
      break
    } catch {
      $lastError = $_.Exception.Message
    }
    Start-Sleep -Milliseconds 500
  }
  if (-not $replaced) { throw ('atomic_replace_failed: ' + $lastError) }
  $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($targetHash -ne $ExpectedAsarSha.ToLowerInvariant()) { throw 'installed_payload_sha256_mismatch' }
  Remove-Item -LiteralPath $targetOld -Force -ErrorAction SilentlyContinue
""")
 s=replace(s,
 """      Copy-Item -LiteralPath $backup -Destination $target -Force
      Write-Log 'Rollback restored previous app.asar.'""",
 """      if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $originalHash) { throw 'rollback_backup_hash_mismatch' }
      Copy-Item -LiteralPath $backup -Destination $targetNew -Force
      if (Test-Path -LiteralPath $target) {
        $failedTarget = Join-Path $ResourcesPath ('app.asar.nano-failed-' + [guid]::NewGuid().ToString('N'))
        [System.IO.File]::Replace($targetNew, $target, $failedTarget, $true)
        Remove-Item -LiteralPath $failedTarget -Force -ErrorAction SilentlyContinue
      } else { Move-Item -LiteralPath $targetNew -Destination $target -Force }
      if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $originalHash) { throw 'rollback_restore_verification_failed' }
      Write-Log 'Rollback restored and verified previous app.asar.'""")
 s=replace(s,
 """      const patch = findApplicablePatch(manifest, currentVersion);
      if (patch) {""",
 """      if (!manifest.published || compareVersions(manifest.version, currentVersion) <= 0) {
        return { success: false, error: 'update_version_not_newer' };
      }
      const patch = findApplicablePatch(manifest, currentVersion);
      if (patch) {""")
 s=replace(s,
 """      if (ext === '.zip' || payload.updateKind === 'patch') {
        const manifest = normalizeManifest(payload.manifest || {}, DEFAULT_MANIFEST_URL);
        const patch = findApplicablePatch(manifest, app.getVersion());
        if (!patch) return { success: false, error: 'patch_not_applicable' };
        sendProgress(event, { phase: 'applying_patch', percent: 100, updateKind: 'patch' });
        return await launchPatchInstaller(filePath, manifest, patch);
      }
      if (ext !== '.exe') return { success: false, error: 'invalid_installer' };
      sendProgress(event, { phase: 'installing', percent: 100, updateKind: 'full' });""",
 """      const manifest = normalizeManifest(payload.manifest || {}, DEFAULT_MANIFEST_URL);
      if (!manifest.published || compareVersions(manifest.version, app.getVersion()) <= 0) {
        return { success: false, error: 'update_version_not_newer' };
      }
      if (ext === '.zip' || payload.updateKind === 'patch') {
        if (ext !== '.zip') return { success: false, error: 'invalid_patch_file' };
        const patch = findApplicablePatch(manifest, app.getVersion());
        if (!patch) return { success: false, error: 'patch_not_applicable' };
        if (path.basename(filePath) !== patch.fileName || !isZipFile(filePath)) {
          return { success: false, error: 'patch_filename_or_format_mismatch' };
        }
        if (await sha256File(filePath) !== patch.sha256) {
          return { success: false, error: 'patch_checksum_changed' };
        }
        sendProgress(event, { phase: 'applying_patch', percent: 100, updateKind: 'patch' });
        return await launchPatchInstaller(filePath, manifest, patch);
      }
      if (ext !== '.exe') return { success: false, error: 'invalid_installer' };
      if (!manifest.download.sha256 || path.basename(filePath) !== manifest.download.fileName ||
          readMagic(filePath, 2).toString('ascii') !== 'MZ' ||
          await sha256File(filePath) !== manifest.download.sha256) {
        return { success: false, error: 'installer_integrity_check_failed' };
      }
      sendProgress(event, { phase: 'installing', percent: 100, updateKind: 'full' });""")
 return s
def patch_backup(s):
 s=replace(s,
 """    fs.renameSync(tmp,dest);
    fs.renameSync(shaTmp,dest+'.sha256');
    return {filePath:dest,checksum:sha};""",
 """    fs.renameSync(tmp,dest);
    try { fs.renameSync(shaTmp,dest+'.sha256'); }
    catch(error) {
      try { fs.unlinkSync(dest); } catch {}
      throw error;
    }
    return {filePath:dest,checksum:sha};""")
 s=between(s,"function verifyBackup(filePath){","function pruneBackups(directory",
 r"""function verifyBackup(filePath){
  try {
    const stat=fs.statSync(filePath);
    if(!stat.isFile() || stat.size>MAX) return false;
    const contents=fs.readFileSync(filePath);
    const parsed=JSON.parse(contents.toString('utf8'));
    if(!parsed||Array.isArray(parsed)||typeof parsed!=='object') return false;
    const sidecar=fs.readFileSync(filePath+'.sha256','utf8').trim();
    const match=/^([a-f0-9]{64})  ([^\\/]+\.json)$/i.exec(sidecar);
    return Boolean(match && match[2]===path.basename(filePath) && match[1].toLowerCase()===digest(contents));
  } catch { return false; }
}
""")
 return s
def build(data):
 magic,block,hs,n=struct.unpack_from('<4I',data)
 assert magic==4 and block==hs+4
 header=json.loads(data[16:16+n]);content=8+block
 entries=[]
 def visit(node,prefix=''):
  for name,entry in node.get('files',{}).items():
   if 'files' in entry: visit(entry,prefix+name+'/')
   elif 'offset' in entry:entries.append((prefix+name,entry))
 visit(header)
 assert len(entries)>200
 entries.sort(key=lambda it:int(it[1]['offset']))
 payload=bytearray();changed=set()
 for filename,entry in entries:
  start=content+int(entry['offset']);blob=data[start:start+entry['size']]
  assert len(blob)==entry['size']
  if filename in ORIGINAL:
   assert SHA(blob)==ORIGINAL[filename],('source_changed',filename)
   blob=(patch_updater if filename=='updater-main.cjs' else patch_backup)(blob.decode()).encode()
   changed.add(filename)
  elif filename=='package.json':
   src=blob.decode()
   assert json.loads(src)['version']=='1.0.93'
   blob=replace(src,'"version": "1.0.93"','"version": "1.0.94"').encode()
   changed.add(filename)
  entry['offset']=str(len(payload));entry['size']=len(blob)
  if filename in changed and 'integrity' in entry:
   entry['integrity']['hash']=SHA(blob)
   entry['integrity']['blocks']=[SHA(blob[i:i+4194304]) for i in range(0,len(blob),4194304)]
  payload.extend(blob)
 assert changed=={'updater-main.cjs','backup-safety.cjs','package.json'}
 h=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode()
 padded=(len(h)+7)&~3
 return struct.pack('<4I',4,padded+4,padded,len(h))+h+b'\0'*(padded-4-len(h))+payload
if __name__=='__main__':
 source,destination,sha_out=sys.argv[1:4]
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar']
  data=z.read('payload/app.asar')
 assert SHA(data)==BASE_ASAR,'v1.0.93 base payload SHA mismatch'
 final=build(data)
 with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('payload/app.asar',final)
 info={'from':'1.0.93','version':'1.0.94','sha256':SHA(Path(destination).read_bytes()),'asarSha256':SHA(final)}
 Path(sha_out).write_text(json.dumps(info,indent=2)+'\n')
 print(json.dumps(info,indent=2))
