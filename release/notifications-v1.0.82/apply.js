/* Apply NANO POS v1.0.82 notifications fix onto verified v1.0.81 ASAR. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('Expected extracted app.asar');
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
const write=(f,v)=>fs.writeFileSync(path.join(root,f),v,'utf8');
const one=(s,from,to,label)=>{const count=s.split(from).length-1;if(count!==1)throw Error(label+': expected 1 match, got '+count);return s.replace(from,to);};
let bridge=read('browser-bridge.js');
bridge=one(bridge,
 " || channel === 'get-notifications'",
 "",
 'remove broken empty notifications fallback');
const begin="   if (channel === 'get-stock-debt-summary') return { count: 0, total: 0 };";
if(!bridge.includes(begin))throw Error('Unsupported notification API insertion point');
const provider=fs.readFileSync(path.join(__dirname,'notification-provider.js.txt'),'utf8');
bridge=one(bridge,begin,provider+'\n'+begin,'add live notification source');
bridge=one(bridge,
 "try { window.nanoNative?.pcSyncLocalChanged?.({ revision: db.revision, at: Date.now() }); } catch {}",
 "try { window.nanoNative?.pcSyncLocalChanged?.({ revision: db.revision, at: Date.now() }); } catch {}\n     try { window.dispatchEvent(new CustomEvent('nano-pos-data-saved',{detail:{revision:db.revision}})); } catch {}",
 'refresh on saved stock changes');
write('browser-bridge.js',bridge);
let renderer=read('renderer.js');
renderer=one(renderer,'async function fetchNotifications(){',
 'async function fetchNotifications(){if(window.NANO_NOTIFICATIONS_182)return window.NANO_NOTIFICATIONS_182.refresh();',
 'replace original notification display with safe functional data-bound renderer');
write('renderer.js',renderer);
let html=read('index.html');
for(const id of ['notificationToggle','notificationsContent','notifBadge','notificationsDropdown','inventorySearch','productsSection']){
 if(!html.includes('id="'+id+'"'))throw Error('Original notification/inventory element missing: '+id);
}
html=one(html,'</head>','<link rel="stylesheet" href="nano-notifications.css" />\n</head>','notification stylesheet');
html=one(html,'</body>','<script defer src="nano-notifications.js"></script>\n</body>','notification script');
write('index.html',html);
for(const name of ['nano-notifications.js','nano-notifications.css'])
 fs.copyFileSync(path.join(__dirname,name),path.join(root,name));
const pkg=JSON.parse(read('package.json'));
if(pkg.version!=='1.0.81')throw Error('Wrong baseline version: '+pkg.version);
pkg.version='1.0.82';write('package.json',JSON.stringify(pkg,null,2)+'\n');
if(fs.existsSync(path.join(root,'package-lock.json'))){
 const lock=JSON.parse(read('package-lock.json'));lock.version='1.0.82';
 if(lock.packages?.[''])lock.packages[''].version='1.0.82';
 write('package-lock.json',JSON.stringify(lock,null,2)+'\n');
}
console.log('Real notifications, live counts and product navigation enabled without stock modifications.');
