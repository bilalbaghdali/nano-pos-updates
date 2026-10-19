/* NANO POS v1.0.86 — open the sourced reminder only after a successful user login. */
(function(w){
'use strict';
const d=w.document;
const KEY='nano-faith-rotation-v185',MODAL='nanoFaithReminder183';
let inMemoryCursor=0,pendingDisplay=false;
const $=id=>d.getElementById(id);
function loginVisible(){return !!$('loginOverlay')&&!$('loginOverlay').classList.contains('hidden');}
function lockVisible(){return !!$('lockOverlay')&&!$('lockOverlay').classList.contains('hidden');}
function hasAuthenticatedUser(){
 try{const user=JSON.parse(w.localStorage.getItem('pos_current_user')||'null');return !!user&&typeof user==='object'&&(user.id!=null||user.username);}
 catch{return false;}
}
function getIndex(items){
 let previous={};try{previous=JSON.parse(w.localStorage.getItem(KEY)||'null')||{}}catch{}
 let cursor=Number(previous.nextIndex);
 if(!Number.isSafeInteger(cursor)||cursor<0)cursor=inMemoryCursor;
 let index=cursor%items.length;
 if(items.length>1&&String(items[index].id)===String(previous.lastId||''))index=(index+1)%items.length;
 const current=items[index],record={nextIndex:(index+1)%items.length,lastId:String(current.id),totalShown:Math.max(0,Number(previous.totalShown)||0)+1};
 inMemoryCursor=record.nextIndex;
 try{w.localStorage.setItem(KEY,JSON.stringify(record));}catch(e){console.warn('[NANO Reminder] Local rotation storage unavailable',e);}
 return current;
}
function node(tag,text,cls){
 const e=d.createElement(tag);
 if(text!==undefined&&text!==null)e.textContent=String(text);
 if(cls)e.className=cls;
 return e;
}
function show(){
 const items=w.NANO_FAITH_ITEMS_183;
 if(!Array.isArray(items)||items.length!==100)throw Error('100 verified reminders not loaded');
 if($(MODAL))return;
 const item=getIndex(items);
 const background=node('div');background.id=MODAL;
 background.style.setProperty('position','fixed','important');
 background.style.setProperty('inset','0','important');
 background.style.setProperty('display','flex','important');
 background.style.setProperty('z-index','2147483000','important');
 const dialog=node('section',null,'nano-faith-dialog');
 dialog.dir='rtl';dialog.tabIndex=-1;dialog.setAttribute('role','dialog');
 dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-labelledby','nanoFaithTitle183');
 const header=node('header'),tag=node('span',item.type,'nano-faith-type');
 const title=node('h2','رسالة طيبة لبداية يومك');title.id='nanoFaithTitle183';
 const dismiss=node('button','×','nano-faith-cross');dismiss.type='button';dismiss.setAttribute('aria-label','إغلاق');
 header.append(tag,title,dismiss);
 const verse=node('blockquote',item.text,'nano-faith-quote');
 const reference=node('p',item.reference,'nano-faith-ref');
 const heading=node('h3','المعنى والشرح المختصر','nano-faith-explain-title');
 const interpretation=node('p',item.explanation,'nano-faith-explain');
 const citation=node('p','المصدر: '+item.source,'nano-faith-attribution');
 const footer=node('footer'),link=node('a','قراءة المصدر والتفسير');
 link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';
 const close=node('button','متابعة إلى البرنامج','nano-faith-continue');close.type='button';
 footer.append(link,close);dialog.append(header,verse,reference,heading,interpretation,citation,footer);
 background.append(dialog);d.body.append(background);
 const focusBefore=d.activeElement;
 function leave(){
   background.remove();d.removeEventListener('keydown',esc);
   try{focusBefore?.focus?.({preventScroll:true})}catch{}
 }
 function esc(e){if(e.key==='Escape'){e.preventDefault();leave();}}
 dismiss.addEventListener('click',leave);close.addEventListener('click',leave);
 background.addEventListener('click',e=>{if(e.target===background)leave()});
 d.addEventListener('keydown',esc);dialog.focus();
}
function handleAuthenticated(event){
 // This event is dispatched only from the successful loginUser branch, after
 // the NANOLoginSuccessEffect finishes and the session has been established.
 // Merely opening the app, resuming a session, or unlocking does NOT trigger it.
 if(event?.detail?.via!=='native-success'||!hasAuthenticatedUser())return;
 if(pendingDisplay||$(MODAL))return;
 pendingDisplay=true;
 let attempts=0;
 const displayAfterLogin=()=>{
   if(!pendingDisplay)return;
   if(!hasAuthenticatedUser()){pendingDisplay=false;return;}
   // The original login screen is hidden by a 500ms transition. Wait for it,
   // rather than showing a reminder below the still-visible login overlay.
   if(loginVisible()||lockVisible()){
     if(++attempts<=60){w.setTimeout(displayAfterLogin,200);return;}
     pendingDisplay=false;
     console.warn('[NANO Reminder] Login overlay never closed after successful authentication');
     return;
   }
   pendingDisplay=false;
   try{show();}catch(error){console.error('[NANO Reminder] Popup failed after successful login',error);}
 };
 w.setTimeout(displayAfterLogin,100);
}
function init(){
 // Strictly successful credentials + completed login effect; never on page load.
 w.addEventListener('nano-pos-login-success',handleAuthenticated);
}
w.NANO_FAITH_186={handleAuthenticated};
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);