/* Restores existing product analytics modal with real sale/stock figures. */
(function(w){
'use strict';
const d=w.document;
const by=id=>d.getElementById(id);
const set=(id,v)=>{const el=by(id);if(el)el.textContent=String(v);};
const num=n=>Number.isFinite(Number(n))?Number(n):0;
const qty=n=>Number(num(n).toFixed(3)).toLocaleString('fr-DZ');
const amount=n=>num(n).toFixed(2)+' د.ج';
let current=0;
async function open(id,name,barcode){
 const modal=by('productAnalyticsModal');if(!modal)return;
 const request=++current;
 set('analyticsProductName',name||'—');set('analyticsProductBarcode',barcode||'—');
 for(const key of ['analyticsTotalRevenue','analyticsNetProfit','analyticsTotalSold','analyticsStockValue',
   'analyticsProfitMargin','analyticsAvgDaily','analyticsDaysOut',
   'analyticsInvCurrent','analyticsInvValid','analyticsInvExpired','analyticsInvFinishedBatches','analyticsInvTotalBatches'])
   set(key,'…');
 const tbody=by('analyticsVariantsTbody');if(tbody)tbody.replaceChildren();
 const table=by('analyticsVariantsTable'),empty=by('analyticsVariantsEmpty');
 table?.classList.add('hidden');empty?.classList.remove('hidden');
 modal.classList.remove('hidden');modal.classList.add('flex');
 try{
   if(typeof w.api?.getProductAnalytics!=='function')throw Error('خدمة تحليلات المنتج غير متاحة');
   const data=await w.api.getProductAnalytics(id);
   if(request!==current)return;
   if(!data||data.success===false)throw Error(data?.error||data?.message||'لم يمكن جلب التحليلات');
   set('analyticsTotalRevenue',amount(data.totalRevenue));
   set('analyticsNetProfit',amount(data.totalProfit??data.profit));
   set('analyticsTotalSold',qty(data.totalSold));
   set('analyticsStockValue',amount(data.stockValue));
   set('analyticsProfitMargin',num(data.profitMargin).toFixed(1)+'%');
   set('analyticsAvgDaily',qty(data.avgDailySales??data.avgDaily));
   set('analyticsDaysOut',(num(data.daysOut)||0)+' يوم');
   const inv=data.inventoryStats||{};
   set('analyticsInvCurrent',qty(inv.current_stock));
   set('analyticsInvValid',qty(inv.valid_stock));
   set('analyticsInvExpired',qty(inv.expired_stock));
   set('analyticsInvFinishedBatches',num(inv.finished_batches));
   set('analyticsInvTotalBatches',num(inv.total_batches));
   const variants=Array.isArray(data.variantsPerf)?data.variantsPerf:[];
   if(variants.length&&tbody){
     for(const row of variants){
       const tr=d.createElement('tr');
       for(const value of [row.variant_name||'—',qty(row.sold_qty),amount(row.revenue),qty(row.remaining_stock)]){
         const td=d.createElement('td');td.className='py-2 px-4 text-xs font-bold';td.textContent=value;tr.append(td);
       }tbody.append(tr);
     }
     empty?.classList.add('hidden');table?.classList.remove('hidden');
   }
 }catch(e){
   if(request!==current)return;
   console.error('NANO POS product analytics:',e);
   set('analyticsTotalRevenue','تعذر التحميل');
   set('analyticsNetProfit',String(e.message||e));
   if(typeof w.showToast==='function')w.showToast('تعذر جلب تحليلات المنتج: '+String(e.message||e),'error');
 }
}
w.openProductAnalyticsModal=open;
})(typeof window!=='undefined'?window:globalThis);