/* NANO POS v1.0.46 — scope the top search to the currently visible business section.
 * No changes to original database, permissions, auth, or native search functions. */
(function (root) {
  'use strict';
  if (!root.document || root.__nanoSectionSearch146) return;
  root.__nanoSectionSearch146 = true;
  const doc = root.document;
  const labels = {
    suppliersSection: ['الموردين','Fournisseurs','Suppliers'],
    customersSection: ['الزبائن','Clients','Customers'],
    productsSection: ['المخزون والمنتجات','Stock et produits','Inventory and products'],
    salesLogSection: ['فواتير البيع','Ventes','Sales history'],
    purchasesSection: ['فواتير الشراء','Achats','Purchases'],
    proformasSection: ['الفواتير المبدئية','Proformas','Proforma invoices'],
    ordersSection: ['الطلبيات','Commandes','Orders'],
    promotionsSection: ['العروض الترويجية','Promotions','Promotions'],
    bundlesSection: ['الحزم','Lots','Bundles'],
    usersSection: ['المستخدمين','Utilisateurs','Users'],
    caisseSection: ['الصندوق','Caisse','Cash register'],
    analyticsSection: ['التحليلات والتقارير','Rapports','Reports'],
    printSection: ['ملصقات الطباعة','Étiquettes','Print labels'],
    stocktakeSection: ['الجرد','Inventaire','Stocktake'],
    manufacturingSection: ['التصنيع','Fabrication','Manufacturing'],
    settingsSection: ['الإعدادات','Paramètres','Settings'],
    aboutSection: ['حول البرنامج','À propos','About'],
    nanoHomeSection: ['الصفحة الرئيسية','Accueil','Home'],
    salesSection: ['البيع','Ventes','Sales']
  };
  const nativeInputs = {
    suppliersSection: 'supplierSearch',
    customersSection: 'customerSearch',
    productsSection: 'inventorySearch',
    printSection: 'plSearch'
  };
  const resultsContainers = {
    salesLogSection:['#salesHistoryTableBody'], purchasesSection:['#purchasesBody'],
    proformasSection:['#proformasTableBody'],ordersSection:['#ordersTableBody'],
    promotionsSection:['#promotionsTbody'],bundlesSection:['#bundlesTableBody'],
    usersSection:['#usersTableBody'],caisseSection:['#caisseTxBody','#caisseHistoryBody'],
    analyticsSection:['#anTopProductsTable','#anCustDebtsTable','#anSupDebtsTable','#anDebtAgingTable','#anLowStockTable','#anExpiryTable','#anExpensesTable','#anCapitalTable','#anCaisseLogTable']
  };
  const normalize = value => String(value == null ? '' : value).normalize('NFKC')
    .replace(/[\u064b-\u065f\u0670\u0640]/g,'').replace(/[إأآٱ]/g,'ا')
    .replace(/ى/g,'ي').replace(/ة/g,'ه').replace(/\s+/g,' ').trim().toLocaleLowerCase();
  const visible = element => !!(element && element.isConnected && !element.classList.contains('hidden') &&
      root.getComputedStyle(element).display!=='none' && element.getClientRects().length);
  const activeSection = () => {
    const open = [...doc.querySelectorAll('.content-section')].filter(visible);
    if (open.length === 1) return open[0];
    if (open.length > 1) return open.find(el=>el.id === root.location.hash.slice(1)) || open[0];
    const hash = root.location.hash.slice(1);
    const candidate = doc.getElementById(hash);
    return candidate?.classList.contains('content-section') && !candidate.classList.contains('hidden') ? candidate : null;
  };
  const language = () => {
    const l=String(root.currentLanguage||doc.documentElement.lang||'ar').toLowerCase();
    return l.startsWith('fr')?1:l.startsWith('en')?2:0;
  };
  const tr = values => values[language()];
  const searchName = section => tr(labels[section?.id] || ['هذه الصفحة','Cette page','This section']);
  let previousId='',observed=null,searchTimer=null,previousTerm='',lastAppliedTerm='',busy=false;
  let originalPlaceholder='',summary=null,suggestions=null;
  const tableRecords = new Set();
  const saved = new WeakMap();
  const emit = (node,event) => node.dispatchEvent(new Event(event,{bubbles:true}));
  const clearSuggestions = () => { if(suggestions){suggestions.remove(); suggestions=null;} };
  const restoreRows = () => {
    for (const row of tableRecords) {
      const original=saved.get(row);
      if (!original)continue;
      row.style.display=original.display;
      row.hidden=original.hidden;
      row.removeAttribute('data-nano-scoped-match');
    }
    tableRecords.clear();
  };
  const nativeSearch = (section,term,clearOnly=false) => {
    const id=nativeInputs[section.id],el=id&&doc.getElementById(id);
    if (!el || !section.contains(el)) return false;
    if (el.value !== term) {
      el.value=term;
      emit(el,'input'); emit(el,'keyup');
    } else if(!clearOnly){
      emit(el,'keyup');
    }
    return true;
  };
  const ensureSummary = input => {
    if(summary?.isConnected)return summary;
    const n=doc.createElement('div'); n.id='nano-v146-search-status'; n.setAttribute('role','status');n.setAttribute('aria-live','polite');
    n.style.cssText='display:none;position:absolute;z-index:30;top:100%;inset-inline-start:0;max-width:100%;padding:5px 10px;margin-top:3px;font-size:11px;border-radius:8px;background:#f8fafc;color:#334155;box-shadow:0 2px 10px #0001;pointer-events:none';
    (input.parentElement||doc.body).appendChild(n);summary=n;return n;
  };
  const status = (input, message) => {
    if(!input)return;
    const el=ensureSummary(input);
    el.textContent=message;el.style.display=message?'block':'none';
  };
  const searchableRows = section => {
    const selectors=resultsContainers[section.id];
    if(!selectors)return [];
    return selectors.flatMap(s=>[...section.querySelectorAll(s+' > tr')]);
  };
  const fallbackRows = section => {
    // A few workflows do not have their own search API. Search only record rows,
    // never forms, sidebar navigation, edit actions or authentication controls.
    const rows=searchableRows(section);
    if(rows.length)return rows;
    const candidates=section.querySelectorAll('[data-searchable-row], [data-record-row]');
    return [...candidates].filter(x=>x.getAttribute('data-searchable-row')!=='false');
  };
  const showSectionMatches = (section,term,input) => {
    clearSuggestions();
    if (!term) {status(input,'');return;}
    // Non-list sections (settings, stocktake, home, etc.) navigate to the
    // relevant existing control/setting instead of hiding application forms.
    const candidates=[...section.querySelectorAll('h1,h2,h3,h4,label,button,[role="tab"],summary')]
      .filter(node=>visible(node) && !node.closest('[role="dialog"],.hidden') &&
        normalize(node.textContent||'').includes(normalize(term)));
    const seen=new Set(), matches=[];
    for(const node of candidates){
      const value=(node.textContent||'').replace(/\s+/g,' ').trim();
      if(value && value.length<=160 && !seen.has(value)) {seen.add(value);matches.push([node,value]);}
      if(matches.length>=12)break;
    }
    status(input,tr([`${matches.length} نتيجة في ${searchName(section)}`,
      `${matches.length} résultat(s) dans ${searchName(section)}`,
      `${matches.length} matches in ${searchName(section)}`]));
    if(!matches.length)return;
    const box=doc.createElement('div');box.id='nano-v146-section-matches';
    box.style.cssText='position:absolute;z-index:45;top:calc(100% + 30px);left:0;right:0;max-height:290px;overflow:auto;background:white;color:#0f172a;border:1px solid #cbd5e1;border-radius:10px;box-shadow:0 12px 30px #0002;';
    for(const [node,text] of matches){
      const btn=doc.createElement('button');btn.type='button';btn.textContent=text;
      btn.style.cssText='display:block;width:100%;text-align:start;padding:9px 12px;border:0;background:white;color:#0f172a;font-size:12px;cursor:pointer;';
      btn.addEventListener('click',()=>{clearSuggestions();node.scrollIntoView({block:'center',behavior:'smooth'});if(node.matches('button,[role="tab"]'))node.focus({preventScroll:true});});
      box.appendChild(btn);
    }
    (input.parentElement||doc.body).appendChild(box);suggestions=box;
  };
  const filterRows = (section,term,input) => {
    const rows=fallbackRows(section);
    restoreRows();clearSuggestions();
    if (!term) {status(input,'');return;}
    let count=0;
    const needle=normalize(term);
    for(const row of rows){
      if(!saved.has(row))saved.set(row,{display:row.style.display,hidden:row.hidden});
      tableRecords.add(row);
      const match=normalize(row.textContent||'').includes(needle);
      row.hidden=!match;
      if(!match)row.style.display='none';
      if(match)count++;
      row.dataset.nanoScopedMatch=match?'1':'0';
    }
    if(!rows.length){
      showSectionMatches(section,term,input);
    }else{
      status(input,tr([`${count} من ${rows.length} سجل معروض`,`${count} sur ${rows.length} lignes affichées`,`${count} of ${rows.length} displayed records`]));
    }
  };
  const resetPrevious = () => {
    const old=doc.getElementById(previousId);
    if(old && nativeInputs[previousId])nativeSearch(old,'',true);
    restoreRows();clearSuggestions();
    if(summary)summary.style.display='none';
    previousTerm='';lastAppliedTerm='';
  };
  const setPlaceholder = (input,section) => {
    if(!input)return;
    if(!originalPlaceholder)originalPlaceholder=input.getAttribute('placeholder')||'';
    input.removeAttribute('data-i18n-placeholder');
    const n=searchName(section);
    input.placeholder=tr([`البحث في ${n}...`,`Rechercher : ${n}...`,`Search ${n}...`]);
    input.setAttribute('aria-label',input.placeholder);
  };
  const apply = (input, force=false) => {
    if(busy || !input)return;
    const section=activeSection();
    if(!section)return;
    if(previousId!==section.id){resetPrevious();previousId=section.id;input.value='';}
    setPlaceholder(input,section);
    const term=input.value.trim();
    if(!force && term===lastAppliedTerm)return;
    lastAppliedTerm=term;
    if(nativeInputs[section.id]){
      restoreRows();clearSuggestions();status(input,'');nativeSearch(section,term);return;
    }
    filterRows(section,term,input);
  };
  const syncSection = (input) => {
    const section=activeSection();
    if(!section)return;
    if(previousId!==section.id){resetPrevious();previousId=section.id;input.value='';}
    setPlaceholder(input,section);
  };
  const init = () => {
    const input=doc.getElementById('globalSearch');
    if(!input || input.dataset.nanoScopedSearch146==='1')return;
    input.dataset.nanoScopedSearch146='1';
    syncSection(input);
    input.addEventListener('input',()=>{
      root.clearTimeout(searchTimer); searchTimer=root.setTimeout(()=>apply(input),120);
    });
    input.addEventListener('keydown',evt=>{
      if(evt.key==='Escape' && input.value){input.value='';apply(input,true);evt.stopPropagation();}
    });
    // Navigate() manipulates hidden classes without a custom nav event.
    // Observing only the active sections avoids polling and closes stale search state.
    const sections=[...doc.querySelectorAll('.content-section')];
    const observer=new MutationObserver(()=>{
      const now=activeSection();
      if(now?.id!==previousId){syncSection(input);}
    });
    sections.forEach(x=>observer.observe(x,{attributes:true,attributeFilter:['class','style']}));
    root.addEventListener('hashchange',()=>syncSection(input));
    new MutationObserver(()=>setPlaceholder(input,activeSection())).observe(doc.documentElement,{attributes:true,attributeFilter:['lang']});
    doc.addEventListener('click',evt=>{
      if(evt.target.closest('.nav-btn,[data-target-section]'))root.setTimeout(()=>syncSection(input),0);
    });
    // Newly populated result tables should respect the current term.
    const listingObserver=new MutationObserver(mutations=>{
      if(!input.value.trim() || busy || nativeInputs[previousId])return;
      if(mutations.some(x=>x.target?.closest?.('#nano-v146-search-status')))return;
      root.clearTimeout(searchTimer);
      searchTimer=root.setTimeout(()=>{busy=true;try{const section=activeSection();if(section?.id===previousId)filterRows(section,input.value,input);}finally{busy=false;}},160);
    });
    for(const section of sections){
      if(resultsContainers[section.id]) listingObserver.observe(section,{subtree:true,childList:true});
    }
    root.NANO_SECTION_SEARCH146={getCurrentSection:()=>activeSection()?.id||'',apply:(query)=>{input.value=String(query);apply(input,true);},normalize};
  };
  if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);
