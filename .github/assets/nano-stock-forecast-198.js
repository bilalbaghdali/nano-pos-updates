/* NANO POS v1.0.98 — read-only inventory coverage and reorder suggestions.
   No writes, no purchases, no schema/activation changes. */
(function(root){
  'use strict';
  if(root.NANO_STOCK_FORECAST_198)return;
  const finite = value => {
    if (value == null || value === '') return null;
    const n = Number(value);
    return Number.isFinite(n) && n >= 0 ? n : null;
  };
  const round = n => Math.round((n + Number.EPSILON) * 100) / 100;
  function recommend({stock, minimum, avgDaily, baselineOrder=0, horizonDays=14, safetyDays=3}={}) {
    const qty=finite(stock), low=minimum==null?0:finite(minimum);
    const rate=finite(avgDaily), base=finite(baselineOrder);
    const horizon=finite(horizonDays), safety=finite(safetyDays);
    if(qty===null || rate===null || low===null || base===null || horizon===null || safety===null ||
       horizon<1 || horizon>90 || safety>30) return {ok:false,reason:'insufficient_data'};
    const coverDays=rate>0?round(qty/rate):null;
    const predictedNeed=rate*(horizon+safety);
    const proposed=rate>0?Math.max(base,Math.max(0,predictedNeed+low-qty)):base;
    if(!Number.isFinite(proposed) || proposed>100000000) return {ok:false,reason:'out_of_range'};
    return {ok:true,estimated:true,stock:qty,avgDaily:rate,coverDays,
      baselineOrder:base,order:Math.ceil(proposed*100)/100,
      horizonDays:horizon,safetyDays:safety,
      warning:'Indicative estimate based on the available average sales rate; confirm before ordering.'};
  }
  const api=Object.freeze({recommend,finite});
  root.NANO_STOCK_FORECAST_198=api;
  if(typeof module!=='undefined' && module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
