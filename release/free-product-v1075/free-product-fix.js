/* NANO POS v1.0.75 — Free product dialog/cart fix; no inventory record is created. */
(function () {
  'use strict';
  const ids=['customProductModal','customProductNameInput','customProductPriceInput','customProductCostInput'];
  const el=id=>document.getElementById(id);
  const text={
    ar:{missing:'نافذة المنتج الحر غير متوفرة.',name:'أدخل اسم المنتج الحر.',price:'أدخل سعر بيع صحيحًا لا يقل عن صفر.',cost:'سعر الشراء الاختياري غير صالح.',cart:'تعذر تحديث سلة البيع.',added:'تمت إضافة المنتج الحر إلى السلة.'},
    fr:{missing:'Fenêtre de produit libre indisponible.',name:'Saisissez le nom du produit.',price:'Prix de vente non valide.',cost:"Prix d'achat non valide.",cart:'Impossible de mettre à jour le panier.',added:'Produit ajouté au panier.'},
    en:{missing:'Free-product dialog unavailable.',name:'Enter a free-product name.',price:'Invalid selling price.',cost:'Invalid optional cost.',cart:'Unable to update cart.',added:'Free product added to cart.'}
  };
  const language=()=>{const l=String(window.currentLanguage||document.documentElement.lang||'ar').toLowerCase().slice(0,2);return text[l]?l:'ar'};
  const toast=(message,kind='warning')=>{
    if(typeof window.showToast==='function')window.showToast(message,kind);
    else if(typeof window.alert==='function')window.alert(message);
  };
  const number=input=>{
    const v=String(input??'').trim().replace(/\s/g,'').replace(/,/g,'.');
    return /^(?:\d+\.?\d*|\.\d+)$/.test(v)?Number(v):NaN;
  };
  function parts(){return ids.map(el);}
  function open(){
    const [dialog,name,price,cost]=parts();
    if(![dialog,name,price,cost].every(Boolean)){toast(text[language()].missing,'error');return false;}
    // Detach from layout/stacking contexts which can hide the existing fixed modal.
    if(dialog.parentElement!==document.body)document.body.appendChild(dialog);
    name.value='';price.value='';cost.value='';
    dialog.classList.remove('hidden');dialog.classList.add('flex');
    dialog.style.display='flex';dialog.removeAttribute('inert');
    dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');
    setTimeout(()=>name.focus(),0);
    return true;
  }
  function close(){
    const dialog=el('customProductModal');
    if(!dialog)return;
    dialog.classList.add('hidden');dialog.classList.remove('flex');
    dialog.style.removeProperty('display');
  }
  function add(){
    const [dialog,nameEl,priceEl,costEl]=parts();
    if(![dialog,nameEl,priceEl,costEl].every(Boolean)){toast(text[language()].missing,'error');return false;}
    const name=String(nameEl.value||'').trim(),price=number(priceEl.value);
    const optional=String(costEl.value||'').trim(),cost=optional?number(optional):null;
    // Cart renderer interpolates names in HTML: reject markup in free-item names.
    if(!name||name.length>180||/[<>]/.test(name)){toast(text[language()].name);nameEl.focus();return false;}
    if(!Number.isFinite(price)||price<0){toast(text[language()].price);priceEl.focus();return false;}
    if(cost!==null&&(!Number.isFinite(cost)||cost<0)){toast(text[language()].cost);costEl.focus();return false;}
    let items;try{items=(typeof cart!=='undefined'&&Array.isArray(cart))?cart:window.cart;}catch{items=null;}
    if(!Array.isArray(items)||typeof window.updateCartUI!=='function'){toast(text[language()].cart,'error');return false;}
    const item={
      batch_id:null,
      product:{id:null,name,image:null,unit:null,color:null,weight_volume:null,wholesale_unit:null,wholesale_qty:null,has_variants:0,batches:[],extra_prices:[],variants:[]},
      variant:null,qty:1,is_wholesale:false,custom_price_set:true,price_label:null,
      selling_price:price,pos_price:price,original_price:null,applied_promotion_id:null,
      is_custom:true,custom_product_name:name,custom_cost_price:cost
    };
    items.unshift(item);
    try{window.updateCartUI();}
    catch(error){
      items.shift();console.error('Free product cart update error:',error);
      toast(text[language()].cart,'error');return false;
    }
    close();toast(text[language()].added,'success');return true;
  }
  // Original actions are available through inline HTML onclick and the keyboard shortcut.
  window.openCustomProductModal=open;
  window.closeCustomProductModal=close;
  window.addCustomProductToCart=add;
  function setup(){
    const dialog=el('customProductModal');
    if(!dialog||dialog.dataset.freeProductFix==='1')return;
    dialog.dataset.freeProductFix='1';
    dialog.addEventListener('keydown',e=>{
      if(e.key==='Escape'){e.preventDefault();e.stopPropagation();close();}
      if(e.key==='Enter'&&!e.shiftKey&&e.target?.tagName==='INPUT'){
        e.preventDefault();e.stopPropagation();add();
      }
    });
    dialog.addEventListener('click',e=>{if(e.target===dialog)close();});
    const style=document.createElement('style');style.id='nanoFreeProductFixStyle';
    style.textContent='#customProductModal{padding:12px;box-sizing:border-box;overscroll-behavior:contain}#customProductModal>div{width:min(440px,100%);max-height:calc(100dvh - 24px);overflow-y:auto;box-sizing:border-box}#customProductModal input{min-width:0}';
    document.head.appendChild(style);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup,{once:true});else setup();
})();
