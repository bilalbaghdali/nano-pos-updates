/* NANO POS v1.0.108 — one amount: credit if less, change if more. */
(function(root){
 'use strict';
 const d=root.document,calc=root.NANO_FLEX_CORE_108,notes=root.NANO_CASH_PLAN_106;
 if(!d||!calc||root.NANO_FLEX_108)return;
 const get=id=>d.getElementById(id);
 const modal=get('checkoutModal'),tender=get('nanoTenderAmount108'),hidden=get('checkoutPaidAmount');
 if(!modal||!tender||!hidden)return;
 const language=()=>{const x=String(root.currentLanguage||d.documentElement.lang||'ar').slice(0,2);return ['fr','en'].includes(x)?x:'ar';};
 const translations={
  ar:{debt:'الدين الذي سيُسجل على الزبون',change:'الصرف الذي يجب إرجاعه',paid:'المبلغ المحتسب كدفعة',denoms:'طريقة إرجاع الصرف',customer:'المبلغ لا يغطي الفاتورة. اختر زبونًا أو أضفه لتسجيل الباقي دينًا.',invalid:'أدخل مبلغًا صالحًا دون أرقام سالبة (فاصلتان عشريتان كحد أقصى).',noncash:'المبلغ الزائد يمكن إرجاعه نقدًا فقط. استخدم النقد أو صحح المبلغ.',empty:'أدخل المبلغ المقدم من الزبون.',complete:'الفاتورة مسددة بالكامل',noChange:'لا يوجد صرف لإرجاعه',dzd:'د.ج'},
  fr:{debt:'Dette restante du client',change:'Monnaie à rendre',paid:'Montant appliqué au paiement',denoms:'Coupures conseillées',customer:'Sélectionnez ou ajoutez un client pour enregistrer le solde à crédit.',invalid:'Saisissez un montant valide (2 décimales maximum).',noncash:'Une somme supérieure au total ne peut être rendue en monnaie que pour les espèces.',empty:'Saisissez le montant reçu.',complete:'Facture réglée',noChange:'Aucune monnaie à rendre',dzd:'DZD'},
  en:{debt:'Balance owed by customer',change:'Change to return',paid:'Applied payment',denoms:'Suggested denominations',customer:'Choose or add a customer to record the outstanding balance.',invalid:'Enter a valid nonnegative amount (up to 2 decimals).',noncash:'Change can only be returned on cash payment; correct the amount or choose cash.',empty:'Enter the amount received.',complete:'Invoice paid in full',noChange:'No change due',dzd:'DZD'}
 };
 const t=()=>translations[language()];
 const box=get('nanoFlexibleSummary108');
 let current=null,lastShown=false;
 const total=()=>{
   const value=String(get('checkoutTotalUI')?.textContent||'')
     .replace(/[٠-٩]/g,x=>String(x.charCodeAt(0)-1632))
     .replace(/[۰-۹]/g,x=>String(x.charCodeAt(0)-1776));
   const match=value.match(/\d+(?:[,.]\d{1,2})?/);return match?calc.cents(match[0]):null;
 };
 function isShown(){return !modal.classList.contains('hidden');}
 function issue(code){
   return ({invalid_amount:t().invalid,customer_required:t().customer,
      overpayment_requires_cash:t().noncash,invalid_method:t().invalid})[code]||t().invalid;
 }
 function compute(){
   const sum=total();
   if(sum===null||tender.value.trim()==='')return null;
   return calc.plan(calc.format(sum),tender.value,get('checkoutPaymentMethod')?.value,
     get('posCustomerSelect')?.value);
 }
 function render(){
   if(!isShown())return;
   const sum=total();current=compute();
   if(sum===null||tender.value.trim()===''){
     box.textContent=t().empty;box.style.color='#b45309';
     hidden.value='0';hidden.dispatchEvent(new root.Event('input',{bubbles:true}));
     return;
   }
   const raw=calc.cents(tender.value),paid=sum===null||raw===null?null:Math.min(raw,sum);
   if(paid!==null){
     const desired=calc.format(paid);
     if(hidden.value!==desired){hidden.value=desired;hidden.dispatchEvent(new root.Event('input',{bubbles:true}));}
   }
   box.replaceChildren();
   if(!current||!current.ok&&current.error!=='customer_required'){
     box.textContent=issue(current?.error);box.style.color='#b91c1c';return;
   }
   const l=t(),amount=(v)=>calc.format(v)+' '+l.dzd;
   const line=(label,value)=>{const el=d.createElement('p');el.style.cssText='margin:5px 0;font-size:13px;display:flex;justify-content:space-between;gap:12px;';const labelNode=d.createElement('span');labelNode.textContent=label;const valueNode=d.createElement('strong');valueNode.textContent=value;el.append(labelNode,valueNode);box.append(el);};
   line(l.paid,amount(current.paidCents));
   if(current.debtCents>0){
     line(l.debt,amount(current.debtCents));box.style.color='#92400e';
     if(!current.ok){
       const warning=d.createElement('p');warning.textContent=l.customer;
       warning.style.cssText='color:#b91c1c;font-weight:700;font-size:13px;margin-top:8px';
       box.append(warning);
     }
   }else if(current.changeCents>0){
     line(l.change,amount(current.changeCents));box.style.color='#065f46';
     if(notes?.plan){
       const part=notes.plan(calc.format(current.totalCents),calc.format(current.tenderCents));
       if(part?.ok){
         const heading=d.createElement('strong');heading.textContent=l.denoms+':';
         const list=d.createElement('div');list.style.cssText='display:flex;flex-wrap:wrap;gap:6px;margin-top:7px';
         for(const item of part.pieces){
           const chip=d.createElement('span');chip.style.cssText='border:1px solid #a7f3d0;border-radius:7px;padding:4px 8px;background:white;font-weight:700;';
           chip.textContent=item.count+' × '+item.denomination+' '+l.dzd;list.append(chip);
         }
         if(part.centimes){const chip=d.createElement('small');chip.textContent=String(part.centimes)+' centimes';list.append(chip);}
         box.append(heading,list);
       }
     }
   }else{line(l.change,l.noChange);box.style.color='#065f46';}
   root.NANO_PAYMENT_QUALITY_105?.render?.();
 }
 // The old cashier module used to reject underpayments. We deliberately disable
 // only its script tag in index.html. Here the persisted paidAmount remains <= total.
 function validateAndMaybeChoose(){
   if(!tender.value.trim()){box.textContent=t().empty;return false;}
   const p=compute();
   if(!p||!p.ok){
     box.textContent=issue(p?.error);box.style.color='#b91c1c';
     if(p?.error==='customer_required')root.nanoOpenCreditPicker107?.();
     return false;
   }
   return true;
 }
 tender.addEventListener('input',render);
 get('checkoutPaymentMethod')?.addEventListener('change',render);
 get('posCustomerSelect')?.addEventListener('change',render);
 modal.addEventListener('click',e=>{
   const button=e.target?.closest?.('button[onclick]');
   if(!button)return;
   if(/\b(?:processSale|processSaleAndPrintReceipt)\s*\(\s*\)/.test(button.getAttribute('onclick')||'')&&!validateAndMaybeChoose()){
     e.preventDefault();e.stopImmediatePropagation();
     tender.focus();
   }
 },true);
 const original=root.__browserElectron?.ipcRenderer?.invoke;
 if(typeof original==='function'){
   const bridge=root.__browserElectron.ipcRenderer;
   const previous=original.bind(bridge);
   bridge.invoke=function(channel,...args){
     if(channel==='process-sale'&&args[0]&&!args[0].editSaleId){
       const payload=args[0],c=payload.checkout||{};
       const sum=calc.cents(c.total),given=calc.cents(tender.value);
       if(sum===null||given===null)return Promise.resolve({success:false,error:'invalid_amount'});
       const plan=calc.plan(calc.format(sum),calc.format(given),c.paymentMethod,c.customerId);
       if(!plan.ok){
         if(plan.error==='customer_required')root.nanoOpenCreditPicker107?.();
         return Promise.resolve({success:false,error:plan.error});
       }
       const next={...c,paidAmount:calc.format(plan.paidCents)};
       if(plan.method==='cash')next.cashTenderedAmount=calc.format(plan.tenderCents);
       else delete next.cashTenderedAmount;
       args[0]={...payload,checkout:next};
     }
     return previous(channel,...args);
   };
 }
 function observe(){
   const shown=isShown();
   if(shown&&!lastShown){tender.value='';render();}
   if(!shown&&lastShown){tender.value='';box.textContent='';current=null;}
   lastShown=shown;
 }
 if(root.MutationObserver){
   new root.MutationObserver(observe).observe(modal,{attributes:true,attributeFilter:['class']});
   const el=get('checkoutTotalUI');
   if(el)new root.MutationObserver(render).observe(el,{childList:true,subtree:true,characterData:true});
 }
 observe();
 root.NANO_FLEX_108=Object.freeze({render,compute,validateAndMaybeChoose});
})(typeof window!=='undefined'?window:globalThis);
