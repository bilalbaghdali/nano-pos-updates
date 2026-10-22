#!/usr/bin/env python3
"""Build v1.0.112 from verified production v1.0.111 ASAR. Preserve sales and all user data.
Only fail-closed general data saves, user-facing warning, version and notes.
"""
import zipfile,hashlib,json,struct,sys
from pathlib import Path
SHA=lambda b:hashlib.sha256(b).hexdigest()
OFFICIAL='2003aba8a945d4761e2b1aca167047827eb55e99869fd74903dc5b324f31578c'
def one(s,before,after):
 assert s.count(before)==1,(before[:130],s.count(before))
 return s.replace(before,after)
def patch_bridge(s):
 old=""" const save = () => {
   try {
     db.revision++;
     localStorage.setItem(KEY, JSON.stringify(db));
     try { window.nanoNative?.pcSyncLocalChanged?.({ revision: db.revision, at: Date.now() }); } catch {}
     try { window.dispatchEvent(new CustomEvent('nano-pos-data-saved',{detail:{revision:db.revision}})); } catch {}
   } catch (error) {
     db = JSON.parse(localStorage.getItem(KEY) || JSON.stringify(initial));
     console.error('تعذر حفظ البيانات في المتصفح. تحقق من مساحة التخزين.');
   }
 };"""
 new=""" const save = () => {
   // Never tell an inventory/customer/expense caller it succeeded if persistence
   // failed. Stage the revision only after localStorage accepted the full snapshot.
   try {
     const snapshot={...db,revision:Number(db.revision||0)+1};
     localStorage.setItem(KEY, JSON.stringify(snapshot));
     db=snapshot;
     try { window.nanoNative?.pcSyncLocalChanged?.({ revision: db.revision, at: Date.now() }); } catch {}
     try { window.dispatchEvent(new CustomEvent('nano-pos-data-saved',{detail:{revision:db.revision}})); } catch {}
     return true;
   } catch (error) {
     // Reload last known persisted snapshot; do not keep in-memory fake changes.
     try { db = JSON.parse(localStorage.getItem(KEY) || JSON.stringify(initial)); } catch {}
     console.error('[NANO POS] storage write failed; transaction not confirmed:', error);
     try { window.dispatchEvent(new CustomEvent('nano-storage-save-failed',{detail:{code:'storage_write_failed'}})); } catch {}
     // Reject the caller rather than returning its existing {success:true}.
     throw new Error('nano_storage_write_failed_no_changes');
   }
 };"""
 s=one(s,old,new)
 assert "const snapshot={...db,revision:Number(db.revision||0)+1};" in s
 # Invoice and payment transactional implementations are left untouched
 assert "sale.invoice_number=window.NANO_INVOICE_SEQUENCE_111.commit" in s
 return s
def notes(s):
 s=one(s,"const FALLBACK_VERSION = '1.0.111';","const FALLBACK_VERSION = '1.0.112';")
 a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
 return s[:a]+"""  const OFFLINE = {
    ar:['حماية الحفظ العام: رفض نجاح عمليات المنتجات والزبائن والموردين إذا تعذر حفظ البيانات فعليًا.',
        'رسالة تنبيه واضحة عند امتلاء التخزين أو فشل الكتابة، مع استعادة آخر حالة محفوظة وعدم إنشاء تغيير وهمي.',
        'الاحتفاظ بمحرك البيع الذري والأرقام السنوية FA والفواتير والطباعة والمزامنة كما هي.',
        'توفير مثبت Windows x64 كامل بصيغة EXE إلى جانب حزمة التحديث الآلي مع الحفاظ على التفعيل والنسخ الاحتياطية.'],
    fr:['Protection des sauvegardes des produits et clients : refus de valider une écriture non enregistrée.',
        'Alerte explicite et restauration du dernier état sauvegardé en cas d’erreur de stockage.',
        'Conservation des ventes atomiques, des factures FA et de la synchronisation.',
        'Installateur Windows x64 EXE complet, avec mise à jour interne et données préservées.'],
    en:['Fail-closed product and customer edits when local storage rejects a write.',
        'Visible warning and rollback to previously saved state on storage errors.',
        'Preserve transactional sales, annual FA invoices, receipt printing and synchronization.',
        'Full Windows x64 EXE installer plus in-app patch, preserving licenses and backups.']
  };
"""+s[b:]
def build(source,dest,work):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar']
  raw=z.read('payload/app.asar')
 assert SHA(raw)==OFFICIAL,('unexpected_official_base',SHA(raw))
 magic,b,hs,n=struct.unpack_from('<4I',raw)
 assert magic==4 and b==hs+4
 tree=json.loads(raw[16:16+n]);base=8+b
 assert 'nano-storage-warning-112.js' not in tree['files']
 items=[]
 def walk(t,p=''):
  for name,e in t.get('files',{}).items():
   if 'files' in e:walk(e,p+name+'/')
   else:items.append((p+name,e))
 walk(tree);assert len(items)>500
 items.sort(key=lambda it:int(it[1]['offset']))
 changed=set();buf=bytearray()
 for name,e in items:
  blob=raw[base+int(e['offset']):base+int(e['offset'])+e['size']]
  assert len(blob)==e['size']
  if name=='browser-bridge.js':
   blob=patch_bridge(blob.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='index.html':
   s=blob.decode('utf8')
   s=one(s,'<script src="browser-bridge.js"></script>',
         '<script src="browser-bridge.js"></script>\\n    <script src="nano-storage-warning-112.js"></script>')
   s=s.replace('</script>\\n    <script src="nano-storage-warning-112.js"', '</script>\n    <script src="nano-storage-warning-112.js"')
   blob=s.encode('utf8');changed.add(name)
  elif name=='package.json':
   s=blob.decode('utf8');assert json.loads(s)['version']=='1.0.111'
   blob=one(s,'"version": "1.0.111"','"version": "1.0.112"').encode('utf8');changed.add(name)
  elif name=='release-notes.js':
   blob=notes(blob.decode('utf8')).encode('utf8');changed.add(name)
  e['offset']=str(len(buf));e['size']=len(blob)
  if name in changed and 'integrity' in e:
   integrity=e['integrity'];integrity['hash']=SHA(blob)
   size=int(integrity.get('blockSize',4194304))
   integrity['blocks']=[SHA(blob[i:i+size]) for i in range(0,len(blob),size)]
  buf.extend(blob)
  if name in changed or name in ('nano-invoice-sequence-111.js','nano-invoice-layout-111.js',
                  'nano-payment-ledger-102.js','backup-safety.cjs','electron-main.cjs','renderer.js'):
   p=work/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob)
 assert changed=={'browser-bridge.js','index.html','package.json','release-notes.js'},changed
 name='nano-storage-warning-112.js'
 blob=Path('.github/assets/'+name).read_bytes()
 tree['files'][name]={'size':len(blob),'offset':str(len(buf)),
    'integrity':{'algorithm':'SHA256','hash':SHA(blob),'blockSize':4194304,'blocks':[SHA(blob)]}}
 buf.extend(blob);(work/name).write_bytes(blob)
 header=json.dumps(tree,separators=(',',':'),ensure_ascii=False).encode('utf8')
 padded=(len(header)+7)&~3
 asar=struct.pack('<4I',4,padded+4,padded,len(header))+header+b'\0'*(padded-4-len(header))+buf
 with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',asar)
 with zipfile.ZipFile(dest) as z:assert SHA(z.read('payload/app.asar'))==SHA(asar)
 print(json.dumps({'version':'1.0.112','changes':sorted(changed),'added':name,'asarSha256':SHA(asar),'zipSha256':SHA(dest.read_bytes())}))
if __name__=='__main__':
 a,b,c=map(Path,sys.argv[1:4]);c.mkdir(exist_ok=True,parents=True);build(a,b,c)
