'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const crypto=require('node:crypto'),vm=require('node:vm');
const root=process.argv[2];
if (!root) throw new Error('source_directory_required');
const updates=fs.readFileSync(path.join(root,'updater-main.cjs'),'utf8');
const backups=require(path.join(root,'backup-safety.cjs'));
const pkg=require(path.join(root,'package.json'));
assert.equal(pkg.version,'1.0.94');
assert.match(updates,/\[System\.IO\.File\]::Replace\(\$targetNew, \$target, \$targetOld, \$true\)/);
assert.match(updates,/patch_checksum_changed/);
assert.match(updates,/installer_checksum_required/);
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'nano-pos-194-test-'));
async function run(){
 try {
  const store=path.join(temp,'backups');
  const snapshot=JSON.stringify({products:[{id:1}],sales:[],purchases:[],customers:[],suppliers:[]});
  const good=backups.saveVerifiedBackup(store,'nano_auto_backup_test.json',snapshot);
  assert.equal(backups.verifyBackup(good.filePath),true);
  assert.throws(()=>backups.saveVerifiedBackup(store,'nano_auto_backup_test.json',snapshot));
  assert.throws(()=>backups.saveVerifiedBackup(store,'../unsafe.json',snapshot));
  assert.equal(backups.verifyBackup(path.join(store,'not_found.json')),false);
  fs.writeFileSync(good.filePath,'{"products":[]}');
  assert.equal(backups.verifyBackup(good.filePath),false);
  const valid=backups.saveVerifiedBackup(store,'nano_backup_manual.json',snapshot);
  fs.unlinkSync(valid.filePath+'.sha256');
  assert.equal(backups.verifyBackup(valid.filePath),false);
  const retained=backups.saveVerifiedBackup(store,'nano_backup_retain.json',snapshot);
  backups.pruneBackups(store,{maxAutomatic:1});
  assert.equal(backups.verifyBackup(retained.filePath),true);
  const mockedElectron={app:{getVersion:()=> '1.0.93',getPath:()=>temp,isPackaged:false},shell:{openExternal:async()=>{}},BrowserWindow:{fromWebContents:()=>null}};
  const mod={exports:{}},ipc={};
  vm.runInNewContext(updates,{module:mod,exports:mod.exports,require:k=>k==='electron'?mockedElectron:require(k),process,Buffer,URL,setTimeout,clearTimeout,console},{filename:'updater-main.cjs'});
  mod.exports.registerUpdaterIpc({handle:(event,fn)=>ipc[event]=fn});
  assert.equal(mod.exports.compareVersions('1.0.94','1.0.93'),1);
  const dir=path.join(temp,'updates');fs.mkdirSync(dir);
  const update=path.join(dir,'safe-patch.zip');
  fs.writeFileSync(update,Buffer.from([0x50,0x4b,0x03,0x04,1,2,3]));
  const digest=crypto.createHash('sha256').update(fs.readFileSync(update)).digest('hex');
  const manifest={
    product:'NANO POS',version:'1.0.94',published:true,
    patches:[{id:'safety',fromVersions:['1.0.93'],fileName:'safe-patch.zip',
      directUrl:'https://github.com/example/p.zip',sha256:'0'.repeat(64),appAsarSha256:'1'.repeat(64)}]
  };
  const install=ipc['nano-update-install'];
  const bad=await install({}, {filePath:update,updateKind:'patch',manifest});
  assert.equal(bad.error,'patch_checksum_changed');
  const downgrade=await install({}, {filePath:update,updateKind:'patch',manifest:{...manifest,version:'1.0.93'}});
  assert.equal(downgrade.error,'update_version_not_newer');
  const passedIntegrity=await install({}, {filePath:update,updateKind:'patch',manifest:{...manifest,patches:[{...manifest.patches[0],sha256:digest}]}});
  assert.equal(passedIntegrity.error,'patch_requires_packaged_app');
  const malicious=await install({}, {filePath:update,updateKind:'full',manifest:{...manifest,patches:[],download:{directUrl:'https://example.com/test',fileName:'safe-patch.zip'}}});
  assert.equal(malicious.error,'patch_not_applicable');
  const marker='return String.raw'+String.fromCharCode(96);
  const start=updates.indexOf(marker);
  const end=updates.indexOf(String.fromCharCode(96)+';\n}',start);
  assert(start>=0 && end>start);
  const ps=updates.slice(start+marker.length,end);
  assert(ps.includes('Atomic replacement'));
  fs.writeFileSync(path.join(root,'test-patch-helper.ps1'),ps,'utf8');
  console.log('PASS: downgrade, package integrity, backup corruption, Windows helper extraction');
 } finally {fs.rmSync(temp,{recursive:true,force:true});}
}
run().catch(e=>{console.error(e);process.exitCode=1});
