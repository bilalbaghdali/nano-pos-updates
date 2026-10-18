'use strict';
// Allow-listed Windows support applications only; no shell commands and no automatic remote sessions.
const fs=require('node:fs');
const path=require('node:path');
const {spawn}=require('node:child_process');
const urls=Object.freeze({anydesk:'https://anydesk.com/en/downloads/windows',tailscale:'https://tailscale.com/download/windows'});
function pathsFor(id,env){
  const roots=[...new Set([env.ProgramFiles,env['ProgramFiles(x86)'],env.PROGRAMFILES,env['PROGRAMFILES(X86)'],env.LOCALAPPDATA].filter(Boolean))];
  const list=[];
  for(const root of roots){
    if(id==='anydesk'){
      list.push(path.win32.join(root,'AnyDesk','AnyDesk.exe'));
      try{for(const item of fs.readdirSync(root,{withFileTypes:true})){
        if(item.isDirectory()&&/^AnyDesk-[\w-]{1,48}$/i.test(item.name))list.push(path.win32.join(root,item.name,item.name+'.exe'));
      }}catch{}
    }else if(id==='tailscale'){
      list.push(path.win32.join(root,'Tailscale','tailscale-ipn.exe'));
      list.push(path.win32.join(root,'Tailscale IPN','tailscale-ipn.exe'));
    }
  }
  return [...new Set(list)];
}
async function launchSupportTool(tool,opts={}){
  const id=String(tool||'').toLowerCase();
  if(!Object.hasOwn(urls,id))return {ok:false,error:'unsupported_tool'};
  if((opts.platform||process.platform)!=='win32')return {ok:false,error:'windows_only',downloadUrl:urls[id]};
  const exists=opts.exists||((f)=>{try{return fs.statSync(f).isFile();}catch{return false;}});
  const executable=pathsFor(id,opts.env||process.env).find(exists);
  if(!executable)return {ok:false,error:'not_installed',downloadUrl:urls[id]};
  try{
    await new Promise((resolve,reject)=>{
      const child=(opts.spawn||spawn)(executable,[],{cwd:path.win32.dirname(executable),detached:true,stdio:'ignore',windowsHide:false,shell:false});
      child.once('error',reject);
      child.once('spawn',()=>{child.unref();resolve();});
    });
    return {ok:true,launched:true};
  }catch{return {ok:false,error:'launch_failed',downloadUrl:urls[id]};}
}
module.exports={launchSupportTool,pathsFor,urls};