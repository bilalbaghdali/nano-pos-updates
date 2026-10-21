'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const crypto=require('node:crypto');
const {createOperationGuard,getSharedOperationGuard}=require('./sync-operation-guard.cjs');
const {createMobileSyncServer}=require('./mobile-sync-server.cjs');
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function error(fn,code){try{await fn();assert.fail('expected '+code);}catch(e){assert.equal(e.code,code);}}
const directory=fs.mkdtempSync(path.join(os.tmpdir(),'nano-sync-test-'));
async function ledger(){
 const file=path.join(directory,'ledger.json'),guard=createOperationGuard({storeFile:file});
 let count=0;
 const dispatch=async()=>{await wait(20);return {id:++count};};
 const item={deviceId:'mobile:a',operationId:'mob-operation-1001',channel:'process-sale',args:[{product_id:4}],dispatch};
 const [a,b]=await Promise.all([guard.call(item),guard.call(item)]);
 assert.deepEqual(a,b);assert.equal(count,1);
 assert.deepEqual(await createOperationGuard({storeFile:file}).call(item),a);
 assert.equal(count,1,'successful operation must never replay after restart');
 await error(()=>guard.call({...item,args:[{product_id:5}]}),'operation_id_reused_with_different_payload');
 assert.deepEqual(await guard.call({...item,deviceId:'mobile:b'}),{id:2});
 const sharedFile=path.join(directory,'shared.json');
 const phone=getSharedOperationGuard({storeFile:sharedFile});
 const computer=getSharedOperationGuard({storeFile:sharedFile});
 assert.strictEqual(phone,computer);
 let active=0,max=0;
 const exec=async()=>{active++;max=Math.max(max,active);await wait(20);active--;return true;};
 await Promise.all([
   phone.call({deviceId:'mobile:a',operationId:'mob-work-00001',channel:'process-sale',args:[],dispatch:exec}),
   computer.call({deviceId:'pc:cashier',operationId:'pc-work-000002',channel:'save-purchase',args:[],dispatch:exec}),
   phone.call({deviceId:'mobile:b',operationId:'mob-work-00003',channel:'update-product',args:[],dispatch:exec})
 ]);
 assert.equal(max,1,'two phones and a PC must never mutate in parallel');
 await error(()=>phone.call({deviceId:'mobile:a',operationId:'',channel:'process-sale',args:[],dispatch:exec,requireOperationId:true}),'operation_id_required');
 const pendingFile=path.join(directory,'pending.json');
 const hash=crypto.createHash('sha256').update(JSON.stringify(['process-sale',[{id:4}]])).digest('hex');
 fs.writeFileSync(pendingFile,JSON.stringify({schema:1,records:[[JSON.stringify(['mobile:a','mob-crashed-001']),{state:'pending',hash,at:Date.now()}]]}));
 const guard2=createOperationGuard({storeFile:pendingFile});
 let invalidReplay=0;
 await error(()=>guard2.call({deviceId:'mobile:a',operationId:'mob-crashed-001',channel:'process-sale',args:[{id:4}],dispatch:async()=>invalidReplay++}),'operation_state_uncertain');
 assert.equal(invalidReplay,0);
 let failures=0;
 await error(()=>guard2.call({deviceId:'mobile:a',operationId:'mob-failed-0002',channel:'process-sale',args:[],dispatch:async()=>{failures++;throw Error('simulated timeout after write');}}),'operation_state_uncertain');
 await error(()=>guard2.call({deviceId:'mobile:a',operationId:'mob-failed-0002',channel:'process-sale',args:[],dispatch:async()=>{failures++;}}),'operation_state_uncertain');
 assert.equal(failures,1);
 console.log('PASS: cross-client ordering, in-flight reuse, collision, crash/restart and unknown state');
}
async function httpTest(){
 const userdata=path.join(directory,'userData');fs.mkdirSync(userdata,{recursive:true});
 let sales=0;
 const server=createMobileSyncServer({app:{getPath:()=>userdata},port:0,
   dispatchRpc:async channel=>{if(channel==='process-sale'){sales++;await wait(15);return {success:true,id:sales};}return []},
   dispatchBarcode:async()=>({success:true})});
 await server.start();
 const base='http://127.0.0.1:'+server.info().port;
 const send=async(p,data,headers={})=>{const res=await fetch(base+p,{method:'POST',headers:{'Content-Type':'application/json',...headers},body:JSON.stringify(data)});return {status:res.status,...await res.json()}};
 try{
   const code=server.info().pairCode;
   const [a,b]=await Promise.all([
     send('/nano-sync/pair',{code,deviceName:'Phone A'},{'X-Nano-Device':'phone-a'}),
     send('/nano-sync/pair',{code,deviceName:'Phone B'},{'X-Nano-Device':'phone-b'})
   ]);
   assert.equal(a.success,true);assert.equal(b.success,true);
   const ah={Authorization:'Bearer '+a.token,'X-Nano-Device':a.deviceId},bh={Authorization:'Bearer '+b.token,'X-Nano-Device':b.deviceId};
   const cmd={channel:'process-sale',args:[{product_id:10}],operationId:'mobile-sale-000001'};
   const [r1,r2]=await Promise.all([send('/nano-sync/call',cmd,ah),send('/nano-sync/call',cmd,ah)]);
   assert.equal(r1.success,true);assert.deepEqual(r1.result,r2.result);assert.equal(sales,1);
   const r3=await send('/nano-sync/call',cmd,bh);assert.equal(r3.success,true);assert.equal(sales,2);
   const conflict=await send('/nano-sync/call',{...cmd,args:[{product_id:11}]},ah);assert.equal(conflict.status,409);assert.equal(sales,2);
   const absent=await send('/nano-sync/call',{...cmd,operationId:''},ah);assert.equal(absent.status,400);
   const read=await send('/nano-sync/call',{channel:'get-products',args:[]},ah);assert.equal(read.success,true);
   console.log('PASS: authenticated multi-phone HTTP, replay and conflict responses');
 }finally{server.stop();}
}
(async()=>{try{await ledger();await httpTest();console.log('ALL SYNC 1.0.96 TESTS PASSED');}finally{fs.rmSync(directory,{recursive:true,force:true});}})().catch(e=>{console.error(e);process.exitCode=1});
