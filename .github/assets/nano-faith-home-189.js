(function (w) {
'use strict';
const d=w.document,H='nanoHomeSection',KEY='nano-faith-rotation-v185';
let onHome=false,ready=false,cursor=0;
const byId=id=>d.getElementById(id);
function authed(){
  try {const u=JSON.parse(w.localStorage.getItem('pos_current_user')||'null');return !!u&&typeof u==='object'&&(u.id!=null||u.username);}catch{return false;}
}
function overlayOpen(id){const e=byId(id);return !!e&&!e.classList.contains('hidden')&&w.getComputedStyle(e).display!=='none';}
function visible(){
  const e=byId(H);
  return !!e&&!e.classList.contains('hidden')&&!e.hidden&&w.getComputedStyle(e).display!=='none'&&authed()&&!overlayOpen('loginOverlay')&&!overlayOpen('lockOverlay');
}
function element(tag,cls,content){const e=d.createElement(tag);if(cls)e.className=cls;if(content!=null)e.textContent=String(content);return e;}
function next(items){
  let state={};try{state=JSON.parse(w.localStorage.getItem(KEY)||'null')||{};}catch{}
  let n=Number(state.nextIndex);if(!Number.isSafeInteger(n)||n<0)n=cursor;
  let index=n%items.length;
  if(items.length>1&&String(items[index].id)===String(state.lastId||''))index=(index+1)%items.length;
  const current=items[index];cursor=(index+1)%items.length;
  try{w.localStorage.setItem(KEY,JSON.stringify({nextIndex:cursor,lastId:String(current.id),totalShown:Math.max(0,Number(state.totalShown)||0)+1}));}catch{}
  return current;
}
function styles(){
  if(byId('nanoFaithHomeStyle189'))return;
  const s=element('style');s.id='nanoFaithHomeStyle189';
  s.textContent=`#nanoHomeSection .nano-home-hero{flex-wrap:wrap}
  #nanoHomeSection .nano-faith-home-banner{flex:0 0 100%;width:100%;min-width:0;direction:rtl;text-align:right;color:#fff;background:#152a5680;padding:14px 18px;}
  #nanoHomeSection .nano-faith-home-top{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:7px}
  #nanoHomeSection .nano-faith-home-type{background:#fff3;border-radius:25px;padding:4px 11px;font-size:12px;font-weight:800}
  #nanoHomeSection .nano-faith-home-title{font-size:12px;}
  #nanoHomeSection .nano-faith-home-quote{margin:7px 0;max-height:150px;overflow-y:auto;font-size:clamp(14px,1.36vw,19px);line-height:1.8;color:#fff;}
  #nanoHomeSection .nano-faith-home-reference{font-size:12px;font-weight:600;margin:0 0 5px}
  #nanoHomeSection .nano-faith-home-details{border-top:1px solid rgba(255,255,255,.22);padding-top:8px;font-size:12px}
  #nanoHomeSection .nano-faith-home-details summary{cursor:pointer;font-weight:600;display:list-item;}
  #nanoHomeSection .nano-faith-home-details[open] summary{}
  #nanoHomeSection .nano-faith-home-details p{margin:8px 0;line-height:1.75;color:#fff}
  #nanoHomeSection .nano-faith-home-details a{color:#e1f7ff;text-decoration:underline;}
  html.nano-nova-desktop #nanoHomeSection .nano-faith-home-banner{background:rgba(255,255,255,.1);}
  @media(max-width:760px){#nanoHomeSection .nano-faith-home-banner{padding:11px 12px}#nanoHomeSection .nano-faith-home-quote{font-size:14px;max-height:180px}}`;
  (d.head||d.documentElement).appendChild(s);
}
function render(){
  const items=w.NANO_FAITH_ITEMS_183,home=byId(H),hero=home?.querySelector('.nano-home-hero');
  if(!hero||!Array.isArray(items)||items.length!==100)return;
  styles();const item=next(items);
  let panel=byId('nanoFaithHomeBanner189');if(!panel){panel=element('aside','nano-faith-home-banner');panel.id='nanoFaithHomeBanner189';panel.dir='rtl';panel.setAttribute('aria-label','آية أو حديث من مصادر موثوقة');hero.appendChild(panel);}
  panel.replaceChildren();
  const top=element('div','nano-faith-home-top'),kind=element('span','nano-faith-home-type',item.type),label=element('span','nano-faith-home-title','وقفة إيمانية');
  top.append(kind,label);
  const quote=element('p','nano-faith-home-quote',item.text),ref=element('p','nano-faith-home-reference',item.reference);
  const details=element('details','nano-faith-home-details'),summary=element('summary',null,'الشرح والمصدر');
  const explanation=element('p',null,item.explanation),source=element('p',null,'المصدر: '+item.source),link=element('a',null,'الاطلاع على المصدر');
  try{const url=new URL(item.url);if(url.protocol==='https:'){link.href=url.href;link.target='_blank';link.rel='noopener noreferrer';}}catch{}
  details.append(summary,explanation,source);if(link.href)details.append(link);
  panel.append(top,quote,ref,details);
  panel.dataset.faithId=String(item.id);
}
function sync(){
  const now=visible();if(!now){onHome=false;return;}
  if(!onHome){onHome=true;try{render();}catch(e){console.error('[NANO Faith home]',e);}}
}
function init(){
  if(ready)return;ready=true;
  const home=byId(H);if(!home)return;
  const observer=new MutationObserver(sync);
  observer.observe(home,{attributes:true,attributeFilter:['class','style','hidden']});
  ['loginOverlay','lockOverlay'].forEach(id=>{const e=byId(id);if(e)observer.observe(e,{attributes:true,attributeFilter:['class','style','hidden']});});
  w.addEventListener('nano-section-shown',sync);
  w.addEventListener('nano-pos-login-success',()=>w.setTimeout(sync,700));
  w.addEventListener('focus',sync);
  sync();
}
w.NANO_FAITH_189={refresh:sync};
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);
