/* Sourced reminder after verified login transition, not on failed attempts. */
(function(w){
'use strict';
const d=w.document;
let wasOpen=false;
let lastShownId='';
let inMemoryNext=0;
function launch(){
 if(d.getElementById('nanoFaithReminder183'))return;
 const all=w.NANO_FAITH_ITEMS_183||[];if(!all.length)return;
 const STORAGE_KEY='nano-faith-rotation-v184';
 let previous={};
 try{previous=JSON.parse(w.localStorage.getItem(STORAGE_KEY)||'null')||{}}catch{}
 // Persist each consumed reminder across app restarts and across multiple logins.
 // The first login after upgrading can pick up the old session-only index.
 let next=Number(previous.nextIndex);
 if(!Object.prototype.hasOwnProperty.call(previous,'nextIndex'))next=inMemoryNext;
 if(!Number.isSafeInteger(next)||next<0){
   try{next=Number(w.sessionStorage.getItem('nano-faith-index')||0)}catch{next=0}
 }
 if(!Number.isSafeInteger(next)||next<0)next=0;
 let idx=next%all.length;
 const lastId=String(previous.lastId||lastShownId||'');
 if(all.length>1&&String(all[idx].id||idx)===lastId)idx=(idx+1)%all.length;
 const item=all[idx];
 lastShownId=String(item.id||idx);
 const record={nextIndex:(idx+1)%all.length,lastId:lastShownId,shownCount:Math.max(0,Number(previous.shownCount)||0)+1,updatedAt:new Date().toISOString()};
 try{w.localStorage.setItem(STORAGE_KEY,JSON.stringify(record))}catch{
   // A blocked/full storage engine can only guarantee rotation for this window.
   inMemoryNext=record.nextIndex;
 }

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