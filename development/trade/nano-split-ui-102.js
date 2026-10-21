/* NANO POS v1.0.102 — split payment editor in existing checkout.
   This is opt-in. It only attaches validated rows to the existing checkout RPC. */
(function(win){
 'use strict';
 const doc=win.document;if(!doc||win.NANO_SPLIT_UI_102)return;win.NANO_SPLIT_UI_102=true;
 const methods=[['cash','نقدًا','Espèces','Cash'],['card','بطاقة','Carte','Card'],
  ['ccp','CCP','CCP','CCP'],['cheque','شيك','Chèque','Cheque'],
  ['virement','تحويل بنكي','Virement','Bank transfer'],['other','أخرى','Autre','Other']];
 const lang=()=>String(win.currentLanguage||doc.documentElement.lang||'ar').slice(0,2);
 const choose=item=>item[lang()==='fr'?2:lang()==='en'?3:1];
 const by=id=>doc.getElementById(id);
 let enabled=false,editor=null,controls=[],previousPaidReadonly=false,wrapped=false;
 function rows(){
  return controls.filter(c=>String(c.input.value).trim()&&Number(c.input.value)>0)
    .map(c=>({method:c.method,amount:c.input.value}));
 }
 function totalPaid(){
  let cents=0;
  for(const row of rows()){
   const amount=win.NANO_PAYMENT_LEDGER_102?.asCents(row.amount);
   if(amount==null||!Number.isSafeInteger(amount))throw Error('invalid_split_payment');
   cents+=amount;
  }
  return (cents/100).toFixed(2);
 }
 function recalc(){
  if(!enabled)return;
  const input=by('checkoutPaidAmount'),message=by('nanoSplitStatus102');
  try{
   const paid=totalPaid();
   if(input){input.value=paid;input.dispatchEvent(new win.Event('input',{bubbles:true}));}
   if(message){message.textContent=(lang()==='fr'?'Paiements reçus : ':lang()==='en'?'Payments received: ':'المدفوع حتى الآن: ')+paid;message.style.color='#047857';}
  }catch(e){if(message){message.textContent=e.message;message.style.color='#b91c1c';}}
 }
 function reset(){
  enabled=false;
  const toggle=by('nanoSplitEnabled102');if(toggle)toggle.checked=false;
  const box=by('nanoSplitFields102');if(box)box.hidden=true;
  const input=by('checkoutPaidAmount');if(input)input.readOnly=previousPaidReadonly;
  const method=by('checkoutPaymentMethod');if(method)method.disabled=false;
  for(const control of controls)control.input.value='';
 }
 function attach(){
  const modal=by('checkoutModal'),bridge=win.__browserElectron?.ipcRenderer;
  if(!modal||!bridge||typeof bridge.invoke!=='function'||!win.NANO_PAYMENT_LEDGER_102?.split)return;
  if(!editor){
   const select=by('checkoutPaymentMethod');if(!select?.parentNode)return;
   editor=doc.createElement('section');editor.id='nanoSplitEditor102';
   editor.style.cssText='padding:10px;border:1px solid #cbd5e1;border-radius:12px;margin-top:9px;background:#f8fafc';
   const title=doc.createElement('label');title.style.cssText='display:flex;gap:6px;align-items:center;font-weight:800';
   const check=doc.createElement('input');check.type='checkbox';check.id='nanoSplitEnabled102';
   title.append(check,doc.createTextNode(lang()==='fr'?'Paiement multiple et partiel':lang()==='en'?'Split / partial payment':'الدفع المختلط أو الجزئي'));
   editor.append(title);
   const fields=doc.createElement('div');fields.id='nanoSplitFields102';fields.hidden=true;
   fields.style.cssText='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:12px 0';
   for(const method of methods){
     const label=doc.createElement('label');
     label.textContent=choose(method);label.style.cssText='display:grid;gap:4px;font-size:12px;font-weight:600';
     const input=doc.createElement('input');input.type='number';input.min='0';input.step='0.01';input.placeholder='0.00';
     input.style.cssText='width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:6px';
     input.addEventListener('input',recalc);label.append(input);fields.append(label);
     controls.push({method:method[0],input});
   }
   editor.append(fields);
   const status=doc.createElement('p');status.id='nanoSplitStatus102';status.setAttribute('role','status');status.style.margin='6px';
   editor.append(status);
   check.addEventListener('change',()=>{
     enabled=check.checked;fields.hidden=!enabled;
     const paid=by('checkoutPaidAmount'),method=by('checkoutPaymentMethod');
     if(enabled){previousPaidReadonly=!!paid?.readOnly;if(paid)paid.readOnly=true;if(method)method.disabled=true;recalc();}
     else{if(paid)paid.readOnly=previousPaidReadonly;if(method)method.disabled=false;}
   });
   select.parentNode.insertAdjacentElement('afterend',editor);
   new win.MutationObserver(()=>{if(modal.classList.contains('hidden')&&enabled)reset();})
     .observe(modal,{attributes:true,attributeFilter:['class']});
  }
  if(!wrapped){
   wrapped=true;
   const original=bridge.invoke.bind(bridge);
   bridge.invoke=(channel,...args)=>{
     if(channel==='process-sale'&&enabled&&args[0]&&typeof args[0]==='object'){
       const current=args[0],checkout=current.checkout||{},inputRows=rows();
       const split=win.NANO_PAYMENT_LEDGER_102.split(String(checkout.total),
         inputRows,checkout.customerId);
       args[0]={...current,checkout:{...checkout,payments:split.payments,
         paidAmount:split.paidAmount,paymentMethod:split.paymentMethod,
         cashTenderedAmount:null}};
     }
     return original(channel,...args);
   };
  }
 }
 if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',attach,{once:true});
 else attach();
})(typeof window!=='undefined'?window:globalThis);
