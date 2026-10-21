'use strict';
// NANO POS 1.0.96: shared durable RPC idempotency ledger.
// An ambiguous in-flight operation is never replayed automatically.
const crypto=require('node:crypto'),fs=require('node:fs'),path=require('node:path');
const shared=new Map();
const readonly=/^(get-|check-|login-user$|next-doc-number$|discover-|export-|download-|open-external-link$|open-youtube-video$|scale:(status|sniff|probe)|cloud-sync:(status|get-)|get-relay-status$)/i;
const isMutation=c=>!readonly.test(String(c||''));
function failure(code,statusCode=409){const e=new Error(code);e.code=code;e.statusCode=statusCode;return e;}
function stable(v){if(Array.isArray(v))return v.map(stable);if(v&&typeof v==='object'){const o={};for(const k of Object.keys(v).sort())o[k]=stable(v[k]);return o;}return v;}
function createOperationGuard({storeFile=null,ttlMs=7*24*60*60*1000,maxEntries=20000}={}){
  const records=new Map(),inflight=new Map();let tail=Promise.resolve();
  const location=storeFile?path.resolve(storeFile):null;
  if(location&&fs.existsSync(location)){
    const stored=JSON.parse(fs.readFileSync(location,'utf8'));
    if(stored?.schema!==1||!Array.isArray(stored.records))throw failure('operation_ledger_invalid',503);
    for(const [key,entry] of stored.records){
      if(typeof key!=='string'||!entry||!['pending','committed','uncertain'].includes(entry.state)||!/^[a-f0-9]{64}$/.test(String(entry.hash)))
        throw failure('operation_ledger_invalid',503);
      records.set(key,entry);
    }
  }
  function prune(){
    const now=Date.now();
    for(const [key,item] of records)
      if(item.state==='committed'&&!inflight.has(key)&&now-item.at>ttlMs)records.delete(key);
    if(records.size>maxEntries)
      for(const [key,item] of records){if(records.size<=maxEntries)break;if(item.state==='committed'&&!inflight.has(key))records.delete(key);}
    // Unknown outcomes remain in the ledger for manual reconciliation.
  }
  function persist(){
    if(!location)return;
    fs.mkdirSync(path.dirname(location),{recursive:true});
    const temp=location+'.'+process.pid+'.tmp';
    try{
      fs.writeFileSync(temp,JSON.stringify({schema:1,records:[...records.entries()]}),{encoding:'utf8',mode:0o600});
      fs.renameSync(temp,location);
    }catch(error){
      try{fs.unlinkSync(temp);}catch{}
      throw failure('operation_ledger_write_failed',503);
    }
  }
  function serialized(fn){const result=tail.then(fn);tail=result.then(()=>{},()=>{});return result;}
  function call({deviceId,operationId,channel,args,dispatch,requireOperationId=false}){
    if(typeof dispatch!=='function')throw failure('invalid_dispatch',400);
    if(typeof channel!=='string'||!channel.trim())throw failure('invalid_channel',400);
    const id=String(operationId||'').trim();
    if(id&&!/^[a-zA-Z0-9_-]{8,128}$/.test(id))throw failure('invalid_operation_id',400);
    if(!Array.isArray(args))throw failure('invalid_operation_args',400);
    const mutation=isMutation(channel);
    if(mutation&&!id&&requireOperationId)throw failure('operation_id_required',400);
    if(!mutation||!id)return serialized(()=>dispatch(channel,args));
    const device=String(deviceId||'').trim();
    if(!device)throw failure('invalid_device',400);
    const key=JSON.stringify([device,id]);
    const hash=crypto.createHash('sha256').update(JSON.stringify(stable([channel,args]))).digest('hex');
    const previous=records.get(key);
    if(previous){
      if(previous.hash!==hash)throw failure('operation_id_reused_with_different_payload');
      if(inflight.has(key))return inflight.get(key);
      if(previous.state==='committed')return Promise.resolve(previous.result);
      throw failure('operation_state_uncertain');
    }
    const entry={state:'pending',hash,at:Date.now()};
    records.set(key,entry);
    try{prune();persist();}catch(e){records.delete(key);throw e;}
    const promise=serialized(async()=>{
      try{
        const output=await dispatch(channel,args);
        entry.result=output===undefined?null:JSON.parse(JSON.stringify(output));
        entry.state='committed';entry.at=Date.now();persist();
        return output;
      }catch(error){
        entry.state='uncertain';delete entry.result;
        try{persist();}catch{}
        throw failure('operation_state_uncertain');
      }
    });
    inflight.set(key,promise);
    promise.then(()=>inflight.delete(key),()=>inflight.delete(key));
    return promise;
  }
  return {call,size:()=>records.size,isMutation};
}
function getSharedOperationGuard({storeFile,...options}={}){
  if(!storeFile)throw failure('operation_store_required',500);
  const key=path.resolve(storeFile);
  if(!shared.has(key))shared.set(key,createOperationGuard({storeFile:key,...options}));
  return shared.get(key);
}
module.exports={createOperationGuard,getSharedOperationGuard,isMutation};
