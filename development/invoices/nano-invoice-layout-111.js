/* NANO POS v1.0.111 — real invoice composition for the selected blue design.
 * Document fields and values stay intact; only existing DOM is rearranged/styled.
 */
(function(root){
 'use strict';
 const WIDTH={R58:58,R80:80,R80D:80,A5:148,A4:210};
 function render(input,options={}){
   const {paper='A4',scope='sale',language='ar'}=options;
   if(scope!=='sale'&&scope!=='receipt')return String(input||'');
   let doc;
   try{doc=new DOMParser().parseFromString(String(input||''),'text/html')}catch{return input}
   if(!doc?.body)return input;
   const main=doc.body.querySelector('main,.page,.paper,article')||doc.body;
   if(main.classList.contains('np111-sheet'))return String(input||'');
   const narrow=['R58','R80','R80D'].includes(paper);
   const mm=WIDTH[paper]||210;
   main.classList.add('np111-sheet');main.dataset.paper=paper;
   const elem=(tag,name)=>{const n=doc.createElement(tag);n.className=name;return n};
   const hero=elem('div','np111-hero'),intro=elem('div','np111-intro');
   const brand=main.querySelector('.np110-banner'),title=main.querySelector('.np110-title');
   if(brand)intro.append(brand);
   if(title)intro.append(title);
   hero.append(intro);
   const originalHead=main.querySelector('header,.header-grid,.head,.company-card');
   if(originalHead&&!intro.contains(originalHead)&&originalHead!==main){
     originalHead.classList.add('np111-store');hero.append(originalHead);
   }
   main.insertBefore(hero,main.firstChild);
   const docMeta=main.querySelector('.doc,.meta-grid,.meta,.info-box,.title-card');
   if(docMeta&&!hero.contains(docMeta)&&docMeta!==main)docMeta.classList.add('np111-meta');
   // Display the actual saved number; never manufacture a print-time sequence.
   const actual=String(main.textContent||'').match(/\bFA-\d{4}-\d{2,}\b/);
   if(actual){
     const stamp=elem('div','np111-number'),tag=elem('span','np111-number-label'),number=elem('strong','np111-number-value');
     tag.textContent=language==='fr'?'N° facture':language==='en'?'Invoice No.':'رقم الفاتورة';
     number.textContent=actual[0];number.setAttribute('dir','ltr');
     stamp.append(tag,number);hero.append(stamp);
   }
   const items=main.querySelector('table.items,table.items-table,.items-table,[data-purpose="items-table"],table');
   if(items)items.classList.add('np111-items');
   const summary=main.querySelector('.totals,.tot,.amounts-card,.financial-summary,.summary-layout');
   if(summary)summary.classList.add('np111-summary');
   for(const productArea of main.querySelectorAll('table tbody,.items,.items-table,[data-purpose="items-table"]')){
     for(const image of productArea.querySelectorAll('img,picture,.product-photo,.product-image,.item-photo,[data-product-image]')){
       if(image.closest('.barcode-box,.barcode-wrap,.qr-code,.qrcode,[id*="Barcode"]'))continue;
       image.remove();
     }
   }
   // Append after all original template styles so the preview, printer and PDF
   // share identical layout and do not fall back to the legacy black style.
   const css=[
     ':root{--n111-ink:#082e66;--n111-accent:#1469d2;--n111-soft:#ecf4ff;--n111-stroke:#cee0f7}',
     'html,body{background:white!important;color:var(--n111-ink)!important;print-color-adjust:exact!important;-webkit-print-color-adjust:exact!important}',
     'body{margin:0 auto!important;padding:0!important;max-width:'+mm+'mm!important;width:100%!important;min-width:0!important}',
     'body .np111-sheet{width:100%!important;max-width:'+mm+'mm!important;min-width:0!important;min-height:0!important;margin:0 auto!important;padding:'+(paper==='R58'?'2.8mm 2mm':narrow?'4mm 3mm':'11mm 10mm')+'!important;border:0!important;border-radius:0!important;box-shadow:none!important;background:white!important}',
     '.np111-sheet,.np111-sheet *{box-sizing:border-box!important}',
     '.np111-hero{background:white!important;border:1px solid var(--n111-stroke)!important;border-radius:'+(narrow?'6px':'15px')+'!important;overflow:hidden!important;margin:0 0 '+(narrow?'8px':'19px')+'!important;break-inside:avoid!important}',
     '.np111-hero .np110-banner{margin:0!important;padding:'+(narrow?'12px 6px':'23px 15px')+'!important;border-radius:0!important;background:linear-gradient(135deg,#052654,#0c4c9a 60%,#1675e1)!important;color:white!important;print-color-adjust:exact!important}',
     '.np111-hero .np110-banner strong{color:white!important;font-weight:900!important;font-size:'+(paper==='R58'?'17px':narrow?'21px':'31px')+'!important}',
     '.np111-hero .np110-title{border-radius:0!important;margin:0!important;padding:'+(narrow?'7px 3px':'13px')+'!important;background:#e7f2ff!important;border-bottom:1px solid var(--n111-stroke)!important;color:#063b80!important}',
     '.np111-store{min-width:0!important;min-height:0!important;max-width:100%!important;margin:0!important;border:0!important;border-radius:0!important;box-shadow:none!important;background:white!important;padding:'+(narrow?'9px 6px':'17px 23px')+'!important}',
     '.np111-store .shop-name,.np111-store .company-name,.np111-store .brand{font-weight:900!important;color:#063a7d!important;font-size:'+(narrow?'14px':'21px')+'!important}',
     '.np111-store img{max-height:'+(narrow?'43px':'80px')+'!important;max-width:33%!important;object-fit:contain!important}',
     '.np111-number{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:7px!important;padding:'+(narrow?'8px':'12px 20px')+'!important;background:#e8f2ff!important;border-top:1px solid var(--n111-stroke)!important;font-weight:900!important;color:#124a93!important}',
     '.np111-number-value{direction:ltr!important;unicode-bidi:isolate!important;color:#0c438b!important;background:white!important;border:1px solid #bad5f4!important;padding:6px 8px!important;border-radius:7px!important;font-size:'+(narrow?'12px':'19px')+'!important;white-space:nowrap!important}',
     '.np111-meta{background:#f5f9ff!important;border:1px solid var(--n111-stroke)!important;border-radius:'+(narrow?'5px':'11px')+'!important;padding:'+(narrow?'5px':'12px')+'!important;margin-bottom:'+(narrow?'9px':'19px')+'!important;max-width:100%!important;min-width:0!important}',
     '.np111-sheet .head-main,.np111-sheet .head-accent,.np111-sheet table thead,.np111-sheet table thead th,.np111-sheet .items-head,.np111-sheet .items-head>div{background:#0c448d!important;color:#fff!important;border-color:#3273ba!important;print-color-adjust:exact!important;-webkit-print-color-adjust:exact!important}',
     '.np111-sheet table{width:100%!important;max-width:100%!important;table-layout:fixed!important;border-collapse:collapse!important;margin:'+(narrow?'9px 0':'15px 0')+'!important}',
     '.np111-sheet table tbody tr:nth-child(even){background:#f0f6ff!important}',
     '.np111-sheet table td,.np111-sheet table tbody td{padding:'+(narrow?'4px 2px':'9px 6px')+'!important;border-bottom:1px solid #dfeafa!important;overflow-wrap:anywhere!important}',
     '.np111-summary{background:#f1f7ff!important;border:1px solid var(--n111-stroke)!important;border-radius:'+(narrow?'5px':'12px')+'!important;padding:'+(narrow?'6px':'12px')+'!important;margin-top:11px!important;max-width:100%!important}',
     '.np111-sheet .grand,.np111-sheet .grand-total,.np111-sheet .total-box,.np111-sheet .line.grand{background:linear-gradient(90deg,#073470,#156ed9)!important;color:white!important;border:0!important;border-radius:8px!important;margin:7px 0!important;padding:'+(narrow?'7px 5px':'13px 10px')+'!important;font-weight:900!important;font-size:'+(narrow?'13px':'20px')+'!important}',
     '.np111-sheet .grand *,.np111-sheet .grand-total *,.np111-sheet .total-box *{color:#fff!important}',
     '.np111-sheet .np110-footer{background:#e7f2ff!important;color:#164d96!important;border:1px solid #d0e1fa!important;border-radius:8px!important;margin-top:'+(narrow?'9px':'20px')+'!important}',
     '.np111-sheet .product-photo,.np111-sheet .product-image,.np111-sheet .item-photo,.np111-sheet [data-product-image]{display:none!important}',
     '.np111-sheet .barcode-wrap,.np111-sheet .barcode-box{max-width:100%!important;overflow:hidden!important}',
     '.np111-sheet .barcode-wrap img,.np111-sheet .barcode-box img{max-width:100%!important;height:auto!important}',
     narrow?'.np111-sheet .header-grid,.np111-sheet .meta-grid,.np111-sheet .summary-layout{display:block!important;grid-template-columns:1fr!important}.np111-sheet .info-box,.np111-sheet .company-card{max-width:100%!important;min-width:0!important}.np111-sheet table thead th,.np111-sheet table tbody td{font-size:'+(paper==='R58'?'7px':'9px')+'!important}.np111-sheet h1,.np111-sheet h2{font-size:14px!important}':'.np111-sheet table thead th{font-size:11px!important;padding:9px 6px!important}.np111-sheet table tbody td{font-size:11px!important}',
     '@media print{@page{margin:0;size:'+mm+'mm '+(paper==='A5'?'210':'297')+'mm}html,body{background:white!important;margin:0!important;padding:0!important}.np111-sheet{box-shadow:none!important}.np111-hero,.np111-number,.np111-summary{print-color-adjust:exact!important;-webkit-print-color-adjust:exact!important}}'
   ].join('\n');
   const tag=elem('style','');tag.setAttribute('data-nano-layout-111','');tag.textContent=css;
   (doc.head||doc.body).append(tag);
   return '<!doctype html>\n'+doc.documentElement.outerHTML;
 }
 root.NANO_INVOICE_LAYOUT_111=Object.freeze({render});
 if(typeof module!=='undefined'&&module.exports)module.exports={render};
})(typeof window!=='undefined'?window:globalThis);
