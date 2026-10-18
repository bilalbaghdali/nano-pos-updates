'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Expected extracted app.asar directory');
const read=name=>fs.readFileSync(path.join(root,name),'utf8');
const write=(name,value)=>fs.writeFileSync(path.join(root,name),value,'utf8');
function replaceOnce(source,oldText,newText,part){if(source.split(oldText).length!==2)throw Error('Expected one '+part);return source.replace(oldText,newText);}
let main=read('electron-main.cjs');
main=replaceOnce(main,"const { initShopLogo } = require('./shop-logo-window.cjs');","const { initShopLogo } = require('./shop-logo-window.cjs');\nconst { launchSupportTool } = require('./support-launcher.cjs');",'support launcher import');
main=replaceOnce(main,"ipcMain.handle('nano-trial-status', () => trialState({ dataDir: stableTrialDir() }));","ipcMain.handle('nano-trial-status', () => trialState({ dataDir: stableTrialDir() }));\nipcMain.handle('nano-support-launch-tool', (_event, toolId) => launchSupportTool(toolId));",'native launcher IPC');
write('electron-main.cjs',main);
let preload=read('electron-native-preload.cjs');
preload=replaceOnce(preload,"  openExternal: url => ipcRenderer.invoke('nano-open-external', url),","  openExternal: url => ipcRenderer.invoke('nano-open-external', url),\n  launchSupportTool: id => ipcRenderer.invoke('nano-support-launch-tool', id),",'restricted renderer API');
write('electron-native-preload.cjs',preload);
let html=read('index.html');
html=replaceOnce(html,'<script src="support-center.js"></script>','<script src="support-center.js"></script>\n<script src="support-buttons.js"></script>','support UI injection');
write('index.html',html);
for(const name of ['support-launcher.cjs','support-buttons.js']){
 const from=path.join(__dirname,name);
 if(!fs.existsSync(from))throw Error('Missing '+from);
 fs.copyFileSync(from,path.join(root,name));
}
const packageJson=JSON.parse(read('package.json'));
if(packageJson.version!=='1.0.73')throw Error('Wrong base version: '+packageJson.version);
packageJson.version='1.0.74';write('package.json',JSON.stringify(packageJson,null,2)+'\n');
const lockPath=path.join(root,'package-lock.json');
if(fs.existsSync(lockPath)){const lock=JSON.parse(read('package-lock.json'));lock.version='1.0.74';if(lock.packages?.[''])lock.packages[''].version='1.0.74';write('package-lock.json',JSON.stringify(lock,null,2)+'\n');}
console.log('Support launch buttons ready in v1.0.74');
