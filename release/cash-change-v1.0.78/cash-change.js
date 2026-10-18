/* NANO POS v1.0.78 — recorded cash tender and expected change. */
(function(w){
'use strict';
const d=w.document;
if(!d||w.NANO_CASH_CHANGE_178)return;
const get=id=>d.getElementById(id);
const labels={
ar:{tender:'المبلغ الذي سلّمه الزبون (د.ج)',change:'الصرف الواجب إرجاعه',short:'المتبقي من الفاتورة',applied:'المبلغ المحتسب في الفاتورة',required:'أدخل المبلغ الذي سلّمه الزبون.',invalid:'أدخل مبلغًا نقديًا صحيحًا بخانتين عشريتين كحد أقصى.',customer:'لا يمكن تسجيل دين دون اختيار زبون.',notEnough:'المبلغ المستلم أقل من المبلغ النقدي المطلوب.',history:'سجل الصرف',heading:'سجل مبالغ النقد والصرف المحسوب',empty:'لا توجد عمليات صرف مسجلة.',help:'هذه القيم تمثل الصرف الواجب إرجاعه، ولا تؤكد تسليمه فعليًا.',ref:'مرجع البيع',date:'التاريخ',cashier:'البائع',total:'الفاتورة',received:'المستلم',cash:'المحتسب',due:'الصرف',close:'إغلاق'},
fr:{tender:'Somme remise par le client (DZD)',change:'Monnaie à rendre',short:'Reste à payer',applied:'Paiement affecté à la vente',required:'Saisissez la somme remise.',invalid:'Montant invalide (2 décimales maximum).',customer:'Sélectionnez un client pour le crédit.',notEnough:'Somme remise insuffisante.',history:'Journal de monnaie',heading:'Historique de la monnaie à rendre',empty:'Aucun historique.',help:'La monnaie calculée ne prouve pas sa remise effective.',ref:'Vente',date:'Date',cashier:'Caissier',total:'Total',received:'Remis',cash:'Imputé',due:'Monnaie',close:'Fermer'},
en:{tender:'Cash handed by customer (DZD)',change:'Change to return',short:'Unpaid balance',applied:'Cash applied to sale',required:'Enter cash handed by the customer.',invalid:'Invalid amount (max 2 decimals).',customer:'Select a customer for unpaid credit.',notEnough:'Cash handed is below amount applied.',history:'Change log',heading:'Recorded cash and calculated change',empty:'No recorded transactions.',help:'Calculated change is not proof the cashier actually returned it.',ref:'Sale',date:'Date',cashier:'Cashier',total:'Total',received:'Tendered',cash:'Applied',due:'Change',close:'Close'}
};
function T(){const l=String(w.currentLanguage||d.documentElement.lang||'ar').slice(0,2);return labels[l]||labels.ar;}
const numeric=v=>String(v??'').trim().replace(/[٠-٩]/g,c=>String(c.charCodeAt(0)-1632)).replace(/[۰-۹]/g,c=>String(c.charCodeAt(0)-1776)).replace(/,/g,'.').replace(/\s/g,'');
function parseCents(v){const s=numeric(v);if(!/^\d+(?:\.\d{1,2})?$/.test(s))return null;const [a,b='']=s.split('.');const n=Number(a)*100+Number((b+'00').slice(0,2));return Number.isSafeInteger(n)&&n>=0&&n<=100000000000? n:null;}
const fmt=x=>x===null?'—':(x/100).toFixed(2);
function warn(message){if(typeof w.showToast==='function')w.showToast(message,'warning');else w.alert?.(message);}
function cash(){return get('checkoutPaymentMethod')?.value==='cash';}
function visible(){const modal=get('checkoutModal');return modal&&!modal.classList.contains('hidden');}
function split(){const panel=get('nanoSplitPanel');return !!panel&&!panel.hidden;}
function customer(){return !!String(get('posCustomerSelect')?.value||'').trim();}
function total(){const m=String(get('checkoutTotalUI')?.textContent||'').match(/[\d٠-٩۰-۹]+(?:[.,][\d٠-٩۰-۹]+)?/);return parseCents(m?.[0]||'');}
function refresh(){
  const panel=get('nanoCashChangePanel'),input=get('nanoCashTendered');
  if(!panel||!input)return;
  panel.hidden=!cash()||!visible();
  if(panel.hidden)return;
  const amount=total(),given=parseCents(input.value);
  const debt=get('nanoCashBalance'),change=get('nanoCashChangeDue'),status=get('nanoCashMessage');
  const methodSplit=split();
  const cashApplied=methodSplit?parseCents(get('nanoSplitCash')?.value||''):amount===null||given===null?null:Math.min(given,amount);
  if(!methodSplit&&cashApplied!==null){
    const paid=get('checkoutPaidAmount');
    if(paid&&paid.value!==fmt(cashApplied)){
      paid.value=fmt(cashApplied);
      paid.dispatchEvent(new Event('input',{bubbles:true}));
    }
  }
  const valid=amount!==null&&given!==null&&cashApplied!==null&&given>=cashApplied&&cashApplied<=amount;
  change.textContent=valid?fmt(given-cashApplied):'—';
  debt.textContent=valid?fmt(amount-cashApplied):'—';
  status.textContent=!input.value.trim()?'':valid?'':T().notEnough;
  input.setAttribute('aria-invalid',valid||!input.value.trim()?'false':'true');
}
function prepare(payload){
 if(!visible()||!cash()||!payload||payload.editSaleId||payload.checkout?.total<0)return {ok:true};
 const input=get('nanoCashTendered');
 if(!input||!input.value.trim())return {ok:false,message:T().required};
 const tender=parseCents(input.value),sum=Number.isFinite(Number(payload.checkout?.total))?Math.round(Number(payload.checkout.total)*100):null,current=Number.isFinite(Number(payload.checkout?.paidAmount))?Math.round(Number(payload.checkout.paidAmount)*100):null;
 if(tender===null||sum===null)return {ok:false,message:T().invalid};
 const applied=split()?current:Math.min(sum,tender);
 if(applied===null||applied>sum||tender<applied)return {ok:false,message:T().notEnough};
 if(sum>applied&&!customer())return {ok:false,message:T().customer};
 if(payload.checkout.customerId==null&&sum>applied)return {ok:false,message:T().customer};
 payload.checkout.paidAmount=applied/100;
 payload.checkout.cashTenderedAmount=tender/100;
 // Authoritative change is recalculated in browser-bridge before saving a sale.
 refresh();
 return {ok:true};
}
function createModal(){
 const outer=d.createElement('div');outer.id='nanoCashAuditModal';outer.className='hidden';
 outer.innerHTML='<div class="nano-cash-audit-card"><div class="nano-cash-audit-head"><h3 id="nanoCashAuditHeading"></h3><button type="button" id="nanoCashAuditClose">×</button></div><div class="nano-cash-audit-scroll"><table><thead><tr id="nanoCashAuditThead"></tr></thead><tbody id="nanoCashAuditRows"></tbody></table></div><small id="nanoCashAuditHelp"></small></div>';
 d.body.append(outer);
 get('nanoCashAuditClose').addEventListener('click',()=>outer.classList.add('hidden'));
 outer.addEventListener('click',e=>{if(e.target===outer)outer.classList.add('hidden')});
}
async function history(){
 if(!get('nanoCashAuditModal'))createModal();
 const modal=get('nanoCashAuditModal'),t=T();
 modal.classList.remove('hidden');
 get('nanoCashAuditHeading').textContent=t.heading;
 get('nanoCashAuditHelp').textContent=t.help;
 get('nanoCashAuditThead').replaceChildren(...[t.ref,t.date,t.cashier,t.total,t.received,t.cash,t.due].map(x=>{const th=d.createElement('th');th.textContent=x;return th;}));
 const body=get('nanoCashAuditRows');body.replaceChildren();
 try{
   if(typeof w.api?.getCashChangeAudit!=='function')throw Error('Cash change audit API unavailable');
   const rows=await w.api.getCashChangeAudit({limit:300});
   if(!Array.isArray(rows))throw Error('Invalid audit result');
   if(!rows.length){const tr=d.createElement('tr'),td=d.createElement('td');td.colSpan=7;td.textContent=t.empty;tr.append(td);body.append(tr);}
   for(const rec of rows){
      const tr=d.createElement('tr');
      const values=[rec.sale_id,rec.recorded_at?new Date(rec.recorded_at).toLocaleString():'',rec.cashier_name||rec.cashier_user_id||'',rec.sale_total,rec.cash_tendered_amount,rec.cash_applied_amount,rec.cash_change_due];
      values.forEach((val,i)=>{const td=d.createElement('td');td.textContent=i>2?Number(val||0).toFixed(2):String(val??'');tr.append(td);});body.append(tr);
   }
 }catch(e){const tr=d.createElement('tr'),td=d.createElement('td');td.colSpan=7;td.textContent=String(e.message||e);tr.append(td);body.append(tr);}
}
function init(){
 const modal=get('checkoutModal'),paid=get('checkoutPaidAmount');
 if(!modal||!paid||get('nanoCashChangePanel'))return;
 const box=d.createElement('div');box.id='nanoCashChangePanel';box.hidden=true;
 box.innerHTML='<label id="nanoCashTenderLabel" for="nanoCashTendered"></label><input id="nanoCashTendered" type="number" step="0.01" min="0" inputmode="decimal" autocomplete="off" placeholder="0.00" /><div class="nano-cash-change-grid"><div><small id="nanoCashChangeLabel"></small><strong id="nanoCashChangeDue">—</strong></div><div><small id="nanoCashBalanceLabel"></small><strong id="nanoCashBalance">—</strong></div></div><p id="nanoCashMessage" role="status" aria-live="polite"></p>';
 const stamp=get('checkoutStampBox');
 (stamp||paid.parentElement).before(box);
 get('nanoCashTenderLabel').textContent=T().tender;
 get('nanoCashChangeLabel').textContent=T().change;
 get('nanoCashBalanceLabel').textContent=T().short;
 const input=get('nanoCashTendered');input.addEventListener('input',refresh);
 paid.addEventListener('input',()=>{if(split())refresh()});
 get('nanoSplitCash')?.addEventListener('input',refresh);
 get('nanoSplitToggle')?.addEventListener('click',()=>setTimeout(refresh,0));
 get('checkoutPaymentMethod')?.addEventListener('change',refresh);
 let wasVisible=false;
 const observer=new MutationObserver(()=>{
   const on=!!visible();
   if(on&&!wasVisible){input.value='';setTimeout(()=>{refresh();if(cash())input.focus({preventScroll:true})},0);}
   if(!on&&wasVisible)input.value='';
   wasVisible=on;refresh();
 });
 observer.observe(modal,{attributes:true,attributeFilter:['class']});
 const toolbar=get('posToolbar');
 if(toolbar){
   const button=d.createElement('button');button.type='button';button.id='nanoCashAuditOpen';button.className='nano-cash-audit-open';button.textContent=T().history;
   button.addEventListener('click',history);toolbar.append(button);
 }
 refresh();
}
w.NANO_CASH_CHANGE_178={prepare,parseCents,refresh,history};
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);