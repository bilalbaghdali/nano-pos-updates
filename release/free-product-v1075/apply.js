'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];
if(!root)throw Error('Missing extracted app.asar directory');
const read=file=>fs.readFileSync(path.join(root,file),'utf8');
const write=(file,v)=>fs.writeFileSync(path.join(root,file),v,'utf8');
let html=read('index.html');
const marker='<script src="renderer.js"></script>';
if(html.split(marker).length!==2)throw Error('Unexpected renderer script order');
for(const id of ['customProductModal','customProductNameInput','customProductPriceInput','customProductCostInput']){
 if(!html.includes('id="'+id+'"'))throw Error('Missing free product modal element '+id);
}
for(const action of ['openCustomProductModal()','addCustomProductToCart()','closeCustomProductModal()']){
 if(!html.includes(action))throw Error('Missing free product action '+action);
}
if(html.includes('src="nano-free-product-fix.js"'))throw Error('Duplicate fix script');
const renderer=read('renderer.js');
for(const fn of ['function openCustomProductModal()','function addCustomProductToCart()','function updateCartUI()']){
 if(!renderer.includes(fn))throw Error('Renderer code unexpectedly changed: '+fn);
}
html=html.replace(marker,marker+'\n    <script defer src="nano-free-product-fix.js"></script>');
write('index.html',html);
fs.copyFileSync(path.join(__dirname,'free-product-fix.js'),path.join(root,'nano-free-product-fix.js'));
const packageFile='package.json',pkg=JSON.parse(read(packageFile));
if(pkg.version!=='1.0.74')throw Error('Wrong source version '+pkg.version);
pkg.version='1.0.75';
write(packageFile,JSON.stringify(pkg,null,2)+'\n');
const lockPath=path.join(root,'package-lock.json');
if(fs.existsSync(lockPath)){
 const lock=JSON.parse(read('package-lock.json'));
 lock.version='1.0.75';
 if(lock.packages?.[''])lock.packages[''].version='1.0.75';
 write('package-lock.json',JSON.stringify(lock,null,2)+'\n');
}
console.log('Free-product modal fix applied to 1.0.75; checkout logic unchanged');
