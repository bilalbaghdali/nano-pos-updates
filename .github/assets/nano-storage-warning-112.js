/* NANO POS v1.0.112 — persistent storage write failure warning.
 * Displays an alert only on a failed save, never modifies sale data or user settings.
 */
(function(root){
 'use strict';
 if(root.NANO_STORAGE_WARNING_112)return;
 let el=null;
 const labels={
   ar:'تعذر حفظ التعديلات على الكمبيوتر. لم يتم تأكيد العملية. تحقق من مساحة التخزين أو صلاحيات الملف، وراجع السجل قبل إعادة المحاولة.',
   fr:'Impossible de sauvegarder les modifications. Opération non confirmée. Vérifiez l’espace disque et les droits, puis le registre avant de réessayer.',
   en:'Changes could not be saved. The operation is unconfirmed. Check disk space and permissions, and review records before retrying.'
 };
 function message(){const l=String(root.currentLanguage||root.document?.documentElement?.lang||'ar').slice(0,2);return labels[l]||labels.ar}
 function render(){
   if(!root.document?.body)return;
   if(!el||!el.isConnected){
     el=root.document.createElement('div');el.id='nano-storage-save-failed-112';
     el.setAttribute('role','alert');el.setAttribute('aria-live','assertive');
     el.style.cssText='position:fixed;z-index:2147483646;bottom:12px;left:12px;right:12px;max-width:730px;margin:auto;background:#fff4f4;color:#8b1521;border:2px solid #cc3744;border-radius:12px;padding:15px 18px;font:700 14px/1.7 Arial,sans-serif;box-shadow:0 10px 28px rgba(0,0,0,.22);direction:auto';
     const msg=root.document.createElement('span');msg.className='nano-storage-msg';
     const close=root.document.createElement('button');close.textContent='×';close.type='button';
     close.setAttribute('aria-label','Dismiss / إغلاق');
     close.style.cssText='float:right;margin:0 9px;background:transparent;border:0;font-size:26px;color:#8b1521;cursor:pointer';
     close.addEventListener('click',()=>el?.remove());
     el.append(close,msg);root.document.body.append(el);
   }
   el.querySelector('.nano-storage-msg').textContent=message();
 }
 root.addEventListener?.('nano-storage-save-failed',render);
 root.NANO_STORAGE_WARNING_112=Object.freeze({show:render});
})(typeof window!=='undefined'?window:globalThis);
