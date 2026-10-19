/* Apply selected local backup/export folder to verified NANO POS 1.0.80. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Missing extracted v1.0.80 ASAR');
const read=n=>fs.readFileSync(path.join(root,n),'utf8'),write=(n,s)=>fs.writeFileSync(path.join(root,n),s,'utf8');
function once(s,a,b,what){const count=s.split(a).length-1;if(count!==1)throw Error(what+': expected 1, found '+count);return s.replace(a,b);}
function many(s,a,b,expected,what){const count=s.split(a).length-1;if(count!==expected)throw Error(what+': expected '+expected+', found '+count);return s.split(a).join(b);}
let main=read('electron-main.cjs');
main=once(main,
 "const { initShopLogo } = require('./shop-logo-window.cjs');",
 "const { initShopLogo } = require('./shop-logo-window.cjs');\nconst { registerLocalStorage } = require('./nano-local-folder.cjs');",
 'native settings import');
main=once(main,
 "registerEmbeddedApkIpc({ ipcMain, dialog, app, getWindow: () => mainWindow });",
 "registerEmbeddedApkIpc({ ipcMain, dialog, app, getWindow: () => mainWindow });\nconst nanoLocalStorage = registerLocalStorage({ ipcMain, dialog, app, getWindow: () => mainWindow });",
 'native settings registration');
// Route automatic/local backup flows through selected destination, but leave MEGA
// integration tied to its existing internal temporary files to avoid breaking cloud.
main=many(main,
 "const backupDir = path.join(app.getPath('userData'), 'backups');",
 "const backupDir = nanoLocalStorage.backupsDir();",
 2,'manual and shutdown backup destinations');
main=once(main,
 "const directory = path.join(app.getPath('userData'), 'backups');",
 "const directory = nanoLocalStorage.backupsDir();",
 'hourly backup destination');
// Export and PDF native dialogs start in the preferred folder; user can override on each save.
main=once(main,
 "defaultPath: app.getPath('documents'), properties: ['openDirectory', 'createDirectory']",
 "defaultPath: nanoLocalStorage.exportDir(), properties: ['openDirectory', 'createDirectory']",
 'explicit select folder default');
main=once(main,
 "defaultPath: path.join(app.getPath('documents'), safeName) };",
 "defaultPath: path.join(nanoLocalStorage.exportDir(), safeName) };",
 'save dialog destination');
main=once(main,
 "defaultPath: path.join(app.getPath('documents'), safeName.toLowerCase().endsWith('.pdf') ? safeName : \`\${safeName}.pdf\`),",
 "defaultPath: path.join(nanoLocalStorage.exportDir(), safeName.toLowerCase().endsWith('.pdf') ? safeName : \`\${safeName}.pdf\`),",
 'PDF dialog destination');
write('electron-main.cjs',main);
let preload=read('electron-native-preload.cjs');
preload=once(preload,
 "  saveFile: payload => ipcRenderer.invoke('nano-native-save-file', payload),",
 "  saveFile: payload => ipcRenderer.invoke('nano-native-save-file', payload),\n  getLocalFolder: () => ipcRenderer.invoke('nano-local-folder-get'),\n  chooseLocalFolder: () => ipcRenderer.invoke('nano-local-folder-choose'),\n  resetLocalFolder: () => ipcRenderer.invoke('nano-local-folder-reset'),",
 'restricted preload API');
write('electron-native-preload.cjs',preload);
let html=read('index.html');
for(const id of ['settingsSection','settingsTab-import-export','settingsTab-general','productsSection','salesSection'])
 if(!html.includes('id="'+id+'"'))throw Error('Missing original NANO section '+id);
if(html.includes('nano-local-folder-ui.js'))throw Error('Folder picker already exists');
html=once(html,'</head>','<link rel="stylesheet" href="nano-local-folder.css" />\n</head>','settings CSS link');
html=once(html,'</body>','<script defer src="nano-local-folder-ui.js"></script>\n</body>','settings JS link');
write('index.html',html);
for(const name of ['nano-local-folder.cjs','nano-local-folder-ui.js','nano-local-folder.css'])
 fs.copyFileSync(path.join(__dirname,name),path.join(root,name));
// The restock CSV export honors the selected folder while preserving browser fallback.
let restock=read('nano-inventory-shortages.js');
restock=once(restock,
 "function downloadCSV(){\n if(!data.length)return;\n const blob=new Blob([csvText()],{type:'text/csv;charset=utf-8'});",
 "async function downloadCSV(){\n if(!data.length)return;\n if(typeof root.nanoNative?.saveFile==='function'){\n   try {\n     const saved=await root.nanoNative.saveFile({defaultFileName:'NANO-POS-LOW-STOCK-'+new Date().toISOString().slice(0,10)+'.csv',content:csvText(),mimeType:'text/csv;charset=utf-8',title:L().csv,selectFolder:false});\n     if(saved?.success||saved?.canceled)return;\n     notify(saved?.error||L().sendError,'warning');return;\n   } catch(e){notify(L().sendError+' '+e.message,'warning');return;}\n }\n const blob=new Blob([csvText()],{type:'text/csv;charset=utf-8'});",
 'inventory report CSV save location');
write('nano-inventory-shortages.js',restock);
const pkg=JSON.parse(read('package.json'));
if(pkg.version!=='1.0.80')throw Error('Unexpected source version: '+pkg.version);
pkg.version='1.0.81';write('package.json',JSON.stringify(pkg,null,2)+'\n');
if(fs.existsSync(path.join(root,'package-lock.json'))){
 const lock=JSON.parse(read('package-lock.json'));lock.version='1.0.81';
 if(lock.packages?.[''])lock.packages[''].version='1.0.81';
 write('package-lock.json',JSON.stringify(lock,null,2)+'\n');
}
console.log('Local storage setting installed; original store, license, sale and cloud logic untouched');
