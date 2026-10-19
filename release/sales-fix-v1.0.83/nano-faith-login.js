/* Sourced reminder after verified login transition, not on failed attempts. */
(function(w){
'use strict';
const d=w.document;
let wasOpen=false;
function launch(){
 if(d.getElementById('nanoFaithReminder183'))return;
 const all=w.NANO_FAITH_ITEMS_183||[];if(!all.length)return;
 const idx=(()=>{try{const n=Number(w.sessionStorage.getItem('nano-faith-index')||0);
   w.sessionStorage.setItem('nano-faith-index',String(n+1));return n%all.length;}catch{return 0}})();
 const item=all[idx];
 const create=(tag,content,cls)=>{const el=d.createElement(tag);if(content)el.textContent=content;if(cls)el.className=cls;return el;};
 const overlay=create('div');overlay.id='nanoFaithReminder183';
 const modal=create('section',null,'nano-faith-dialog');
 modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');
 modal.setAttribute('aria-labelledby','nanoFaithTitle183');modal.dir='rtl';modal.tabIndex=-1;
 const header=create('header');
 const kind=create('span',item.type,'nano-faith-type');
 const title=create('h2','رسالة طيبة لبداية يومك');title.id='nanoFaithTitle183';
 const cross=create('button','×','nano-faith-cross');cross.type='button';cross.setAttribute('aria-label','إغلاق');
 header.append(kind,title,cross);
 const quote=create('blockquote',item.text,'nano-faith-quote');
 const ref=create('p',item.reference,'nano-faith-ref');
 const explanationTitle=create('h3','المعنى والشرح المختصر','nano-faith-explain-title');
 const explanation=create('p',item.explanation,'nano-faith-explain');
 const attribution=create('p','المصدر: '+item.source+' — '+item.reference,'nano-faith-attribution');
 const footer=create('footer');
 const source=create('a','قراءة المصدر والتفسير');source.href=item.url;source.target='_blank';source.rel='noopener noreferrer';
 const closeBtn=create('button','متابعة إلى البرنامج','nano-faith-continue');closeBtn.type='button';
 footer.append(source,closeBtn);
 modal.append(header,quote,ref,explanationTitle,explanation,attribution,footer);
 overlay.append(modal);d.body.append(overlay);
 const oldFocus=d.activeElement;
 function close(){overlay.remove();d.removeEventListener('keydown',escape);oldFocus?.focus?.({preventScroll:true});}
 function escape(e){if(e.key==='Escape'){e.preventDefault();close();}}
 cross.addEventListener('click',close);closeBtn.addEventListener('click',close);
 overlay.addEventListener('click',e=>{if(e.target===overlay)close()});
 d.addEventListener('keydown',escape);modal.focus();
}
function init(){
 const login=d.getElementById('loginOverlay');if(!login)return;
 wasOpen=!login.classList.contains('hidden');
 let shown=false;
 const observer=new MutationObserver(()=>{
   const visible=!login.classList.contains('hidden');
   if(visible){wasOpen=true;shown=false;return;}
   if(!wasOpen||shown)return;
   shown=true;wasOpen=false;
   setTimeout(()=>{if(login.classList.contains('hidden'))launch();else shown=false;},350);
 });
 observer.observe(login,{attributes:true,attributeFilter:['class']});
}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);