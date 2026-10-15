/* NANO POS v1.0.68 authoritative, opt-in promotion and wholesale pricing. */
(function(root){'use strict';
const rounded=n=>Math.round((Number(n)+Number.EPSILON)*100)/100;
const amount=x=>{const n=Number(x);if(!Number.isFinite(n)||n<0||n>1e12)throw Error('سعر غير صالح');return rounded(n);};
const date=x=>String(x||'').slice(0,10);
function active(p,now,qty,productId){
 if(!p||String(p.product_id??p.productId??'')!==String(productId))return false;
 if(p.is_active===false||p.is_active===0||p.active===false||p.status==='inactive')return false;
 const today=date(now.toISOString()),start=date(p.start_date??p.startDate),end=date(p.end_date??p.endDate);
 if(start&&today<start)return false;
 if(end&&today>end)return false;
 const min=Number(p.min_qty??p.min_quantity??1),max=Number(p.max_qty??p.max_quantity??0);
 if(!Number.isFinite(min)||min<1||qty<min)return false;
 if(max&&(!Number.isFinite(max)||qty>max))return false;
 return true;
}
function quote(product,qty,promotions=[],tier='auto',now=new Date()){
 if(!product)throw Error('المنتج غير موجود');
 qty=Number(qty);if(!Number.isFinite(qty)||qty<=0||qty>1e7)throw Error('الكمية غير صالحة');
 const retail=amount(product.pos_price??product.selling_price??product.price??0);
 const wholesale=Number(product.wholesale_price??0);
 const wholesaleMinimum=Number(product.wholesale_qty??product.wholesale_min_qty??Infinity);
 const eligibleWholesale=wholesale>0&&Number.isFinite(wholesale)&&
   (tier==='wholesale'||(tier==='auto'&&Number.isFinite(wholesaleMinimum)&&qty>=wholesaleMinimum));
 let base=eligibleWholesale?amount(wholesale):retail;
 let best={price:base,promotion_id:null,discount:0,tier:eligibleWholesale?'wholesale':'retail'};
 for(const promo of promotions||[]){
  if(!active(promo,now,qty,product.id))continue;
  const discount=Number(promo.discount_value??promo.value);
  if(!Number.isFinite(discount)||discount<=0)continue;
  const type=String(promo.discount_type||promo.type||'').toLowerCase();
  let next=null;
  if(type==='percentage'&&discount<=100)next=rounded(base*(1-discount/100));
  else if(['fixed','amount'].includes(type))next=rounded(Math.max(0,base-discount));
  else if(['fixed_price','special_price'].includes(type))next=rounded(discount);
  if(next!==null&&next>=0&&next<best.price)best={price:next,promotion_id:promo.id??null,discount:rounded(base-next),tier:best.tier};
 }
 return {...best,base_price:base,product_id:product.id,quantity:qty};
}
function reprice(input,products,promotions,now=new Date()){
 if(!input||!Array.isArray(input.items)||!input.items.length)throw Error('السلة فارغة');
 const copy=structuredClone(input),lines=[];
 let subtotal=0;
 for(const item of copy.items){
  const qty=Number(item.qty??item.quantity);
  if(!Number.isFinite(qty)||qty<=0)throw Error('الكمية غير صالحة');
  const product=(products||[]).find(p=>String(p.id)===String(item.id??item.product_id));
  if(!product){
   if(!item.is_custom)throw Error('منتج غير موجود في المخزون');
   subtotal+=qty*amount(item.pos_price??item.price??0);continue;
  }
  const q=quote(product,qty,promotions,item.price_tier||'auto',now);
  item.pos_price=q.price;
  item.active_promotion_id=q.promotion_id;
  item.pricing_tier=q.tier;
  lines.push(q);subtotal+=qty*q.price;
 }
 subtotal=rounded(subtotal);
 const checkout=copy.checkout&&typeof copy.checkout==='object'?copy.checkout:{};
 const discount=amount(checkout.discount??0),tax=Number(checkout.taxPercentage??0);
 if(!Number.isFinite(tax)||tax<0||tax>100)throw Error('نسبة الضريبة غير صالحة');
 const total=rounded(Math.max(0,subtotal-discount)*(1+tax/100));
 copy.checkout={...checkout,subtotal,total,applyOffers:true};
 copy.pricing_rules_applied=lines;
 return {payload:copy,subtotal,total,lines};
}
const API={active,quote,reprice};
if(typeof module!=='undefined'&&module.exports)module.exports=API;
root.NANO_PRICING_168=API;
})(typeof window!=='undefined'?window:globalThis);