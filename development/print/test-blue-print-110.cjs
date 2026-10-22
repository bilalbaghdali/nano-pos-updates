'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const script=fs.readFileSync('nano-blue-print-110.js','utf8');
const center=fs.readFileSync('document-print-preview.js','utf8');
const index=fs.readFileSync('index.html','utf8');
assert.ok(index.indexOf('src="nano-blue-print-110.js"')<index.indexOf('src="document-print-preview.js"'));
assert.equal(JSON.parse(fs.readFileSync('package.json','utf8')).version,'1.0.110');
const example=['<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>body{background:pink}.paper{width:210mm}</style></head>',
'<body><main class="paper"><header class="head"><div class="shop-name">متجر السعادة</div><div>الجزائر، المدية</div><div>0770 000 000</div>',
'<img id="companyLogoImg" src="data:image/png;base64,AAAA" alt="Store Logo"></header>',
'<div class="title">فاتورة بيع</div><div class="meta"><span>2026/10/22</span><span>#INV-109</span><span>الزبون: أحمد</span></div>',
'<table class="items"><thead><tr><th>المنتج</th><th>الكمية</th><th>سعر الوحدة</th><th>المجموع</th></tr></thead>',
'<tbody><tr><td><img src="data:image/png;base64,BBBB" alt="Product Photo"> حليب 1 لتر</td><td>2</td><td>120.00</td><td>240.00</td></tr></tbody></table>',
'<div class="totals"><div class="row">الخصم: 20.00</div><div class="row grand"><span>الإجمالي</span><strong>220.00 د.ج</strong></div>',
'<div class="row"><span>المدفوع</span><b>120.00</b></div><div class="row"><span>الدين المتبقي</span><b>100.00</b></div></div>',
'<div class="barcode-wrap"><img src="data:image/svg+xml,qr" alt="QR"></div></main></body></html>'].join('');
function validate(content,paper,lang){
 const view=new JSDOM(content).window.document;
 assert.ok(view.querySelector('.np110-banner'));
 assert.ok(view.querySelector('.np110-title'));
 assert.ok(view.querySelector('.np110-footer'));
 assert.equal(view.documentElement.lang,lang);
 assert.equal(view.querySelector('tbody img'),null,'product photo must be removed');
 assert.ok(view.querySelector('#companyLogoImg'),'shop logo remains');
 assert.ok(view.querySelector('.barcode-wrap img'),'QR remains');
 for(const fact of ['متجر السعادة','المدية','#INV-109','أحمد','حليب 1 لتر','220.00','120.00','100.00','20.00'])
  assert.ok(view.body.textContent.includes(fact),'missing shop or financial data: '+fact);
 const width=paper==='R58'?58:paper==='R80'||paper==='R80D'?80:paper==='A5'?148:210;
 assert.ok(content.includes('@page{size:'+width+'mm'));
 return view;
}
(async()=>{
 const dom=new JSDOM('<!doctype html><html lang="ar"><body></body></html>',{
   url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window;
 w.eval(script);
 assert.ok(w.NANO_BLUE_PRINT_110);
 for(const paper of ['R58','R80','R80D','A4','A5']){
   for(const scope of ['receipt','sale']){
     const result=w.NANO_BLUE_PRINT_110.render(example,{paper,language:'ar',color:true,scope});
     validate(result,paper,'ar');
     if(paper==='R80D')assert.ok(result.includes('.np110-document .totals'));
   }
 }
 const fr=w.NANO_BLUE_PRINT_110.render(example,{paper:'R80',language:'fr',color:false,scope:'receipt'});
 assert.ok(fr.includes('Ticket de caisse'));
 assert.ok(fr.includes('grayscale(1)'));
 validate(fr,'R80','fr');
 assert.equal(w.NANO_BLUE_PRINT_110.render(example,{scope:'other',paper:'A4'}),example);
 let sentPrint=null,sentPdf=null,callCount=0;
 w.printInvoice=async()=>example;
 w.printReceipt=async()=>example;
 w.currentLanguage='ar';
 w.nanoNative={
   printHtml:async x=>{sentPrint=x;callCount++;return {success:true};},
   exportPdf:async x=>{sentPdf=x;return {success:true};},
   getPrinters:async()=>[]
 };
 w.localStorage.setItem('nano.print.center.v135.i.template','classic');
 w.eval(center);
 await w.printInvoice('sale',1);
 let dialog=w.document.getElementById('nano-document-print-preview');
 assert.ok(dialog);
 let selects=[...dialog.querySelectorAll('select')];
 const [language,paper,printer,design]=selects;
 assert.equal(design.value,'blue110','default must adopt the approved blue layout');
 assert.ok([...paper.options].some(x=>x.value==='R80D'));
 const frame=dialog.querySelector('iframe');
 for(const mode of ['R58','R80','R80D','A4','A5']){
   paper.value=mode;paper.dispatchEvent(new w.Event('change'));
   validate(frame.srcdoc,mode,'ar');
 }
 paper.value='R80D';paper.dispatchEvent(new w.Event('change'));
 const preview=frame.srcdoc;
 dialog.querySelectorAll('button')[0].click();await new Promise(r=>setTimeout(r,15));
 assert.equal(callCount,1);
 assert.equal(sentPrint.htmlContent,preview,'printer must use exactly same decorated HTML as preview');
 assert.equal(sentPrint.pageSize.width,80);
 await w.printReceipt('sale',2);
 dialog=w.document.getElementById('nano-document-print-preview');
 const receiptPaper=dialog.querySelectorAll('select')[1];
 assert.equal(receiptPaper.value,'R80');
 receiptPaper.value='R58';receiptPaper.dispatchEvent(new w.Event('change'));
 const receiptPreview=dialog.querySelector('iframe').srcdoc;
 validate(receiptPreview,'R58','ar');
 dialog.querySelectorAll('button')[1].click();await new Promise(r=>setTimeout(r,15));
 assert.equal(sentPdf.htmlContent,receiptPreview,'PDF must match 58mm preview');
 assert.equal(sentPdf.pageSize.width,58);
 w.NanoDocumentPreview.show({html:example,kind:'p',scope:'other',language:'ar'});
 dialog=w.document.getElementById('nano-document-print-preview');
 assert.ok(!dialog.querySelector('iframe').srcdoc.includes('np110-banner'),'proforma unchanged');
 dom.window.close();
 console.log('PASS: five formats, invoice+receipt, AR/FR, preserved shop/financial/QR, removed product pictures; printed/PDF matches preview');
})().catch(e=>{console.error(e);process.exitCode=1});
