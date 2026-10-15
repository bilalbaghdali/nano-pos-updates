/* NANO POS v1.0.68: explicit opt-in for active promotions and wholesale unit prices. */
(function(root){'use strict';const d=root.document;if(!d||root.NANO_PRICING_UI_168)return;root.NANO_PRICING_UI_168=true;
function setup(){
 if(d.getElementById('nanoApplyOffersToggle'))return;
 const sales=d.getElementById('salesSection');if(!sales)return;
 const label=d.createElement('label');label.id='nanoPricingModeLabel';label.setAttribute('for','nanoApplyOffersToggle');
 label.style.cssText='display:flex;align-items:center;gap:10px;flex-wrap:wrap;cursor:pointer;padding:10px 13px;margin:8px 0;border:1px solid #d1fae5;border-radius:12px;background:#ecfdf5;color:#065f46;font:bold 12px Arial;direction:rtl';
 const check=d.createElement('input');check.type='checkbox';check.id='nanoApplyOffersToggle';check.style.cssText='width:18px;height:18px;accent-color:#047857';
 const title=d.createElement('span');title.textContent='تطبيق عروض المنتجات السارية وسعر الجملة حسب الكمية عند اعتماد البيع';
 const note=d.createElement('small');note.textContent='اختياري · يعيد الكمبيوتر الرئيسي حساب الإجمالي، ولا يكدّس أكثر من عرض على المنتج';note.style.color='#64748b';
 label.append(check,title,note);
 (sales.querySelector('header')||sales).append(label);
}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',setup,{once:true});else setup();
})(typeof window!=='undefined'?window:globalThis);