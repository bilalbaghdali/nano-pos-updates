'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const script=fs.readFileSync('update-manager.js','utf8');
const sha='a'.repeat(64);
const flush=async(n=15)=>{for(let i=0;i<n;i++)await new Promise(resolve=>setImmediate(resolve));};
function setup({loginVisible=true,disabled=false,valid=true,available=true}={}){
  const storage=new Map();
  if(disabled)storage.set('nano-pos-auto-update-enabled-v1','false');
  let isLogin=loginVisible;
  const elStore=new Map(),callbacks=[],observers=[],events={},counts={check:0,download:0,install:0};
  const mkElement=id=>({
    id,disabled:false,textContent:'',innerHTML:'',dataset:{},style:{},
    classList:{contains:kind=>id==='loginOverlay'&&kind==='hidden'?!isLogin:false,
      add(){},remove(){},toggle(){}},
    addEventListener(type,fn){events[id+':'+type]=fn;},
    querySelector(){return {textContent:''};},querySelectorAll(){return[];}
  });
  const document={
    readyState:'complete',documentElement:{lang:'ar'},
    getElementById(id){if(!elStore.has(id))elStore.set(id,mkElement(id));return elStore.get(id);},
    querySelectorAll(){return[];}
  };
  const manifest={
    published:true,version:'1.0.97',features:{ar:['تحديث آلي']},
    releaseDate:'2026-10-21',selectedUpdateType:'patch',
    patches:[{fromVersions:['1.0.96'],directUrl:'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.97/test.zip',sha256:valid?sha:'bad',appAsarSha256:sha,fileName:'test.zip'}],
    download:{directUrl:'',pageUrl:''}
  };
  const nanoNative={
    getCurrentAppVersion:async()=>({version:'1.0.96'}),
    checkForUpdates:async()=>{counts.check++;return {success:true,available,currentVersion:'1.0.96',selectedUpdateType:'patch',manifest}},
    downloadUpdate:async()=>{counts.download++;return {success:true,updateKind:'patch',filePath:'/verified/updates/test.zip'}},
    installUpdate:async payload=>{counts.install++;assert.equal(payload.manifest.version,'1.0.97');return {success:true}},
    onUpdateProgress(){return()=>{}}
  };
  const window={nanoNative,currentLanguage:'ar',NANO_SALE_SAFE_195:{isPending:()=>false}};
  const ctx={window,document,console,Date,Promise,
    localStorage:{getItem:key=>storage.get(key)||null,setItem:(k,v)=>storage.set(k,v)},
    setTimeout:fn=>{callbacks.push(fn);return callbacks.length;},
    setInterval:fn=>0,
    MutationObserver:class {constructor(fn){this.fn=fn;observers.push(this);}observe(){}},
  };
  vm.runInNewContext(script,ctx,{filename:'update-manager.js'});
  return {window,counts,callbacks,observers,login(v){isLogin=v},manifest,storage};
}
async function start(t){
  await flush();
  assert.ok(t.callbacks.length>0,'startup check should be scheduled');
  await t.callbacks.shift()();
  await flush();
}
(async()=>{
 const auto=setup();await start(auto);
 assert.equal(auto.counts.check,1,'check on startup');
 assert.equal(auto.counts.download,1,'automatic in-app download');
 assert.equal(auto.counts.install,1,'automatic install at login screen');
 await auto.window.checkForUpdates(false);await flush();
 assert.equal(auto.counts.download,1,'do not redownload same version');
 assert.equal(auto.counts.install,1,'do not relaunch twice');

 const busy=setup({loginVisible:false});await start(busy);
 assert.equal(busy.counts.download,1,'stage in the background during work');
 assert.equal(busy.counts.install,0,'NEVER auto-restart in active sales');
 busy.login(true);for(const obs of busy.observers)obs.fn();await flush();
 assert.equal(busy.counts.install,1,'auto install once user returns to login');

 const off=setup({disabled:true});await start(off);
 assert.equal(off.counts.download,0,'user setting disables automatic download');

 const invalid=setup({valid:false});await start(invalid);
 assert.equal(invalid.counts.download,0,'reject unverified update manifest');

 const current=setup({available:false});await start(current);
 assert.equal(current.counts.download,0,'never download when up to date');

 console.log('PASS automatic start, safe install at login, busy cashier, dedupe, opt-out, manifest integrity.');
})().catch(error=>{console.error(error);process.exitCode=1});
