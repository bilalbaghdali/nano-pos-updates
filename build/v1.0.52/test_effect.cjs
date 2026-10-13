const assert = require('node:assert/strict');
const fs=require('fs');const vm=require('vm');
const source=fs.readFileSync(__dirname+'/nano-login-success-effect.js','utf8');
function makeElement(tag='div') {
 const n={tagName:tag.toUpperCase(),innerHTML:'',removed:false,attrs:{},children:{},style:{setProperty(k,v,p){this[k]=v}},classList:{add(){}}};
 n.setAttribute=(k,v)=>n.attrs[k]=v;
 n.querySelector=(selector)=>{
   if(!n.children[selector]) n.children[selector]=makeElement(selector);
   return n.children[selector];
 };
 n.remove=()=>{n.removed=true;};
 return n;
}
async function test() {
 let now=0;let nextId=1;let tasks=[];let effects=[];
 const body={items:[],appendChild(e){this.items.push(e);e.attached=true;}};
 const doc={body,documentElement:{lang:'ar'},createElement:makeElement};
 const schedule=(fn,delay=0)=>{const id=nextId++;tasks.push({id,time:now+delay,fn});return id};
 const clear=id=>{tasks=tasks.filter(x=>x.id!==id)};
 const env={window:{matchMedia:()=>({matches:false}),addEventListener(){}},document:doc,
  performance:{now:()=>now},setTimeout:schedule,clearTimeout:clear,
  requestAnimationFrame:f=>schedule(()=>f(now),16),cancelAnimationFrame:clear,
  console};
 env.window.document=doc;
 vm.runInNewContext(source,env,{filename:'effect.js'});
 // Invalid credentials: the caller must not invoke the effect.
 const invalid={success:false};
 if(invalid.success) await env.window.NANOLoginSuccessEffect.play();
 assert.equal(body.items.length,0,'bad login must not animate');
 const result=env.window.NANOLoginSuccessEffect.play();
 assert.equal(body.items.length,1);
 const veil=body.items[0];
 assert.equal(veil.id,'nano-auth-success-veil');
 assert.equal(veil.style['z-index'],'2147483647');
 assert.equal(veil.children['.nano-auth-card'].attrs['data-stage'],undefined);
 // DOM dataset isn't modeled by query stub; stage change writes dataset.
 veil.children['.nano-auth-card'].dataset={};
 for(let iter=0;iter<400 && tasks.length;iter++) {
   tasks.sort((a,b)=>a.time-b.time);const item=tasks.shift();now=item.time;item.fn();
 }
 await result;
 assert.equal(veil.children['.nano-auth-card'].dataset.stage,'granted');
 assert.equal(veil.children['.nano-auth-title'].textContent,'تم تسجيل الدخول بنجاح');
 assert.ok(veil.removed,'veil removed after completion');
 console.log('PASS: denied credentials no overlay; valid credentials progress and green confirmation; overlay cleaned');
}
test().catch(e=>{console.error(e);process.exit(1)});