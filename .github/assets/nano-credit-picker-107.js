/* NANO POS 1.0.107 — credit checkout customer picker.
 * Never creates an invoice by itself: uses the existing complete-credit sale path.
 * Customer creation calls the native customer API and sets initial debt to ZERO.
 */
(function(root){
 'use strict';
 const doc=root.document;
 if(!doc||root.NANO_CREDIT_PICKER_107)return;
 const checkout=doc.getElementById('checkoutModal');
 if(!checkout)return;
 const api=()=>root.api||null;
 const labels={
  ar:{title:'البيع بالكريدي',desc:'اختر الزبون الذي ستُسجَّل عليه قيمة الفاتورة، أو أضف زبونًا جديدًا.',search:'ابحث بالاسم أو الهاتف',existing:'الزبائن المسجلون',new:'إضافة زبون جديد',name:'اسم الزبون *',phone:'رقم الهاتف',address:'العنوان / الولاية',create:'حفظ الزبون والبيع بالكريدي',choose:'اختيار الزبون',cancel:'إلغاء',empty:'لا يوجد زبائن مطابقون؛ يمكنك إضافة زبون جديد.',loading:'تحميل الزبائن…',missing:'أدخل اسم الزبون.',saveError:'تعذر حفظ الزبون. لم يتم تسجيل بيع.',readError:'تعذر جلب الزبائن. لم يتم تسجيل بيع.',duplicate:'يوجد زبون بنفس رقم الهاتف؛ اختره من القائمة.',credit:'دين كامل',nameRequired:'اختر زبونًا مسجلًا قبل إتمام البيع.',ready:'الزبون المحدد: '},
  fr:{title:'Vente à crédit',desc:'Choisissez un client pour enregistrer toute la facture comme dette, ou créez un client.',search:'Chercher par nom ou téléphone',existing:'Clients enregistrés',new:'Nouveau client',name:'Nom du client *',phone:'Téléphone',address:'Adresse / Wilaya',create:'Enregistrer le client et choisir le crédit',choose:'Choisir ce client',cancel:'Annuler',empty:'Aucun client; créez-en un.',loading:'Chargement des clients…',missing:'Saisissez le nom du client.',saveError:'Échec de la création. Aucune vente enregistrée.',readError:'Clients indisponibles. Aucune vente enregistrée.',duplicate:'Ce numéro existe déjà; sélectionnez le client.',credit:'Crédit total',nameRequired:'Sélectionnez un client.',ready:'Client choisi : '},
  en:{title:'Sell on credit',desc:'Choose an existing customer or create one to record the full invoice as customer debt.',search:'Search by name or phone',existing:'Saved customers',new:'Add customer',name:'Customer name *',phone:'Phone number',address:'Address / Wilaya',create:'Save customer and select credit',choose:'Select customer',cancel:'Cancel',empty:'No matching customers; add a new one.',loading:'Loading customers…',missing:'Enter a customer name.',saveError:'Unable to save customer. Sale has not been posted.',readError:'Unable to load customers. Sale has not been posted.',duplicate:'Phone number is already assigned; choose that customer.',credit:'Full credit',nameRequired:'Select a customer first.',ready:'Selected customer: '}
 };
 const t=()=>{const lang=String(root.currentLanguage||doc.documentElement.lang||'ar').slice(0,2);return labels[lang]||labels.ar;};
 const elt=(tag,id,styles='')=>{const x=doc.createElement(tag);if(id)x.id=id;if(styles)x.style.cssText=styles;return x;};
 const dialog=elt('div','nanoCreditOverlay107','position:fixed;inset:0;z-index:210;background:rgba(15,23,42,.72);display:none;align-items:center;justify-content:center;padding:12px;');
 dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-labelledby','nanoCreditTitle107');
 const card=elt('section','','background:#fff;color:#0f172a;border-radius:18px;width:min(96vw,530px);max-height:90vh;overflow-y:auto;padding:20px;box-shadow:0 22px 75px rgba(0,0,0,.3);');
 const title=elt('h2','nanoCreditTitle107','font-size:22px;font-weight:800;margin-bottom:6px');
 const note=elt('p','nanoCreditDesc107','font-size:13px;color:#475569;margin-bottom:13px');
 const search=elt('input','nanoCreditSearch107','width:100%;padding:11px;border:1px solid #94a3b8;border-radius:10px;margin:8px 0;');
 search.type='search';search.autocomplete='off';
 const status=elt('p','nanoCreditStatus107','font-size:12px;margin:6px 0;color:#b45309');
 status.setAttribute('role','status');
 const results=elt('div','nanoCreditList107','max-height:200px;overflow-y:auto;display:grid;gap:6px;margin:8px 0 12px;');
 const newButton=elt('button','nanoCreditNew107','width:100%;padding:10px;background:#eff6ff;color:#1e40af;font-weight:800;border-radius:10px;border:1px solid #bfdbfe;');
 newButton.type='button';
 const createForm=elt('form','nanoCreditNewForm107','display:none;gap:8px;grid-template-columns:1fr;margin-top:10px;');
 const name=elt('input','nanoCreditName107','padding:10px;border:1px solid #cbd5e1;border-radius:8px;width:100%');
 const phone=elt('input','nanoCreditPhone107','padding:10px;border:1px solid #cbd5e1;border-radius:8px;width:100%');
 const address=elt('input','nanoCreditAddress107','padding:10px;border:1px solid #cbd5e1;border-radius:8px;width:100%');
 name.required=true;name.maxLength=150;phone.maxLength=35;address.maxLength=250;
 const formLabel=(input,text)=>{const wrap=elt('label','','font-size:12px;font-weight:700;display:grid;gap:4px');const cap=elt('span');cap.textContent=text;wrap.append(cap,input);return wrap;};
 const nameWrap=formLabel(name,'');const phoneWrap=formLabel(phone,'');const addressWrap=formLabel(address,'');
 const save=elt('button','nanoCreditSave107','padding:11px;background:#059669;color:white;font-weight:800;border-radius:9px;');
 save.type='submit';
 createForm.append(nameWrap,phoneWrap,addressWrap,save);
 const cancel=elt('button','nanoCreditCancel107','padding:10px;margin-top:12px;width:100%;background:#f1f5f9;color:#334155;border-radius:9px');
 cancel.type='button';
 card.append(title,note,search,status,results,newButton,createForm,cancel);
 dialog.append(card);doc.body.append(dialog);
 let customers=[],visible=false,busy=false,sequence=0,lastFocus=null;
 function translate(){
  const l=t();title.textContent=l.title;note.textContent=l.desc;search.placeholder=l.search;
  newButton.textContent=l.new;save.textContent=l.create;cancel.textContent=l.cancel;
  nameWrap.firstChild.textContent=l.name;phoneWrap.firstChild.textContent=l.phone;addressWrap.firstChild.textContent=l.address;
 }
 function warning(message,bad=true){status.textContent=message||'';status.style.color=bad?'#b91c1c':'#047857';}
 function hide(){
  visible=false;sequence++;dialog.style.display='none';createForm.style.display='none';
  search.value='';name.value='';phone.value='';address.value='';
  warning('');if(lastFocus?.focus)lastFocus.focus();lastFocus=null;
 }
 function selectCustomer(customer){
  if(!customer||customer.id==null||!String(customer.name||'').trim()){warning(t().nameRequired);return;}
  // Calls the existing POS customer selector so the customer search label and info buttons stay in sync.
  if(typeof root.selectPosCustomer==='function')root.selectPosCustomer(customer.id,customer.name);
  else{
    const hidden=doc.getElementById('posCustomerSelect');
    if(hidden)hidden.value=String(customer.id);
    const field=doc.getElementById('posCustomerSearchInput');if(field)field.value=customer.name;
  }
  const customerId=doc.getElementById('posCustomerSelect');
  if(!customerId||String(customerId.value)!==String(customer.id)){
    warning(t().nameRequired);return;
  }
  customerId.dispatchEvent(new root.Event('change',{bubbles:true}));
  root.checkoutMarkAsDebt?.();
  const paid=doc.getElementById('checkoutPaidAmount');
  if(paid){paid.value='0';paid.dispatchEvent(new root.Event('input',{bubbles:true}));}
  root.NANO_PAYMENT_QUALITY_105?.render?.();
  hide();
  // This only chooses full credit; invoice is created when cashier confirms checkout.
 }
 function render(){
  results.replaceChildren();
  const query=String(search.value||'').toLocaleLowerCase().trim();
  const filtered=customers.filter(c=>
    String(c?.name||'').toLocaleLowerCase().includes(query)||
    String(c?.phone||'').includes(query)).slice(0,100);
  if(!filtered.length){
    const empty=elt('p','','padding:12px;text-align:center;color:#64748b;');
    empty.textContent=t().empty;results.append(empty);
  }
  for(const item of filtered){
    const btn=elt('button','','padding:10px 12px;border:1px solid #e2e8f0;border-radius:9px;text-align:start;display:flex;justify-content:space-between;gap:12px;');
    btn.type='button';btn.disabled=busy;
    const label=elt('strong');label.textContent=String(item.name);
    const tel=elt('span','','font-size:12px;color:#64748b;');tel.textContent=String(item.phone||'');
    btn.append(label,tel);btn.addEventListener('click',()=>selectCustomer(item));results.append(btn);
  }
 }
 async function refresh(){
  const list=await api()?.getCustomers?.();
  if(!Array.isArray(list))throw new Error('customer_list_unavailable');
  customers=list.filter(x=>x?.id!=null&&String(x.name||'').trim());
  if(typeof root.loadCustomersSelect==='function')await root.loadCustomersSelect();
  render();
 }
 async function open(){
  if(busy)return;
  const checkout=doc.getElementById('checkoutModal');
  if(!checkout||checkout.classList.contains('hidden'))return;
  if(!api()||typeof api().getCustomers!=='function')return warning(t().readError);
  lastFocus=doc.activeElement;visible=true;dialog.style.display='flex';createForm.style.display='none';
  translate();warning(t().loading,false);search.value='';
  const ticket=++sequence;
  try{await refresh();if(ticket===sequence)warning('');}
  catch(e){if(ticket===sequence){customers=[];render();warning(t().readError);}}
  if(ticket===sequence)search.focus();
 }
 async function add(event){
  event.preventDefault();if(busy||!visible)return;
  const n=name.value.trim(),p=phone.value.trim(),a=address.value.trim();
  if(!n){warning(t().missing);name.focus();return;}
  const duplicate=p&&customers.find(c=>String(c.phone||'').trim()===p);
  if(duplicate){warning(t().duplicate);search.value=p;render();createForm.style.display='none';return;}
  busy=true;save.disabled=true;newButton.disabled=true;warning('');
  const ticket=sequence;
  try{
    if(typeof api()?.addCustomer!=='function')throw Error('customer_creation_unavailable');
    // An initial debt would be counted twice: only the confirmed sale posts the credit.
    const res=await api().addCustomer({name:n,phone:p,address:a,initial_debt:0,credit_limit:0,balance:0});
    if(!res||res.success===false||res.id==null)throw Error(res?.error||'customer_creation_failed');
    const savedId=String(res.id);
    await refresh();
    if(!visible||ticket!==sequence)return;
    const created=customers.find(c=>String(c.id)===savedId);
    if(!created)throw Error('saved_customer_unavailable');
    selectCustomer(created);
    root.dispatchEvent?.(new root.CustomEvent('nano-reference-data-changed',{detail:{type:'customer'}}));
  }catch(e){if(visible&&ticket===sequence)warning(t().saveError);}
  finally{busy=false;save.disabled=false;newButton.disabled=false;}
 }
 search.addEventListener('input',render);
 newButton.addEventListener('click',()=>{createForm.style.display=createForm.style.display==='grid'?'none':'grid';if(createForm.style.display==='grid')name.focus();});
 createForm.addEventListener('submit',add);
 cancel.addEventListener('click',hide);
 dialog.addEventListener('click',e=>{if(e.target===dialog&&!busy)hide();});
 dialog.addEventListener('keydown',e=>{if(e.key==='Escape'&&!busy){e.preventDefault();hide();}});
 // A completed or abandoned sale must never leave a credit picker over the next checkout.
 if(root.MutationObserver){
  new root.MutationObserver(()=>{if(checkout.classList.contains('hidden')&&visible&&!busy)hide();})
    .observe(checkout,{attributes:true,attributeFilter:['class']});
 }
 root.nanoOpenCreditPicker107=open;
 root.NANO_CREDIT_PICKER_107=Object.freeze({open,close:hide,refresh});
})(typeof window!=='undefined'?window:globalThis);
