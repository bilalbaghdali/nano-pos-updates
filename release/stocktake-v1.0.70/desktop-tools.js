/* Desktop-only stocktake reporting tools. No changes to inventory data. */
(function(){'use strict';
if(location.pathname.includes('/mobile/'))return;
function init(){
const section=document.getElementById('stocktakeSection');if(!section||document.getElementById('nanoDesktopStocktakeTools'))return;
const toolbar=document.createElement('div');toolbar.id='nanoDesktopStocktakeTools';toolbar.style.cssText='display:flex;gap:8px;flex-wrap:wrap;padding:10px;background:#f0fdfa;border:1px solid #99f6e4;border-radius:12px;margin:8px 0;direction:rtl';
const heading=document.createElement('span');heading.textContent='أدوات الجرد على الكمبيوتر — لا تعدل المخزون';heading.style.cssText='font-weight:700;color:#115e59;margin:auto 0';toolbar.append(heading);
function button(title,fn){const b=document.createElement('button');b.type='button';b.textContent=title;b.style.cssText='border:1px solid #0d9488;border-radius:8px;padding:8px 12px;background:white;color:#115e59;font-weight:700';b.addEventListener('click',fn);toolbar.append(b)}
button('تصدير الجدول الظاهر CSV',()=>{
 const tables=[...section.querySelectorAll('table')].filter(x=>x.offsetParent!==null);const table=tables.sort((a,b)=>b.querySelectorAll('tr').length-a.querySelectorAll('tr').length)[0];
 if(!table||!table.querySelector('tr')){alert('افتح قائمة جرد تحتوي على منتجات قبل التصدير.');return;}
 const rows=[...table.querySelectorAll('tr')].map(tr=>[...tr.querySelectorAll('th,td')].map(c=>{const input=c.querySelector('input,select');return String(input?input.value:c.innerText||c.textContent||'').replace(/\s+/g,' ').trim()}));
 const escape=v=>'"'+v.replace(/"/g,'""')+'"';const csv='\ufeff'+rows.map(r=>r.map(escape).join(',')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download='NANO-POS-Stocktake-'+new Date().toISOString().slice(0,10)+'.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
});
button('طباعة تقرير الجرد',()=>{
 const content=section.querySelector('#stocktakeRoot');if(!content||!content.innerText.trim()){alert('افتح الجرد قبل طباعة التقرير.');return;}
 const w=window.open('','_blank','width=1000,height=750');if(!w){alert('اسمح بنافذة معاينة الطباعة من إعدادات البرنامج.');return;}
 const clean=content.cloneNode(true);clean.querySelectorAll('button,script').forEach(x=>x.remove());clean.querySelectorAll('input,textarea,select').forEach(x=>{const v=document.createElement('span');v.textContent=x.value||'';x.replaceWith(v)});
 w.document.open();w.document.write('<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><title>تقرير جرد NANO POS</title><style>body{font:14px Arial;padding:24px;color:#111}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px}*{box-sizing:border-box}button{display:none}</style><h2>تقرير جرد NANO POS</h2><p>'+new Date().toLocaleString('ar-DZ')+'</p>'+clean.innerHTML+'</html>');w.document.close();w.focus();w.print();
});
section.insertBefore(toolbar,section.firstChild);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();