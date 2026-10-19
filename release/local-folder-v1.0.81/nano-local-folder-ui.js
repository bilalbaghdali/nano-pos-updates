/* NANO POS v1.0.81 — trusted local backup/export folder in Settings > Import/Export. */
(function(win){
'use strict';
const doc=win.document;if(!doc||win.NANO_LOCAL_FOLDER_UI_181)return;win.NANO_LOCAL_FOLDER_UI_181=true;
const $=id=>doc.getElementById(id);
const words={
 ar:{title:'مجلد التخزين المحلي',subtitle:'اختر المكان المفضل لحفظ النسخ الاحتياطية المحلية والملفات المصدّرة.',selected:'المجلد المحدد',backups:'مجلد النسخ الاحتياطية',exports:'الموقع الافتراضي للتصدير',choose:'اختيار مجلد',reset:'إعادة الوضع الافتراضي',refresh:'تحديث الحالة',default:'المجلد الافتراضي',unavailable:'المجلد المختار غير متاح حاليًا؛ تحفظ النسخ التلقائية في المجلد الأصلي لحماية بياناتك.',safe:'تُحفظ النسخ في مجلد NANO-POS-Backups داخل المجلد الذي تختاره. لا يتم نقل قاعدة البيانات أو النسخ القديمة.',saved:'تم اعتماد مجلد التخزين المحلي.',resetDone:'تمت استعادة مكان الحفظ الافتراضي.',fail:'تعذر حفظ اختيار المجلد.',readonly:'اختيار مجلد التخزين متاح في برنامج Windows الرئيسي فقط.',busy:'جارٍ القراءة…'},
 fr:{title:'Dossier de stockage local',subtitle:'Choisir le dossier des sauvegardes locales et des exports.',selected:'Dossier choisi',backups:'Sauvegardes',exports:'Emplacement d’export',choose:'Choisir un dossier',reset:'Dossier par défaut',refresh:'Actualiser',default:'Par défaut',unavailable:'Le dossier choisi est indisponible. Les sauvegardes sont conservées dans le dossier intégré.',safe:'Les sauvegardes vont dans NANO-POS-Backups; les données et sauvegardes anciennes ne sont pas déplacées.',saved:'Dossier enregistré.',resetDone:'Dossier par défaut restauré.',fail:'Choix non enregistré.',readonly:'Disponible uniquement dans NANO POS Windows.',busy:'Chargement…'},
 en:{title:'Local storage folder',subtitle:'Select where local backups and exports should be saved.',selected:'Selected folder',backups:'Backup folder',exports:'Default export location',choose:'Choose folder',reset:'Use default',refresh:'Refresh status',default:'Default',unavailable:'Selected folder is unavailable; automatic backups fall back to the original safe location.',safe:'Backups go into NANO-POS-Backups within the selected folder. Existing database and backups are not moved.',saved:'Local storage folder saved.',resetDone:'Default location restored.',fail:'Folder could not be saved.',readonly:'Available in the Windows desktop app only.',busy:'Loading…'}
};
const W=()=>{const lang=String(win.currentLanguage||doc.documentElement.lang||'ar').toLowerCase().slice(0,2);return words[lang]||words.ar;};
let pending=false;
function notify(message){if(typeof win.showToast==='function')win.showToast(message,'info');const status=$('nanoLocalFolderMessage');if(status)status.textContent=message;}
function setValue(id,value){const el=$(id);if(el){el.textContent=value;el.title=value;}}
function api(){return win.nanoNative;}
async function refresh(){
 const w=W(),native=api();
 if(!native?.getLocalFolder){setValue('nanoLocalFolderMessage',w.readonly);setDisabled(true);return;}
 try{
   const current=await native.getLocalFolder();
   if(!current?.success)throw Error(current?.error||w.fail);
   setValue('nanoLocalFolderSelected',current.configuredFolder||w.default);
   setValue('nanoLocalFolderBackups',current.backupFolder||'—');
   setValue('nanoLocalFolderExports',current.exportFolder||'—');
   setValue('nanoLocalFolderMessage',current.fallbackUsed?w.unavailable:w.safe);
   const badge=$('nanoLocalFolderBadge');
   if(badge)badge.textContent=current.fallbackUsed?'⚠️':current.isDefault?'': '✓';
   setDisabled(false);
 }catch(e){setValue('nanoLocalFolderMessage',w.fail+' '+String(e.message||''));setDisabled(false);}
}
function setDisabled(state){
 for(const id of ['nanoLocalFolderChoose','nanoLocalFolderReset','nanoLocalFolderRefresh']){
   const button=$(id);if(button)button.disabled=state;
 }
}
async function act(type){
 if(pending)return;
 const native=api(),w=W();if(!native?.getLocalFolder){notify(w.readonly);return;}
 pending=true;setDisabled(true);
 try{
   const response=type==='choose'?await native.chooseLocalFolder():await native.resetLocalFolder();
   if(response?.canceled)return;
   if(!response?.success){notify(w.fail+' '+String(response?.error||''));return;}
   await refresh();notify(type==='choose'?w.saved:w.resetDone);
 }catch(e){notify(w.fail+' '+String(e.message||''));}
 finally{pending=false;setDisabled(false);}
}
function init(){
 const tab=$('settingsTab-import-export');
 if(!tab||$('nanoLocalFolderCard'))return;
 const w=W();
 const card=doc.createElement('section');card.id='nanoLocalFolderCard';card.className='nano-local-folder-card';
 card.innerHTML='<div class="nano-local-folder-head"><span class="material-symbols-outlined">folder_open</span><div><h3 id="nanoLocalFolderTitle"></h3><p id="nanoLocalFolderDescription"></p></div><span id="nanoLocalFolderBadge"></span></div>'+
  '<div class="nano-local-folder-paths"><div><span id="nanoLocalFolderSelectedLabel"></span><code id="nanoLocalFolderSelected"></code></div>'+
  '<div><span id="nanoLocalFolderBackupsLabel"></span><code id="nanoLocalFolderBackups"></code></div>'+
  '<div><span id="nanoLocalFolderExportsLabel"></span><code id="nanoLocalFolderExports"></code></div></div>'+
  '<div class="nano-local-folder-actions"><button type="button" id="nanoLocalFolderChoose"></button>'+
  '<button type="button" id="nanoLocalFolderReset"></button><button type="button" id="nanoLocalFolderRefresh"></button></div>'+
  '<p id="nanoLocalFolderMessage" role="status" aria-live="polite"></p>';
 tab.insertBefore(card,tab.firstElementChild);
 const names={
 nanoLocalFolderTitle:w.title,nanoLocalFolderDescription:w.subtitle,
 nanoLocalFolderSelectedLabel:w.selected,nanoLocalFolderBackupsLabel:w.backups,
 nanoLocalFolderExportsLabel:w.exports,nanoLocalFolderChoose:w.choose,
 nanoLocalFolderReset:w.reset,nanoLocalFolderRefresh:w.refresh,
 nanoLocalFolderMessage:w.busy,
 };
 for(const [id,value] of Object.entries(names))setValue(id,value);
 $('nanoLocalFolderChoose').addEventListener('click',()=>act('choose'));
 $('nanoLocalFolderReset').addEventListener('click',()=>act('reset'));
 $('nanoLocalFolderRefresh').addEventListener('click',refresh);
 refresh();
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init,{once:true});else init();
})(typeof window!=='undefined'?window:globalThis);