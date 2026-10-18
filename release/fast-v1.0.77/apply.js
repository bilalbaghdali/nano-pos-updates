/* Apply NANO POS v1.0.77 fast sales UI on verified v1.0.76 package. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Missing extracted app.asar source');
const read=file=>fs.readFileSync(path.join(root,file),'utf8');
const write=(file,value)=>fs.writeFileSync(path.join(root,file),value,'utf8');
const main=read('index.html');
const required=['salesSection','posBarcodeScanInput','posProductSearchInput','posCartContainer','cartItemsList','checkoutModal',
 'checkoutPaidAmount','checkoutPaymentMethod','checkoutTotalUI','posCustomerSelect','posToolbar','posSummaryBar'];
for(const id of required)if(!main.includes('id="'+id+'"'))throw Error('Expected UI field is missing: '+id);
const renderer=read('renderer.js');
for(const fn of ['function setCartItemQty(','function updateCartUI(','function processSale(','function checkoutCalcChange(',
 'function openCustomProductModal(','function setupPosBarcodeScanner(','function addCustomProductToCart(']){
 if(!renderer.includes(fn))throw Error('Expected sales function unavailable: '+fn);
}
if(main.includes('src="nano-fast-pos.js"')||main.includes('href="nano-fast-pos.css"'))throw Error('Fast POS assets duplicated');
let html=main.replace('</head>','<link rel="stylesheet" href="nano-fast-pos.css" />\n</head>');
if(html===main)throw Error('Could not attach stylesheet');
html=html.replace('</body>','<script defer src="nano-fast-pos.js"></script>\n</body>');
if(!html.includes('src="nano-fast-pos.js"'))throw Error('Could not attach script');
write('index.html',html);
fs.copyFileSync(path.join(__dirname,'fast-pos.js'),path.join(root,'nano-fast-pos.js'));
fs.copyFileSync(path.join(__dirname,'fast-pos.css'),path.join(root,'nano-fast-pos.css'));
const pkg=JSON.parse(read('package.json'));
if(pkg.version!=='1.0.76')throw Error('Wrong input version: '+pkg.version);
pkg.version='1.0.77';write('package.json',JSON.stringify(pkg,null,2)+'\n');
const lockFile='package-lock.json';
if(fs.existsSync(path.join(root,lockFile))){
 const lock=JSON.parse(read(lockFile));lock.version='1.0.77';
 if(lock.packages&&lock.packages[''])lock.packages[''].version='1.0.77';
 write(lockFile,JSON.stringify(lock,null,2)+'\n');
}
console.log('Fast sale shortcuts and mixed cash/debt controls added; original checkout and stock logic untouched');
