'use strict';
const fs=require('fs'),path=require('path');
const root=process.argv[2];if(!root)throw Error('root missing');
const css=path.join(root,'nano-price-display.css');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const pkgPath=path.join(root,'package.json');
const pkg=JSON.parse(fs.readFileSync(pkgPath,'utf8'));
if(pkg.version!=='1.0.72')throw Error('wrong base version '+pkg.version);
if(!html.includes('href="nano-price-display.css"')||!html.includes('src="nano-price-display.js"'))throw Error('digital display missing');
if(!fs.existsSync(css))throw Error('original display stylesheet missing');
fs.writeFileSync(css,fs.readFileSync(path.join(__dirname,'nano-price-display.css'),'utf8'));
pkg.version='1.0.73';fs.writeFileSync(pkgPath,JSON.stringify(pkg,null,2)+'\n');
const lockPath=path.join(root,'package-lock.json');
if(fs.existsSync(lockPath)){const lock=JSON.parse(fs.readFileSync(lockPath,'utf8'));lock.version='1.0.73';if(lock.packages?.[''])lock.packages[''].version='1.0.73';fs.writeFileSync(lockPath,JSON.stringify(lock,null,2)+'\n')}
console.log('Desktop POS display responsive layout installed.');
