/* NANO POS v1.0.34 unified print center */
(()=>{'use strict';
if(window.__nanoPrintCenterV134)return;window.__nanoPrintCenterV134=1;
const I=window.printInvoice,R=window.printReceipt,P=window.printProforma;
let active=null;
const U={ar:{i:'معاينة الفاتورة',r:'معاينة الوصل',p:'معاينة الفاتورة المبدئية',l:'لغة الطباعة',x:'طباعة',d:'حفظ PDF',c:'إغلاق',u:'جاري تحديث المعاينة…',e:'تعذر تحديث المعاينة'},fr:{i:'Aperçu de la facture',r:'Aperçu du reçu',p:'Aperçu pro forma',l:"Langue d’impression",x:'Imprimer',d:'Enregistrer PDF',c:'Fermer',u:"Mise à jour de l’aperçu…",e:"Impossible de mettre à jour l’aperçu"},en:{i:'Invoice preview',r:'Receipt preview',p:'Pro-forma preview',l:'Print language',x:'Print',d:'Save PDF',c:'Close',u:'Updating preview…',e:'Could not update preview'}};
const ui=()=>U[window.currentLanguage]||U.ar,esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));
const LANGS=['ar','fr','en'];
function lang(h,f){const m=String(h||'').match(/<html\b[^>]*\blang=["'](ar|fr|en)["']/i);return m?m[1].toLowerCase():(LANGS.includes(f)?f:'ar')}
const C=[
 {ar:'المرجع',fr:'Référence',en:'Reference',v:['المرجع','مرجع','Référence','Reference','Ref','Réf']},
 {ar:'التاريخ',fr:'Date',en:'Date',v:['التاريخ','Date']},
 {ar:'بيانات العميل',fr:'Client',en:'Customer',v:['بيانات العميل','العميل','الزبون','Client','Customer']},
 {ar:'المورد',fr:'Fournisseur',en:'Supplier',v:['المورد','Fournisseur','Supplier']},
 {ar:'البيانات التجارية',fr:'Informations commerciales',en:'Business details',v:['البيانات التجارية','Informations commerciales','Business details']},
 {ar:'الرمز',fr:'Code',en:'Code',v:['الرمز','Code']},
 {ar:'المنتج / الوصف',fr:'Article / description',en:'Product / description',v:['المنتج / الوصف','المنتج','الوصف','Article / description','Désignation','Designation','Product / description','Product']},
 {ar:'الكمية',fr:'Qté',en:'Qty',v:['الكمية','Qté','Qte','Quantité','Quantity','Qty']},
 {ar:'الوحدة',fr:'Unité',en:'Unit',v:['الوحدة','Unité','Unite','Unit']},
 {ar:'قطعة',fr:'Pièce',en:'Piece',v:['قطعة','حبة','Pièce','Piece']},
 {ar:'سعر الوحدة',fr:'Prix unitaire',en:'Unit price',v:['سعر الوحدة','Prix unitaire','Prix HT','Unit price']},
 {ar:'الضريبة',fr:'TVA',en:'Tax',v:['الضريبة','ضريبة','TVA','Tax']},
 {ar:'الإجمالي',fr:'Total',en:'Total',v:['الإجمالي','المجموع','Total']},
 {ar:'المجموع الفرعي',fr:'Sous-total',en:'Subtotal',v:['المجموع الفرعي','الإجمالي الفرعي','Sous-total','Sous total','Subtotal','Total HT']},
 {ar:'التخفيض',fr:'Remise',en:'Discount',v:['التخفيض','خصم','Remise','Discount']},
 {ar:'إجمالي الضريبة',fr:'Total TVA',en:'Tax total',v:['إجمالي الضريبة','مجموع الضريبة','Total TVA','Tax total']},
 {ar:'الصافي للدفع',fr:'Net à payer',en:'Net to pay',v:['الصافي للدفع','صافي للدفع','Net à payer','Net a payer','Net to pay']},
 {ar:'الرصيد السابق',fr:'Solde antérieur',en:'Previous balance',v:['الرصيد السابق','الرصيد القديم','Solde antérieur','Solde anterieur','Previous balance','Old balance']},
 {ar:'المتبقي للدفع',fr:'Reste à payer',en:'Remaining to pay',v:['المتبقي للدفع','الباقي للدفع','Reste à payer','Reste a payer','Remaining to pay']},
 {ar:'إجمالي الدين',fr:'Solde dû total',en:'Total debt',v:['إجمالي الدين','الدين الإجمالي','Solde dû total','Solde du total','Total debt']},
 {ar:'الطابع',fr:'Timbre',en:'Stamp',v:['الطابع','حق الطابع','Timbre','Stamp','Stamp duty']},
 {ar:'المبلغ كتابةً',fr:'Montant en lettres',en:'Amount in words',v:['المبلغ كتابةً','المبلغ بالحروف','Montant en lettres','Amount in words']},
 {ar:'طريقة الدفع',fr:'Mode de paiement',en:'Payment method',v:['طريقة الدفع','Mode de paiement','Mode Règlement','Mode de règlement','Payment method','Settlement mode']},
 {ar:'نقداً',fr:'Espèces',en:'Cash',v:['نقداً','نقدا','نقدي','Espèces','Especes','Cash']},
 {ar:'آجل',fr:'Crédit',en:'Credit',v:['آجل','دين','Crédit','Credit']},
 {ar:'بطاقة',fr:'Carte',en:'Card',v:['بطاقة','Carte','Card']},
 {ar:'تحويل',fr:'Virement',en:'Transfer',v:['تحويل','Virement','Transfer','Bank transfer']},
 {ar:'فاتورة',fr:'Facture',en:'Invoice',v:['فاتورة','Facture','Invoice']},
 {ar:'فاتورة بيع',fr:'Facture de vente',en:'Sales invoice',v:['فاتورة بيع','Facture de vente','Sales invoice']},
 {ar:'فاتورة شراء',fr:"Facture d’achat",en:'Purchase invoice',v:['فاتورة شراء',"Facture d’achat","Facture d'achat",'Purchase invoice']},
 {ar:'فاتورة مبدئية',fr:'Facture pro forma',en:'Pro-forma invoice',v:['فاتورة مبدئية','الفاتورة المبدئية','Facture pro forma','Pro-forma invoice','Proforma invoice']},
 {ar:'العنوان',fr:'Adresse',en:'Address',v:['العنوان','Adresse','Address']},
 {ar:'الهاتف',fr:'Tél',en:'Phone',v:['الهاتف','هاتف','Tél','Tel','Téléphone','Phone']},
 {ar:'توقيع وختم',fr:'Signature et cachet',en:'Signature and stamp',v:['توقيع وختم','الختم والتوقيع','Cachet et Signature du fournisseur','Signature et cachet','Signature and stamp']},
 {ar:'رقم الفاتورة',fr:'N° facture',en:'Invoice No.',v:['رقم الفاتورة','N° facture','No facture','Invoice No.','Invoice number']}
];
const lookup={ar:new Map(),fr:new Map(),en:new Map()};
const norm=s=>String(s||'').replace(/\u00a0/g,' ').replace(/\s+/g,' ').trim().replace(/[：:]$/,'').trim().toLocaleLowerCase();
for(const c of C)for(const v of c.v)for(const l of LANGS)lookup[l].set(norm(v),c[l]);
function productCells(doc){const skip=new Set();doc.querySelectorAll('table').forEach(table=>{let idx=-1;const row=[...table.querySelectorAll('tr')].find(r=>r.querySelector('th'));if(row){[...row.querySelectorAll('th')].some((th,i)=>{const n=norm(th.textContent);if(/المنتج|الوصف|article|désignation|designation|product|description/.test(n)){idx=i;return true}return false})}if(idx>=0)table.querySelectorAll('tbody tr').forEach(tr=>{const td=tr.querySelectorAll('td')[idx];if(td)skip.add(td)});});return skip}
function localize(h,l){h=String(h||'');const d=l==='ar'?'rtl':'ltr';try{const doc=new DOMParser().parseFromString(h,'text/html');doc.documentElement.lang=l;doc.documentElement.dir=d;const skip=productCells(doc);const walker=doc.createTreeWalker(doc.body,NodeFilter.SHOW_TEXT);let n;while(n=walker.nextNode()){if(!n.parentElement||[...skip].some(x=>x===n.parentElement||x.contains(n)))continue;if(n.parentElement.closest('[data-product-name],.product-name,.item-name'))continue;const raw=n.nodeValue,trim=raw.trim();if(!trim)continue;const colon=/[:：]\s*$/.test(trim);const key=norm(trim);let val=lookup[l].get(key);if(!val){let m=trim.match(/^(TVA|Tax|الضريبة)\s*(\d+(?:[.,]\d+)?%)$/i);if(m)val=(l==='ar'?'الضريبة':l==='fr'?'TVA':'Tax')+' '+m[2]}if(val){const lead=raw.match(/^\s*/)?.[0]||'',tail=raw.match(/\s*$/)?.[0]||'';n.nodeValue=lead+val+(colon?':':'')+tail}}return '<!DOCTYPE html>\n'+doc.documentElement.outerHTML}catch(_){return h.replace(/<html\b([^>]*)>/i,(m,a)=>`<html${a.replace(/\s(?:lang|dir)=["'][^"']*["']/gi,'')} lang="${l}" dir="${d}">`)}}
function close(){if(active){active.remove();active=null}}
const PAPER={A4:{label:'A4',width:210,height:297},A5:{label:'A5',width:148,height:210},R80:{label:'80mm',width:80,height:297},R58:{label:'58mm',width:58,height:297}};
const PC={ar:{paper:'الورق',printer:'الطابعة',copies:'النسخ',color:'ألوان',test:'اختبار',defaultPrinter:'الطابعة الافتراضية',testTitle:'اختبار طباعة NANO POS',testOk:'تم إرسال صفحة الاختبار للطابعة',printFail:'تعذر إرسال المستند للطابعة'},fr:{paper:'Papier',printer:'Imprimante',copies:'Copies',color:'Couleur',test:'Test',defaultPrinter:'Imprimante par défaut',testTitle:'Test d’impression NANO POS',testOk:'Page de test envoyée à l’imprimante',printFail:"Impossible d’envoyer le document"},en:{paper:'Paper',printer:'Printer',copies:'Copies',color:'Color',test:'Test',defaultPrinter:'Default printer',testTitle:'NANO POS print test',testOk:'Test page sent to printer',printFail:'Could not send document to printer'}};
const PF={ar:{template:'القالب',footer:'تذييل',classic:'كلاسيكي',modern:'عصري',compact:'مضغوط'},fr:{template:'Modèle',footer:'Pied de page',classic:'Classique',modern:'Moderne',compact:'Compact'},en:{template:'Template',footer:'Footer',classic:'Classic',modern:'Modern',compact:'Compact'}};
const prefKey=k=>'nano.print.center.v135.'+k;
function readPref(kind){try{return{paper:localStorage.getItem(prefKey(kind+'.paper'))||localStorage.getItem('nano.print.center.v134.'+kind+'.paper')||(kind==='r'?'R80':'A4'),printer:localStorage.getItem(prefKey(kind+'.printer'))||'',copies:Math.max(1,Math.min(9,Number(localStorage.getItem(prefKey(kind+'.copies')))||1)),color:localStorage.getItem(prefKey(kind+'.color'))!=='false',template:localStorage.getItem(prefKey(kind+'.template'))||'classic',footer:localStorage.getItem(prefKey(kind+'.footer'))||''}}catch{return{paper:kind==='r'?'R80':'A4',printer:'',copies:1,color:true,template:'classic',footer:''}}}
function savePref(kind,p){try{localStorage.setItem(prefKey(kind+'.paper'),p.paper);localStorage.setItem(prefKey(kind+'.printer'),p.printer||'');localStorage.setItem(prefKey(kind+'.copies'),String(p.copies));localStorage.setItem(prefKey(kind+'.color'),String(!!p.color));localStorage.setItem(prefKey(kind+'.template'),p.template||'classic');localStorage.setItem(prefKey(kind+'.footer'),String(p.footer||'').slice(0,120))}catch{}}
function applyPaper(h,paper,color){const p=PAPER[paper]||PAPER.A4,css=`<style data-nano-print-center>@page{size:${p.width}mm ${p.height}mm;margin:0}html{background:#e2e8f0}body{max-width:${p.width}mm;margin:0 auto!important;box-sizing:border-box}${color?'':'html,body{filter:grayscale(1)!important}'}</style>`;return /<\/head>/i.test(h)?h.replace(/<\/head>/i,css+'</head>'):css+h}
function decorate(h,l,paper,color,template='classic',footer=''){
 h=localize(h,l);try{if(window.NanoCurrency?.decorateHtml)h=window.NanoCurrency.decorateHtml(h,l)}catch{}
 h=applyPaper(h,paper,color);
 const presets={classic:'',modern:'body{font-family:Arial,sans-serif!important}table{border-collapse:collapse!important}thead{background:#e6f5f2!important}th{border-bottom:2px solid #0f766e!important}.header,.invoice-header{border-bottom:2px solid #0f766e!important}',compact:'body{font-size:10px!important;line-height:1.26!important}td,th{padding:3px 4px!important}h1,h2{margin:4px 0!important}'};
 const css='<style data-nano-v135-template>'+((presets[template]||''))+'</style>';
 h=/<\/head>/i.test(h)?h.replace(/<\/head>/i,css+'</head>'):css+h;
 if(footer){const safe=esc(footer).slice(0,500),note='<footer data-nano-v135-footer style="font:11px Arial;text-align:center;border-top:1px solid #bbb;padding:8px;margin-top:12px">'+safe+'</footer>';h=/<\/body>/i.test(h)?h.replace(/<\/body>/i,note+'</body>'):h+note}
 return h;
}
function show({html,kind='i',language,onLanguageChange,print,pdf}){
  const q=ui(),ex=PC[window.currentLanguage]||PC.ar,prefs=readPref(kind);let L=lang(html,language),raw=String(html||''),t=0;close();
  const o=document.createElement('div');active=o;o.id='nano-document-print-preview';o.setAttribute('role','dialog');o.setAttribute('aria-modal','true');o.style.cssText='position:fixed;inset:0;z-index:2147483646;background:rgba(15,23,42,.90);display:flex;flex-direction:column;padding:14px;gap:10px;direction:rtl';
  const b=document.createElement('div');b.style.cssText='display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:white;border-radius:14px;padding:10px 12px;font:600 13px Arial;color:#0f172a;box-shadow:0 8px 30px rgba(0,0,0,.18)';
  const heading=document.createElement('strong');heading.textContent=q[kind]||q.i;heading.style.cssText='min-width:150px;margin-inline-end:auto';const status=document.createElement('span');status.style.cssText='font:12px Arial;color:#b91c1c;max-width:260px';b.append(heading,status);
  const mkLabel=(txt,el)=>{const w=document.createElement('label');w.style.cssText='display:flex;align-items:center;gap:5px;white-space:nowrap';const s=document.createElement('span');s.textContent=txt+':';w.append(s,el);return w};
  const styleCtl=el=>{el.style.cssText='border:1px solid #cbd5e1;border-radius:8px;padding:7px 9px;background:#fff;color:#0f172a;font:600 12px Arial';return el};
  const langSel=styleCtl(document.createElement('select'));[['ar','العربية'],['fr','Français'],['en','English']].forEach(([v,n])=>langSel.add(new Option(n,v)));langSel.value=L;b.append(mkLabel(q.l,langSel));
  const paperSel=styleCtl(document.createElement('select'));Object.entries(PAPER).forEach(([v,p])=>paperSel.add(new Option(p.label,v)));paperSel.value=PAPER[prefs.paper]?prefs.paper:(kind==='r'?'R80':'A4');b.append(mkLabel(ex.paper,paperSel));
  const printerSel=styleCtl(document.createElement('select'));printerSel.style.minWidth='155px';printerSel.add(new Option(ex.defaultPrinter,''));b.append(mkLabel(ex.printer,printerSel));
  const copies=styleCtl(document.createElement('input'));copies.type='number';copies.min='1';copies.max='9';copies.value=String(prefs.copies);copies.style.width='55px';b.append(mkLabel(ex.copies,copies));
  const color=document.createElement('input');color.type='checkbox';color.checked=prefs.color;b.append(mkLabel(ex.color,color));
  const styleText=PF[window.currentLanguage]||PF.ar;
  const designSel=styleCtl(document.createElement('select'));
  [['classic',styleText.classic],['modern',styleText.modern],['compact',styleText.compact]].forEach(([key,label])=>designSel.add(new Option(label,key)));
  designSel.value=prefs.template;b.append(mkLabel(styleText.template,designSel));
  const footerInput=styleCtl(document.createElement('input'));footerInput.type='text';footerInput.maxLength=120;footerInput.value=prefs.footer;footerInput.placeholder=styleText.footer;footerInput.style.width='145px';b.append(mkLabel(styleText.footer,footerInput));
  const frame=document.createElement('iframe');frame.title='معاينة المستند';frame.setAttribute('sandbox','allow-same-origin');frame.style.cssText='flex:1;min-height:0;width:100%;border:0;border-radius:14px;background:#e2e8f0';
  const button=(label,handler,bg)=>{const x=document.createElement('button');x.type='button';x.textContent=label;x.style.cssText=`border:0;border-radius:9px;padding:8px 13px;cursor:pointer;color:#fff;background:${bg};font:700 12px Arial`;x.addEventListener('click',handler);return x};
  const state=()=>({paper:paperSel.value,printer:printerSel.value,copies:Math.max(1,Math.min(9,Number(copies.value)||1)),color:!!color.checked,template:designSel.value,footer:footerInput.value.slice(0,120)});
  const refreshFrame=()=>{const p=state();savePref(kind,p);frame.srcdoc=decorate(raw,L,p.paper,p.color,p.template,p.footer)};
  const disable=v=>{b.querySelectorAll('button,select,input').forEach(x=>x.disabled=!!v)};
  const run=async fn=>{disable(true);status.textContent='';try{await fn();close()}catch(e){status.textContent=e?.message||ex.printFail;disable(false)}};
  langSel.addEventListener('change',async()=>{const wanted=langSel.value,previous=L,token=++t;disable(true);status.textContent=q.u;try{if(typeof onLanguageChange==='function'){const updated=await onLanguageChange(wanted);if(token!==t||active!==o)return;if(typeof updated!=='string'||!updated.trim())throw new Error(q.e);raw=updated}L=wanted;refreshFrame();status.textContent=''}catch(e){langSel.value=previous;status.textContent=e?.message||q.e}finally{if(active===o)disable(false)}});
  paperSel.addEventListener('change',refreshFrame);copies.addEventListener('change',()=>{const p=state();copies.value=String(p.copies);savePref(kind,p)});color.addEventListener('change',refreshFrame);designSel.addEventListener('change',refreshFrame);footerInput.addEventListener('change',refreshFrame);printerSel.addEventListener('change',()=>savePref(kind,state()));
  const nativePrint=async()=>{const p=state(),H=decorate(raw,L,p.paper,p.color),size=PAPER[p.paper]||PAPER.A4;if(window.nanoNative?.printHtml){const r=await window.nanoNative.printHtml({htmlContent:H,deviceName:p.printer,pageSize:{width:size.width,height:size.height},copies:p.copies,color:p.color});if(!r?.success)throw new Error(r?.error||ex.printFail);return r}if(typeof print==='function')return print(L,H);throw new Error(ex.printFail)};
  const nativePdf=async()=>{const p=state(),H=decorate(raw,L,p.paper,p.color),size=PAPER[p.paper]||PAPER.A4;if(window.nanoNative?.exportPdf){const names={i:'nano-pos-invoice.pdf',r:'nano-pos-receipt.pdf',p:'nano-pos-proforma.pdf'};const r=await window.nanoNative.exportPdf({htmlContent:H,pageSize:{width:size.width,height:size.height},defaultFileName:names[kind]||'nano-pos-document.pdf'});if(r?.canceled)return;if(!r?.success)throw new Error(r?.error||q.e);return r}if(typeof pdf==='function')return pdf(L,H)};
  const testPrint=async()=>{const p=state(),size=PAPER[p.paper]||PAPER.A4;if(!window.nanoNative?.printHtml)throw new Error(ex.printFail);const now=new Date().toLocaleString(L==='ar'?'ar-DZ':L==='fr'?'fr-FR':'en-US');const sample=`<!doctype html><html lang="${L}" dir="${L==='ar'?'rtl':'ltr'}"><meta charset="utf-8"><style>@page{size:${size.width}mm ${size.height}mm;margin:10mm}body{font-family:Arial;padding:10mm}h1{font-size:22px}.box{border:2px solid #111;border-radius:12px;padding:16px}.big{font-size:28px;font-weight:800}</style><body><div class="box"><h1>${ex.testTitle}</h1><p>NANO POS v1.0.35</p><p>${now}</p><p class="big">${window.NanoCurrency?.formatCurrency?.(1250.5,L)||'1250.50 DA'}</p></div></body></html>`;const r=await window.nanoNative.printHtml({htmlContent:sample,deviceName:p.printer,pageSize:{width:size.width,height:size.height},copies:1,color:p.color});if(!r?.success)throw new Error(r?.error||ex.printFail);status.style.color='#059669';status.textContent=ex.testOk;setTimeout(()=>{if(active===o){status.textContent='';status.style.color='#b91c1c'}},2500)};
  b.append(button(q.x,()=>run(nativePrint),'#059669'));if(pdf||window.nanoNative?.exportPdf)b.append(button(q.d,()=>run(nativePdf),'#2563eb'));if(window.nanoNative?.printHtml)b.append(button(ex.test,()=>{disable(true);testPrint().catch(e=>status.textContent=e?.message||ex.printFail).finally(()=>disable(false))},'#7c3aed'));b.append(button(q.c,close,'#475569'));
  o.append(b,frame);document.body.appendChild(o);refreshFrame();
  (async()=>{try{if(window.NanoCurrency?.load)await window.NanoCurrency.load();refreshFrame();const list=await window.nanoNative?.getPrinters?.();if(Array.isArray(list)){for(const p of list)printerSel.add(new Option((p.displayName||p.name)+(p.isDefault?' ★':''),p.name));printerSel.value=[...printerSel.options].some(x=>x.value===prefs.printer)?prefs.printer:''}}catch{}})();
  return o;
}
window.NanoDocumentPreview={show};
async function W(fn,k,a){const x=[...a],m=x[3]??'print';if(m!=='print')return fn.apply(window,x);x[3]='html';let h=await fn.apply(window,x),l=LANGS.includes(x[4])?x[4]:lang(h,x[4]);return show({html:h,kind:k,language:l,onLanguageChange:async n=>localize(await fn.call(window,a[0],a[1],a[2],'html',n),n),print:async n=>fn.call(window,a[0],a[1],a[2],'print',n),pdf:async n=>fn.call(window,a[0],a[1],a[2],'pdf',n)})}
if(typeof I==='function'){const n=(...a)=>W(I,'i',a);window.printInvoice=n;try{printInvoice=n}catch(_){}}
if(typeof R==='function'){const n=(...a)=>W(R,'r',a);window.printReceipt=n;try{printReceipt=n}catch(_){}}
async function cap(id,l){if(typeof P!=='function')throw Error('Pro-forma unavailable');let z=null,O=window.NanoDocumentPreview.show;window.NanoDocumentPreview.show=x=>(z=x,null);try{await P.call(window,id,l)}finally{window.NanoDocumentPreview.show=O}if(!z?.html)throw Error(ui().e);z.html=localize(z.html,l||z.language||lang(z.html));return z}
if(typeof P==='function'){const n=async(id,l=null)=>{const z=await cap(id,l),L=l||z.language||lang(z.html);return show({html:z.html,kind:'p',language:L,onLanguageChange:async x=>(await cap(id,x)).html,print:async x=>{const d=await cap(id,x);return d.print?.(x,d.html)},pdf:async x=>{const d=await cap(id,x);return d.pdf?.(x,d.html)}})};window.printProforma=n;try{printProforma=n}catch(_){}}
})();
