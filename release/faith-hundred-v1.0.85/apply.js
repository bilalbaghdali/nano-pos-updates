'use strict';
const fs=require('node:fs'),path=require('node:path');
const folder=process.argv[2];
if(!folder)throw Error('Expected extracted NANO POS v1.0.84 application');
const read=n=>fs.readFileSync(path.join(folder,n),'utf8');
const write=(n,s)=>fs.writeFileSync(path.join(folder,n),s,'utf8');
const pkg=JSON.parse(read('package.json'));
if(pkg.version!=='1.0.84')throw Error('Wrong source version '+pkg.version);
const html=read('index.html');
for(const marker of ['id="loginOverlay"','id="lockOverlay"','faith-items.js','nano-faith-login.js','nano-faith-login.css'])
 if(!html.includes(marker))throw Error('Existing login/reminder dependency missing '+marker);
let renderer=read('renderer.js');
const marker="initUserSession(),setTimeout(()=>window.nanoPlayLoginBlessing?.(),120)";
if(renderer.split(marker).length!==2)throw Error('Expected one verified successful-login path, found '+(renderer.split(marker).length-1));
// Tie reminder to successful authentication, rather than a CSS overlay transition.
// This branch runs only after loginUser returns success and login animation completes.
renderer=renderer.replace(marker,
 "initUserSession(),window.dispatchEvent(new CustomEvent('nano-pos-login-success',{detail:{via:'native-success'}})),setTimeout(()=>window.nanoPlayLoginBlessing?.(),120)");
write('renderer.js',renderer);
for(const name of ['nano-faith-login.js','faith-items.js'])
 fs.copyFileSync(path.join(__dirname,name),path.join(folder,name));
const texts=read('faith-items.js');
if(!texts.includes('NANO_FAITH_ITEMS_183'))throw Error('100 reminders missing');
const popup=read('nano-faith-login.js');
if(!popup.includes("addEventListener('nano-pos-login-success'")||
   !popup.includes('items.length!==100'))throw Error('Direct login event and validation missing');
pkg.version='1.0.85';write('package.json',JSON.stringify(pkg,null,2)+'\n');
if(fs.existsSync(path.join(folder,'package-lock.json'))){
 const lock=JSON.parse(read('package-lock.json'));lock.version='1.0.85';
 if(lock.packages?.[''])lock.packages[''].version='1.0.85';
 write('package-lock.json',JSON.stringify(lock,null,2)+'\n');
}
console.log('v1.0.85: explicit login success triggers visible 100-message Quran/Sahih rotation');
