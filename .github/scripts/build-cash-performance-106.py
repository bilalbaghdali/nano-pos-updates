#!/usr/bin/env python3
"""NANO POS v1.0.106: SHA-verifiable cash tender + fast first window.
Copies entire verified ASAR with four targeted changes, no user data migrations."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
SHA=lambda blob:hashlib.sha256(blob).hexdigest()
BASE='cca80aeebdc24b3343624535b7555d66099fd2140f0a23005dfa296aee2f3aa7'
def once(s,a,b):
 assert s.count(a)==1,('source_marker_drift',a[:110],s.count(a))
 return s.replace(a,b)
def native(s):
 mark='    await startLocalServer();\n'
 assert s.count(mark)==1
 start=s.index(mark)
 end=s.index('    // Back up the latest renderer snapshot hourly',start)
 original=s[start:end]
 assert original.count('    createWindow();')==1
 assert 'mobileSyncServer = createMobileSyncServer' in original
 assert 'await mobileSyncServer.start();' in original
 assert 'await pcSyncService.start();' in original
 services=original[len(mark):]
 services=once(services,'    createWindow();\n','')
 # Keep both LAN/mobile synchronization services, start after the UI is already loading.
 new="""    await startLocalServer();
    // Show the checkout/login window before optional network servers finish binding.
    // Startup was previously blocked by both await start() calls.
    createWindow();
    const startOptionalConnectivity106=async()=>{
"""+services+"""      // Opening the UI before PC sync requires an explicit follow-up client sync.
      // This preserves the previous behavior even if did-finish-load came first.
      try{
        if(pcSyncService?.info?.().mode==='client')
          await pcSyncService.syncNow();
      }catch(error){console.warn('[NANO PC Sync] delayed startup sync:',error);}
    };
    const optionalTimer106=setTimeout(()=>{
      if(!mainWindow||mainWindow.isDestroyed())return;
      void startOptionalConnectivity106().catch(error=>
        console.error('[NANO POS] optional connectivity initialization:',error));
    },700);
    optionalTimer106.unref?.();
"""
 return once(s,original,new)
def notes(s):
 s=once(s,"const FALLBACK_VERSION = '1.0.105';","const FALLBACK_VERSION = '1.0.106';")
 a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
 return s[:a]+"""  const OFFLINE = {
    ar:['استعادة الدفع النقدي بالصرف: إدخال المبلغ المستلم وحساب الصرف الواجب إرجاعه.',
        'عرض اقتراح للفئات النقدية بالدينار الجزائري لتسهيل إرجاع الصرف، مع حفظ سجل الصرف السابق.',
        'فتح النافذة قبل اكتمال تشغيل خوادم المزامنة الاختيارية لتقليل انتظار الإقلاع.',
        'الحفاظ على طريقة دفع واحدة ومنع الصرف غير الكافي والدفع المختلط، مع حماية الفواتير والديون.'],
    fr:['Retour de la monnaie à rendre : montant remis, monnaie exacte et coupures suggérées.',
        'Affichage des billets et pièces DZD conseillés pour le caissier.',
        'Affichage de la fenêtre sans attendre les serveurs de synchronisation secondaires.',
        'Paiement unique et sauvegardes, clients et activation conservés.'],
    en:['Restore cash tender, exact change and recommended DZD denominations.',
        'Show change as a practical cashier breakdown without split payments.',
        'Open the window before optional mobile/LAN sync servers finish starting.',
        'Keep payment records, inventory, backup, activation and single-method checkout.']
  };
"""+s[b:]
def build(source,target,work):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar'];raw=z.read('payload/app.asar')
 assert SHA(raw)==BASE,'Unexpected original v1.0.105 ASAR'
 magic,block,hs,n=struct.unpack_from('<4I',raw)
 assert magic==4 and block==hs+4
 head=json.loads(raw[16:16+n]);start=8+block
 added=['nano-cash-plan-106.js','nano-cash-guide-106.js']
 for x in added:assert x not in head['files']
 members=[]
 def walk(node,prefix=''):
  for k,v in node.get('files',{}).items():
   if 'files' in v:walk(v,prefix+k+'/')
   elif 'offset' in v:members.append((prefix+k,v))
 walk(head);assert len(members)>200
 members.sort(key=lambda x:int(x[1]['offset']))
 output=bytearray();modified=set()
 for name,entry in members:
  content=raw[start+int(entry['offset']):start+int(entry['offset'])+entry['size']]
  assert len(content)==entry['size']
  if name=='electron-main.cjs':
   content=native(content.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='browser-bridge.js':
   content=once(content.decode('utf8'),
      'paid:__paid105,method:__method105,',
      'paid:__paid105,method:__method105,\n         ...(__checkout105.cashTenderedAmount == null ? {} : {cashTenderedCents:__money105(__checkout105.cashTenderedAmount)}),').encode('utf8');modified.add(name)
  elif name=='index.html':
   s=content.decode('utf8')
   s=once(s,'<script defer src="nano-payment-quality-105.js"></script>',
     '<script defer src="nano-payment-quality-105.js"></script>\n'
     '  <script defer src="nano-cash-plan-106.js"></script>\n'
     '  <script defer src="nano-cash-guide-106.js"></script>')
   assert 'src="nano-split-ui-102.js"' not in s
   content=s.encode('utf8');modified.add(name)
  elif name=='release-notes.js':
   content=notes(content.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='package.json':
   s=content.decode('utf8');assert json.loads(s)['version']=='1.0.105'
   content=once(s,'"version": "1.0.105"','"version": "1.0.106"').encode('utf8');modified.add(name)
  entry['offset']=str(len(output));entry['size']=len(content)
  if name in modified and 'integrity' in entry:
   x=entry['integrity'];x['hash']=SHA(content)
   size=int(x.get('blockSize',4194304));x['blocks']=[SHA(content[i:i+size]) for i in range(0,len(content),size)]
  output.extend(content)
  if name in modified or name in ('browser-bridge.js','nano-payment-quality-105.js','nano-checkout-choice-104.js','nano-cash-change.js','nano-payment-ledger-102.js'):
   (work/name).parent.mkdir(parents=True,exist_ok=True)
   (work/name).write_bytes(content)
 assert modified=={'electron-main.cjs','browser-bridge.js','index.html','release-notes.js','package.json'}
 for name in added:
  content=Path('.github/assets/'+name).read_bytes()
  head['files'][name]={'size':len(content),'offset':str(len(output)),
    'integrity':{'algorithm':'SHA256','hash':SHA(content),
      'blockSize':4194304,'blocks':[SHA(content)]}}
  output.extend(content);(work/name).write_bytes(content)
 hdr=json.dumps(head,separators=(',',':'),ensure_ascii=False).encode('utf8')
 pad=(len(hdr)+7)&~3
 final=struct.pack('<4I',4,pad+4,pad,len(hdr))+hdr+b'\0'*(pad-4-len(hdr))+output
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',final)
 with zipfile.ZipFile(target) as z:assert SHA(z.read('payload/app.asar'))==SHA(final)
 print(json.dumps({'version':'1.0.106','modified':sorted(modified),'added':added,
   'asarSHA256':SHA(final),'zipSHA256':SHA(target.read_bytes())}))
if __name__=='__main__':
 source,target,work=map(Path,sys.argv[1:4]);work.mkdir(parents=True,exist_ok=True)
 build(source,target,work)
