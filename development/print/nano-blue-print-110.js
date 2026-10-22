/* NANO POS v1.0.110 — unified blue/white sales printing, no product photos.
 * Preserves all original line items, totals, tax, customer debt, QR and store logo.
 */
(function(root){
 'use strict';
 const PAPER=Object.freeze({
   R58:{width:58,style:'compact'},R80:{width:80,style:'thermal'},
   R80D:{width:80,style:'detailed'},A4:{width:210,style:'a4'},A5:{width:148,style:'a5'}
 });
 const TEXT={
  ar:{sale:'فاتورة بيع',receipt:'وصل بيع',thanks:'شكرًا لتسوقكم',again:'نتمنى رؤيتكم مجددًا'},
  fr:{sale:'Facture de vente',receipt:'Ticket de caisse',thanks:'Merci pour votre visite',again:'À bientôt'},
  en:{sale:'Sales invoice',receipt:'Sales receipt',thanks:'Thank you for shopping',again:'See you again'}
 };
 function stylesheet(paper,color){
   const p=PAPER[paper]||PAPER.A4,thin=p.width<=80,mini=p.width===58;
   const pad=mini?'3mm 2.5mm':thin?'4mm 3mm':'9mm';
   return [
'@page{size:'+p.width+'mm '+(p.style==='a5'?'210':'297')+'mm;margin:0}',
':root{--np-navy:#082f6c;--np-royal:#1569da;--np-pale:#e8f2ff}',
'html,body{background:#fff!important;color:#0b2d62!important;print-color-adjust:exact;-webkit-print-color-adjust:exact}',
'body{width:100%!important;max-width:'+p.width+'mm!important;margin:0 auto!important;padding:0!important;min-width:0!important;overflow-wrap:anywhere!important;font-family:Cairo,Tajawal,Arial,sans-serif!important}',
'body *,body *::before,body *::after{box-sizing:border-box!important}',
'body>main,body>article,body .paper,body .page,body .receipt-canvas,body .doc-container,body .thermal-width{width:100%!important;max-width:'+p.width+'mm!important;min-width:0!important;min-height:0!important;background:#fff!important;margin:0 auto!important;padding:'+pad+'!important;border:0!important;border-radius:0!important;box-shadow:none!important}',
'.np110-document{overflow:hidden!important}',
'.np110-banner{direction:ltr!important;background:linear-gradient(135deg,#062354,#1671e5)!important;color:#fff!important;text-align:center!important;border-radius:'+(mini?'3px':'10px 10px 23px 23px')+'!important;padding:'+(mini?'8px 4px':'13px 9px')+'!important;margin:0 0 7px!important;break-inside:avoid!important;print-color-adjust:exact!important}',
'.np110-banner strong{color:#fff!important;font-family:Arial,sans-serif!important;font-weight:900!important;font-size:'+(mini?'17px':thin?'21px':'30px')+'!important;letter-spacing:.2px}',
'.np110-banner span{display:block!important;margin-top:3px!important;color:#e4f1ff!important;font-size:'+(mini?'9px':thin?'11px':'13px')+'!important}',
'.np110-title{text-align:center!important;color:#063776!important;background:#e6f1ff!important;padding:'+(mini?'5px 3px':thin?'7px':'10px')+'!important;font-weight:900!important;font-size:'+(mini?'12px':thin?'15px':'20px')+'!important;border-radius:7px!important;margin:6px 0 10px!important;break-inside:avoid!important}',
'.company-card,.company-info,.meta-grid,.header-grid,.info-box,.head,.header,.doc,.title-card{max-width:100%!important;min-width:0!important;border-color:#d7e6fa!important;box-shadow:none!important}',
'.company-name,.brand,.shop-name{color:var(--np-navy)!important;font-weight:900!important}',
'.title-band,.doc .badge{background:#e6f1ff!important;color:var(--np-navy)!important;border-radius:5px!important}',
'section,header,footer{max-width:100%!important}',
'table,.items,.items-table table{width:100%!important;max-width:100%!important;table-layout:fixed!important;border-collapse:collapse!important;font-size:'+(mini?'7px':thin?'9px':'11px')+'!important}',
'table thead,thead,.items-head{background:#083a83!important;color:white!important}',
'table thead th,thead th,.items-head>div{background:#083a83!important;color:white!important;border-color:#d3e2f6!important;padding:'+(mini?'3px 1px':thin?'5px 2px':'8px 4px')+'!important;overflow-wrap:anywhere!important;font-weight:900!important}',
'tbody tr:nth-child(even){background:#f0f6ff!important}',
'tbody td{color:#102d59!important;overflow-wrap:anywhere!important;white-space:normal!important;padding:'+(mini?'2px 1px':thin?'4px 2px':'7px 5px')+'!important;border-color:#dce7f5!important}',
'tr{break-inside:avoid!important}',
'.items-head{max-width:100%!important;gap:2px!important;min-width:0!important}',
'.items img,.items-table tbody img,[data-purpose="items-table"] img,.item-photo,.product-photo,.product-image,[data-product-image]{display:none!important}',
'.grand,.grand-total,.total-box,.total-value,.line.grand-total{background:linear-gradient(90deg,#073574,#1468d7)!important;color:white!important;border-radius:6px!important;padding:'+(mini?'5px 3px':thin?'7px 5px':'10px')+'!important;font-weight:900!important}',
'.grand *,.grand-total *,.total-box *,.total-value *,.line.grand-total *{color:white!important}',
'[data-role="discount-row"] *{color:#c32939!important}',
'.totals,.amounts-card,.pay-table,.payment-box{max-width:100%!important;min-width:0!important;border-color:#d1e5ff!important}',
'.barcode-wrap,.barcode-box,#thermalBarcodeWrap{max-width:100%!important}',
'.barcode-wrap img,.barcode-box img,#thermalBarcodeImg,.qr-code img,.qrcode img{max-width:100%!important;height:auto!important}',
'.np110-footer{color:#0e4d9b!important;background:linear-gradient(165deg,#f5faff,#d9ebff)!important;padding:'+(mini?'8px 3px':thin?'11px 5px':'16px')+'!important;border-radius:8px!important;text-align:center!important;font-weight:800!important;margin-top:12px!important;break-inside:avoid!important;font-size:'+(mini?'9px':thin?'11px':'13px')+'!important}',
'.np110-footer span{display:block!important;color:#5c7fa9!important;margin-top:3px!important;font-size:90%!important}',
'.footer-note,footer,.foot{border-top-color:#bcd4f7!important;color:#12509d!important}',
thin?[
'.header-grid,.meta-grid,.summary-layout,.footer-grid,.company-card{display:block!important;grid-template-columns:none!important}',
'.info-box,.company-info,.company-card,.words-box,.payment-box{width:100%!important;padding:4px 2px!important}',
'h1{font-size:'+(mini?'13px':'16px')+'!important;margin:3px 0!important}',
'h2{font-size:'+(mini?'12px':'14px')+'!important;margin:3px 0!important}',
'.logo-wrap,img#companyLogoImg,img#thermalLogoImg{max-width:'+(mini?'18mm':'23mm')+'!important}',
'.items-head>div:first-child{display:none!important}',
'.items-head{font-size:'+(mini?'7px':'8px')+'!important}',
'.pay-table td,.pay-table th{padding:2px 1px!important}'
].join('\n'):'',
p.style==='detailed'?'.np110-document .head,.np110-document .header,.np110-document .meta,.np110-document .party{background:#eff6ff!important;border:1px solid #d3e5ff!important;border-radius:7px!important;padding:7px!important}.np110-document .totals,.np110-document .amounts-card{background:#f3f8ff!important;border:1px solid #d3e5ff!important;padding:7px!important}':'',
p.style==='compact'?'.np110-banner{background:#092b61!important}table th,table td{font-size:7px!important}':'',
color===false?'html,body{filter:grayscale(1)!important;-webkit-filter:grayscale(1)!important}':'',
'@media print{html,body{width:'+p.width+'mm!important;max-width:'+p.width+'mm!important;padding:0!important;margin:0!important}.np110-banner,.np110-title,.np110-footer{print-color-adjust:exact!important;-webkit-print-color-adjust:exact!important}}'
   ].join('\n');
 }
 function render(input,options){
   const opts=options||{},html=String(input||''),scope=String(opts.scope||'');
   if(scope!=='sale'&&scope!=='receipt')return html;
   const paper=PAPER[opts.paper]?opts.paper:'A4';
   const lang=TEXT[opts.language]?opts.language:'ar',txt=TEXT[lang];
   let doc;
   try{doc=new DOMParser().parseFromString(html,'text/html')}catch(_){return html}
   if(!doc||!doc.body)return html;
   const content=doc.body.querySelector('main')||doc.body.querySelector('article')||doc.body.querySelector('.paper')||doc.body;
   content.classList.add('np110-document');
   const banner=doc.createElement('div');banner.className='np110-banner';
   const brand=doc.createElement('strong');brand.textContent='NANO POS';
   const sub=doc.createElement('span');sub.textContent=scope==='sale'?txt.sale:txt.receipt;
   banner.append(brand,sub);
   const title=doc.createElement('div');title.className='np110-title';
   title.textContent=scope==='sale'?txt.sale:txt.receipt;
   content.insertBefore(title,content.firstChild);
   content.insertBefore(banner,title);
   for(const region of doc.body.querySelectorAll('table tbody, .items, .items-table tbody, [data-purpose="items-table"]')){
     for(const image of region.querySelectorAll('img,picture,.product-photo,.product-image,.item-photo,[data-product-image]')){
       if(image.closest('.barcode-box,.barcode-wrap,[id*="Barcode"],.qr-code,.qrcode'))continue;
       image.remove();
     }
   }
   const footer=doc.createElement('div');footer.className='np110-footer';
   footer.textContent=txt.thanks;
   const last=doc.createElement('span');last.textContent=txt.again;footer.append(last);
   content.append(footer);
   const style=doc.createElement('style');style.setAttribute('data-nano-blue-print-110','');
   style.textContent=stylesheet(paper,opts.color!==false);
   (doc.head||doc.body).append(style);
   doc.documentElement.lang=lang;doc.documentElement.dir=lang==='ar'?'rtl':'ltr';
   return '<!doctype html>\n'+doc.documentElement.outerHTML;
 }
 root.NANO_BLUE_PRINT_110=Object.freeze({render,PAPER});
 if(typeof module!=='undefined'&&module.exports)module.exports={render,PAPER};
})(typeof window!=='undefined'?window:globalThis);
