/* Remote support launcher buttons in the existing NANO POS contact support modal. */
(()=>{'use strict';
const TEXT={
 ar:{title:'الدعم عن بُعد',anydesk:'فتح AnyDesk',tailscale:'فتح Tailscale',opening:'جاري فتح البرنامج...',opened:'تم طلب فتح البرنامج.',missing:'البرنامج غير مثبت على هذا الكمبيوتر.',windows:'التشغيل متاح من برنامج Windows فقط.',failed:'تعذر تشغيل البرنامج.',download:'تنزيل من الموقع الرسمي',consent:'لا تسمح بالتحكم عن بُعد إلا لشخص تثق به.'},
 fr:{title:'Assistance à distance',anydesk:'Ouvrir AnyDesk',tailscale:'Ouvrir Tailscale',opening:'Ouverture...',opened:'Lancement demandé.',missing:'Application non installée sur ce PC.',windows:'Lancement réservé à Windows.',failed:'Impossible de lancer le logiciel.',download:'Téléchargement officiel',consent:'N’autorisez une session à distance qu’avec une personne de confiance.'},
 en:{title:'Remote support',anydesk:'Open AnyDesk',tailscale:'Open Tailscale',opening:'Opening...',opened:'Launch requested.',missing:'App not installed on this PC.',windows:'Desktop Windows app only.',failed:'Unable to launch.',download:'Official download',consent:'Only approve remote access for someone you trust.'}
};
const URL={anydesk:'https://anydesk.com/en/downloads/windows',tailscale:'https://tailscale.com/download/windows'};
function lang(){const v=String(window.NANOI18N?.current?.()||window.currentLanguage||document.documentElement.lang||'ar').toLowerCase().split(/[-_]/)[0];return TEXT[v]?v:'ar';}
function translate(){const t=TEXT[lang()];const put=(id,txt)=>{const e=document.getElementById(id);if(e)e.textContent=txt;};
 put('nanoRemoteToolsTitle',t.title);put('nanoRemoteConsent',t.consent);
 put('nanoRemoteAnyDeskText',t.anydesk);put('nanoRemoteTailscaleText',t.tailscale);
}
async function openTool(id){
 const t=TEXT[lang()],button=document.getElementById(id==='anydesk'?'nanoRemoteAnyDesk':'nanoRemoteTailscale'),status=document.getElementById('nanoRemoteStatus');
 if(!button||!status)return;
 button.disabled=true;status.textContent=t.opening;
 let result;
 try{result=window.nanoNative?.launchSupportTool?await window.nanoNative.launchSupportTool(id):{ok:false,error:'windows_only'};}
 catch{result={ok:false,error:'launch_failed'};}
 finally{button.disabled=false;}
 if(result?.ok){status.textContent=t.opened;return;}
 const reason=result?.error==='not_installed'?t.missing:result?.error==='windows_only'?t.windows:t.failed;
 status.replaceChildren(document.createTextNode(reason+' '));
 const a=document.createElement('a');a.href=URL[id];a.textContent=t.download;a.rel='noopener noreferrer';a.target='_blank';
 a.addEventListener('click',ev=>{ev.preventDefault();window.nanoNative?.openExternal?.(URL[id]).catch(()=>{})||window.open(URL[id],'_blank','noopener');});
 status.append(a);
}
function install(){
 const body=document.querySelector('#nanoSupportModal .nano-support-body');if(!body||document.getElementById('nanoRemoteTools'))return;
 const section=document.createElement('section');section.id='nanoRemoteTools';
 section.innerHTML='<h3 id="nanoRemoteToolsTitle"></h3><div class="nano-remote-tools-buttons"><button type="button" id="nanoRemoteAnyDesk"><span class="material-symbols-outlined">desktop_windows</span><span id="nanoRemoteAnyDeskText"></span></button><button type="button" id="nanoRemoteTailscale"><span class="material-symbols-outlined">hub</span><span id="nanoRemoteTailscaleText"></span></button></div><p id="nanoRemoteStatus" role="status" aria-live="polite"></p><p id="nanoRemoteConsent"></p>';
 const note=body.querySelector('#nanoSupportNote');if(note)body.insertBefore(section,note);else body.append(section);
 const style=document.createElement('style');style.id='nanoRemoteToolsStyle';
 style.textContent=`#nanoRemoteTools{padding:12px;margin-top:15px;border-radius:13px;border:1px solid #dbeafe;background:#f8fbff}#nanoRemoteTools h3{margin:0 0 10px;font-size:13px;font-weight:900;color:#1d4ed8}.nano-remote-tools-buttons{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.nano-remote-tools-buttons button{display:flex;align-items:center;justify-content:center;gap:6px;padding:12px 8px;border:1px solid #bfdbfe;border-radius:11px;background:white;color:#1d4ed8;font:800 12px Tajawal,Cairo,sans-serif;cursor:pointer}.nano-remote-tools-buttons button:hover{background:#dbeafe}.nano-remote-tools-buttons button:disabled{opacity:.6;cursor:wait}.nano-remote-tools-buttons .material-symbols-outlined{font-size:19px}#nanoRemoteStatus{margin:8px 0 0;font-size:12px;line-height:1.7;color:#334155}#nanoRemoteStatus:empty{display:none}#nanoRemoteStatus a{color:#2563eb;font-weight:800;text-decoration:underline}#nanoRemoteConsent{font-size:11px;line-height:1.5;color:#64748b;margin:8px 0 0}.nano-support-card{max-height:calc(100vh - 32px);overflow-y:auto}.dark #nanoRemoteTools{background:#17255420;border-color:#334155}.dark .nano-remote-tools-buttons button{background:#1e293b;color:#bfdbfe;border-color:#334155}@media(max-width:420px){.nano-remote-tools-buttons{grid-template-columns:1fr}}`;
 document.head.append(style);
 section.querySelector('#nanoRemoteAnyDesk').addEventListener('click',()=>openTool('anydesk'));
 section.querySelector('#nanoRemoteTailscale').addEventListener('click',()=>openTool('tailscale'));
 translate();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
window.addEventListener('nano-language-synchronized',translate);
})();