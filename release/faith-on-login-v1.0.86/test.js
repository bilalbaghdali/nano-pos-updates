'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {JSDOM}=require('/tmp/testkit/node_modules/jsdom');
const root=process.argv[2];if(!root)throw Error('Missing extracted application folder');
const faith=fs.readFileSync(root+'/nano-faith-login.js','utf8');
const data=fs.readFileSync(root+'/faith-items.js','utf8');
const renderer=fs.readFileSync(root+'/renderer.js','utf8');
assert.equal((renderer.match(/nano-pos-login-success/g)||[]).length,1,'Success event must be emitted once');
assert(renderer.includes("detail:{via:'native-success'}"),'Success event must be in authenticated login branch');
const model={window:{}};vm.runInNewContext(data,model);const all=model.window.NANO_FAITH_ITEMS_183;
assert.equal(all.length,100);assert.equal(new Set(all.map(x=>x.id)).size,100);
const store=new Map();const key='nano-faith-rotation-v185';
const sleep=n=>new Promise(resolve=>setTimeout(resolve,n));
async function run(mode,expected){
 const html='<html lang="ar"><body><div id="loginOverlay" class="login-active"></div><div id="lockOverlay" class="hidden"></div></body></html>';
 const dom=new JSDOM(html,{url:'http://localhost:8040/',runScripts:'outside-only'});
 const w=dom.window,d=w.document;
 Object.defineProperty(w,'localStorage',{configurable:true,value:{
   getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k)
 }});
 const set=w.setTimeout.bind(w);
 w.setTimeout=(cb,delay,...args)=>set(cb,Math.min(delay,14),...args);
 w.eval(data);w.eval(faith);d.dispatchEvent(new w.Event('DOMContentLoaded'));
 await sleep(25);
 assert(!d.getElementById('nanoFaithReminder183'),'No popup before login');
 if(mode==='startup'||mode==='invalid'){
   store.set('pos_current_user',JSON.stringify({id:1,username:'admin'}));
   if(mode==='invalid'){
     w.dispatchEvent(new w.CustomEvent('nano-pos-login-success',{detail:{via:'overlay-transition'}}));
     d.getElementById('loginOverlay').classList.add('hidden');
   } else{
     d.getElementById('loginOverlay').classList.add('hidden');
   }
   await sleep(40);
   assert(!d.getElementById('nanoFaithReminder183'),'A non-login event generated a popup');
   dom.window.close();return;
 }
 if(mode==='success'){
   // Credentials have succeeded and persisted a session.
   store.set('pos_current_user',JSON.stringify({id:1,username:'admin'}));
   w.dispatchEvent(new w.CustomEvent('nano-pos-login-success',{detail:{via:'native-success'}}));
   await sleep(46);
   assert(!d.getElementById('nanoFaithReminder183'),'Faith popup appeared over login overlay before transition');
   d.getElementById('loginOverlay').classList.add('hidden');
   await sleep(45);
   const modal=d.getElementById('nanoFaithReminder183');
   assert(modal,'Popup does not appear after successful login transition');
   assert.equal(modal.querySelector('.nano-faith-quote').textContent,all[expected].text,'Wrong rotated message');
   assert.equal(modal.querySelector('.nano-faith-attribution').textContent,'المصدر: '+all[expected].source);
   assert.equal(modal.querySelector('a').href,all[expected].url);
   assert.equal(modal.style.zIndex,'','Popup style overrides are attached to overlay, not dialog');
   assert(d.getElementById('nanoFaithReminder183').style.zIndex,'Popup must overlay main screen');
   modal.querySelector('.nano-faith-continue').click();
   assert(!d.getElementById('nanoFaithReminder183'),'Close button failed');
 }
 dom.window.close();
}
(async()=>{
 await run('startup');await run('invalid');
 assert(!store.has(key),'Failed login or startup advanced rotation');
 for(let i=0;i<3;i++)await run('success',i);
 const current=JSON.parse(store.get(key));assert.equal(current.totalShown,3);assert.equal(current.nextIndex,3);
 await run('startup');assert.equal(JSON.parse(store.get(key)).totalShown,3);
 console.log('PASS: strict successful-login popup; delayed until login overlay closes; 100 messages preserved; startup and failed-login do not trigger; links, close and persistent rotation work.');
})().catch(err=>{console.error(err);process.exitCode=1});
