// Fix the v1.0.70 desktop stocktake regression. Do not change business data.
'use strict';
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
if (!root) throw new Error('Missing extracted ASAR directory');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const write = (file, content) => fs.writeFileSync(path.join(root, file), content);
const file = 'browser-bridge.js';
let bridge = read(file);
const bad = "if (channel.startsWith('nano-count-') || ['get-stocktake-sheet','get-stocktake-drafts','create-stocktake-draft','approve-stocktake-draft','reject-stocktake-draft'].includes(channel)) return {success:false,error:'mobile_stocktake_disabled',message:'جرد الهاتف والجرد الجماعي متوقفان؛ استخدم جرد الكمبيوتر.'};";
if (bridge.split(bad).length !== 2) {
  throw new Error('Expected exactly one desktop-wide stocktake restriction; refusing unsafe changes');
}
bridge = bridge.replace(bad, '// Desktop stocktake stays available; the authenticated mobile-sync server still blocks handset counting.');
for (const route of ["if (channel === 'get-stocktake-sheet')", "if (channel === 'create-stocktake')", "if (channel === 'get-stocktakes')"]) {
  if (!bridge.includes(route)) throw new Error('Missing desktop stocktake route '+route);
}
write(file, bridge);
const mobileServer = read('mobile-sync-server.cjs');
if (!mobileServer.includes("error:'mobile_stocktake_disabled'") ||
    !mobileServer.includes("'get-stocktake-sheet'")) {
  throw new Error('Mobile stocktake ban was removed unexpectedly');
}
const html = read('index.html');
if (!html.includes('src="stocktake/stocktake-ui.js"') ||
    !html.includes('src="stocktake/desktop-tools.js"')) {
  throw new Error('Desktop stocktake UI or report tools are missing');
}
const pkg = JSON.parse(read('package.json'));
if (pkg.version !== '1.0.70') throw new Error('Wrong baseline: '+pkg.version);
pkg.version = '1.0.71';
write('package.json', JSON.stringify(pkg, null, 2)+'\n');
const lockPath = path.join(root, 'package-lock.json');
if (fs.existsSync(lockPath)) {
  const lock = JSON.parse(read('package-lock.json'));
  lock.version = '1.0.71';
  if (lock.packages && lock.packages['']) lock.packages[''].version = '1.0.71';
  write('package-lock.json', JSON.stringify(lock, null, 2)+'\n');
}
console.log('Desktop stocktake unblocked, phone restrictions preserved; version 1.0.71');
