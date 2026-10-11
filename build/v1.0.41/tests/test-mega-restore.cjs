'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {saveVerifiedBackup,verifyBackup}=require('../current/backup-safety.cjs');
const {createMegaRestoreCoordinator,safeSnapshot}=require('../current/mega-restore-safety.cjs');
const fixture=(num=1)=>JSON.stringify({products:[{id:num}],customers:[],suppliers:[],sales:[],purchases:[],expenses:[],revision:num});
test('preview returns exact counts without modifying live data',async()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nano-mega-rest-test-'));
  try{
    const s=saveVerifiedBackup(dir,'nano_backup_sample.json',fixture(1));
    const make=createMegaRestoreCoordinator({userDataDir:dir,downloadBackup:async()=>({filePath:s.filePath,verified:true})});
    const out=await make.prepare('nano_backup_sample.json');
    assert.deepEqual(out.summary,{products:1,customers:0,suppliers:0,sales:0,purchases:0,expenses:0});
    assert.ok(out.token.length>=32);assert.equal(fs.readdirSync(dir).filter(n=>n.startsWith('nano_pre_')).length,0);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('verified restore makes safety copy before handing back snapshot and rejects reuse',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nano-mega-rest-test-'));
 try{
  const s=saveVerifiedBackup(dir,'nano_backup_sample.json',fixture(1));
  const svc=createMegaRestoreCoordinator({userDataDir:dir,downloadBackup:async()=>({filePath:s.filePath,verified:true})});
  const p=await svc.prepare('nano_backup_sample.json');
  const result=svc.commit(p.token,fixture(2));
  assert.equal(result.success,true);assert.deepEqual(JSON.parse(result.snapshot),JSON.parse(fixture(1)));
  assert.ok(verifyBackup(result.safetyBackup));assert.equal(fs.readFileSync(result.safetyBackup,'utf8'),fixture(2));
  assert.throws(()=>svc.commit(p.token,fixture(2)),/mega_restore_session_expired/);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('rejects invalid filenames, invalid schema, expired token and changed remote contents',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nano-mega-rest-test-'));
 try{
  const s=saveVerifiedBackup(dir,'nano_backup_sample.json',fixture());let clock=1;
  const svc=createMegaRestoreCoordinator({userDataDir:dir,downloadBackup:async()=>({filePath:s.filePath,verified:true}),now:()=>clock});
  await assert.rejects(()=>svc.prepare('../passwd'),/invalid_backup_name/);
  const p=await svc.prepare('nano_backup_sample.json');clock=6*60*1000+1;
  assert.throws(()=>svc.commit(p.token,fixture()),/mega_restore_session_expired/);
  clock=2;const p2=await svc.prepare('nano_backup_sample.json');
  fs.appendFileSync(s.filePath,' ');
  assert.throws(()=>svc.commit(p2.token,fixture()),/mega_backup_integrity_failed/);
  assert.throws(()=>safeSnapshot('{}'),/mega_restore_invalid_schema/);
  assert.throws(()=>safeSnapshot('[]'),/mega_restore_invalid_schema/);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('refuses restore if safety backup cannot be persisted',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nano-mega-rest-test-'));
 try{
  const s=saveVerifiedBackup(dir,'nano_backup_sample.json',fixture());
  const svc=createMegaRestoreCoordinator({userDataDir:dir,downloadBackup:async()=>({filePath:s.filePath,verified:true}),saveBackup:()=>{throw new Error('disk_full');}});
  const p=await svc.prepare('nano_backup_sample.json');
  assert.throws(()=>svc.commit(p.token,fixture()),/disk_full/);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});