#!/usr/bin/env python3
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
SPEECH = r"""
;
/* NANO POS v2.0.17: general improvements and cart price speech; prayer feature removed */
(function(){
  if (window.__nanoCartSpeechV202) return;
  window.__nanoCartSpeechV202 = true;
  var activeList=null, listObserver=null, lastSignature='', timer=null;
  function uiLang(){
    var lang=(window.currentLanguage || document.getElementById('settLanguage')?.value || document.documentElement.lang || '').toLowerCase();
    if(lang.indexOf('ar')===0 || document.documentElement.dir==='rtl') return 'ar';
    if(lang.indexOf('fr')===0) return 'fr';
    var txt=(document.body&&document.body.innerText||'').slice(0,3000);
    if(/[\u0600-\u06FF]/.test(txt)) return 'ar';
    if(/Produits|Ventes|Paramètres|Ajouter au panier/i.test(txt)) return 'fr';
    return 'en';
  }
  function notify(lang){
    var msg=lang==='ar'?'تمت إضافة المنتج إلى السلة':lang==='fr'?'Produit ajouté au panier':'Product added to cart';
    var old=document.getElementById('__nanoCartSpeechToast'); if(old) old.remove();
    var el=document.createElement('div'); el.id='__nanoCartSpeechToast'; el.textContent='✓  '+msg;
    el.style.cssText='position:fixed;z-index:2147483647;top:18px;right:18px;max-width:calc(100vw - 36px);padding:12px 18px;border-radius:12px;background:#0f766e;color:white;font:700 14px/1.4 system-ui,sans-serif;box-shadow:0 8px 30px #0003;';
    if(lang==='ar'){el.style.right='auto';el.style.left='18px';el.dir='rtl';}
    document.body.appendChild(el); setTimeout(function(){if(el.isConnected)el.remove();},2200);
  }
  function normalizePrice(raw){
    var s=String(raw||'').replace(/[\s\u00a0]/g,'');
    if(!s)return null;
    var comma=s.lastIndexOf(','), dot=s.lastIndexOf('.');
    if(comma>=0 && dot>=0){
      var decimal=Math.max(comma,dot), decimals=s.length-decimal-1;
      s=s.slice(0,decimal).replace(/[.,]/g,'')+(decimals>0&&decimals<=2?'.'+s.slice(decimal+1):s.slice(decimal+1));
    }else if(comma>=0){
      var tail=s.length-comma-1;
      s=tail>0&&tail<=2?s.slice(0,comma)+'.'+s.slice(comma+1):s.replace(/,/g,'');
    }else if(dot>=0 && s.length-dot-1>2)s=s.replace(/\./g,'');
    var n=Number(s);
    return Number.isFinite(n)&&n>=0?String(n):null;
  }
  function priceFromRow(row){
    if(!row)return null;
    var selectors=['[data-unit-price]','[data-product-price]','[data-price]','.cart-item-price','.item-price','.product-price','[class*="unit-price"]','[class*="item-price"]','[class*="product-price"]','[class*="price"]:not([class*="total"]):not([class*="discount"])'];
    for(var i=0;i<selectors.length;i++){
      var nodes=[];
      try{nodes=(row.matches&&row.matches(selectors[i])?[row]:[]).concat(Array.from(row.querySelectorAll(selectors[i])))}catch(e){}
      for(var j=0;j<nodes.length;j++){
        var n=nodes[j], raw=n.getAttribute('data-unit-price')||n.getAttribute('data-product-price')||n.getAttribute('data-price')||n.textContent||'';
        var price=normalizePrice(String(raw).match(/\d[\d\s.,]*/)?.[0]||'');
        if(price!==null)return price;
      }
    }
    return null;
  }
  function speakPrice(row,lang){
    if(!('speechSynthesis' in window)||!window.SpeechSynthesisUtterance)return;
    var price=priceFromRow(row);
    if(price===null)return;
    var prefix=lang==='ar'?'سعر المنتج المضاف إلى السلة':lang==='fr'?'Prix du produit ajouté au panier':'Price of the added product';
    var currency=lang==='ar'?'دينار جزائري':lang==='fr'?'dinars algériens':'Algerian dinars';
    var utter=new SpeechSynthesisUtterance(prefix+' '+price+' '+currency);
    utter.lang=lang==='ar'?'ar-DZ':lang==='fr'?'fr-FR':'en-US'; utter.rate=0.92;
    try{window.speechSynthesis.cancel();window.speechSynthesis.speak(utter);}catch(e){}
  }
  function rows(list){
    return Array.from(list.children||[]).filter(function(n){
      var text=n.nodeType===1?(n.innerText||n.textContent||'').trim():'';
      return !!text&&!/empty cart|panier vide|السلة فارغة/i.test(text)&&!n.querySelector('[data-i18n="empty_cart_msg"]');
    });
  }
  function observeList(list){
    if(!list||activeList===list)return;
    if(listObserver)listObserver.disconnect();
    activeList=list; lastSignature='';
    function scan(){
      clearTimeout(timer);
      timer=setTimeout(function(){
        if(!activeList||!activeList.isConnected)return;
        var current=rows(activeList);
        var signature=current.map(function(r){return (r.innerText||r.textContent||'').replace(/\s+/g,' ').trim();}).join('||');
        if(signature && signature!==lastSignature){
          var hadPrevious=!!lastSignature; lastSignature=signature;
          if(hadPrevious){var row=current[current.length-1],lang=uiLang();notify(lang);speakPrice(row,lang);}
        }else lastSignature=signature;
      },120);
    }
    listObserver=new MutationObserver(scan);
    listObserver.observe(list,{childList:true,subtree:true,characterData:true,attributes:true});
    scan();
  }
  function findList(){return document.getElementById('cartItemsList')||document.querySelector('[id*="cartItemsList"],[data-cart-items],.cart-items-list');}
  function init(){var list=findList();if(list)observeList(list);}
  function start(){
    init();
    if(document.body)new MutationObserver(init).observe(document.body,{childList:true,subtree:true});
    setInterval(init,1000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
"""




OPS_CHARTS = r"""
;
/* NANO POS v2.0.17: live operational charts for cash, stock, sales and purchases */
(function(){
  if (window.__nanoOperationalAnalyticsV217) return;
  window.__nanoOperationalAnalyticsV217 = true;
  var chartRefs = Object.create(null), renderSequence = 0, currentStats = null;
  var cacheRevision = null, cachedProducts = null, cachedPurchases = null;
  var productsPromise = null, purchasesPromise = null, refreshTimer = null;
  function lang(){
    var raw = String(window.currentLanguage || document.getElementById('settLanguage')?.value ||
      localStorage.getItem('nano_pos_language') || document.documentElement.lang || '').toLowerCase();
    if (raw.indexOf('fr')===0) return 'fr';
    if (raw.indexOf('en')===0) return 'en';
    if (document.documentElement.dir==='rtl' || raw.indexOf('ar')===0) return 'ar';
    var body = (document.body && document.body.innerText || '').slice(0,1800);
    if (/المبيعات|المخزون|الصندوق/.test(body)) return 'ar';
    if (/Ventes|Stock|Caisse/.test(body)) return 'fr';
    return 'en';
  }
  var dict = {
    ar:{
      title:'لوحة الحركة التجارية والصندوق والمخزون',
      subtitle:'تتحدث الرسوم حسب الفترة المحددة، وتُحدّث بعد حفظ عمليات البيع أو الشراء أو المخزون والمزامنة.',
      sales:'المبيعات', purchases:'المشتريات', expenses:'المصاريف',
      cash:'حركة الصندوق', cashNote:'حسب الجلسة المفتوحة؛ وإذا لم توجد جلسة تُعرض حركة الفترة المحددة.',
      in:'المقبوضات', out:'المدفوعات', cashSales:'مبيعات نقدية', deposits:'إيداعات', withdrawals:'سحوبات', refunds:'مرتجعات',
      periodCompare:'مقارنة البيع والشراء والمصاريف', periodNote:'القيم المالية ضمن الفترة المحددة أعلاه.',
      trend:'حركة البيع والشراء عبر الزمن', trendNote:'يوميًا للفترات القصيرة، وشهريًا أو ربع سنويًا للفترات الأطول.',
      stockUnits:'توزيع وحدات المخزون حسب الفئة', stockNote:'يعرض الوحدات الموجودة حاليًا، لا قيمة المبيعات.',
      stockValue:'قيمة المخزون بالتكلفة وسعر البيع', stockValueNote:'مقارنة قيمة الوحدات المتبقية بسعر التكلفة وقيمتها المحتملة بسعر البيع.',
      costValue:'قيمة المخزون بالتكلفة', sellValue:'قيمة المخزون بسعر البيع',
      salesCount:'عدد فواتير البيع', purchaseCount:'عدد فواتير الشراء',
      netFlow:'صافي حركة الفترة', boxBalance:'الرصيد المتوقع للصندوق',
      stockTotal:'إجمالي الوحدات', lowStock:'منتجات تحت حد المخزون',
      noSession:'لا توجد مناوبة مفتوحة؛ تعرض الدائرة المقبوضات والمدفوعات في الفترة المحددة.',
      noData:'لا توجد بيانات كافية لعرض هذا الرسم في الفترة المحددة.',
      noProducts:'لا توجد كميات مخزنة كافية لتوزيعها حسب الفئة.',
      category:'غير مصنف', other:'فئات أخرى', unit:'وحدة', dinar:'دج'
    },
    fr:{
      title:'Tableau de bord des ventes, achats, caisse et stock',
      subtitle:'Les graphiques suivent la période sélectionnée et se rafraîchissent après une opération ou une synchronisation.',
      sales:'Ventes', purchases:'Achats', expenses:'Dépenses',
      cash:'Mouvements de caisse', cashNote:'Session ouverte ; sinon, flux de la période sélectionnée.',
      in:'Entrées', out:'Sorties', cashSales:'Ventes en espèces', deposits:'Dépôts', withdrawals:'Retraits', refunds:'Remboursements',
      periodCompare:'Comparaison ventes, achats et dépenses', periodNote:'Montants financiers de la période sélectionnée.',
      trend:'Évolution des ventes et des achats', trendNote:'Par jour sur une courte période, par mois ou trimestre sur une longue période.',
      stockUnits:'Répartition des unités en stock par catégorie', stockNote:'Unités actuellement en stock, et non chiffre d’affaires.',
      stockValue:'Valeur du stock au coût et au prix de vente', stockValueNote:'Compare le coût du stock restant à sa valeur potentielle au prix de vente.',
      costValue:'Valeur au coût', sellValue:'Valeur au prix de vente',
      salesCount:'Factures de vente', purchaseCount:'Factures d’achat',
      netFlow:'Flux net de la période', boxBalance:'Solde prévisionnel de caisse',
      stockTotal:'Unités en stock', lowStock:'Produits sous le seuil',
      noSession:'Aucune session ouverte ; le graphique montre les entrées et sorties de la période.',
      noData:'Données insuffisantes pour cette période.',
      noProducts:'Aucune quantité en stock à répartir par catégorie.',
      category:'Non classé', other:'Autres catégories', unit:'unité(s)', dinar:'DA'
    },
    en:{
      title:'Sales, purchases, cash and inventory dashboard',
      subtitle:'Charts follow the selected period and refresh after saved transactions or synchronization.',
      sales:'Sales', purchases:'Purchases', expenses:'Expenses',
      cash:'Cash-register movements', cashNote:'Open session; if none is open, the selected-period cash flow is shown.',
      in:'Cash received', out:'Cash paid', cashSales:'Cash sales', deposits:'Deposits', withdrawals:'Withdrawals', refunds:'Refunds',
      periodCompare:'Sales, purchases and expenses comparison', periodNote:'Financial values for the selected period.',
      trend:'Sales and purchases over time', trendNote:'Daily for short periods, monthly or quarterly for longer periods.',
      stockUnits:'Inventory units by category', stockNote:'Current on-hand units, not sales revenue.',
      stockValue:'Inventory at cost and sale value', stockValueNote:'Compares remaining stock cost with its potential value at selling prices.',
      costValue:'Inventory cost value', sellValue:'Inventory sale value',
      salesCount:'Sales invoices', purchaseCount:'Purchase invoices',
      netFlow:'Net period cash flow', boxBalance:'Expected cash balance',
      stockTotal:'Units in stock', lowStock:'Products below minimum',
      noSession:'No open cash session; this chart shows cash in and out for the selected period.',
      noData:'Not enough data for this chart in the selected period.',
      noProducts:'No stocked units available to break down by category.',
      category:'Uncategorized', other:'Other categories', unit:'units', dinar:'DZD'
    }
  };
  function words(){ return dict[lang()] || dict.en; }
  function n(v){ var x=Number(v); return Number.isFinite(x)?x:0; }
  function money(v){
    try { return new Intl.NumberFormat(lang()==='ar'?'ar-DZ':lang()==='fr'?'fr-DZ':'en-US',{maximumFractionDigits:0}).format(n(v))+' '+words().dinar; }
    catch(e){ return Math.round(n(v)).toLocaleString()+' '+words().dinar; }
  }
  function number(v){
    try { return new Intl.NumberFormat(lang()==='ar'?'ar-DZ':lang()==='fr'?'fr-DZ':'en-US',{maximumFractionDigits:0}).format(n(v)); }
    catch(e){ return String(Math.round(n(v))); }
  }
  function setText(id,value){ var el=document.getElementById(id); if(el) el.textContent=String(value); }
  function card(id,title,icon,colour,canvas,empty){
    return '<article class="bg-white dark:bg-surface-container-low rounded-2xl border border-slate-200 dark:border-outline-variant/10 shadow-sm p-5 min-w-0">'
      +'<h3 class="font-headline font-black text-sm text-slate-800 dark:text-on-surface mb-2 flex items-center gap-2">'
      +'<span class="material-symbols-outlined '+colour+'">'+icon+'</span><span id="'+id+'Title">'+title+'</span></h3>'
      +'<p id="'+id+'Note" class="text-[11px] font-bold text-slate-500 dark:text-on-surface-variant mb-3"></p>'
      +'<div class="relative w-full" style="height:270px"><canvas id="'+canvas+'" style="width:100%;height:270px"></canvas>'
      +'<div id="'+empty+'" class="hidden absolute inset-0 flex items-center justify-center text-center text-xs font-bold text-slate-400 px-5"></div></div></article>';
  }
  function ensurePanel(){
    var tab=document.getElementById('analyticsTab-charts');
    if(!tab) return null;
    var root=document.getElementById('nanoOperationalAnalyticsV217');
    if(!root){
      root=document.createElement('div'); root.id='nanoOperationalAnalyticsV217';
      root.className='mb-8 space-y-5';
      root.innerHTML='<div class="rounded-2xl border border-blue-100 dark:border-outline-variant/20 bg-blue-50/60 dark:bg-surface-container-low p-5">'
        +'<div class="flex flex-wrap items-start justify-between gap-3"><div><h2 id="nanoOpsTitle" class="text-xl font-black text-slate-900 dark:text-on-surface"></h2><p id="nanoOpsSubtitle" class="text-xs font-bold text-slate-500 dark:text-on-surface-variant mt-2"></p></div>'
        +'<span class="material-symbols-outlined text-blue-600 dark:text-primary text-3xl">monitoring</span></div>'
        +'<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 mt-5">'
        +'<div class="rounded-xl bg-white dark:bg-surface-container-high p-4 border border-slate-100 dark:border-outline-variant/10"><p id="nanoOpsSalesLabel" class="text-xs font-bold text-slate-500"></p><strong id="nanoOpsSalesValue" class="block text-lg font-black text-emerald-600 mt-2">0</strong><p id="nanoOpsSalesMeta" class="text-[10px] text-slate-400 mt-1"></p></div>'
        +'<div class="rounded-xl bg-white dark:bg-surface-container-high p-4 border border-slate-100 dark:border-outline-variant/10"><p id="nanoOpsPurchasesLabel" class="text-xs font-bold text-slate-500"></p><strong id="nanoOpsPurchasesValue" class="block text-lg font-black text-blue-600 mt-2">0</strong><p id="nanoOpsPurchasesMeta" class="text-[10px] text-slate-400 mt-1"></p></div>'
        +'<div class="rounded-xl bg-white dark:bg-surface-container-high p-4 border border-slate-100 dark:border-outline-variant/10"><p id="nanoOpsCashLabel" class="text-xs font-bold text-slate-500"></p><strong id="nanoOpsCashValue" class="block text-lg font-black text-violet-600 mt-2">0</strong><p id="nanoOpsCashMeta" class="text-[10px] text-slate-400 mt-1"></p></div>'
        +'<div class="rounded-xl bg-white dark:bg-surface-container-high p-4 border border-slate-100 dark:border-outline-variant/10"><p id="nanoOpsStockLabel" class="text-xs font-bold text-slate-500"></p><strong id="nanoOpsStockValue" class="block text-lg font-black text-amber-600 mt-2">0</strong><p id="nanoOpsStockMeta" class="text-[10px] text-slate-400 mt-1"></p></div>'
        +'</div></div>'
        +'<div class="grid grid-cols-1 xl:grid-cols-2 gap-5">'
        +card('nanoOpsCash','', 'account_balance_wallet','text-emerald-600','nanoChartCashSession','nanoChartCashSessionEmpty')
        +card('nanoOpsCompare','', 'bar_chart','text-blue-600','nanoChartSalesPurchases','nanoChartSalesPurchasesEmpty')
        +card('nanoOpsTrend','', 'stacked_bar_chart','text-violet-600','nanoChartPurchaseTrend','nanoChartPurchaseTrendEmpty')
        +card('nanoOpsStock','', 'pie_chart','text-amber-600','nanoChartStockCategories','nanoChartStockCategoriesEmpty')
        +card('nanoOpsValue','', 'inventory_2','text-cyan-600','nanoChartInventoryValue','nanoChartInventoryValueEmpty')
        +'</div>';
      tab.insertBefore(root,tab.firstChild);
    }
    var w=words();
    setText('nanoOpsTitle',w.title); setText('nanoOpsSubtitle',w.subtitle);
    setText('nanoOpsSalesLabel',w.sales); setText('nanoOpsPurchasesLabel',w.purchases);
    setText('nanoOpsCashLabel',w.netFlow); setText('nanoOpsStockLabel',w.stockTotal);
    setText('nanoOpsCashTitle',w.cash); setText('nanoOpsCompareTitle',w.periodCompare);
    setText('nanoOpsTrendTitle',w.trend); setText('nanoOpsStockTitle',w.stockUnits);
    setText('nanoOpsValueTitle',w.stockValue);
    setText('nanoOpsCompareNote',w.periodNote); setText('nanoOpsTrendNote',w.trendNote);
    setText('nanoOpsStockNote',w.stockNote); setText('nanoOpsValueNote',w.stockValueNote);
    setText('nanoOpsCashNote',w.cashNote);
    return root;
  }
  function setEmpty(canvasId,emptyId,message){
    var c=document.getElementById(canvasId), e=document.getElementById(emptyId);
    if(c) c.style.display='none';
    if(e){e.textContent=message;e.classList.remove('hidden');}
  }
  function useCanvas(canvasId,emptyId){
    var c=document.getElementById(canvasId), e=document.getElementById(emptyId);
    if(!c) return null;
    c.style.display='block'; if(e)e.classList.add('hidden');
    if(chartRefs[canvasId]){try{chartRefs[canvasId].destroy();}catch(err){} delete chartRefs[canvasId];}
    return c;
  }
  function draw(canvasId,emptyId,type,labels,datasets,opts){
    var canvas=useCanvas(canvasId,emptyId);
    if(!canvas) return;
    if(typeof Chart==='undefined'){setEmpty(canvasId,emptyId,'Chart.js');return;}
    var total=0; datasets.forEach(function(ds){(ds.data||[]).forEach(function(v){total+=Math.abs(n(v));});});
    if(!labels.length || total===0){setEmpty(canvasId,emptyId,words().noData);return;}
    try{
      chartRefs[canvasId]=new Chart(canvas,{type:type,data:{labels:labels,datasets:datasets},options:Object.assign({
        responsive:true,maintainAspectRatio:false,animation:{duration:250},
        plugins:{legend:{display:type==='doughnut'||type==='pie',position:'bottom',labels:{font:{family:'Tajawal',weight:'bold'},padding:14}},
          tooltip:{callbacks:{label:function(ctx){var v=ctx.parsed&&typeof ctx.parsed.y==='number'?ctx.parsed.y:(typeof ctx.parsed==='number'?ctx.parsed:(ctx.raw||0));return ' '+ctx.label+': '+money(v);}}}},
        scales:type==='bar'?{y:{beginAtZero:true,ticks:{callback:function(v){return number(v);}}},x:{ticks:{font:{family:'Tajawal',weight:'bold'},autoSkip:true,maxRotation:0}}}:{}
      },opts||{})});
    }catch(err){console.error('[NANO analytics] chart failed',canvasId,err);setEmpty(canvasId,emptyId,words().noData);}
  }
  function getRevision(data){return data&&data.statisticsInputs&&data.statisticsInputs.revision!==undefined?String(data.statisticsInputs.revision):'unknown';}
  function invalidateCaches(data){
    var rev=getRevision(data);
    if(cacheRevision!==rev){cacheRevision=rev;cachedProducts=null;cachedPurchases=null;productsPromise=null;purchasesPromise=null;}
  }
  function getProducts(){
    if(Array.isArray(cachedProducts)) return Promise.resolve(cachedProducts);
    if(!productsPromise){
      productsPromise=Promise.resolve(window.api&&window.api.getProducts?window.api.getProducts():[])
        .then(function(r){cachedProducts=Array.isArray(r)?r:(Array.isArray(r&&r.products)?r.products:[]);return cachedProducts;})
        .catch(function(e){console.warn('[NANO analytics] stock products unavailable',e);cachedProducts=[];return cachedProducts;});
    }
    return productsPromise;
  }
  function getPurchases(){
    if(Array.isArray(cachedPurchases)) return Promise.resolve(cachedPurchases);
    if(!purchasesPromise){
      purchasesPromise=Promise.resolve(window.api&&window.api.getPurchases?window.api.getPurchases():[])
        .then(function(r){cachedPurchases=Array.isArray(r)?r:(Array.isArray(r&&r.purchases)?r.purchases:[]);return cachedPurchases;})
        .catch(function(e){console.warn('[NANO analytics] purchases unavailable',e);cachedPurchases=[];return cachedPurchases;});
    }
    return purchasesPromise;
  }
  function getCaisse(userId){
    if(!window.api||typeof window.api.getCaisseSummary!=='function') return Promise.resolve(null);
    return Promise.resolve(window.api.getCaisseSummary(userId)).catch(function(e){console.warn('[NANO analytics] cash summary unavailable',e);return null;});
  }
  function datePart(v){var s=String(v||'').slice(0,10);return /^\d{4}-\d{2}-\d{2}$/.test(s)?s:'';}
  function filterDates(){
    return {from:datePart(document.getElementById('analyticsDateFrom')?.value),to:datePart(document.getElementById('analyticsDateTo')?.value)};
  }
  function purchaseDate(p){return datePart(p&&(p.invoice_date||p.purchase_date||p.date||p.created_at||p.updated_at));}
  function purchaseTotal(p){return n(p&&(p.total??p.total_amount??p.invoice_total??p.amount));}
  function inRange(d,range){return !!d&&(!range.from||d>=range.from)&&(!range.to||d<=range.to);}
  function bucketFor(date,mode){
    if(mode==='day') return date;
    if(mode==='month') return date.slice(0,7);
    var y=Number(date.slice(0,4)),m=Number(date.slice(5,7));
    return String(y)+'-Q'+String(Math.floor((m-1)/3)+1);
  }
  function modeFor(range,dates){
    var a=range.from||dates[0]||'', b=range.to||dates[dates.length-1]||'';
    if(!a||!b)return 'day';
    var span=Math.abs(new Date(b+'T00:00:00').getTime()-new Date(a+'T00:00:00').getTime())/86400000;
    return span<=45?'day':span<=550?'month':'quarter';
  }
  function showBucket(key,mode){
    if(mode==='day') return key.slice(8,10)+'/'+key.slice(5,7);
    if(mode==='month') return key.slice(5,7)+'/'+key.slice(0,4);
    var m=key.match(/^(\d{4})-Q([1-4])$/);return m?(lang()==='ar'?'الربع ':'Q')+m[2]+' '+m[1]:key;
  }
  function stockByCategory(products){
    var groups=Object.create(null);
    (products||[]).forEach(function(p){
      var qty=Math.max(0,n(p.stock??p.quantity??p.current_stock));
      if(qty<=0)return;
      var c=String(p.category||p.family||p.group||words().category).trim()||words().category;
      groups[c]=(groups[c]||0)+qty;
    });
    var rows=Object.keys(groups).map(function(k){return {label:k,value:groups[k]};}).sort(function(a,b){return b.value-a.value;});
    if(rows.length>8){var rest=rows.slice(7).reduce(function(s,r){return s+r.value;},0);rows=rows.slice(0,7);rows.push({label:words().other,value:rest});}
    return rows;
  }
  function drawCore(data,caisse,purchases,products){
    var w=words(), sales=data&&data.sales||{}, purch=data&&data.purchases||{}, inv=data&&data.inventory||{};
    var rev=n(sales.revenue??sales.net_revenue), purchTotal=n(purch.total_purchases), expenses=n(data&&data.totalExpenses);
    var cashIn=n(data&&data.cashIn), cashOut=n(data&&data.cashOut), cashDelta=cashIn-cashOut;
    setText('nanoOpsSalesValue',money(rev));
    setText('nanoOpsSalesMeta',number(sales.total_sales_count)+' · '+w.salesCount);
    setText('nanoOpsPurchasesValue',money(purchTotal));
    setText('nanoOpsPurchasesMeta',number(purch.total_invoices)+' · '+w.purchaseCount);
    var boxBalance=caisse&&caisse.active?n(caisse.expectedBalance??caisse.currentBalance??caisse.balance):cashDelta;
    setText('nanoOpsCashValue',money(boxBalance));
    setText('nanoOpsCashLabel',caisse&&caisse.active?w.boxBalance:w.netFlow);
    setText('nanoOpsCashMeta',caisse&&caisse.active?(lang()==='ar'?'مناوبة مفتوحة':lang()==='fr'?'Session ouverte':'Open session'):(lang()==='ar'?'حسب الفترة المحددة':lang()==='fr'?'Période sélectionnée':'Selected period'));
    setText('nanoOpsStockValue',number(inv.total_units)+' '+w.unit);
    setText('nanoOpsStockMeta',number((data&&data.lowStock||[]).length)+' · '+w.lowStock);
    if(caisse&&caisse.active){
      var cData=[
        n(caisse.totalSalesCash),n(caisse.totalCashIn),n(caisse.totalExpenses),
        n(caisse.totalCashOut),n(caisse.totalRefunds)
      ];
      draw('nanoChartCashSession','nanoChartCashSessionEmpty','doughnut',
        [w.cashSales,w.deposits,w.expenses,w.withdrawals,w.refunds],
        [{data:cData,backgroundColor:['#10b981','#3b82f6','#ef4444','#f59e0b','#8b5cf6'],borderColor:'transparent',borderWidth:2}],
        {plugins:{legend:{display:true,position:'bottom'}}});
    }else{
      draw('nanoChartCashSession','nanoChartCashSessionEmpty','doughnut',[w.in,w.out],
        [{data:[cashIn,cashOut],backgroundColor:['#10b981','#ef4444'],borderColor:'transparent',borderWidth:2}],
        {plugins:{legend:{display:true,position:'bottom'}}});
      setText('nanoOpsCashNote',w.noSession);
    }
    draw('nanoChartSalesPurchases','nanoChartSalesPurchasesEmpty','bar',
      [w.sales,w.purchases,w.expenses],
      [{label:w.periodCompare,data:[rev,purchTotal,expenses],backgroundColor:['#10b981','#3b82f6','#ef4444'],borderRadius:7,maxBarThickness:76}],
      {plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{callback:function(v){return number(v);}}}}});
    var cost=n(inv.cost_value), sell=n(inv.sell_value);
    draw('nanoChartInventoryValue','nanoChartInventoryValueEmpty','bar',[w.costValue,w.sellValue],
      [{label:w.stockValue,data:[cost,sell],backgroundColor:['#0ea5e9','#10b981'],borderRadius:7,maxBarThickness:92}],
      {plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{callback:function(v){return number(v);}}}}});
    var cats=stockByCategory(products);
    if(cats.length){
      draw('nanoChartStockCategories','nanoChartStockCategoriesEmpty','doughnut',
        cats.map(function(x){return x.label;}),
        [{data:cats.map(function(x){return x.value;}),backgroundColor:['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#f97316','#94a3b8'],borderWidth:2,borderColor:'transparent'}],
        {plugins:{legend:{display:true,position:'bottom'},tooltip:{callbacks:{label:function(ctx){return ' '+ctx.label+': '+number(ctx.raw)+' '+w.unit;}}}}});
    }else setEmpty('nanoChartStockCategories','nanoChartStockCategoriesEmpty',w.noProducts);
    var range=filterDates(), salesBy={}, purchaseBy={}, dates=[];
    (data&&data.dailySalesTrend||[]).forEach(function(r){
      var d=datePart(r.date); if(!inRange(d,range))return;
      salesBy[d]=(salesBy[d]||0)+n(r.revenue);dates.push(d);
    });
    (purchases||[]).forEach(function(p){
      var d=purchaseDate(p); if(!inRange(d,range))return;
      purchaseBy[d]=(purchaseBy[d]||0)+purchaseTotal(p);dates.push(d);
    });
    dates=Array.from(new Set(dates)).sort();
    var mode=modeFor(range,dates), buckets={}, keys=[];
    dates.forEach(function(d){
      var k=bucketFor(d,mode);if(!buckets[k]){buckets[k]={sales:0,purchases:0};keys.push(k);}
      buckets[k].sales+=(salesBy[d]||0);buckets[k].purchases+=(purchaseBy[d]||0);
    });
    keys=Array.from(new Set(keys)).sort();
    draw('nanoChartPurchaseTrend','nanoChartPurchaseTrendEmpty','bar',
      keys.map(function(k){return showBucket(k,mode);}),
      [
        {label:w.sales,data:keys.map(function(k){return Math.round(buckets[k].sales);}),backgroundColor:'#10b981',borderRadius:4,maxBarThickness:28},
        {label:w.purchases,data:keys.map(function(k){return Math.round(buckets[k].purchases);}),backgroundColor:'#3b82f6',borderRadius:4,maxBarThickness:28}
      ],
      {plugins:{legend:{display:true,position:'bottom'}},scales:{y:{beginAtZero:true,ticks:{callback:function(v){return number(v);}}},x:{ticks:{autoSkip:true,maxTicksLimit:14,maxRotation:0}}}});
  }
  function render(data){
    currentStats=data||{}; var token=++renderSequence;
    ensurePanel(); invalidateCaches(currentStats);
    var rev=getRevision(currentStats), userId;
    try{userId=typeof currentUser!=='undefined'&&currentUser?currentUser.id:undefined;}catch(e){}
    Promise.all([getCaisse(userId),getPurchases(),getProducts()]).then(function(parts){
      if(token!==renderSequence)return;
      drawCore(currentStats,parts[0],parts[1],parts[2]);
      setText('nanoOpsCashNote',words().cashNote);
      if(!(parts[0]&&parts[0].active))setText('nanoOpsCashNote',words().noSession);
      try{Object.keys(chartRefs).forEach(function(id){if(chartRefs[id])chartRefs[id].resize();});}catch(e){}
    }).catch(function(e){console.warn('[NANO analytics] refresh failed',e);});
  }
  var originalRender=window.renderAnalyticsCharts;
  if(typeof originalRender==='function'){
    window.renderAnalyticsCharts=function(data){
      var result=originalRender.apply(this,arguments);
      try{render(data);}catch(e){console.error('[NANO analytics] dashboard render failed',e);}
      return result;
    };
  }
  var originalSwitch=window.switchAnalyticsTab;
  if(typeof originalSwitch==='function'){
    window.switchAnalyticsTab=function(){
      var result=originalSwitch.apply(this,arguments);
      var tab=arguments[0];
      if(tab==='charts')setTimeout(function(){try{Object.keys(chartRefs).forEach(function(id){chartRefs[id]?.resize();});}catch(e){}},80);
      return result;
    };
  }
  function scheduleRefresh(){
    var section=document.getElementById('analyticsSection');
    if(!section||section.classList.contains('hidden')||refreshTimer)return;
    refreshTimer=setTimeout(function(){
      refreshTimer=null;
      if(document.getElementById('analyticsSection')&&!document.getElementById('analyticsSection').classList.contains('hidden')&&typeof loadAnalytics==='function'){
        try{loadAnalytics();}catch(e){console.warn('[NANO analytics] automatic refresh failed',e);}
      }
    },500);
  }
  window.addEventListener('nano-pos-data-saved',scheduleRefresh);
  window.addEventListener('visibilitychange',function(){if(!document.hidden)scheduleRefresh();});
  try{window.api?.cloudSync?.onDataChanged?.(scheduleRefresh);}catch(e){}
})();
"""


def build(src,dest,work):
  with zipfile.ZipFile(src) as z:
    assert z.namelist()==['payload/app.asar'],z.namelist()
    raw=z.read('payload/app.asar')
  magic,block,hs,n=struct.unpack_from('<4I',raw)
  assert magic==4 and block==hs+4
  tree=json.loads(raw[16:16+n]); start=8+block
  entries=[]
  def walk(node,prefix=''):
    for name,e in node.get('files',{}).items():
      path=prefix+name
      if 'files' in e: walk(e,path+'/')
      elif 'offset' in e and 'size' in e: entries.append((path,e))
  walk(tree); entries.sort(key=lambda x:int(x[1]['offset']))
  # Audit the stable baseline before making a consolidated release.
  by_name={name:e for name,e in entries}
  required=[
    'update-manager.js','mega-backup-ui.js','browser-bridge.js','nano-fast-pos.js',
    'nano-cash-change.js','nano-flex-payment-108.js','nano-credit-picker-107.js',
    'nano-payment-ledger-102.js','nano-payment-quality-105.js','nano-restock-assistant.js',
    'nano-stock-forecast-198.js','nano-po-auto-supplier-100.js','nano-po-shortage-ui-100.js',
    'nano-inventory-shortages.js','nano-product-analytics.js','nano-trade-analytics-101.js',
    'nano-sales-safe-195.js','navigation-performance.js','nano-price-display.js','nano-sales-layout.js'
  ]
  missing=[name for name in required if name not in by_name]
  assert not missing, 'Stable 1.0.118 feature modules missing: '+', '.join(missing)
  def read_entry(name):
    e=by_name[name]; a=start+int(e['offset']); return raw[a:a+int(e['size'])]
  html=read_entry('index.html').decode('utf-8')
  missing_refs=[name for name in required if name not in html]
  assert not missing_refs, 'Feature modules exist but are not loaded by index.html: '+', '.join(missing_refs)
  update_code=read_entry('update-manager.js').decode('utf-8')
  assert 'sha256' in update_code and 'loginSafeForRestart' in update_code and 'NANO_SALE_SAFE_195' in update_code, 'Safe-update/verification guards missing'
  backup_code=read_entry('mega-backup-ui.js').decode('utf-8')
  assert 'restore' in backup_code.lower() and 'backup' in backup_code.lower() and 'MEGA' in backup_code, 'Backup/restore module missing'
  payment_code=read_entry('nano-cash-change.js').decode('utf-8')
  assert 'change' in payment_code.lower() and 'cash' in payment_code.lower(), 'Cash change workflow missing'
  inventory_code=read_entry('nano-po-auto-supplier-100.js').decode('utf-8')
  assert 'supplier' in inventory_code.lower() and 'outstanding' in inventory_code.lower(), 'Automatic supplier/duplicate-order guard missing'
  renderer_base=read_entry('renderer.js').decode('utf-8')
  assert '__nanoPrayer' not in renderer_base and 'api.aladhan.com' not in renderer_base and 'مواقيت الصلاة' not in renderer_base, 'Prayer feature unexpectedly present in stable base'
  buf=bytearray(); found=set()
  for name,e in entries:
    blob=raw[start+int(e['offset']):start+int(e['offset'])+int(e['size'])]
    assert len(blob)==int(e['size']),name
    if name=='package.json':
      pkg=json.loads(blob.decode()); assert pkg.get('version')=='1.0.118',pkg.get('version')
      pkg['version']='2.0.17'; blob=(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n').encode(); found.add(name)
    elif name=='renderer.js':
      text=blob.decode('utf-8')
      assert 'cartItemsList' in text and 'speechSynthesis' not in text
      combined=text+SPEECH+OPS_CHARTS
      assert '__nanoCartSpeechV202' in combined and 'SpeechSynthesisUtterance' in combined, 'Cart price speech missing'
      assert '__nanoOperationalAnalyticsV217' in combined and 'nanoChartSalesPurchases' in combined and 'nanoChartCashSession' in combined and 'nanoChartStockCategories' in combined and 'nanoChartPurchaseTrend' in combined and 'nanoChartInventoryValue' in combined, 'Operational analytics charts missing'
      assert '__nanoPrayer' not in combined and 'api.aladhan.com' not in combined and 'مواقيت الصلاة' not in combined, 'Prayer feature remains in output'
      blob=combined.encode('utf-8'); found.add(name)
    e['offset']=str(len(buf)); e['size']=len(blob)
    if name in found and 'integrity' in e:
      e['integrity']['hash']=sha(blob)
      bs=int(e['integrity'].get('blockSize',4194304))
      e['integrity']['blocks']=[sha(blob[i:i+bs]) for i in range(0,len(blob),bs)]
    buf.extend(blob)
    if name in found:
      p=Path(work)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob)
  assert found=={'package.json','renderer.js'},found
  header=json.dumps(tree,separators=(',',':'),ensure_ascii=False).encode()
  padded=(len(header)+7)&~3
  out=struct.pack('<4I',4,padded+4,padded,len(header))+header+b'\0'*(padded-4-len(header))+buf
  dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',out)
  check=zipfile.ZipFile(dest).read('payload/app.asar')
  assert sha(check)==sha(out)
  print(json.dumps({'version':'2.0.17','patchSha256':sha(dest.read_bytes()),'appAsarSha256':sha(out),'sizeBytes':dest.stat().st_size}))
if __name__=='__main__':
  if len(sys.argv)!=4: raise SystemExit('build-v217.py BASE.zip OUTPUT.zip WORKDIR')
  build(*sys.argv[1:])
