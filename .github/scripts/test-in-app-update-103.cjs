'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('update-manager.js','utf8');
const SHA='a'.repeat(64),base='https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.103/';
const settle=async(n=25)=>{for(let i=0;i<n;i++)await new Promise(resolve=>setImmediate(resolve));};
function mock({current='1.0.102',supported=true,enableAuto=false,busy=false,failure=false}={}){
 const listeners={},elements=new Map(),observers=[],timers=[],store=new Map();
 if(!enableAuto)store.set('nano-pos-auto-update-enabled-v1','false');
 const counts={check:0,download:0,install:0,openPage:0,errors:[]};
 function mk(id){
  return {id,dataset:{},disabled:false,innerHTML:'',textContent:'',style:{},
    classList:{contains:kind=>kind==='hidden'&&id==='loginOverlay'?busy:false,
      add(){},remove(){},toggle(){}},
    querySelector:()=>({textContent:''}),querySelectorAll:()=>[],
    addEventListener(type,cb){listeners[id+':'+type]=cb;}
  };
 }
 const document={readyState:'complete',documentElement:{lang:'ar'},
  getElementById(id){if(!elements.has(id))elements.set(id,mk(id));return elements.get(id);}};
 const manifest={published:true,version:'1.0.103',releaseDate:'2026-10-21',mandatory:false,
  features:{ar:['تصحيح التحديث الداخلي']},selectedUpdateType:supported?'patch':'full',
  patches:[{id:'repair103',fromVersions:supported?[current]:[],
    directUrl:base+'full-asar.zip',sha256:SHA,appAsarSha256:SHA}],
  download:{directUrl:'',pageUrl:'https://github.com/bilalbaghdali/nano-pos-updates/releases/tag/v1.0.103'}};
 const nanoNative={
  checkForUpdates:async()=>{counts.check++;return {success:true,available:true,manifest,currentVersion:current,selectedUpdateType:manifest.selectedUpdateType}},
  downloadUpdate:async()=>{counts.download++;return failure?{success:false,manual:true,pageUrl:manifest.download.pageUrl,error:'download_http_503'}:
    {success:true,filePath:'C:/verified/update.zip',updateKind:'patch'};},
  installUpdate:async data=>{counts.install++;assert.equal(data.manifest.version,'1.0.103');return {success:true};},
  openUpdatePage:async()=>{counts.openPage++;return {success:true};},
  getCurrentAppVersion:async()=>({version:current}),
  onUpdateProgress:()=>()=>{},
  getLastUpdateResult:async()=>null
 };
 const window={nanoNative,currentLanguage:'ar',NANO_SALE_SAFE_195:{isPending:()=>false},
  showToast:(msg,kind)=>counts.errors.push([String(msg),kind])};
 const context={window,document,console,Date,Promise,
  localStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)},
  setTimeout:fn=>{timers.push(fn);return timers.length},
  setInterval:()=>0,
  MutationObserver:class{constructor(fn){this.fn=fn;observers.push(this);}observe(){}}
 };
 vm.runInNewContext(code,context,{filename:'update-manager.js'});
 return {counts,manifest,elements,listeners,timers,observers,busy(v){busy=v}};
}
async function start(t){
 await settle();
 assert.ok(t.timers.length,'startup check registered');
 await t.timers.shift()();await settle();
}
async function click(t){
 assert.equal(typeof t.listeners['updateModalDownloadBtn:click'],'function');
 await t.listeners['updateModalDownloadBtn:click']();await settle();
}
(async()=>{
 const active=mock();await start(active);
 assert.equal(active.elements.get('updateModalDownloadBtn').dataset.mode,'download');
 await click(active);
 assert.equal(active.counts.download,1,'click downloads zip within app');
 assert.equal(active.counts.install,1,'click installs verified zip within app');
 assert.equal(active.counts.openPage,0,'NEVER open browser');

 const unsupported=mock({supported:false});await start(unsupported);
 assert.equal(unsupported.elements.get('updateModalDownloadBtn').dataset.mode,'none');
 await click(unsupported);
 assert.equal(unsupported.counts.download,0,'do not install unsupported ZIP');
 assert.equal(unsupported.counts.openPage,0,'unsupported version stays in app');

 const failed=mock({failure:true});await start(failed);await click(failed);
 assert.equal(failed.counts.download,1);
 assert.equal(failed.counts.openPage,0,'a network fallback must NOT open GitHub');
 assert.ok(failed.counts.errors.some(x=>x[1]==='error'));

 const auto=mock({enableAuto:true,busy:true});await start(auto);
 assert.equal(auto.counts.download,1,'automatic download starts');
 assert.equal(auto.counts.install,0,'no restart while cashier is working');
 auto.busy(false);for(const obs of auto.observers)obs.fn();await settle();
 assert.equal(auto.counts.install,1,'install after returning to login');
 assert.equal(auto.counts.openPage,0);

 console.log('PASS v1.0.103: in-app click downloads and installs; unsupported and failed downloads never open browser; safe auto-restart.');
})().catch(e=>{console.error(e);process.exitCode=1;});
