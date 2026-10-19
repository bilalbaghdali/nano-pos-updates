'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {JSDOM}=require('/tmp/ui-test/node_modules/jsdom');
const extracted=process.argv[2];if(!extracted)throw Error('Must provide extracted app folder');
async function verifyNative(){
 const base=fs.mkdtempSync(path.join(os.tmpdir(),'nano-local-folder-test-'));
 const config=path.join(base,'data'),documents=path.join(base,'docs'),selected=path.join(base,'chosen');
 fs.mkdirSync(config,{recursive:true});fs.mkdirSync(documents);fs.mkdirSync(selected);
 const handles=new Map();const window={webContents:{},isDestroyed:()=>false};
 let dialogResult={canceled:false,filePaths:[selected]};
 const ipcMain={handle:(name,cb)=>{assert(!handles.has(name),'Duplicate IPC '+name);handles.set(name,cb);}};
 const dialog={showOpenDialog:async(win,opts)=>{assert.equal(win,window);assert(opts.properties.includes('openDirectory'));assert(opts.properties.includes('createDirectory'));return dialogResult;}};
 const app={getPath:key=>({userData:config,documents})[key]};
 const service=require(path.join(extracted,'nano-local-folder.cjs')).registerLocalStorage({
   ipcMain,dialog,app,getWindow:()=>window
 });
 const event={sender:window.webContents};
 const rpc=(name,...args)=>{assert(handles.has(name),'Missing handler '+name);return handles.get(name)(event,...args);};
 const initial=await rpc('nano-local-folder-get');
 assert(initial.isDefault);assert.equal(initial.backupFolder,path.join(config,'backups'));
 assert.equal(initial.exportFolder,documents);
 assert.throws(()=>handles.get('nano-local-folder-get')({sender:{}}),/desktop_only/);
 const chosen=await rpc('nano-local-folder-choose');
 assert(chosen.success);assert.equal(chosen.configuredFolder,selected);
 assert.equal(chosen.backupFolder,path.join(selected,'NANO-POS-Backups'));
 assert.equal(service.exportDir(),selected);
 fs.writeFileSync(path.join(service.backupsDir(),'test-backup.json'),'{"sale":"safe"}');
 const reopened=await rpc('nano-local-folder-get');assert.equal(reopened.configuredFolder,selected);
 dialogResult={canceled:true};
 const canceled=await rpc('nano-local-folder-choose');assert(canceled.canceled);
 assert.equal((await rpc('nano-local-folder-get')).configuredFolder,selected,'Cancel unexpectedly changed configuration');
 fs.renameSync(selected,selected+'-disconnected');
 const fallback=await rpc('nano-local-folder-get');
 assert(fallback.fallbackUsed,'Unavailable drive did not trigger fallback');
 assert.equal(fallback.backupFolder,path.join(config,'backups'));
 assert.equal(fallback.exportFolder,documents);
 const reset=await rpc('nano-local-folder-reset');
 assert(reset.success&&reset.isDefault);
 assert.equal(service.backupsDir(),path.join(config,'backups'));
 assert(fs.existsSync(path.join(selected+'-disconnected','NANO-POS-Backups','test-backup.json')),'Old backups were modified');
 fs.rmSync(base,{recursive:true,force:true});
 console.log('PASS native folder picker, persistence, canceled selection, disconnection fallback, reset, trusted IPC');
}
async function verifyUI(){
 const html='<html lang="ar"><head></head><body><section id="settingsTab-import-export"><div id="originalDataTools"><button>Export data</button></div></section></body></html>';
 const dom=new JSDOM(html,{url:'http://localhost/',runScripts:'outside-only'});
 const window=dom.window,document=window.document;let chosen=0,reset=0;
 window.nanoNative={
 getLocalFolder:async()=>({success:true,isDefault:!chosen,configuredFolder:chosen?'C:\\\\POS-Store':'',backupFolder:chosen?'C:\\\\POS-Store\\\\NANO-POS-Backups':'C:\\\\AppData\\\\backups',exportFolder:chosen?'C:\\\\POS-Store':'C:\\\\Documents'}),
 chooseLocalFolder:async()=>{chosen++;return {success:true}},
 resetLocalFolder:async()=>{chosen=0;reset++;return {success:true}}
 };
 window.eval(fs.readFileSync(path.join(extracted,'nano-local-folder-ui.js'),'utf8'));
 document.dispatchEvent(new window.Event('DOMContentLoaded'));
 await new Promise(resolve=>setTimeout(resolve,30));
 const card=document.getElementById('nanoLocalFolderCard');
 assert(card,'Missing settings panel');
 assert.equal(document.querySelectorAll('#nanoLocalFolderCard').length,1);
 assert(document.getElementById('originalDataTools'),'Original settings panel removed');
 assert(document.getElementById('nanoLocalFolderSelected').textContent.length>0);
 document.getElementById('nanoLocalFolderChoose').click();
 await new Promise(resolve=>setTimeout(resolve,35));
 assert.equal(chosen,1);
 assert(document.getElementById('nanoLocalFolderSelected').textContent.includes('POS-Store'));
 document.getElementById('nanoLocalFolderReset').click();
 await new Promise(resolve=>setTimeout(resolve,35));
 assert.equal(reset,1);
 assert(document.getElementById('nanoLocalFolderSelected').textContent.includes('الافتراضي'));
 console.log('PASS settings UI mounts once, chooser persists, reset and preserves original tab');
}
(async()=>{await verifyNative();await verifyUI();})().catch(e=>{console.error(e);process.exitCode=1;});
