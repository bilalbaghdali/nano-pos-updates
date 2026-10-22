'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const input=[
'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">',
'<style>body{background:#ddd}.paper{width:210mm}.head{border:2px solid black}</style></head><body>',
'<main class="paper"><header class="head"><div class="brand">متجر الأمانة</div>',
'<div>المدية ـ الجزائر</div><div>0555000000</div>',
'<img id="companyLogoImg" src="data:image/png;base64,AAAA" alt="store logo"></header>',
'<div class="doc"><div>فاتورة بيع</div><strong class="no">FA-2026-01</strong></div>',
'<section class="meta"><div>الزبون: أحمد</div><div>2026/10/22</div></section>',
'<table class="items"><thead><tr><th>المنتج</th><th>الكمية</th><th>السعر</th><th>المجموع</th></tr></thead>',
'<tbody><tr><td><img src="data:image/png;base64,BBBB" alt="product"> حليب</td><td>2</td><td>120</td><td>240</td></tr></tbody></table>',
'<section class="totals"><div class="row">الخصم 20</div><div class="line grand"><span>الإجمالي</span><span>220 د.ج</span></div>',
'<div class="row"><span>المبلغ المدفوع</span><span>120</span></div>',
'<div class="row"><span>الدين المتبقي</span><span>100</span></div></section>',
'<div class="barcode-box"><img id="barcodeImg" src="data:image/png;base64,CCCC" alt="barcode"></div>',
'</main></body></html>'
].join('');
const setup=()=>{const dom=new JSDOM('<!doctype html><html><body></body></html>',{
 url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window;w.currentLanguage='ar';
 for(const file of ['nano-blue-print-110.js','nano-invoice-layout-111.js'])w.eval(fs.readFileSync(file,'utf8'));
 return {dom,w};};
function verify(html,paper,language='ar'){
 const doc=new JSDOM(html).window.document;
 assert.ok(doc.querySelector('.np111-sheet'),'real print composition missing');
 assert.ok(doc.querySelector('.np111-hero'));
 assert.ok(doc.querySelector('.np111-store'));
 assert.ok(doc.querySelector('.np111-number-value'));
 assert.equal(doc.querySelector('.np111-number-value').textContent,'FA-2026-01');
 assert.ok(!doc.querySelector('tbody img'),'product photos removed');
 assert.ok(doc.querySelector('#companyLogoImg'),'store logo preserved');
 assert.ok(doc.querySelector('#barcodeImg'),'invoice barcode preserved');
 for(const text of ['متجر الأمانة','المدية','أحمد','FA-2026-01','حليب','240','220','120','100','الخصم']){
  assert.ok(doc.body.textContent.includes(text),'missing invoice detail '+text);
 }
 assert.equal(doc.documentElement.lang,language);
 assert.ok(doc.querySelector('[data-nano-layout-111]'),'final design CSS missing');
 const width=paper==='R58'?58:paper==='R80'||paper==='R80D'?80:paper==='A5'?148:210;
 assert.ok(doc.querySelector('[data-nano-layout-111]').textContent.includes('max-width:'+width+'mm'));
 assert.ok(html.includes('np111-summary'));
 assert.ok(html.includes('linear-gradient'));
}
(async()=>{
 const index=fs.readFileSync('index.html','utf8');
 assert.ok(index.includes('src="nano-invoice-layout-111.js"'));
 assert.ok(index.includes('src="nano-invoice-sequence-111.js"'));
 assert.equal(JSON.parse(fs.readFileSync('package.json','utf8')).version,'1.0.111');
 const {dom,w}=setup();
 for(const paper of ['R58','R80','R80D','A4','A5']){
  for(const scope of ['sale','receipt']){
   const base=w.NANO_BLUE_PRINT_110.render(input,{scope,paper,language:'ar',color:true});
   const styled=w.NANO_INVOICE_LAYOUT_111.render(base,{scope,paper,language:'ar'});
   verify(styled,paper);
   assert.equal(w.NANO_INVOICE_LAYOUT_111.render(styled,{scope,paper}),styled,'idempotent layout');
  }
 }
 assert.equal(w.NANO_INVOICE_LAYOUT_111.render(input,{scope:'other'}),input,'purchase print unaffected');
 const french=w.NANO_BLUE_PRINT_110.render(input,{scope:'sale',paper:'A4',language:'fr',color:true});
 verify(w.NANO_INVOICE_LAYOUT_111.render(french,{scope:'sale',paper:'A4',language:'fr'}),'A4','fr');
 // The same decorated DOM must reach the print driver and PDF export.
 let printRequest=null,pdfRequest=null;
 w.printInvoice=async()=>input;w.printReceipt=async()=>input;
 w.nanoNative={printHtml:async data=>{printRequest=data;return {success:true}},
 exportPdf:async data=>{pdfRequest=data;return {success:true}},
 getPrinters:async()=>[]};
 w.eval(fs.readFileSync('document-print-preview.js','utf8'));
 w.NanoDocumentPreview.show({html:input,kind:'i',scope:'sale',language:'ar'});
 let modal=w.document.getElementById('nano-document-print-preview');
 assert.ok(modal);
 const controls=modal.querySelectorAll('select'),paper=controls[1],design=controls[3];
 assert.equal(design.value,'blue110');
 paper.value='R80D';paper.dispatchEvent(new w.Event('change'));
 const preview=modal.querySelector('iframe').srcdoc;
 verify(preview,'R80D');
 modal.querySelector('button').click();
 await new Promise(r=>setTimeout(r,20));
 assert.equal(printRequest.htmlContent,preview,'physical print must match preview');
 assert.equal(printRequest.pageSize.width,80);
 w.NanoDocumentPreview.show({html:input,kind:'r',scope:'receipt',language:'ar'});
 modal=w.document.getElementById('nano-document-print-preview');
 const paper2=modal.querySelectorAll('select')[1];
 paper2.value='R58';paper2.dispatchEvent(new w.Event('change'));
 const previewPdf=modal.querySelector('iframe').srcdoc;verify(previewPdf,'R58');
 modal.querySelectorAll('button')[1].click();
 await new Promise(r=>setTimeout(r,20));
 assert.equal(pdfRequest.htmlContent,previewPdf,'PDF must match preview');
 assert.equal(pdfRequest.pageSize.width,58);
 dom.window.close();
 console.log('PASS: invoice actual structure, FA number, 5 paper sizes, no product photos; printer/PDF identical to preview');
})().catch(e=>{console.error(e);process.exitCode=1});
