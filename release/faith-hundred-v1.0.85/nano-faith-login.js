/* NANO POS v1.0.85 — guaranteed reminder on authenticated login,
   also when a previously authenticated session is unlocked. */
(function(w){
'use strict';
const d=w.document;
const KEY='nano-faith-rotation-v185',MODAL='nanoFaithReminder183';
let latestShown=0,inMemoryCursor=0,shownInThisWindow=0,pendingDisplay=false;
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
 latestShown=Date.now();shownInThisWindow++;
}
function handleAuthenticated(event){
 // A trusted in-app event is emitted strictly after window.api.loginUser succeeds.
 // This handler doesn't perform login itself; no message on a failed authentication.
 const now=Date.now();if(pendingDisplay||now-latestShown<1300)return;
 pendingDisplay=true;
 const delay=(event?.detail?.via==='native-success')?850:700;
 w.setTimeout(()=>{
   const finish=()=>{
     pendingDisplay=false;
     if(!loginVisible()&&!lockVisible()&&!$(MODAL))show();
   };
   if(loginVisible()||lockVisible())w.setTimeout(finish,650);
   else finish();
 },delay);
}
function observeOverlay(id){
 const overlay=$(id);if(!overlay)return;
 let previouslyOpen=!overlay.classList.contains('hidden');
 new MutationObserver(()=>{
   const currentlyOpen=!overlay.classList.contains('hidden');
   if(currentlyOpen){previouslyOpen=true;return;}
   if(!previouslyOpen)return;
   previouslyOpen=false;
   if(!hasAuthenticatedUser())return;
   if(Date.now()-latestShown<1300)return;
   handleAuthenticated({detail:{via:'overlay-transition'}});
 }).observe(overlay,{attributes:true,attributeFilter:['class','style']});
}
function init(){
 w.addEventListener('nano-pos-login-success',handleAuthenticated);
 observeOverlay('loginOverlay');
 observeOverlay('lockOverlay');
 // Reopening a Windows process with an already authenticated user does not
 // necessarily display the login overlay. Show once after the app is usable.
 const tryResume=()=>{
   if(shownInThisWindow||!hasAuthenticatedUser()||loginVisible()||lockVisible())return;
   handleAuthenticated({detail:{via:'startup-resume'}});
 };
 w.setTimeout(tryResume,1800);
}
w.NANO_FAITH_185={show,handleAuthenticated};
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);