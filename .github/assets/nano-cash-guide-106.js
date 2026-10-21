/* NANO POS v1.0.106 — cashier-friendly change; single full cash payment ONLY. */
(function(root){
 'use strict';
 const d=root.document,calculator=root.NANO_CASH_PLAN_106;
 if(!d||!calculator||root.NANO_CASH_GUIDE_106)return;
 const by=id=>d.getElementById(id);
 const modal=by('checkoutModal'),anchor=by('nanoCheckoutChoice104');
 if(!modal||!anchor)return;
 const strings={
  ar:{title:'المبلغ الذي قدمه الزبون',change:'الصرف الذي يُرجع للزبون',show:'طريقة إرجاع الصرف',empty:'أدخل المبلغ النقدي الذي سلّمه الزبون.',wrong:'مبلغ نقدي غير صالح؛ استعمل رقمًا بخانتين عشريتين كحد أقصى.',short:'المبلغ المقدَّم أقل من ثمن الفاتورة.',cashOnly:'يظهر حساب الصرف عند اختيار الدفع النقدي الكامل.',fraction:'باقي السنتيمات (لا يدخل في توزيع فئات الدينار)',dinar:'د.ج'},
  fr:{title:'Montant remis par le client',change:'Monnaie à rendre',show:'Répartition conseillée',empty:'Saisissez le montant en espèces.',wrong:'Montant invalide (2 décimales max).',short:'Montant remis insuffisant.',cashOnly:'La monnaie est calculée seulement pour le paiement total en espèces.',fraction:'Centimes restants hors coupures DZD',dinar:'DZD'},
  en:{title:'Cash handed by customer',change:'Change due',show:'Suggested denominations',empty:'Enter the cash tendered.',wrong:'Invalid cash amount (max 2 decimals).',short:'Cash tendered is less than the invoice total.',cashOnly:'Change is calculated only for a full cash sale.',fraction:'Remaining centimes not covered by DZD denominations',dinar:'DZD'}
 };
 const t=()=>{const x=String(root.currentLanguage||d.documentElement.lang||'ar').slice(0,2);return strings[x]||strings.ar;};
 const panel=d.createElement('section');panel.id='nanoCashGuide106';panel.hidden=true;
 panel.style.cssText='padding:12px;border:1px solid #93c5fd;border-radius:12px;background:#eff6ff;margin:12px 0;direction:inherit;';
 const label=d.createElement('label');label.htmlFor='nanoCashTendered106';label.style.cssText='font-weight:800;font-size:13px;display:block;margin-bottom:6px';
 const tender=d.createElement('input');tender.id='nanoCashTendered106';tender.type='number';tender.min='0';tender.step='0.01';tender.inputMode='decimal';tender.autocomplete='off';tender.placeholder='0.00';
 tender.style.cssText='width:100%;font-size:19px;font-weight:800;padding:10px;border:1px solid #94a3b8;border-radius:9px;color:#0f172a';
 const heading=d.createElement('p');heading.style.cssText='font-size:13px;margin:8px 0 4px';
 const number=d.createElement('strong');number.id='nanoCashChange106';number.style.cssText='font-size:24px;color:#065f46;display:block';
 const breakdown=d.createElement('div');breakdown.id='nanoCashBreakdown106';breakdown.style.cssText='display:flex;gap:6px;flex-wrap:wrap;margin-top:10px';
 const message=d.createElement('p');message.id='nanoCashWarning106';message.style.cssText='font-size:12px;margin-top:7px';message.setAttribute('role','status');
 panel.append(label,tender,heading,number,breakdown,message);
 anchor.insertAdjacentElement('afterend',panel);
 const parseTotal=()=>{
   const raw=String(by('checkoutTotalUI')?.textContent||'').replace(/[٠-٩]/g,x=>String(x.charCodeAt(0)-1632)).replace(/[۰-۹]/g,x=>String(x.charCodeAt(0)-1776));
   const m=raw.match(/\d+(?:[,.]\d{1,2})?/);return m?calculator.cents(m[0]):null;
 };
 const paid=()=>calculator.cents(by('checkoutPaidAmount')?.value||'0');
 const eligible=()=>{
   const total=parseTotal(),value=paid();
   return !modal.classList.contains('hidden')&&by('checkoutPaymentMethod')?.value==='cash'&&
     total!==null&&value===total;
 };
 function render(){
   const tr=t();
   label.textContent=tr.title+' ('+tr.dinar+')';heading.textContent=tr.change;
   panel.hidden=!eligible();
   if(panel.hidden){return;}
   breakdown.replaceChildren();
   const raw=tender.value;
   if(!raw.trim()){number.textContent='—';message.textContent=tr.empty;return;}
   const total=parseTotal();
   const result=calculator.plan(calculator.format(total),raw);
   if(!result.ok){
     number.textContent='—';
     message.textContent=result.code==='cash_insufficient'?tr.short:tr.wrong;
     message.style.color='#b91c1c';
     tender.setAttribute('aria-invalid','true');return;
   }
   tender.setAttribute('aria-invalid','false');
   number.textContent=calculator.format(result.changeCents)+' '+tr.dinar;
   message.textContent=tr.show+':';
   message.style.color='#0369a1';
   for(const item of result.pieces){
     const chip=d.createElement('span');
     chip.style.cssText='background:white;border:1px solid #bfdbfe;border-radius:8px;padding:6px 9px;font-weight:800;font-size:13px';
     chip.textContent=item.count+' × '+item.denomination+' '+tr.dinar;
     breakdown.append(chip);
   }
   if(result.centimes){
     const small=d.createElement('small');
     small.textContent=tr.fraction+': '+String(result.centimes).padStart(2,'0');
     breakdown.append(small);
   }
 }
 const bridge=root.__browserElectron?.ipcRenderer;
 if(bridge&&typeof bridge.invoke==='function'){
   const invoke=bridge.invoke.bind(bridge);
   bridge.invoke=function(channel,...args){
     if(channel==='process-sale'&&args[0]&&!args[0].editSaleId){
       const payload=args[0],checkout=payload.checkout||{};
       const total=calculator.cents(checkout.total),received=calculator.cents(checkout.paidAmount);
       const fullCash=checkout.paymentMethod==='cash'&&total!==null&&received===total;
       if(fullCash){
         const calculated=calculator.plan(checkout.total,tender.value);
         if(!calculated.ok){
           message.textContent=calculated.code==='cash_insufficient'?t().short:!tender.value?t().empty:t().wrong;
           message.style.color='#b91c1c';
           tender.focus();
           return Promise.resolve({success:false,error:calculated.code});
         }
         args[0]={...payload,checkout:{...checkout,
           cashTenderedAmount:calculator.format(calculated.tenderCents)}};
       }else if('cashTenderedAmount' in checkout){
         const {cashTenderedAmount,...rest}=checkout;
         args[0]={...payload,checkout:rest};
       }
     }
     return invoke(channel,...args);
   };
 }
 const statusFields=['checkoutPaidAmount','checkoutPaymentMethod'];
 for(const field of statusFields)by(field)?.addEventListener(field==='checkoutPaymentMethod'?'change':'input',render);
 tender.addEventListener('input',render);
 let lastShown=false;
 function onVisible(){
   const shown=!modal.classList.contains('hidden');
   if(shown&&!lastShown){tender.value='';render();}
   if(!shown&&lastShown){tender.value='';breakdown.replaceChildren();}
   lastShown=shown;
   if(shown)render();
 }
 if(root.MutationObserver){
   new root.MutationObserver(onVisible).observe(modal,{attributes:true,attributeFilter:['class']});
   const amount=by('checkoutTotalUI');
   if(amount)new root.MutationObserver(render).observe(amount,{characterData:true,childList:true,subtree:true});
 }
 onVisible();
 root.NANO_CASH_GUIDE_106=Object.freeze({render,panel});
})(typeof window!=='undefined'?window:globalThis);
