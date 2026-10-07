/* NANO POS v1.0.33 multilingual print controller */
(()=>{'use strict';
if(window.__nanoPrintLangV133)return;window.__nanoPrintLangV133=1;
const I=window.printInvoice,R=window.printReceipt,P=window.printProforma;
let A=null;
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
function close(){if(A){A.remove();A=null}}
function show({html,kind='i',language,onLanguageChange,print,pdf}){const q=ui();let L=LANGS.includes(language)?language:lang(html,language),H=localize(html,L),t=0;close();const o=document.createElement('div');A=o;o.id='nano-document-print-preview';o.style.cssText='position:fixed;inset:0;z-index:2147483646;background:#0f172ade;display:flex;flex-direction:column;padding:14px;gap:10px;direction:rtl';const b=document.createElement('div');b.style.cssText='display:flex;align-items:center;gap:9px;flex-wrap:wrap;background:#fff;border-radius:12px;padding:11px 14px;font:600 14px Arial;color:#0f172a';const hd=document.createElement('strong');hd.textContent=q[kind]||q.i;hd.style.cssText='flex:1;min-width:170px';const st=document.createElement('span');st.style.cssText='font:12px Arial;color:#b91c1c';const f=document.createElement('iframe');f.setAttribute('sandbox','allow-same-origin');f.style.cssText='flex:1;min-height:0;width:100%;border:0;border-radius:12px;background:white';const B=(x,fn,c)=>{const z=document.createElement('button');z.type='button';z.textContent=x;z.style.cssText=`border:0;border-radius:8px;padding:9px 14px;color:#fff;background:${c};font:600 14px Arial;cursor:pointer`;z.onclick=fn;return z};b.append(hd,st);const lab=document.createElement('label');lab.style.cssText='display:flex;align-items:center;gap:6px;white-space:nowrap';lab.innerHTML=`<span>${esc(q.l)}:</span>`;const sel=document.createElement('select');sel.style.cssText='border:1px solid #94a3b8;border-radius:8px;padding:8px 10px;background:#fff;font:600 14px Arial';[['ar','العربية'],['fr','Français'],['en','English']].forEach(([v,n])=>sel.add(new Option(n,v)));sel.value=L;sel.onchange=async()=>{const n=sel.value,p=L,k=++t;if(typeof onLanguageChange!=='function'){L=n;H=localize(H,n);f.srcdoc=H;return}sel.disabled=1;b.querySelectorAll('button').forEach(x=>x.disabled=1);st.textContent=q.u;try{let x=await onLanguageChange(n);if(k!==t||A!==o)return;if(typeof x!=='string'||!x.trim())throw Error(q.e);H=localize(x,n);f.srcdoc=H;L=n;st.textContent=''}catch(e){sel.value=p;st.textContent=e?.message||q.e}finally{if(A===o){sel.disabled=0;b.querySelectorAll('button').forEach(x=>x.disabled=0)}}};lab.append(sel);b.append(lab);const run=async fn=>{b.querySelectorAll('button').forEach(x=>x.disabled=1);st.textContent='';try{await fn(L,H);close()}catch(e){st.textContent=e?.message||q.e;b.querySelectorAll('button').forEach(x=>x.disabled=0)}};b.append(B(q.x,()=>run(print),'#059669'));if(pdf)b.append(B(q.d,()=>run(pdf),'#2563eb'));b.append(B(q.c,close,'#475569'));o.append(b,f);document.body.append(o);f.srcdoc=H;return o}
window.NanoDocumentPreview={show};
async function W(fn,k,a){const x=[...a],m=x[3]??'print';if(m!=='print')return fn.apply(window,x);x[3]='html';let h=await fn.apply(window,x),l=LANGS.includes(x[4])?x[4]:lang(h,x[4]);return show({html:h,kind:k,language:l,onLanguageChange:async n=>localize(await fn.call(window,a[0],a[1],a[2],'html',n),n),print:async n=>fn.call(window,a[0],a[1],a[2],'print',n),pdf:async n=>fn.call(window,a[0],a[1],a[2],'pdf',n)})}
if(typeof I==='function'){const n=(...a)=>W(I,'i',a);window.printInvoice=n;try{printInvoice=n}catch(_){}}
if(typeof R==='function'){const n=(...a)=>W(R,'r',a);window.printReceipt=n;try{printReceipt=n}catch(_){}}
async function cap(id,l){if(typeof P!=='function')throw Error('Pro-forma unavailable');let z=null,O=window.NanoDocumentPreview.show;window.NanoDocumentPreview.show=x=>(z=x,null);try{await P.call(window,id,l)}finally{window.NanoDocumentPreview.show=O}if(!z?.html)throw Error(ui().e);z.html=localize(z.html,l||z.language||lang(z.html));return z}
if(typeof P==='function'){const n=async(id,l=null)=>{const z=await cap(id,l),L=l||z.language||lang(z.html);return show({html:z.html,kind:'p',language:L,onLanguageChange:async x=>(await cap(id,x)).html,print:async x=>{const d=await cap(id,x);return d.print?.(x,d.html)},pdf:async x=>{const d=await cap(id,x);return d.pdf?.(x,d.html)}})};window.printProforma=n;try{printProforma=n}catch(_){}}
})();
