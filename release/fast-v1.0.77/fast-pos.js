/* NANO POS v1.0.77: fast POS utilities. Preserve original sales, barcode and accounting handlers. */
(function(win){
'use strict';
const d=win.document;if(!d||win.NANO_FAST_POS_177)return;win.NANO_FAST_POS_177=true;
const $=id=>d.getElementById(id);
const messages={
 ar:{scan:'باركود',free:'منتج حر',qty:'تعديل الكمية',split:'نقد + كريدي',cash:'المبلغ النقدي',debt:'المتبقي على الزبون',splitOff:'إيقاف التقسيم',customer:'اختر زبونًا أولًا لتسجيل الجزء المتبقي كدين.',invalid:'أدخل مبلغًا نقديًا صحيحًا بين الصفر والإجمالي.',cost:'المدفوع نقدًا',help:'F8 منتج حر · Alt+B باركود · Alt+Q كمية · F1 دفع',empty:'أضف منتجًا إلى السلة أولًا.',warning:'الجزء غير المدفوع يسجل دينًا باسم الزبون المحدد.'},
 fr:{scan:'Code-barres',free:'Produit libre',qty:'Modifier quantité',split:'Espèces + crédit',cash:'Espèces reçues',debt:'Reste client',splitOff:'Annuler',customer:'Sélectionnez un client pour enregistrer le solde à crédit.',invalid:'Montant espèces invalide (0 à total).',cost:'Paiement en espèces',help:'F8 produit libre · Alt+B scanner · Alt+Q quantité · F1 payer',empty:'Ajoutez un article au panier.',warning:'Le solde non payé est une dette du client sélectionné.'},
 en:{scan:'Barcode',free:'Free product',qty:'Edit quantity',split:'Cash + credit',cash:'Cash paid',debt:'Customer debt',splitOff:'Disable split',customer:'Select a customer to record the unpaid balance as credit.',invalid:'Cash amount must be between zero and total.',cost:'Cash payment',help:'F8 free product · Alt+B barcode · Alt+Q quantity · F1 checkout',empty:'Add a product to the cart first.',warning:'Unpaid balance is recorded as debt for the selected customer.'}
};
const txt=()=>{const l=String(win.currentLanguage||d.documentElement.lang||'ar').slice(0,2);return messages[l]||messages.ar};
const notify=(s)=>typeof win.showToast==='function'?win.showToast(s,'warning'):win.alert?.(s);
const price=(v)=>{const s=String(v??'').trim().replace(/[٠-٩]/g,c=>String(c.charCodeAt(0)-1632)).replace(/[۰-۹]/g,c=>String(c.charCodeAt(0)-1776)).replace(/\s/g,'');const x=Number(s.replace(',','.'));return s!==''&&Number.isFinite(x)?x:NaN};
const money=v=>(v/100).toFixed(2);
const cents=v=>Math.round(v*100);
function visible(el){if(!el)return false;for(let p=el;p&&p.nodeType===1;p=p.parentElement){if(p.classList?.contains('hidden')||p.getAttribute?.('aria-hidden')==='true')return false;}return true;}
function salesOn(){return visible($('salesSection'))}
function modalShown(){return [...d.querySelectorAll('[id$="Modal"]')].some(el=>visible(el))}
const btn=(label,title)=>{const b=d.createElement('button');b.type='button';b.className='nano-fast-action';b.textContent=label;b.title=title;return b};
function scanFocus(){const input=$('posBarcodeScanInput');if(!input||!salesOn())return;input.focus({preventScroll:true});input.select();}
function freeProduct(){if(salesOn()&&typeof win.openCustomProductModal==='function')win.openCustomProductModal();}
function quantityButton(){const items=$('cartItemsList');const button=items?.querySelector('button[onclick*="promptItemQty("]');if(button)button.click();else notify(txt().empty);}
function initBar(){
 const bar=$('posToolbar');if(!bar||$('nanoFastBar'))return;
 const box=d.createElement('div');box.id='nanoFastBar';box.className='nano-fast-bar';
 const a=btn(txt().scan,'Alt+B'),b=btn(txt().free,'F8'),c=btn(txt().qty,'Alt+Q');
 a.id='nanoFastScan';b.id='nanoFastFree';c.id='nanoFastQty';
 a.addEventListener('click',scanFocus);b.addEventListener('click',freeProduct);c.addEventListener('click',quantityButton);
 box.append(a,b,c);bar.append(box);
}
// Replace the old prompt only when the user clicks a cart QTY control; retain existing
// setCartItemQty stock checks and batch allocation.
function inlineQuantity(event){
 const target=event.target?.closest?.('button[onclick*="promptItemQty("]');
 if(!target||!$('cartItemsList')?.contains(target)||!salesOn())return;
 const match=String(target.getAttribute('onclick')||'').match(/promptItemQty\(\s*(\d+)\s*\)/);
 if(!match||typeof win.setCartItemQty!=='function')return;
 event.preventDefault();event.stopImmediatePropagation();
 const idx=Number(match[1]);
 const original=String(target.textContent||'').trim().replace(/[^\d.,-]/g,'').replace(',','.');
 const input=d.createElement('input');
 input.type='number';input.className='nano-fast-qty';input.step='any';input.min='0.001';
 input.setAttribute('aria-label',txt().qty);input.value=String(Number(original)||1);
 const anchor=d.createElement('span');anchor.className='nano-fast-qty-anchor';target.replaceWith(anchor);anchor.replaceWith(input);
 let done=false;
 const submit=()=>{if(done)return;done=true;
   const n=price(input.value);
   if(!Number.isFinite(n)||n<=0){notify(txt().invalid);win.updateCartUI?.();return;}
   win.setCartItemQty(idx,n);
 };
 const cancel=()=>{if(done)return;done=true;win.updateCartUI?.()};
 input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();submit();}else if(e.key==='Escape'){e.preventDefault();cancel();}});
 input.addEventListener('blur',submit,{once:true});input.focus();input.select();
}
function modalTotalCents(){
 const element=$('checkoutTotalUI');let raw=String(element?.textContent||'');
 const m=raw.match(/[\d٠-٩۰-۹]+(?:[.,][\d٠-٩۰-۹]+)?/);
 const n=price(m?.[0]||'');
 return Number.isFinite(n)&&n>=0?cents(n):NaN;
}
let splitActive=false;let splitPanel=null;
function cashInput(){return $('nanoSplitCash')}
function debtNode(){return $('nanoSplitDebt')}
function paidInput(){return $('checkoutPaidAmount')}
function applyCash(){
 if(!splitActive||!cashInput())return false;
 const total=modalTotalCents(),cash=price(cashInput().value);
 const valid=Number.isFinite(total)&&Number.isFinite(cash)&&cash>=0&&cents(cash)<=total;
 if(!valid){cashInput().setAttribute('aria-invalid','true');if(debtNode())debtNode().textContent='—';return false;}
 cashInput().removeAttribute('aria-invalid');
 const paid=paidInput();if(!paid)return false;
 paid.value=money(cents(cash));
 paid.dispatchEvent(new Event('input',{bubbles:true}));
 if(typeof win.checkoutCalcChange==='function')win.checkoutCalcChange();
 if(debtNode())debtNode().textContent=money(total-cents(cash));
 return true;
}
function customerSelected(){return String($('posCustomerSelect')?.value||'').trim()!=='';}
function validateSplit(){
 if(!splitActive)return true;
 if(!applyCash()){notify(txt().invalid);cashInput()?.focus();return false;}
 if(cents(price(cashInput().value))<modalTotalCents()&&!customerSelected()){notify(txt().customer);return false;}
 return true;
}
function activateSplit(){
 const t=txt(),section=$('nanoSplitPanel'),toggle=$('nanoSplitToggle'),paid=paidInput();
 if(!section||!toggle||!paid)return;
 if(!splitActive&&!customerSelected()){notify(t.customer);$('posCustomerSearchInput')?.focus();return;}
 splitActive=!splitActive;
 section.hidden=!splitActive;toggle.textContent=splitActive?t.splitOff:t.split;
 const prior=$('nanoSplitOriginalPaid');if(prior)prior.hidden=splitActive;
 if(splitActive){cashInput().value=money(modalTotalCents());applyCash();cashInput().focus();cashInput().select();}
 else {paid.value=money(modalTotalCents());paid.dispatchEvent(new Event('input',{bubbles:true}));win.checkoutCalcChange?.();}
}
function resetSplit(){
 if(!splitPanel)return;
 splitActive=false;splitPanel.hidden=true;
 const toggle=$('nanoSplitToggle');if(toggle)toggle.textContent=txt().split;
 const original=$('nanoSplitOriginalPaid');if(original)original.hidden=false;
}
function setupPayment(){
 const modal=$('checkoutModal'),paid=paidInput();if(!modal||!paid||$('nanoSplitToggle'))return;
 const group=paid.parentElement;
 if(!group)return;group.id='nanoSplitOriginalPaid';
 const section=d.createElement('section');section.className='nano-split-panel';section.id='nanoSplitPanel';section.hidden=true;
 const title=d.createElement('label');title.textContent=txt().cash;title.htmlFor='nanoSplitCash';
 const cash=d.createElement('input');cash.id='nanoSplitCash';cash.type='number';cash.min='0';cash.step='0.01';cash.inputMode='decimal';
 const debtLabel=d.createElement('div');debtLabel.className='nano-split-debt-label';debtLabel.textContent=txt().debt;
 const debt=d.createElement('strong');debt.id='nanoSplitDebt';debt.textContent='0.00';
 const warn=d.createElement('p');warn.textContent=txt().warning;
 section.append(title,cash,debtLabel,debt,warn);
 const toggle=btn(txt().split,txt().split);toggle.id='nanoSplitToggle';toggle.classList.add('nano-split-toggle');toggle.addEventListener('click',activateSplit);
 group.before(toggle);toggle.after(section);splitPanel=section;
 cash.addEventListener('input',applyCash);
 const method=$('checkoutPaymentMethod');
 method?.addEventListener('change',()=>{if(splitActive&&method.value!=='cash')resetSplit();});
 const observer=new MutationObserver(()=>{if(modal.classList.contains('hidden'))resetSplit();});
 observer.observe(modal,{attributes:true,attributeFilter:['class']});
 // Only allow confirmations through the existing native processSale method,
 // which calculates the amount paid and the client debt from the same payload.
 modal.addEventListener('click',e=>{
   const button=e.target?.closest?.('button[onclick]');
   if(!button)return;
   const action=String(button.getAttribute('onclick')||'');
   if(!/\b(?:processSale|processSaleAndPrintReceipt)\s*\(\s*\)/.test(action))return;
   if(!validateSplit()){e.preventDefault();e.stopImmediatePropagation();}
 },true);
 modal.addEventListener('keydown',e=>{if(e.key==='Enter'&&splitActive&&e.target===cash){e.preventDefault();applyCash();}});
}
function hotkeys(e){
 if(!salesOn()||e.repeat||e.ctrlKey||e.metaKey)return;
 if(e.altKey&&!modalShown()){
   const key=e.key.toLowerCase();
   if(key==='b'){e.preventDefault();scanFocus();}
   if(key==='q'){e.preventDefault();quantityButton();}
   if(key==='p'){e.preventDefault();freeProduct();}
 }
}
function restoreBarcodeFocus(){
 const input=$('posBarcodeScanInput');if(!input)return;
 input.addEventListener('keydown',e=>{if(e.key!=='Enter')return;
   // Original barcode scanner processes Enter. Restore focus without ever stealing
   // focus from another input or a modal.
   setTimeout(()=>{if(salesOn()&&!modalShown()&&(d.activeElement===d.body||d.activeElement===input))input.focus({preventScroll:true});},80);
 });
}
function init(){initBar();setupPayment();restoreBarcodeFocus();d.addEventListener('click',inlineQuantity,true);d.addEventListener('keydown',hotkeys,true);}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);