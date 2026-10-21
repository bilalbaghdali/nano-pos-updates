'use strict';
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const guard=require('./nano-sales-safe-195.js');

// Double-submit suppression must be released after success OR error.
assert.equal(guard.begin(),true);
assert.equal(guard.begin(),false);
assert.equal(guard.isPending(),true);
guard.end();
assert.equal(guard.begin(),true);
guard.end();

const catalog=[{id:10,batches:[{id:22,stock:5}]},{id:11,batches:[]}];
assert.equal(guard.inspectInvoice([{product_id:10,batch_id:22,quantity:2}],catalog).ok,true);
assert.equal(guard.inspectInvoice([{product_id:10,batch_id:22},{product_id:11}],catalog).ok,true);
assert.equal(guard.inspectInvoice([{product_id:null,custom_product_name:'Service'}],catalog).ok,true);
assert.equal(guard.inspectInvoice([{product_id:999}],catalog).ok,false);
assert.equal(guard.inspectInvoice([{product_id:10,batch_id:404}],catalog).ok,false);
assert.equal(guard.inspectInvoice([{product_id:null}],catalog).ok,false);
assert.equal(guard.inspectInvoice([],catalog).ok,false);
assert.match(guard.inspectInvoice([{product_id:999}],catalog,'fr').message,/Modification/);

let onKey,focus=0,navigate=0,prevent=0,activeSales=true;
const shortcut=fs.readFileSync('nano-v136-shortcuts.js','utf8');
const searchEl={focus(){focus++;},select(){}};
const document={
  addEventListener(type,fn){if(type==='keydown')onKey=fn;},
  getElementById(id){return id==='salesSection'?{classList:{contains:c=>c==='hidden'?!activeSales:false}}:null;},
  querySelector(){return searchEl;}
};
const window={navigate(){navigate++;}};
vm.runInNewContext(shortcut,{document,window,setTimeout(fn){fn();}});
const ev=key=>({key,altKey:false,shiftKey:false,ctrlKey:false,metaKey:false,defaultPrevented:false,preventDefault(){prevent++;}});
onKey(ev('F2'));
assert.equal(navigate,0,'F2 in POS must remain reserved for suspend-draft');
assert.equal(prevent,0);
activeSales=false;onKey(ev('F2'));
assert.equal(navigate,1,'F2 outside POS should open product search');
assert.equal(focus,1);

const renderer=fs.readFileSync('renderer.js','utf8');
assert.ok(renderer.includes('const __nanoEditCheck195=window.NANO_SALE_SAFE_195?.inspectInvoice('));
assert.ok(renderer.includes('finally{__nanoSaleSafe195?.end();}'));
assert.ok(renderer.indexOf('const __nanoEditCheck195=')<
  renderer.indexOf("cart=[],currentEditSaleId=_0xb1e6f4['id'];"));
const html=fs.readFileSync('index.html','utf8');
assert.equal((html.match(/nano-sales-safe-195\.js/g)||[]).length,1,'load guard exactly once');
const browser=fs.readFileSync('browser-bridge.js','utf8');
assert.ok(browser.includes("if (channel === 'process-sale' && args[0]?.editSaleId != null)"));
assert.ok(browser.includes('const delta=(oldStock.get(key)||0)-(newStock.get(key)||0);'));
assert.ok(browser.includes('updated:true'));
console.log('PASS: sale mutex, lossless invoice editing, F2 shortcut, invoice update invariants');
