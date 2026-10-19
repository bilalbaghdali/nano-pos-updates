/* Only repaints NANO POS v1.0.78 with Nomad Nova v1.2.18 colors. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Expected extracted ASAR directory');
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
const write=(f,s)=>fs.writeFileSync(path.join(root,f),s,'utf8');
let html=read('index.html');
if(!html.includes('id="salesSection"')||!html.includes('id="nanoHomeSection"')||
   !html.includes('id="loginOverlay"')||!html.includes('id="posCheckoutBtn"'))
  throw Error('Original NANO POS structure missing');
const open=/<html\b([^>]*\bclass=")([^"]*)(")([^>]*>)/i;
if(!open.test(html))throw Error('HTML theme class not found');
html=html.replace(open,(all,pre,classes,quote,tail)=>{
 if(classes.split(/\s+/).includes('nano-nova-desktop'))throw Error('Nova already installed');
 return '<html'+pre+(classes+' nano-nova-desktop').trim()+quote+tail;
});
if(html.includes('href="nano-nova-desktop.css"'))throw Error('Duplicate Nova CSS');
if(!html.includes('</head>'))throw Error('HTML head unavailable');
html=html.replace('</head>','  <link rel="stylesheet" href="nano-nova-desktop.css" />\n</head>');
write('index.html',html);
fs.copyFileSync(path.join(__dirname,'nano-nova-desktop.css'),path.join(root,'nano-nova-desktop.css'));
const p=JSON.parse(read('package.json'));
if(p.version!=='1.0.78')throw Error('Wrong source version: '+p.version);
p.version='1.0.79';write('package.json',JSON.stringify(p,null,2)+'\n');
const lock=path.join(root,'package-lock.json');
if(fs.existsSync(lock)){
 const j=JSON.parse(read('package-lock.json'));
 j.version='1.0.79';if(j.packages?.[''])j.packages[''].version='1.0.79';
 write('package-lock.json',JSON.stringify(j,null,2)+'\n');
}
console.log('Installed Nova colors without changing NANO POS JS, data, screens or features.');
