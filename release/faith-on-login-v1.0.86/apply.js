'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Extracted NANO POS v1.0.85 source directory required');
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
const write=(f,s)=>fs.writeFileSync(path.join(root,f),s,'utf8');
const pkg=JSON.parse(read('package.json'));
if(pkg.version!=='1.0.85')throw Error('Unexpected base version '+pkg.version);
const renderer=read('renderer.js'),html=read('index.html');
if((renderer.match(/nano-pos-login-success/g)||[]).length!==1||
   !renderer.includes("detail:{via:'native-success'}"))
 throw Error('Authentication success event was not wired in original application');
for(const s of ['id="loginOverlay"','id="lockOverlay"','faith-items.js','nano-faith-login.js','nano-faith-login.css'])
 if(!html.includes(s))throw Error('Login window or faith UI missing '+s);
fs.copyFileSync(path.join(__dirname,'nano-faith-login.js'),path.join(root,'nano-faith-login.js'));
const changed=read('nano-faith-login.js');
if(!changed.includes("via!=='native-success'")||changed.includes("startup-resume")||changed.includes("observeOverlay("))
 throw Error('Faith modal trigger is not strictly successful login');
pkg.version='1.0.86';write('package.json',JSON.stringify(pkg,null,2)+'\n');
if(fs.existsSync(path.join(root,'package-lock.json'))){
 const lock=JSON.parse(read('package-lock.json'));
 lock.version='1.0.86';if(lock.packages?.[''])lock.packages[''].version='1.0.86';
 write('package-lock.json',JSON.stringify(lock,null,2)+'\n');
}
console.log('v1.0.86: faith popup shown after successful login only; unchanged 100 messages and business logic');
