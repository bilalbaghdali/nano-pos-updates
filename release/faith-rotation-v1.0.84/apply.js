'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Missing extracted v1.0.83 app.asar directory');
const get=file=>fs.readFileSync(path.join(root,file),'utf8');
const set=(file,data)=>fs.writeFileSync(path.join(root,file),data,'utf8');
const pkg=JSON.parse(get('package.json'));
if(pkg.version!=='1.0.83')throw Error('Wrong published baseline '+pkg.version);
const html=get('index.html');
for(const str of ['faith-items.js','nano-faith-login.js','nano-faith-login.css','loginOverlay','productAnalyticsModal'])
 if(!html.includes(str))throw Error('Original reminder or UI is missing '+str);
const existing=get('nano-faith-login.js');
if(!existing.includes("sessionStorage.getItem('nano-faith-index')"))throw Error('Published reminder changed unexpectedly');
for(const name of ['faith-items.js','nano-faith-login.js']){
 fs.copyFileSync(path.join(__dirname,name),path.join(root,name));
}
const revised=get('nano-faith-login.js');
if(!revised.includes("localStorage.setItem(STORAGE_KEY")||!revised.includes("nano-faith-rotation-v184"))
 throw Error('Persistent rotation not installed');
pkg.version='1.0.84';set('package.json',JSON.stringify(pkg,null,2)+'\n');
if(fs.existsSync(path.join(root,'package-lock.json'))){
 const lock=JSON.parse(get('package-lock.json'));lock.version='1.0.84';
 if(lock.packages&&lock.packages[''])lock.packages[''].version='1.0.84';
 set('package-lock.json',JSON.stringify(lock,null,2)+'\n');
}
console.log('Faith reminder rotates across app restarts without changing business data, sales, POS or UI');
