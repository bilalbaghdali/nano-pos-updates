/* Display-only currency formatter. Never change accounting numeric storage or arithmetic. */
(function(root){
  'use strict';
  const DIGITS='٠١٢٣٤٥٦٧٨٩';
  const DIGITS_FA='۰۱۲۳۴۵۶۷۸۹';
  function parseAmount(value) {
    if(typeof value==='number')return Number.isFinite(value)?value:NaN;
    if(value===null||value===undefined)return NaN;
    let str=String(value).trim().replace(/[\u0660-\u0669]/g,ch=>String(DIGITS.indexOf(ch)))
      .replace(/[\u06f0-\u06f9]/g,ch=>String(DIGITS_FA.indexOf(ch)))
      .replace(/[\u00a0\u202f\u2009 ]/g,'').replace(/[^\d.,+\-]/g,'');
    if(!str)return NaN;
    const lastDot=str.lastIndexOf('.'),lastComma=str.lastIndexOf(',');
    const sep=Math.max(lastDot,lastComma);
    if(sep>=0){
      const fraction=str.length-sep-1;
      const delimiter=str.charAt(sep);
      // Exactly three trailing digits in an otherwise integer-like string mean grouping.
      const groupOnly=fraction===3 && str.split(delimiter).every((piece,i)=>i===0||piece.length===3);
      if(groupOnly)str=str.replace(/[.,]/g,'');
      else str=str.slice(0,sep).replace(/[.,]/g,'')+'.'+str.slice(sep+1).replace(/[.,]/g,'');
    }
    const result=Number(str);return Number.isFinite(result)?result:NaN;
  }
  let settings={currency:'د.ج',position:'after'};
  const languages={ar:'fr-DZ',fr:'fr-DZ',en:'en-US'};
  const language=lang=>String(lang||root.currentLanguage||'ar').toLowerCase().split('-')[0];
  function symbolFor(lang){
    const symbol=String(settings.currency||'د.ج').trim();
    if(!['د.ج','دج','DA','DZD'].includes(symbol))return symbol;
    return language(lang)==='ar'?'د.ج':language(lang)==='fr'?'DA':'DZD';
  }
  const posFor=(lang,context)=>context==='barcode'?'before':settings.position;
  function formatNumber(value,options={}) {
    const n=parseAmount(value),digits=Math.min(4,Math.max(0,Number(options.decimals??2)||0));
    if(!Number.isFinite(n))return '—';
    return new Intl.NumberFormat(languages[language(options.lang)]||'fr-DZ',{
      useGrouping:true,minimumFractionDigits:digits,maximumFractionDigits:digits
    }).format(n).replace(/[\u202f\u00a0]/g,'\u00a0');
  }
  function format(value,options={}){
    const lang=options.lang||root.currentLanguage||'ar';
    const number=formatNumber(value,{lang,decimals:options.decimals??2});
    if(number==='—')return number;
    const sym=symbolFor(lang),where=options.position||posFor(lang,options.context);
    return where==='before'?sym+'\u00a0'+number:number+'\u00a0'+sym;
  }
  function configure(prefs){
    if(prefs && typeof prefs==='object'){
      if(typeof prefs.currency==='string'&&prefs.currency.trim())settings.currency=prefs.currency.trim().slice(0,12);
      if(['before','after'].includes(prefs.position))settings.position=prefs.position;
    }
  }
  const api=Object.freeze({parseAmount,formatNumber,format,symbolFor,posFor,configure});
  root.NanoCurrency=api;
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof document!=='undefined'){
    const initialize=async()=>{
      try {const res=await root.api?.getSettings?.();if(res && res.success!==false)configure(res.data||res.settings||res);}
      catch{}
    };
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(initialize,800),{once:true});
    else setTimeout(initialize,800);
    root.addEventListener('shop-name-updated',()=>setTimeout(initialize,150));
  }
})(typeof window!=='undefined'?window:globalThis);