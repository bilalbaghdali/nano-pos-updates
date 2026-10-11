/* NANO POS v1.0.40 — 4-character suggestions in product, customer and supplier lookups. */
(function (root) {
  'use strict';
  const MIN = 4;
  const MAX_RESULTS = 10;
  const TYPES = {
    product: new Set(['productName','posProductSearchInput','globalSearch','inventorySearch',
      'bundleProductSearch','promoProductSearch','plSearch','invProductSearch',
      'advProductSearch','customProductNameInput','stocktakeProductSearch',
      'productionProductSearch','manufacturingProductSearch']),
    customer: new Set(['customerName','customerSearch','posCustomerSearchInput',
      'salesLogCustomerSearchInput']),
    supplier: new Set(['supName','supplierSearch'])
  };
  const CREATE_IDS = new Set(['productName','customerName','supName']);
  const normalize = value => String(value || '').normalize('NFKC')
    .replace(/[\u064b-\u065f\u0670\u0640]/g, '')
    .replace(/[إأآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ة/g,'ه')
    .replace(/\s+/g,' ').trim().toLocaleLowerCase();
  const results = (items, query) => {
    const q = normalize(query);
    if ([...q].length < MIN) return [];
    const clean = new Map();
    for (const item of items || []) {
      if (!item || !item.name || !normalize(item.name).includes(q)) continue;
      const key = String(item.id == null ? normalize(item.name) : item.id);
      if (!clean.has(key)) clean.set(key,item);
    }
    return [...clean.values()].sort((a,b) => {
      const aa=normalize(a.name),bb=normalize(b.name);
      return Number(bb.startsWith(q))-Number(aa.startsWith(q)) || aa.localeCompare(bb);
    }).slice(0,MAX_RESULTS);
  };
  const identify = (el) => {
    if (!el || el.tagName !== 'INPUT' || el.disabled || el.readOnly) return null;
    if (['hidden','number','password','email','date','checkbox','radio'].includes(el.type)) return null;
    const id=el.id||'';
    for (const [kind,set] of Object.entries(TYPES)) if (set.has(id)) return kind;
    // Additional/dynamic product search points, without touching non-product fields.
    const meta=(id+' '+(el.name||'')+' '+(el.getAttribute('data-i18n-placeholder')||'')+' '+(el.placeholder||'')).toLowerCase();
    if (/product|item.search|search.item|search_product|بحث.*منتج|ابحث.*منتج|بحث.*صنف|اسم المنتج/.test(meta)
        && !/barcode|باركود|qty|quantity|price|cost|weight|stock|minstock/.test(meta)) return 'product';
    return null;
  };
  const unwrap = result => Array.isArray(result) ? result :
    Array.isArray(result?.items) ? result.items :
    Array.isArray(result?.data) ? result.data :
    Array.isArray(result?.products) ? result.products : [];
  const apiMethod = {product:'getProducts',customer:'getCustomers',supplier:'getSuppliers'};
  const fetchMatches = async (api, kind, query) => {
    const method=api?.[apiMethod[kind]];
    if (typeof method !== 'function') return [];
    if (kind!=='product') return results(unwrap(await method.call(api)),query);
    const collected=[], maxPages=15, perPage=200;
    for (let page=1;page<=maxPages;page++) {
      const response=await method.call(api,{page,perPage,search:query});
      const batch=unwrap(response);
      collected.push(...batch);
      const matched=results(collected,query);
      // If server-side search is applied, a short page is exhaustive.
      if (batch.length<perPage || (response?.total!=null && page*perPage>=Number(response.total))) return matched;
      // Don't return early on a non-filtering API: later pages may contain better matches.
    }
    return results(collected,query);
  };
  if (typeof module !== 'undefined' && module.exports) module.exports={MIN,normalize,results,identify,fetchMatches};
  if (typeof document === 'undefined') return;
  let overlay=null,active=null,list=[],selected=0,serial=0,timer=null,busy=false;
  const labels=()=>{
    const lang=(root.currentLanguage||document.documentElement.lang||'ar').toLowerCase();
    return lang.startsWith('fr')?{title:'Résultats existants',empty:'Aucun résultat',hint:'Sélectionner'}:
      lang.startsWith('en')?{title:'Existing matches',empty:'No matches',hint:'Choose'}:
      {title:'نتائج موجودة',empty:'لا توجد نتائج مطابقة',hint:'اختيار'};
  };
  const ensure = () => {
    if (overlay) return overlay;
    overlay=document.createElement('div');overlay.id='nano-v140-suggestions';
    overlay.setAttribute('role','listbox');overlay.setAttribute('aria-label','اقتراحات البحث');
    overlay.style.cssText='position:fixed;z-index:2147483000;display:none;background:white;border:1px solid #cbd5e1;border-radius:12px;box-shadow:0 12px 35px #0f172a30;max-height:300px;overflow:auto;min-width:230px;text-align:start;color:#0f172a;font:600 13px system-ui,sans-serif;';
    document.body.appendChild(overlay);return overlay;
  };
  const hide=()=>{if(overlay)overlay.style.display='none';active=null;list=[];selected=0;serial++;clearTimeout(timer);};
  const position=()=>{
    if(!overlay||!active||!active.isConnected)return;
    const r=active.getBoundingClientRect();
    if(r.width<50 || r.bottom<0 || r.top>innerHeight){hide();return;}
    overlay.style.left=Math.max(6,Math.min(r.left,innerWidth-Math.max(230,r.width)-6))+'px';
    overlay.style.width=Math.min(Math.max(230,r.width),innerWidth-12)+'px';
    overlay.style.top=(r.bottom+300>innerHeight && r.top>310?Math.max(4,r.top-304):Math.min(innerHeight-80,r.bottom+4))+'px';
  };
  const texts=()=>labels();
  const render=()=>{
    const box=ensure();box.replaceChildren();position();
    const heading=document.createElement('div');heading.textContent=texts().title;
    heading.style.cssText='padding:9px 12px;background:#f1f5f9;color:#475569;font-size:11px;position:sticky;top:0;';box.appendChild(heading);
    if(!list.length){const empty=document.createElement('div');empty.textContent=texts().empty;empty.style.cssText='padding:12px;color:#64748b;';box.appendChild(empty);}
    for(const [i,item] of list.entries()){
      const row=document.createElement('button');row.type='button';row.setAttribute('role','option');
      row.setAttribute('aria-selected',String(i===selected));
      row.style.cssText='border:0;width:100%;text-align:start;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:10px 12px;background:'+(i===selected?'#dbeafe':'white')+';color:#0f172a;cursor:pointer;';
      const name=document.createElement('span');name.textContent=item.name;row.appendChild(name);
      const tag=document.createElement('small');tag.textContent=item.barcode||item.phone||texts().hint;tag.style.color='#64748b';row.appendChild(tag);
      row.addEventListener('pointerdown',ev=>ev.preventDefault());
      row.addEventListener('click',()=>choose(i));box.appendChild(row);
    }
    box.style.display='block';
  };
  const applyValue=(el,name)=>{
    const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')?.set;
    if(setter)setter.call(el,name);else el.value=name;
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
  };
  const choose=async index=>{
    const input=active,kind=identify(input),item=list[index];if(!input||!item||!kind)return;
    hide();const id=input.id||'';
    try{
      if(id==='productName' && typeof root.openProductModal==='function'){
        await root.openProductModal(item.id);return;
      }
      if(id==='customerName' && typeof root.editCustomer==='function'){
        root.editCustomer(item.id);return;
      }
      if(id==='supName' && typeof root.openSupplierModal==='function'){
        root.openSupplierModal(item);return;
      }
      if(id==='posProductSearchInput' && typeof root.addToCart==='function'){
        await root.addToCart(item.id);return;
      }
      if(id==='customProductNameInput' && typeof root.addToCart==='function'){
        // POS custom-item field: choose the registered item instead of custom duplicate.
        root.addToCart(item.id);return;
      }
      if(id==='bundleProductSearch' && typeof root.addProductToBundle==='function'){
        root.addProductToBundle(item.id,item.name,Number(item.pos_price||item.price||0),item.unit||'',Number(item.cost_price||0));return;
      }
      if(id==='promoProductSearch' && typeof root.selectPromoProduct==='function'){
        root.selectPromoProduct(item);return;
      }
      if(id==='invProductSearch'){
        applyValue(input,item.name);
        // Purchase search creates variant-aware result entries; use its own selector.
        await new Promise(resolve=>setTimeout(resolve,360));
        const idx=(root._invSearchResults||[]).findIndex(x=>String(x?.product?.id)===String(item.id) && !x.isParentOnly);
        if(idx>=0 && typeof root.selectInvProduct==='function')root.selectInvProduct(idx);
        return;
      }
      applyValue(input,item.name);
      input.focus({preventScroll:true});
    }catch(err){console.warn('[NANO POS] selection failed',err);}
  };
  const show=async input=>{
    const kind=identify(input),query=String(input.value||'').trim(),q=normalize(query);
    if(!kind||[...q].length<MIN){hide();return;}
    active=input;let seq=++serial;busy=true;
    try{
      const matches=await fetchMatches(root.api,kind,query);
      if(seq!==serial||active!==input||normalize(input.value)!==q)return;
      list=matches;selected=0;render();
    }catch(err){
      if(seq===serial){hide();console.warn('[NANO POS] suggestion lookup unavailable',err);}
    }finally{if(seq===serial)busy=false;}
  };
  const request=input=>{clearTimeout(timer);if(!identify(input))return;
    if([...normalize(input.value)].length<MIN){hide();return;}
    timer=setTimeout(()=>show(input),160);
  };
  document.addEventListener('input',e=>{const el=e.target;if(identify(el))request(el);},true);
  document.addEventListener('focusin',e=>{const el=e.target;if(identify(el))request(el);else if(!overlay?.contains(el))hide();});
  document.addEventListener('keydown',e=>{
    if(!active||overlay?.style.display==='none'||e.target!==active)return;
    if(e.key==='Escape'){hide();e.preventDefault();return;}
    if(!list.length)return;
    if(e.key==='ArrowDown'){selected=(selected+1)%list.length;render();e.preventDefault();}
    if(e.key==='ArrowUp'){selected=(selected+list.length-1)%list.length;render();e.preventDefault();}
    if(e.key==='Enter'){e.preventDefault();e.stopPropagation();choose(selected);}
  },true);
  document.addEventListener('pointerdown',e=>{if(active && e.target!==active && !overlay?.contains(e.target))hide();},true);
  document.addEventListener('scroll',()=>{if(active)position();},true);
  window.addEventListener('resize',()=>{if(active)position();});
  // Avoid stale matches after create or update; do not intercept or replace existing save APIs.
})(typeof window!=='undefined'?window:globalThis);
