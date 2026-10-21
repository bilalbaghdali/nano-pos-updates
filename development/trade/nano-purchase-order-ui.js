/* NANO POS v1.1.0: simple purchase order panel within the existing purchase list.
   Creating an order NEVER updates stock or supplier debt. */
(function(win){
 'use strict';
 const doc=win.document;if(!doc||win.NANO_PO_UI_110)return;win.NANO_PO_UI_110=true;
 const $=id=>doc.getElementById(id);
 const rpc=(channel,payload)=>win.__browserElectron.ipcRenderer.invoke(channel,...(payload===undefined?[]:[payload]));
 const make=(tag,text)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=String(text);return n;};
 const token=()=>('po-'+(win.crypto?.randomUUID?.()||String(Date.now())+'-'+Math.random().toString(36).slice(2)));
 let panel=null,selected=[],orders=[],suppliers=[];
 function status(message,bad){const v=$('nanoPoStatus110');if(v){v.textContent=String(message||'');v.style.color=bad?'#b91c1c':'#0369a1';}}
 const good=response=>{if(response?.success===false)throw Error(response.error||response.message||'فشل تنفيذ العملية');return response;};
 function field(type,step,value){
  const input=make('input');input.type=type;input.value=String(value??'');
  if(step){input.step=step;input.min=step==='0.001'?'0.001':'0';}
  input.style.cssText='max-width:110px;border:1px solid #94a3b8;border-radius:7px;padding:7px';
  return input;
 }
 function drawSelected(){
  const node=$('nanoPoItems110');if(!node)return;node.replaceChildren();
  for(let i=0;i<selected.length;i++){
   const item=selected[i],line=make('div');
   line.style.cssText='display:flex;flex-wrap:wrap;gap:8px;align-items:center;border-bottom:1px solid #eee;padding:8px';
   const name=make('strong',item.product.name||item.product.barcode||item.product.id);
   name.style.flex='1';
   const qty=field('number','0.001',item.quantity);qty.title='الكمية';
   qty.addEventListener('input',()=>item.quantity=qty.value);
   const cost=field('number','0.01',item.unitCost);cost.title='تكلفة الوحدة';
   cost.addEventListener('input',()=>item.unitCost=cost.value);
   const remove=make('button','حذف');remove.type='button';remove.addEventListener('click',()=>{selected.splice(i,1);drawSelected();});
   line.append(name,qty,cost,remove);node.append(line);
  }
 }
 async function search(){
  const box=$('nanoPoProductResults110');if(!box)return;box.replaceChildren();
  const search=$('nanoPoSearch110').value.trim();if(search.length<2)return;
  const result=good(await rpc('get-products',{search,page:1,perPage:25}));
  const products=Array.isArray(result)?result:result.items||[];
  for(const p of products){
   const b=make('button',(p.name||p.barcode||p.id)+' ('+(p.barcode||'')+')');
   b.type='button';b.style.cssText='display:block;width:100%;text-align:right;padding:5px;border-bottom:1px solid #ddd';
   b.addEventListener('click',()=>{
    if(selected.some(x=>String(x.product.id)===String(p.id))){status('المنتج موجود في القائمة',true);return;}
    selected.push({product:p,quantity:'1',unitCost:String(p.cost_price||0)});
    box.replaceChildren();$('nanoPoSearch110').value='';drawSelected();
   });
   box.append(b);
  }
 }
 async function reload(){
  const results=await Promise.all([rpc('get-suppliers'),rpc('get-purchase-orders')]);
  suppliers=Array.isArray(results[0])?results[0]:[];
  orders=Array.isArray(results[1])?results[1]:[];
  const select=$('nanoPoSupplier110');select.replaceChildren();
  const first=make('option','اختر المورد');first.value='';select.append(first);
  for(const p of suppliers){const option=make('option',p.name||p.id);option.value=String(p.id);select.append(option);}
  const node=$('nanoPoOrders110');node.replaceChildren();
  if(!orders.length)node.append(make('p','لا توجد أوامر شراء'));
  for(const o of orders){
   const row=make('div');row.style.cssText='display:flex;flex-wrap:wrap;align-items:center;gap:8px;border-bottom:1px solid #ddd;padding:7px';
   const title=make('span',o.id+' — '+o.supplierName+' — '+o.status);title.style.flex='1';
   const receive=make('button','استلام جزئي / كامل');receive.type='button';receive.disabled=o.status==='received';
   receive.addEventListener('click',()=>receiveOrder(o));
   row.append(title,receive);node.append(row);
  }
 }
 async function saveOrder(){
  const button=$('nanoPoSave110');if(button.disabled)return;
  button.disabled=true;status('جارٍ إنشاء الأمر…');
  try{
   const data={supplierId:$('nanoPoSupplier110').value,operationId:token(),
    lines:selected.map(i=>({productId:i.product.id,quantity:i.quantity,unitCost:i.unitCost}))};
   const out=good(await rpc('create-purchase-order',data));
   status('حُفظ أمر الشراء '+out.id+' دون تغيير المخزون أو دين المورد');
   selected=[];drawSelected();await reload();
  }catch(e){status(e.message,true);}finally{button.disabled=false;}
 }
 function receiveOrder(order){
  const form=$('nanoPoReceipt110');form.replaceChildren();
  form.append(make('h3','استلام أمر: '+order.id));
  const inputs=[];
  for(const item of order.lines||[]){
   const remaining=Math.max(0,(item.quantityMilli-item.receivedMilli)/1000);
   if(remaining<=0)continue;
   const row=make('div');row.style.cssText='display:flex;align-items:center;gap:12px;padding:6px;flex-wrap:wrap';
   const title=make('span',(item.productName||item.lineId)+' — المتبقي: '+remaining);title.style.flex='1';
   const input=field('number','0.001',remaining);input.max=remaining;inputs.push({lineId:item.lineId,input});
   row.append(title,input);form.append(row);
  }
  if(!inputs.length)return;
  const receiptId=token(),confirm=make('button','اعتماد الاستلام وترحيل المخزون والدين');
  confirm.type='button';confirm.style.cssText='background:#047857;color:white;padding:10px;border-radius:8px;margin:8px 0';
  confirm.addEventListener('click',async()=>{
   if(confirm.disabled)return;confirm.disabled=true;status('جارٍ اعتماد الاستلام…');
   try{
    const lines=inputs.filter(v=>Number(v.input.value)>0).map(v=>({lineId:v.lineId,quantity:v.input.value}));
    if(!lines.length)throw Error('اختر كمية واحدة على الأقل');
    const out=good(await rpc('confirm-purchase-order-receipt',
      {orderId:order.id,receiptId,operationId:receiptId,expectedRevision:order.revision,lines}));
    status('تم الترحيل بنجاح. الفاتورة: '+out.purchaseId);
    form.replaceChildren();await reload();
   }catch(e){status(e.message,true);confirm.disabled=false;}
  });
  form.append(confirm);
 }
 function open(){
  if(panel)return;
  panel=make('div');panel.id='nanoPoDialog110';panel.style.cssText='position:fixed;inset:0;z-index:99990;display:flex;align-items:center;justify-content:center;padding:12px;background:#0009;direction:rtl';
  const card=make('section');card.style.cssText='width:min(900px,100%);max-height:94vh;overflow:auto;background:white;color:#0f172a;border-radius:14px;padding:18px';
  const header=make('div');header.style.cssText='display:flex;align-items:center;justify-content:space-between';
  header.append(make('h2','أوامر الشراء'));
  const close=make('button','إغلاق');close.addEventListener('click',()=>{panel.remove();panel=null;selected=[];});
  header.append(close);card.append(header);
  card.append(make('p','إنشاء أمر شراء لا يغيّر المخزون أو ديون الموردين. التأثير المالي يحدث عند الاستلام المعتمد فقط.'));
  const supplier=make('select');supplier.id='nanoPoSupplier110';supplier.style.cssText='display:block;width:100%;padding:9px;margin:10px 0;border:1px solid #ddd';card.append(supplier);
  const searchInput=field('search',null,'');searchInput.id='nanoPoSearch110';searchInput.placeholder='ابحث عن منتج أو باركود';
  searchInput.style.maxWidth='100%';searchInput.style.width='100%';card.append(searchInput);
  let serial=0;searchInput.addEventListener('input',()=>{const n=++serial;setTimeout(()=>{if(n===serial)search().catch(e=>status(e.message,true));},250);});
  const results=make('div');results.id='nanoPoProductResults110';results.style.cssText='max-height:140px;overflow:auto';card.append(results);
  const items=make('div');items.id='nanoPoItems110';card.append(items);
  const save=make('button','إنشاء أمر شراء دون ترحيل');save.id='nanoPoSave110';
  save.style.cssText='background:#047857;color:white;padding:10px 16px;margin:12px 0;border-radius:8px';
  save.addEventListener('click',saveOrder);card.append(save);
  card.append(make('h3','أوامر الشراء'));
  const refresh=make('button','تحديث');refresh.addEventListener('click',()=>reload().catch(e=>status(e.message,true)));card.append(refresh);
  const orders=make('div');orders.id='nanoPoOrders110';card.append(orders);
  const receipt=make('div');receipt.id='nanoPoReceipt110';card.append(receipt);
  const message=make('p');message.id='nanoPoStatus110';message.setAttribute('role','status');card.append(message);
  panel.append(card);doc.body.append(panel);drawSelected();reload().catch(e=>status(e.message,true));
 }
 function attach(){
  const parent=$('purchasesListView');if(!parent||$('nanoPoOpen110'))return;
  const existing=parent.querySelector('button[onclick*="togglePurchaseView"]');
  const b=make('button','أوامر الشراء');b.id='nanoPoOpen110';
  b.type='button';b.style.cssText='background:#1d4ed8;color:white;padding:10px 14px;margin:4px;border-radius:10px;font-weight:bold';
  b.addEventListener('click',open);
  if(existing&&existing.parentNode)existing.parentNode.insertBefore(b,existing);
  else parent.prepend(b);
 }
 if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',attach,{once:true});
 else attach();
})(typeof window!=='undefined'?window:globalThis);
