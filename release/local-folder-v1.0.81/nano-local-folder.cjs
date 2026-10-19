'use strict';
// Native local backup/export destination. Configuration is independent of POS business data.
// Only OS-directory-picker results can create folder preference; renderer cannot pass a raw path.
const fs=require('node:fs'), path=require('node:path'),os=require('node:os');
function registerLocalStorage({ipcMain,dialog,app,getWindow}){
  const configFile=()=>path.join(app.getPath('userData'),'nano-local-folder.json');
  const legacy=()=>path.join(app.getPath('userData'),'backups');
  function defaultExports(){return app.getPath('documents');}
  function folderIsWritable(folder){
    try{
      if(!path.isAbsolute(folder)||!fs.statSync(folder).isDirectory())return false;
      const name='.nano-write-check-'+process.pid+'-'+Date.now();
      const testFile=path.join(folder,name);
      const fd=fs.openSync(testFile,'wx',0o600);
      try{fs.closeSync(fd);fs.unlinkSync(testFile);}catch{try{fs.closeSync(fd)}catch{}try{fs.unlinkSync(testFile)}catch{}}
      return true;
    }catch{return false;}
  }
  function read(){
    try{
      const config=JSON.parse(fs.readFileSync(configFile(),'utf8'));
      const folder=String(config?.folder||'');
      if(!path.isAbsolute(folder)||folder.length>1024)return null;
      return folder;
    }catch{return null;}
  }
  function write(folder){
    fs.mkdirSync(path.dirname(configFile()),{recursive:true});
    const temp=configFile()+'.tmp-'+process.pid;
    try{
      fs.writeFileSync(temp,JSON.stringify({schemaVersion:1,folder,changedAt:new Date().toISOString()},null,2)+'\n',{mode:0o600});
      fs.renameSync(temp,configFile());
    }finally{try{fs.unlinkSync(temp)}catch{}}
  }
  function selected(){return read();}
  function backupsDir(){
    const configured=read();
    if(configured){
      try{
        if(folderIsWritable(configured)){
          const chosen=path.join(configured,'NANO-POS-Backups');
          fs.mkdirSync(chosen,{recursive:true});
          if(folderIsWritable(chosen))return chosen;
        }
      }catch(e){console.warn('[NANO local folder] Preferred backup folder unavailable',e.message);}
      console.warn('[NANO local folder] Using built-in backup folder because preferred storage is unavailable');
    }
    const builtIn=legacy();
    fs.mkdirSync(builtIn,{recursive:true});
    return builtIn;
  }
  function exportDir(){
    const configured=read();
    return configured&&folderIsWritable(configured)?configured:defaultExports();
  }
  function status(){
    const configured=read();
    const available=!!configured&&folderIsWritable(configured);
    const backup=backupsDir();
    return {success:true,configuredFolder:configured||'',selectedAvailable:available,
      fallbackUsed:!!configured&&!available,backupFolder:backup,
      exportFolder:available?configured:defaultExports(),
      isDefault:!configured,
      note:configured&&!available?'selected_folder_unavailable':'ok'};
  }
  function trusted(event){
    const win=getWindow();
    if(!win||win.isDestroyed?.()||event.sender!==win.webContents)throw Error('desktop_only');
    return win;
  }
  ipcMain.handle('nano-local-folder-get',event=>{
    trusted(event);return status();
  });
  ipcMain.handle('nano-local-folder-choose',async event=>{
    const win=trusted(event);
    const prior=read();
    const options={title:'اختيار مجلد التخزين المحلي لـ NANO POS',
      defaultPath:prior&&folderIsWritable(prior)?prior:defaultExports(),
      properties:['openDirectory','createDirectory']};
    const result=await dialog.showOpenDialog(win,options);
    if(result.canceled||!result.filePaths?.length)return {success:false,canceled:true};
    const folder=String(result.filePaths[0]||'');
    if(!path.isAbsolute(folder)||!folderIsWritable(folder))return {success:false,error:'folder_not_writable'};
    // Disallow saving exports/backups directly inside the installed executable folder.
    const installed=path.resolve(path.dirname(process.execPath)).toLowerCase();
    const candidate=path.resolve(folder).toLowerCase();
    if(candidate===installed||candidate.startsWith(installed+path.sep))return {success:false,error:'folder_inside_program'};
    try{
      const backups=path.join(folder,'NANO-POS-Backups');
      fs.mkdirSync(backups,{recursive:true});
      if(!folderIsWritable(backups))return {success:false,error:'backup_folder_not_writable'};
      write(folder);
      const current=status();
      if(!current.selectedAvailable||current.configuredFolder!==folder)return {success:false,error:'selection_not_saved'};
      return current;
    }catch(e){return {success:false,error:e.message||'folder_write_failed'};}
  });
  ipcMain.handle('nano-local-folder-reset',event=>{
    trusted(event);
    try{fs.unlinkSync(configFile());}catch(e){if(e.code!=='ENOENT')return {success:false,error:e.message};}
    return status();
  });
  return {status,backupsDir,exportDir,selected,legacyDir:legacy};
}
module.exports={registerLocalStorage};
