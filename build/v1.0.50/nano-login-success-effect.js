/* Post-authentication visual feedback. Called ONLY from window.api.loginUser({success:true}) branch in renderer.js. */
(()=>{'use strict';
let active=null;let timeouts=[];let frame=0;
const translations={
  ar:{checking:'جارٍ التحضير...',wait:'جارٍ فتح لوحة NANO POS',granted:'تم تسجيل الدخول',welcome:'مرحبًا بعودتك إلى NANO POS',verified:'تم التحقق'},
  fr:{checking:'Préparation...',wait:'Ouverture de NANO POS',granted:'Accès autorisé',welcome:'Bienvenue sur NANO POS',verified:'VÉRIFIÉ'},
  en:{checking:'Preparing...',wait:'Opening NANO POS',granted:'Access Granted',welcome:'Welcome back to NANO POS',verified:'VERIFIED'}
};
function locale(){
  let value='';try{value=typeof currentLanguage==='string'?currentLanguage:''}catch(_){/* no global locale */}
  value=(value||document.documentElement.lang||'ar').slice(0,2).toLowerCase();return translations[value]||translations.ar;
}
function clear(){for(const h of timeouts)clearTimeout(h);timeouts=[];if(frame)cancelAnimationFrame(frame);frame=0;if(active)active.remove();active=null;}
function play(){
  clear();
  if(!document.body)return;
  const copy=locale();const veil=document.createElement('div');veil.id='nano-auth-success-veil';veil.setAttribute('role','status');veil.setAttribute('aria-live','polite');
  veil.innerHTML='<section class="nano-auth-card" data-stage="checking"><h2 class="nano-auth-title"></h2><p class="nano-auth-sub"></p><div class="nano-auth-meter" aria-hidden="true"><svg viewBox="0 0 100 100"><circle class="nano-auth-track" cx="50" cy="50" r="38"/><circle class="nano-auth-progress" cx="50" cy="50" r="38"/></svg><span class="nano-auth-percent">0</span></div><div class="nano-auth-tick" aria-hidden="true">✓</div><span class="nano-auth-stamp"></span></section>';
  const card=veil.querySelector('.nano-auth-card');const title=veil.querySelector('.nano-auth-title');const sub=veil.querySelector('.nano-auth-sub');const ring=veil.querySelector('.nano-auth-progress');const percent=veil.querySelector('.nano-auth-percent');const stamp=veil.querySelector('.nano-auth-stamp');
  title.textContent=copy.checking;sub.textContent=copy.wait;stamp.textContent=copy.verified;
  document.body.appendChild(veil);active=veil;
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches===true;
  const duration=reduced?100:1100;const start=performance.now();
  function render(now){if(active!==veil)return;const f=Math.max(0,Math.min(1,(now-start)/duration));const eased=1-Math.pow(1-f,2);const value=Math.min(100,Math.round(eased*100));percent.textContent=String(value);ring.style.strokeDashoffset=String(239*(1-eased));if(f<1)frame=requestAnimationFrame(render);else frame=0;}
  frame=requestAnimationFrame(render);
  timeouts.push(setTimeout(()=>{
    if(active!==veil)return;card.dataset.stage='granted';title.textContent=copy.granted;sub.textContent=copy.welcome;
  },duration+90));
  timeouts.push(setTimeout(()=>{if(active!==veil)return;veil.classList.add('nano-auth-out');timeouts.push(setTimeout(()=>{if(active===veil)clear()},reduced?0:300));},duration+1150));
}
window.NANOLoginSuccessEffect=Object.freeze({play,clear});
window.addEventListener('beforeunload',clear);
})();