/* NANO POS: the merchant's own saved shop logo supplies the optional native caption image. */
(function(root){
  'use strict';
  if(!root.document || root.__nanoShopCaption148) return;
  root.__nanoShopCaption148 = true;
  const native = ()=>root.nanoNative?.setShopCaptionLogo;
  const getLogo = result => (result?.data || result?.settings || result || {}).shop_logo || '';
  let last='__unset__';
  async function syncFromSavedSettings() {
    if(typeof native()!=='function'||typeof root.api?.getSettings!=='function') return;
    try {
      const settings=await root.api.getSettings();
      if(!settings || settings.success===false) return;
      const logo=String(getLogo(settings)||'');
      if(logo===last) return;
      const payload = /^data:image\/(png|jpeg);base64,/i.test(logo) ? {dataUrl:logo} : {clear:true};
      const result=await native()(payload);
      if(result?.success)last=logo;
    } catch(e){console.warn('[NANO POS] logo synchronization:',e.message);}
  }
  const install=()=>{
    const saveButton=document.querySelector('button[onclick="saveShopSettings()"]');
    if(saveButton)saveButton.addEventListener('click',()=>{
      // Wait for the existing asynchronous settings save and then read persisted settings.
      setTimeout(syncFromSavedSettings,650);
      setTimeout(syncFromSavedSettings,1600);
    });
    const removeButton=document.querySelector('button[onclick="removeLogo()"]');
    if(removeButton)removeButton.addEventListener('click',()=>{
      // The store's own settings save button remains authoritative.
      const note=document.getElementById('nanoLogoCaptionHint');
      if(note)note.textContent='بعد إزالة الشعار، اضغط حفظ معلومات المتجر لتحديث شريط العنوان.';
    });
    const drop=document.getElementById('settLogoDropzone');
    if(drop && !document.getElementById('nanoLogoCaptionHint')){
      const msg=document.createElement('p');
      msg.id='nanoLogoCaptionHint';msg.className='mt-2 text-xs text-slate-500 dark:text-slate-400';
      msg.textContent='سيظهر شعار المتجر الذي تحفظه هنا بجانب اسم المتجر في شريط عنوان النافذة. بدون شعار سيبقى مكانه فارغًا.';
      drop.insertAdjacentElement('afterend',msg);
    }
    // Restore saved shop-logo association after login, in addition to the app's disk-persisted window logo.
    setTimeout(syncFromSavedSettings,1400);
    setTimeout(syncFromSavedSettings,4400);
    root.addEventListener('shop-name-updated',()=>setTimeout(syncFromSavedSettings,350));
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})(typeof window!=='undefined'?window:globalThis);