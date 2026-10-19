/* Add visible inventory shortage button, printable/shareable restock list to v1.0.79. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const dir=process.argv[2];if(!dir)throw Error('Expected extracted NANO POS 1.0.79 app.asar');
const read=x=>fs.readFileSync(path.join(dir,x),'utf8');
const write=(x,s)=>fs.writeFileSync(path.join(dir,x),s,'utf8');
let html=read('index.html');
for(const id of ['productsSection','inventorySearch','inventoryBody','nanoHomeSection','salesSection']){
 if(!html.includes('id="'+id+'"'))throw Error('Missing original NANO POS section '+id);
}
if(!html.includes('src="nano-restock-assistant.js"'))throw Error('Required existing restock classifier unavailable');
if(!html.includes('href="nano-nova-desktop.css"'))throw Error('Nova palette from v1.0.79 unavailable');
if(html.includes('src="nano-inventory-shortages.js"'))throw Error('Shortage feature already installed');
const head='</head>';
if(html.split(head).length!==2)throw Error('Unexpected head tag');
html=html.replace(head,'<link rel="stylesheet" href="nano-inventory-shortages.css" />\n'+head);
const old='<script defer src="nano-restock-assistant.js"></script>';
if(html.split(old).length!==2)throw Error('Legacy restock initialization found multiple times or not at all');
html=html.replace(old,old+'\n  <script defer src="nano-inventory-shortages.js"></script>');
write('index.html',html);
for(const x of ['nano-inventory-shortages.js','nano-inventory-shortages.css'])
 fs.copyFileSync(path.join(__dirname,x),path.join(dir,x));
const p=JSON.parse(read('package.json'));
if(p.version!=='1.0.79')throw Error('Unexpected baseline version '+p.version);
p.version='1.0.80';write('package.json',JSON.stringify(p,null,2)+'\n');
if(fs.existsSync(path.join(dir,'package-lock.json'))){
 const lock=JSON.parse(read('package-lock.json'));
 lock.version='1.0.80';if(lock.packages?.[''])lock.packages[''].version='1.0.80';
 write('package-lock.json',JSON.stringify(lock,null,2)+'\n');
}
console.log('v1.0.80: inventory shortages in top toolbar, print/CSV/share; stock and checkout unchanged');
