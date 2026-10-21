/* NANO POS 1.0.105: professional single-method checkout.
 * No cash tendered field, no split/mixed payment; preserves existing invoice records.
 */
(function(root){
 'use strict';
 const doc=root.document;if(!doc||root.NANO_PAYMENT_QUALITY_105)return;
 const get=id=>doc.getElementById(id);
 const labels={
 ar:{summary:'ملخص تسديد الفاتورة',total:'المبلغ الإجمالي',method:'طريقة التسديد',pay:'الدفع',paid:'دفع كامل',credit:'دين كامل',customer:'اختر زبونًا مسجلًا قبل البيع بالدين.',processing:'جاري تسجيل الفاتورة…',duplicate:'تم تسجيل هذه العملية مسبقًا. لا تكرر التأكيد.',error:'تعذّر إتمام البيع؛ يمكنك المحاولة مجددًا.',creditInfo:'سيُسجّل المبلغ دينًا على الزبون المحدد.',complete:'ستُسدد قيمة الفاتورة بالكامل.',invalid:'يُسمح بالدفع الكامل أو الدين الكامل فقط.',badMethod:'اختر طريقة دفع واحدة صالحة.'},
 fr:{summary:'Résumé du règlement',total:'Total',method:'Mode de paiement',pay:'Règlement',paid:'Paiement intégral',credit:'Vente à crédit',customer:'Sélectionnez un client enregistré pour la vente à crédit.',processing:'Enregistrement de la facture…',duplicate:'Cette vente a déjà été enregistrée.',error:'Échec de la vente. Vous pouvez réessayer.',creditInfo:'Le montant sera imputé sur le compte client.',complete:'La facture sera réglée intégralement.',invalid:'Choisissez paiement intégral ou crédit intégral.',badMethod:'Sélectionnez un seul mode de paiement.'},
 en:{summary:'Payment summary',total:'Invoice total',method:'Payment method',pay:'Settlement',paid:'Paid in full',credit:'Full credit',customer:'Select a registered customer before selling on credit.',processing:'Saving invoice…',duplicate:'This sale has already been recorded.',error:'Unable to save the sale. Retry is available.',creditInfo:'The whole amount becomes customer debt.',complete:'The whole invoice is paid.',invalid:'Only full payment or full credit is permitted.',badMethod:'Choose a valid single payment method.'}
 };
 const language=()=>{const s=String(root.currentLanguage||doc.documentElement.lang||'ar').toLowerCase();return s.startsWith('fr')?'fr':s.startsWith('en')?'en':'ar';};
 const t=()=>labels[language()];
 const allowed=new Set(['cash','card','cheque','ccp','virement','transfer','other']);
 const normalize=value=>String(value??'').replace(/[٠-٩]/g,c=>String(c.charCodeAt(0)-1632)).replace(/[۰-۹]/g,c=>String(c.charCodeAt(0)-1776)).replace(/\s/g,'').replace(',','.');
 const cents=value=>{const raw=normalize(value),m=raw.match(/^\d+(?:\.\d{1,2})?$/);if(!m)return null;const [a,b='']=raw.split('.');const n=Number(a)*100+Number((b+'00').slice(0,2));return Number.isSafeInteger(n)&&n>=0?n:null;};
 const readTotal=()=>{const text=String(get('checkoutTotalUI')?.textContent||'');const m=text.replace(/[٠-٩]/g,c=>String(c.charCodeAt(0)-1632)).replace(/[۰-۹]/g,c=>String(c.charCodeAt(0)-1776)).match(/\d+(?:[.,]\d{1,2})?/);return cents(m?.[0]||'0');};
 const money=value=>(value/100).toFixed(2);
 const modal=get('checkoutModal');if(!modal)return;
 const summary=doc.createElement('section');summary.id='nanoPaymentSummary105';
 summary.style.cssText='padding:12px;border:1px solid #a7f3d0;background:#ecfdf5;border-radius:12px;margin-top:10px;color:#064e3b';
 summary.setAttribute('role','status');summary.setAttribute('aria-live','polite');
 const row=doc.createElement('div');row.style.cssText='display:flex;justify-content:space-between;gap:14px;align-items:center';
 const heading=doc.createElement('strong');heading.textContent=t().summary;
 const amount=doc.createElement('strong');amount.id='nanoPaymentTotal105';
 row.append(heading,amount);
 const detail=doc.createElement('div');detail.id='nanoPaymentDetail105';detail.style.cssText='font-size:13px;margin-top:6px;line-height:1.6';
 const status=doc.createElement('div');status.id='nanoPaymentWarning105';status.style.cssText='font-size:13px;font-weight:700;margin-top:6px';
 summary.append(row,detail,status);
 const panel=get('nanoCheckoutChoice104');
 if(panel)panel.insertAdjacentElement('afterend',summary);
 else modal.querySelector('.p-6')?.append(summary);
 let busy=false,committed=false,key='',wasVisible=false,lastTotal=null;
 const uuid=()=> 'n105-'+(root.crypto?.randomUUID?.()||Date.now().toString(36)+'-'+Math.random().toString(36).slice(2));
 const warn=(message,level='error')=>{status.textContent=message;status.style.color=level==='error'?'#b91c1c':'#047857';};
 const paid=()=>cents(get('checkoutPaidAmount')?.value||'0');
 const credit=()=>{const total=readTotal();return total>0&&paid()===0;};
 function render(){
   const total=readTotal(),p=paid(),selected=get('checkoutPaymentMethod');
   if(total===null)return;
   if(lastTotal!==null&&lastTotal!==total&&p===lastTotal){
     const input=get('checkoutPaidAmount');
     if(input){input.value=money(total);input.dispatchEvent(new root.Event('input',{bubbles:true}));}
   }
   lastTotal=total;
   const due=credit(),method=selected?.selectedOptions?.[0]?.textContent?.trim()||selected?.value||'';
   heading.textContent=t().summary;amount.textContent=money(total)+' د.ج';
   detail.textContent=t().method+': '+method+' · '+t().pay+': '+(due?t().credit:t().paid)+' · '+(due?t().creditInfo:t().complete);
   if(!busy&&!committed){
     status.textContent=due&&!String(get('posCustomerSelect')?.value||'').trim()?t().customer:'';
     status.style.color='#b45309';
   }
 }
 function setProcessing(on){busy=on;const buttons=modal.querySelectorAll('button[onclick]');
   for(const btn of buttons){
     const handler=String(btn.getAttribute('onclick')||'');
     if(/\b(?:processSale|processSaleAndPrintReceipt)\s*\(\s*\)/.test(handler))
       btn.disabled=on||committed;
   }
 }
 function fail(error){const m=String(error?.message||error||t().error);warn(m);root.showToast?.(m,'error');return {success:false,error:m};}
 const invoke=root.__browserElectron?.ipcRenderer?.invoke;
 if(typeof invoke==='function'){
   const original=invoke.bind(root.__browserElectron.ipcRenderer);
   root.__browserElectron.ipcRenderer.invoke=function(channel,...args){
     if(channel!=='process-sale'||!args[0]||typeof args[0]!=='object'||args[0].editSaleId)
       return original(channel,...args);
     if(committed)return Promise.resolve(fail(t().duplicate));
     if(busy)return Promise.resolve(fail(t().processing));
     const payload=args[0],c=payload.checkout||{},total=cents(String(c.total)),value=cents(String(c.paidAmount)),method=String(c.paymentMethod||'cash');
     if(total===null||value===null||!(value===total||value===0))
       return Promise.resolve(fail(t().invalid));
     if(!allowed.has(method)||Array.isArray(c.payments)||method==='mixed')
       return Promise.resolve(fail(t().badMethod));
     if(value===0&&total>0&&!String(c.customerId||'').trim())
       return Promise.resolve(fail(t().customer));
     if(!key)key=uuid();
     const updated={...payload,checkout:{...c,nanoCheckoutRequestId:key}};
     setProcessing(true);warn(t().processing,'info');
     let result;
     try{result=original(channel,updated,...args.slice(1));}
     catch(err){setProcessing(false);return Promise.resolve(fail(err));}
     return Promise.resolve(result).then(answer=>{
       if(answer?.success){
         committed=true;setProcessing(false);warn('✓ '+t().paid,'info');
       }else{setProcessing(false);warn(answer?.message||answer?.error||t().error);}
       return answer;
     },error=>{setProcessing(false);return fail(error)});
   };
 }
 function onModal(){
   const visible=!modal.classList.contains('hidden');
   if(visible&&!wasVisible){busy=false;committed=false;key=uuid();lastTotal=null;render();setProcessing(false);}
   if(!visible&&wasVisible){busy=false;committed=false;key='';lastTotal=null;status.textContent='';}
   wasVisible=visible;
 }
 if(root.MutationObserver){
   new root.MutationObserver(onModal).observe(modal,{attributes:true,attributeFilter:['class']});
   const total=get('checkoutTotalUI');
   if(total)new root.MutationObserver(render).observe(total,{childList:true,subtree:true,characterData:true});
 }
 modal.addEventListener('click',event=>{
   const button=event.target?.closest?.('button[onclick]');
   if(!button)return;
   const handler=String(button.getAttribute('onclick')||'');
   if(/\b(?:processSale|processSaleAndPrintReceipt)\s*\(\s*\)/.test(handler)){
     if(busy||committed){event.preventDefault();event.stopImmediatePropagation();warn(committed?t().duplicate:t().processing);return;}
     const total=readTotal(),p=paid();
     if(total===null||p===null||!(p===0||p===total)){
       event.preventDefault();event.stopImmediatePropagation();warn(t().invalid);return;
     }
     if(p===0&&total>0&&!String(get('posCustomerSelect')?.value||'').trim()){
       event.preventDefault();event.stopImmediatePropagation();warn(t().customer);
       get('posCustomerSelect')?.focus();return;
     }
   }
   if(handler.includes('checkoutMarkAsDebt')||handler.includes('nanoCheckoutPayFull104')){
     root.setTimeout?.(render,0);
   }
 },true);
 get('checkoutPaymentMethod')?.addEventListener('change',render);
 get('posCustomerSelect')?.addEventListener('change',render);
 get('checkoutPaidAmount')?.addEventListener('input',render);
 onModal();
 root.NANO_PAYMENT_QUALITY_105=Object.freeze({render,readTotal});
})(typeof window!=='undefined'?window:globalThis);
