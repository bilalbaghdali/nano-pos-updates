/* NANO POS v1.0.76 — layout adaptation only; preserves existing barcode, price and checkout behavior. */
(function(win){
  'use strict';
  const doc=win.document;
  if(!doc||win.NANO_SALES_LAYOUT_176)return;
  win.NANO_SALES_LAYOUT_176=true;
  const byId=id=>doc.getElementById(id);
  let frame=0;
  let lastMode=null;
  function update(){
    frame=0;
    const section=byId('salesSection');
    const products=byId('posProductsPane');
    const cart=byId('posCartContainer');
    const summary=byId('posSummaryBar');
    if(!section||!products||!cart||!summary)return;
    section.classList.add('nano-pos-workspace');
    const width=section.clientWidth||section.getBoundingClientRect?.().width||1200;
    const layout=section.getAttribute('data-pos-layout')||'design1';
    const currentlyStacked=section.classList.contains('nano-pos-stack');
    const stack=layout!=='design3'&&(currentlyStacked?width<1010:width<960);
    section.classList.toggle('nano-pos-stack',stack);
    section.classList.toggle('nano-pos-tight',width<680);
    // Design 2 normally locates the summary below products. On a narrow display
    // it belongs below the cart so product cards and checkout both remain visible.
    // Returning to a large screen restores the original Design 2 placement.
    if(layout==='design2'){
      const destination=stack?cart:products;
      if(summary.parentElement!==destination)destination.appendChild(summary);
    }else if(lastMode==='design2'&&layout==='design1'){
      if(summary.parentElement!==cart)cart.appendChild(summary);
    }
    lastMode=layout;
  }
  function schedule(){
    if(frame)return;
    frame=win.requestAnimationFrame?win.requestAnimationFrame(update):1;
    if(!win.requestAnimationFrame)update();
  }
  function init(){
    const section=byId('salesSection');
    if(!section)return;
    schedule();
    if(typeof win.ResizeObserver==='function'){
      const observer=new win.ResizeObserver(schedule);
      observer.observe(section);
      win.NANO_SALES_LAYOUT_176_RESIZE_OBSERVER=observer;
    }else win.addEventListener('resize',schedule,{passive:true});
    if(typeof win.MutationObserver==='function'){
      const observer=new win.MutationObserver(schedule);
      observer.observe(section,{attributes:true,attributeFilter:['data-pos-layout']});
      win.NANO_SALES_LAYOUT_176_MODE_OBSERVER=observer;
    }
    win.addEventListener('resize',schedule,{passive:true});
  }
  if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})(typeof window!=='undefined'?window:globalThis);