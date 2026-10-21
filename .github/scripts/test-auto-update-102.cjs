'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const raw=JSON.parse(fs.readFileSync('nano-pos-update.json','utf8'));
const source=fs.readFileSync('work/updater-main.cjs','utf8');
const moduleShim={exports:{}};
const fakeRequire=(name)=>name==='electron'?{
  app:{getVersion:()=> '1.0.100',getPath:()=>path.join(process.cwd(),'fake-data')},
  shell:{},BrowserWindow:{}
}:require(name);
vm.runInThisContext('(function(require,module,exports,__dirname,__filename){'+source+'\n})',{
  filename:'updater-main.cjs'
})(fakeRequire,moduleShim,moduleShim.exports,process.cwd(),'updater-main.cjs');
const {normalizeManifest,findApplicablePatch,selectUpdateType,compareVersions}=moduleShim.exports;
assert.equal(typeof normalizeManifest,'function');
const manifest=normalizeManifest(raw,'https://raw.githubusercontent.com/bilalbaghdali/nano-pos-updates/main/nano-pos-update.json');
assert.equal(manifest.version,'1.0.102');
assert.equal(manifest.patches.length,1);
const versions=['1.0.97','1.0.98','1.0.99','1.0.100','1.0.101'];
for(const version of versions){
  const choice=findApplicablePatch(manifest,version);
  assert.ok(choice,'Missing automated patch from '+version);
  assert.equal(selectUpdateType(manifest,version),'patch');
  assert.equal(choice.sha256,raw.patches[0].sha256);
  assert.equal(choice.appAsarSha256,raw.patches[0].appAsarSha256);
  assert.equal(compareVersions(manifest.version,version)>0,true);
}
assert.equal(compareVersions('1.0.102','1.0.102'),0);
assert.equal(selectUpdateType(manifest,'1.0.102'),'full');
assert.equal(selectUpdateType(manifest,'1.0.96'),'full','Old app version lacks safe automatic updater; do not pretend it is compatible');
assert.equal(manifest.mandatory,false,'avoid forced app shutdown while cashier operates');
assert.equal(manifest.download.directUrl,'','do not invent a full installer URL');
console.log('PASS: Real production updater selects verified 1.0.102 ASAR for all v1.0.97-v1.0.101');
console.log('PASS: No forced restart, no fake full installer and no downgrade');
