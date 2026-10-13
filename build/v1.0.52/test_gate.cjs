'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
const builder = fs.readFileSync(__dirname+'/build_v152.py','utf8');
const match = builder.match(/\nNEW="""([\s\S]*?)"""\n/);
assert.ok(match,'Cannot locate actual patched success body');
const code=match[1];
function fixture(effect) {
  const calls=[]; const overlay={classList:{add(...c){calls.push('hide-login:'+c.join(','))},remove(...c){calls.push('remove-login:'+c.join(','))}}};
  const password={value:'secret'};
  const document={getElementById(id){if(id==='loginOverlay')return overlay;if(id==='loginPassword')return password;throw Error('Unexpected '+id)}};
  const table={0x2d3:'loginOverlay',0xe2a:'loginPassword',0x2c5:'setItem',0xfe9:'stringify',0xe5b:'add',0x43b:'classList',0x89e:'hidden'};
  const decode=x=>table[x] || x;
  const localStorage={setItem(k,v){calls.push('persist:'+k+':'+v)}};
  const window={NANOLoginSuccessEffect:effect,nanoPlayLoginBlessing(){calls.push('blessing')}};
  const initUserSession=()=>calls.push('open-home');
  const setTimeout=(fn,ms)=>{if(ms===500)calls.push('schedule-login-hide');};
  const f=new AsyncFunction('_0x586903','_0x4e9dc7','window','document','localStorage','setTimeout','initUserSession','JSON','console',code);
  const run=()=>f({user:{id:7,name:'valid'}},decode,window,document,localStorage,setTimeout,initUserSession,JSON,console);
  return {calls,run,password};
}
async function test(){
 let release;
 const gate=fixture({play(){gate.calls.push('animation-start');return new Promise(resolve=>{release=()=>{gate.calls.push('animation-complete');resolve()}})}});
 const attempt=gate.run();
 assert.deepEqual(gate.calls,['animation-start'],'No session commit, home view, or login hiding before animation finishes');
 assert.equal(gate.password.value,'secret','Do not mutate login before animation');
 release();await attempt;
 assert.ok(gate.calls.indexOf('animation-complete')<gate.calls.findIndex(x=>x.startsWith('persist:')));
 assert.ok(gate.calls.indexOf('animation-complete')<gate.calls.findIndex(x=>x.startsWith('hide-login:')));
 assert.ok(gate.calls.indexOf('animation-complete')<gate.calls.indexOf('open-home'));
 assert.equal(gate.password.value,'');
 console.log('PASS: success may open Home only after complete animation');
 const absent=fixture(undefined);
 await assert.rejects(absent.run(),/تأثير تأكيد الدخول غير متاح/);
 assert.deepEqual(absent.calls,[]);
 console.log('PASS: absent animation fails closed with login screen still visible');
 const rejected=fixture({play(){return Promise.reject(new Error('animation failed'))}});
 await assert.rejects(rejected.run(),/animation failed/);
 assert.deepEqual(rejected.calls,[]);
 console.log('PASS: failed animation cannot bypass login screen');
}
test().catch(e=>{console.error(e);process.exitCode=1});