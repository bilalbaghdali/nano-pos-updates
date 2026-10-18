'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Missing extracted NANO POS v1.0.75 directory');
const read=name=>fs.readFileSync(path.join(root,name),'utf8');
const write=(name,data)=>fs.writeFileSync(path.join(root,name),data,'utf8');
let html=read('index.html');
const required=['salesSection','posProductsPane','posCartResizer','posCartContainer','posSummaryBar','posProductGrid','posCheckoutBtn','posProductSearchInput','posBarcodeScanInput','cartTotal'];
for(const id of required)if(!html.includes('id="'+id+'"'))throw Error('Missing required original sale element '+id);
if(!html.includes('href="nano-price-display.css"')||!html.includes('src="nano-price-display.js"'))throw Error('Digital price display missing');
if(html.includes('href="nano-sales-layout.css"')||html.includes('src="nano-sales-layout.js"'))throw Error('Unexpected duplicate layout assets');
const style=/<link\b[^>]*href="nano-price-display\.css"[^>]*>/;
if(!style.test(html))throw Error('Previous display stylesheet not found');
html=html.replace(style,full=>full+'\n<link rel="stylesheet" href="nano-sales-layout.css" />');
if(!html.includes('</body>'))throw Error('Closing body missing');
html=html.replace('</body>','<script defer src="nano-sales-layout.js"></script>\n</body>');
write('index.html',html);
for(const name of ['sales-layout.css','sales-layout.js']){
  fs.copyFileSync(path.join(__dirname,name),path.join(root,'nano-'+name));
}
const pkg=JSON.parse(read('package.json'));
if(pkg.version!=='1.0.75')throw Error('Wrong baseline: '+pkg.version);
pkg.version='1.0.76';write('package.json',JSON.stringify(pkg,null,2)+'\n');
const lock=path.join(root,'package-lock.json');
if(fs.existsSync(lock)){
 const data=JSON.parse(read('package-lock.json'));data.version='1.0.76';
 if(data.packages&&data.packages[''])data.packages[''].version='1.0.76';
 write('package-lock.json',JSON.stringify(data,null,2)+'\n');
}
console.log('NANO POS v1.0.76 responsive sales workspace prepared (sales logic unchanged)');
