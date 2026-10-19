'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require('/tmp/testkit/node_modules/jsdom');
const root=process.argv[2];
if(!root)throw Error('Missing unpacked app directory');
const dataScript=fs.readFileSync(root+'/faith-items.js','utf8');
const dialogScript=fs.readFileSync(root+'/nano-faith-login.js','utf8');
const saved=new Map();
const storage={getItem:k=>saved.has(k)?saved.get(k):null,setItem:(k,v)=>{saved.set(k,String(v))},removeItem:k=>saved.delete(k)};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function loginOnce(expectedIndex,{failed=false,relog=false}={}){
 const dom=new JSDOM('<html lang="ar"><head></head><body><div id="loginOverlay" class="nano-commerce-login"></div></body></html>',
 {url:'http://localhost:8080/',runScripts:'outside-only'});
 const win=dom.window,doc=win.document;
 Object.defineProperty(win,'localStorage',{configurable:true,value:storage});
 win.eval(dataScript);win.eval(dialogScript);
 const all=win.NANO_FAITH_ITEMS_183;
 assert.equal(all.length,6,'Expected six vetted entries');
 assert(all.every((item,i)=>item.id&&item.url.startsWith('https://')&&item.explanation&&item.source),'Unattributed entry found');
 assert.equal(new Set(all.map(item=>item.id)).size,6,'Duplicate citation identity');
 doc.dispatchEvent(new win.Event('DOMContentLoaded'));
 await sleep(12);
 assert(!doc.getElementById('nanoFaithReminder183'),'Dialog shown before successful login');
 if(failed){
   doc.getElementById('loginOverlay').classList.add('nano-invalid-login');
   await sleep(30);
   assert(!doc.getElementById('nanoFaithReminder183'),'Failed login triggered dialog');
   dom.window.close();return null;
 }
 doc.getElementById('loginOverlay').classList.add('hidden');
 await sleep(420);
 let modal=doc.getElementById('nanoFaithReminder183');
 assert(modal,'No dialog after successful login');
 const label=modal.querySelector('.nano-faith-quote')?.textContent;
 const expected=all[expectedIndex];
 assert.equal(label,expected.text,'Text not rotated to expected verse/hadith');
 assert(modal.querySelector('.nano-faith-attribution').textContent.includes(expected.source),'Missing attribution');
 assert.equal(modal.querySelector('footer a').href,expected.url,'Wrong source URL');
 modal.querySelector('.nano-faith-continue').click();
 assert(!doc.getElementById('nanoFaithReminder183'),'Cannot dismiss dialog');
 if(relog){
   doc.getElementById('loginOverlay').classList.remove('hidden');
   await sleep(18);
   doc.getElementById('loginOverlay').classList.add('hidden');
   await sleep(420);
   modal=doc.getElementById('nanoFaithReminder183');
   assert(modal,'Second login in one window did not reopen dialog');
   assert.equal(modal.querySelector('.nano-faith-quote')?.textContent,all[(expectedIndex+1)%all.length].text,
     'Second login repeated content');
   modal.querySelector('.nano-faith-cross').click();
 }
 dom.window.close();
 return expected.id;
}
(async()=>{
 await loginOnce(0,{failed:true});
 assert.equal(saved.size,0,'Failed login unexpectedly persisted a consumed entry');
 const ids=[];
 for(let i=0;i<6;i++)ids.push(await loginOnce(i));
 assert.equal(new Set(ids).size,6,'Messages repeat before all six are seen');
 for(let i=0;i<6;i++)await loginOnce(i);
 const state=JSON.parse(saved.get('nano-faith-rotation-v184'));
 assert.equal(state.shownCount,12);
 assert.equal(state.nextIndex,0);
 await loginOnce(0,{relog:true});
 const nextState=JSON.parse(saved.get('nano-faith-rotation-v184'));
 assert.equal(nextState.nextIndex,2);
 console.log('PASS: no reminder before login, no failed-login display, six-message cycle, persistent rotation across restarts, second login in same window, source links and close');
})().catch(error=>{console.error(error);process.exitCode=1});
