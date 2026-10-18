/* NANO POS v1.0.72: remove automatic offer/wholesale repricing on checkout.
 * Keep product pricing settings and user-entered line prices unchanged. */
'use strict';
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
if (!root) throw Error('Expected extracted ASAR directory');
const read = (name) => fs.readFileSync(path.join(root, name), 'utf8');
const write = (name, data) => fs.writeFileSync(path.join(root, name), data);
function exactReplace(source, oldPart, newPart, where) {
  const count = source.split(oldPart).length - 1;
  if (count !== 1) throw Error('Expected exactly one '+where+' but found '+count);
  return source.replace(oldPart, newPart);
}
for (const file of ['browser-bridge.js', 'mobile/www/browser-bridge.js']) {
  let s=read(file);
  s=exactReplace(s, `   if (channel === 'process-sale' && args[0] && document.getElementById('nanoApplyOffersToggle')?.checked) {
     args[0]={...args[0],checkout:{...(args[0].checkout||{}),applyOffers:true}};
   }
`, '', file+' toggle');
  s=exactReplace(s, `     if (args[0]?.checkout?.applyOffers === true) {
       try {
         const out=window.NANO_PRICING_168.reprice(args[0],db.products,db.promotions||[]);
         args[0]=out.payload;
       } catch(error) { return fail(error.message || 'تعذر تطبيق العروض'); }
     }
`, `     // Never silently reprice a sale at confirmation: honor cart unit prices.
     // Legacy mobile clients may still submit checkout.applyOffers=true.
     if (args[0]?.checkout?.applyOffers === true) {
       args[0] = {...args[0], checkout:{...args[0].checkout,applyOffers:false}};
     }
`, file+' sale reprice');
  write(file,s);
}
for (const file of ['index.html','mobile/www/index.html']) {
  let html=read(file);
  const tag='<script defer src="nano-pricing-ui.js"></script>';
  if (!html.includes(tag)) throw Error('Missing pricing toggle loader in '+file);
  html=html.replace(/^[ \t]*<script defer src="nano-pricing-ui\.js"><\/script>[ \t]*\r?\n/m,'');
  if (html.includes('src="nano-pricing-ui.js"')) throw Error('Pricing toggle script still loaded');
  if(file==='index.html') {
    if (!html.includes('</head>') || !html.includes('</body>')) throw Error('Malformed HTML');
    html=html.replace('</head>',`    <link rel="stylesheet" href="nano-price-display.css" />\n</head>`);
    html=html.replace('</body>',`<script defer src="nano-price-display.js"></script>\n</body>`);
  }
  write(file,html);
}
write('nano-price-display.js', fs.readFileSync(path.join(__dirname,'nano-price-display.js'),'utf8'));
write('nano-price-display.css', fs.readFileSync(path.join(__dirname,'nano-price-display.css'),'utf8'));
const pkg=JSON.parse(read('package.json'));
if(pkg.version!=='1.0.71')throw Error('Unexpected baseline '+pkg.version);
pkg.version='1.0.72';write('package.json',JSON.stringify(pkg,null,2)+'\n');
const lock=path.join(root,'package-lock.json');
if(fs.existsSync(lock)) {
 const j=JSON.parse(read('package-lock.json'));
 j.version='1.0.72';
 if(j.packages?.[''])j.packages[''].version='1.0.72';
 write('package-lock.json',JSON.stringify(j,null,2)+'\n');
}
console.log('v1.0.72 - auto pricing removed; digital total screen added');
