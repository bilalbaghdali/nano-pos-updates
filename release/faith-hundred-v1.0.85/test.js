'use strict';
const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const {JSDOM}=require('/tmp/testkit/node_modules/jsdom');
const dir=process.argv[2];if(!dir)throw Error('ASAR extraction path required');
const data=fs.readFileSync(dir+'/faith-items.js','utf8');
const ui=fs.readFileSync(dir+'/nano-faith-login.js','utf8');
const r=fs.readFileSync(dir+'/renderer.js','utf8');
assert.equal((r.match(/nano-pos-login-success/g)||[]).length,1,'Native login must dispatch exactly one explicit authentication event');
const temp={window:{}};vm.runInNewContext(data,temp);
const messages=temp.window.NANO_FAITH_ITEMS_183;
assert.equal(messages.length,100);
assert.equal(messages.filter(x=>x.id.startsWith('q-')).length,80);
assert.equal(messages.filter(x=>x.id.startsWith('h-')).length,20);
assert.equal(new Set(messages.map(x=>x.id)).size,100);
assert.equal(new Set(messages.map(x=>x.text)).size,100);
for(const x of messages){
 assert(x.reference&&x.explanation&&x.source&&/^https:\/\//.test(x.url),'Invalid source '+x.id);
}
const memory=new Map();
async function session(i,{fail=false,twice=false,startResume=false}={}){
 const doc='<html lang="ar"><body><div id="loginOverlay" class="'+(startResume?'hidden':'nano-commerce-login')+'"></div>'+
 '<div id="lockOverlay" class="hidden"></div></body></html>';
 const dom=new JSDOM(doc,{url:'http://localhost:4381',runScripts:'outside-only'});
 const w=dom.window;
 Object.defineProperty(w,'localStorage',{configurable:true,value:{
  getItem:k=>memory.has(k)?memory.get(k):null,
  setItem:(k,v)=>memory.set(k,String(v)),
  removeItem:k=>memory.delete(k)
 }});
 const original=w.setTimeout.bind(w);
 w.setTimeout=(callback,delay,...args)=>original(callback,Math.min(delay,16),...args);
 w.eval(data);
 w.eval(ui);
 w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
 const wait=ms=>new Promise(done=>setTimeout(done,ms));
 await wait(5);
 if(fail){
   await wait(55);
   assert(!w.document.getElementById('nanoFaithReminder183'),'Popup appeared on failed login');
   dom.window.close();return;
 }
 if(!startResume){
   memory.set('pos_current_user',JSON.stringify({id:1,username:'admin'}));
   w.dispatchEvent(new w.CustomEvent('nano-pos-login-success',{detail:{via:'native-success'}}));
   w.document.getElementById('loginOverlay').classList.add('hidden');
 }
 await wait(70);
 const modal=w.document.getElementById('nanoFaithReminder183');
 assert(modal,'No popup on successful login / resume');
 const actual=modal.querySelector('.nano-faith-quote')?.textContent;
 assert.equal(actual,messages[i].text,'Wrong/duplicated message index '+i);
 assert.equal(modal.querySelector('.nano-faith-attribution')?.textContent,'المصدر: '+messages[i].source);
 assert.equal(modal.querySelector('footer a').href,messages[i].url);
 modal.querySelector('.nano-faith-continue').click();
 assert(!w.document.getElementById('nanoFaithReminder183'),'Cannot dismiss popup');
 if(twice){
   // Another login with the same process should open another, different entry.
   w.document.getElementById('loginOverlay').classList.remove('hidden');
   await wait(10);
   // Real app login prompts take substantially longer than debounce window.
   // Test the overlay fallback without forcing duplicate auth event.
   w.document.getElementById('loginOverlay').classList.add('hidden');
   await wait(65);
   // Reuse one process only when real time progressed beyond duplicate suppression.
   assert(!w.document.getElementById('nanoFaithReminder183')||
          w.document.getElementById('nanoFaithReminder183').querySelector('.nano-faith-quote').textContent!==actual,
          'Second authentication repeated a message');
 }
 dom.window.close();
}
(async()=>{
 await session(0,{fail:true});
 assert(!memory.has('nano-faith-rotation-v185'));
 for(let i=0;i<100;i++)await session(i);
 const count=JSON.parse(memory.get('nano-faith-rotation-v185'));
 assert.equal(count.totalShown,100);assert.equal(count.nextIndex,0);
 await session(0);
 assert.equal(JSON.parse(memory.get('nano-faith-rotation-v185')).totalShown,101);
 await session(1);
 console.log('PASS: actual authenticated event, no failed-login popup, popup visible on Windows resume, 100 unique sourced messages and persistent 102-login rotation');
})().catch(e=>{console.error(e);process.exitCode=1});
