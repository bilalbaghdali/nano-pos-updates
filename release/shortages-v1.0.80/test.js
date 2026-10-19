'use strict';
const assert=require('node:assert/strict'),fs=require('fs');
const {JSDOM}=require('/tmp/ui-test/node_modules/jsdom');
const root=process.argv[2];if(!root)throw Error('Extracted source path required');
const old=fs.readFileSync(root+'/nano-restock-assistant.js','utf8');
const src=fs.readFileSync(root+'/nano-inventory-shortages.js','utf8');
const html='<html lang="ar"><head></head><body><section id="productsSection"><div><div class="flex justify-between"><h2 data-i18n="inventory_management_title">إدارة المخزون</h2><div id="invActions"><button id="priceList">قائمة الأسعار</button><button id="addProduct">إضافة</button></div></div><table id="inventoryBody"></table></div></section></body></html>';
async function run(){
 const dom=new JSDOM(html,{url:'http://localhost:3000/',runScripts:'outside-only'});
 const win=dom.window,doc=win.document;win.showToast=()=>{};
 const rawProducts=[
  {id:1,name:'Milk',barcode:'6131234567890',stock:0,min_stock:5},
  {id:2,name:'Bread',barcode:'6139876543210',stock:2,min_stock:5},
  {id:3,name:'Sugar',barcode:'6131231231231',stock:20,min_stock:5},
  {id:4,name:'No threshold',stock:0},
 ];
 let reads=0;
 win.api={getProducts:async({page,perPage})=>{
   reads++;assert.equal(perPage,200);
   if(page===1)return {items:rawProducts,total:rawProducts.length};
   return {items:[],total:rawProducts.length};
 }};
 win.eval(old);win.eval(src);
 doc.dispatchEvent(new win.Event('DOMContentLoaded'));
 const btn=doc.getElementById('nanoShortageOpen180');
 assert(btn,'New shortage button is missing');
 assert.equal(btn.parentElement.id,'invActions','Stock shortage button not in inventory toolbar');
 assert.equal(doc.getElementById('nanoRestockAssistantBtn'),null,'Old hidden button duplicated');
 btn.click();
 await new Promise(resolve=>setTimeout(resolve,80));
 assert.equal(reads,1,'Expected one inventory paginated read');
 assert.equal(doc.querySelectorAll('#nanoShortageRows180 tr').length,3,'Should list exactly three depleted/low-stock products');
 assert(doc.getElementById('nanoShortageCount180').textContent.includes('3'));
 assert(doc.getElementById('nanoShortageRows180').textContent.includes('Milk'));
 assert(!doc.getElementById('nanoShortageRows180').textContent.includes('Sugar'));
 assert(doc.getElementById('nanoShortageRows180').textContent.includes('No threshold'),'Depleted product without minimum must be listed');
 for(const id of ['nanoShortageRefresh180','nanoShortagePrint180','nanoShortageSend180','nanoShortageCSV180']){
    assert(!doc.getElementById(id).disabled,'Action missing or disabled: '+id);
 }
 doc.getElementById('nanoShortageSend180').click();
 const share=doc.getElementById('nanoShortageShareMenu180');
 assert.equal(share.hidden,false,'Send choices not shown');
 for(const key of ['system','whatsapp','mail','copy','csv'])
   assert(doc.getElementById('nanoShortageShare'+key),'Missing share choice '+key);
 const rows=doc.querySelectorAll('#nanoShortageRows180 tr');
 assert(rows[0].textContent.includes('Milk'));
 assert(rows[0].textContent.includes('8'),'Expected at least 8 units suggested for empty 5-minimum item');
 assert(rows[1].textContent.includes('No threshold'));
 const refresh=doc.getElementById('nanoShortageRefresh180');refresh.click();
 await new Promise(resolve=>setTimeout(resolve,80));
 assert.equal(doc.querySelectorAll('#nanoShortageRows180 tr').length,3,'Refresh duplicates entries');
 doc.getElementById('nanoShortageClose180').click();
 assert(!doc.getElementById('nanoShortageModal180'),'Close should clean up modal');
 btn.click();await new Promise(resolve=>setTimeout(resolve,80));
 assert.equal(doc.querySelectorAll('#nanoShortageRows180 tr').length,3,'Reopening did not work');
 console.log('PASS stock toolbar button, missing/no-threshold/low-stock, refresh, print/export/send actions, reopen');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
