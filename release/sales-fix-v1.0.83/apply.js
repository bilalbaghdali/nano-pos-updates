const fs=require('fs'),path=require('path'),root=process.argv[2];
if(!root)throw Error('Missing source dir');
const get=x=>fs.readFileSync(path.join(root,x),'utf8'),put=(x,v)=>fs.writeFileSync(path.join(root,x),v);
function replace(s,a,b){if(s.split(a).length!==2)throw Error('Unexpected baseline '+a.slice(0,60));return s.replace(a,b);}
let backend=get('browser-bridge.js');
backend=replace(backend,"   if (channel === 'process-sale') {",getPatch('sale-update-branch.txt')+"\n   if (channel === 'process-sale') {");
backend=replace(backend,"   if (channel === 'get-sale-details') {",getPatch('product-analytics-branch.txt')+"\n   if (channel === 'get-sale-details') {");
put('browser-bridge.js',backend);
function getPatch(x){return fs.readFileSync(path.join(__dirname,x),'utf8')}
let renderer=get('renderer.js');
renderer=replace(renderer,"async function executeSalePayload(_0x1ebf74,_0x8b1902){const _0x4ca74f=_0x427934;try{",
 "async function executeSalePayload(_0x1ebf74,_0x8b1902){const _0x4ca74f=_0x427934;try{if(currentEditSaleId!=null)_0x1ebf74.editSaleId=currentEditSaleId;");
put('renderer.js',renderer);
let html=get('index.html');
for(const id of ['loginOverlay','productAnalyticsModal','salesHistoryTableBody'])if(!html.includes('id="'+id+'"'))throw Error('Missing '+id);
html=replace(html,'</head>','<link rel="stylesheet" href="nano-faith-login.css" />\n</head>');
html=replace(html,'</body>','<script defer src="nano-product-analytics.js"></script>\n<script defer src="faith-items.js"></script>\n<script defer src="nano-faith-login.js"></script>\n</body>');
put('index.html',html);
for(const n of ['nano-product-analytics.js','faith-items.js','nano-faith-login.js','nano-faith-login.css'])fs.copyFileSync(path.join(__dirname,n),path.join(root,n));
const pkg=JSON.parse(get('package.json'));if(pkg.version!=='1.0.82')throw Error('Version mismatch');
pkg.version='1.0.83';put('package.json',JSON.stringify(pkg,null,2)+'\n');
if(fs.existsSync(path.join(root,'package-lock.json'))){const lock=JSON.parse(get('package-lock.json'));lock.version='1.0.83';if(lock.packages?.[''])lock.packages[''].version='1.0.83';put('package-lock.json',JSON.stringify(lock,null,2)+'\n')}
