#!/usr/bin/env python3
"""NANO POS 1.0.107 credit picker. Verified original ASAR; only UI, metadata modified.
No update to DB migration, sales ledger, activation, backup or background services.
"""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
SHA=lambda b:hashlib.sha256(b).hexdigest()
BASE_ASAR='fd4f1b2b83c55fe07c3c7f932a6955119ad4f0e6c80f4fb5a1dcf3b5825e4283'
def once(text,old,new):
 assert text.count(old)==1,('source_drift',old[:115],text.count(old))
 return text.replace(old,new)
def patch_notes(src):
 src=once(src,"const FALLBACK_VERSION = '1.0.106';","const FALLBACK_VERSION = '1.0.107';")
 a=src.index('  const OFFLINE = {');b=src.index('  const TITLES = {',a)
 return src[:a]+"""  const OFFLINE = {
    ar:['البيع بالكريدي مباشرة من شاشة الدفع عبر زر «دين كامل».',
        'نافذة لاختيار الزبون المسجل بالبحث عن الاسم أو الهاتف، أو إضافة زبون جديد دون الخروج من شاشة البيع.',
        'إنشاء الزبون برصيد افتتاحي صفر، ثم إسناد الدين إلى حسابه عند تأكيد الفاتورة مرة واحدة فقط.',
        'حماية المبيعات من التكرار والحفاظ على الصرف النقدي والتفعيل والنسخ الاحتياطية.'],
    fr:['Vente à crédit depuis la fenêtre de paiement.',
        'Recherche du client par nom ou téléphone, ou création dans une fenêtre dédiée.',
        'Client créé sans dette initiale; facture et dette enregistrées une seule fois après confirmation.',
        'Préserve la caisse, le stock, les factures, les licences et les sauvegardes.'],
    en:['Full-credit sale directly from the payment window.',
        'Search existing customer by name or phone or create one in a dedicated modal.',
        'New customer starts at zero balance; debt posts only once when the invoice is confirmed.',
        'Preserves cash change, historical invoices, activation and backups.']
  };
"""+src[b:]
def build(source,target,work):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar']
  raw=z.read('payload/app.asar')
 assert SHA(raw)==BASE_ASAR,'official_v106_source_hash_mismatch'
 magic,block,hs,n=struct.unpack_from('<4I',raw)
 assert magic==4 and block==hs+4
 header=json.loads(raw[16:16+n])
 start=8+block
 assert 'nano-credit-picker-107.js' not in header['files']
 members=[]
 def walk(node,prefix=''):
  for name,e in node.get('files',{}).items():
   if 'files' in e:walk(e,prefix+name+'/')
   elif 'offset' in e:members.append((prefix+name,e))
 walk(header);assert len(members)>200
 members.sort(key=lambda item:int(item[1]['offset']))
 data=bytearray();modified=set()
 for name,e in members:
  blob=raw[start+int(e['offset']):start+int(e['offset'])+e['size']]
  assert len(blob)==e['size']
  if name=='index.html':
   src=blob.decode('utf8')
   src=once(src,'onclick="checkoutMarkAsDebt()"','onclick="nanoOpenCreditPicker107()"')
   src=once(src,'<script defer src="nano-cash-guide-106.js"></script>',
     '<script defer src="nano-cash-guide-106.js"></script>\n'
     '  <script defer src="nano-credit-picker-107.js"></script>')
   assert 'src="nano-split-ui-102.js"' not in src
   blob=src.encode('utf8');modified.add(name)
  elif name=='package.json':
   src=blob.decode('utf8');assert json.loads(src)['version']=='1.0.106'
   blob=once(src,'"version": "1.0.106"','"version": "1.0.107"').encode('utf8');modified.add(name)
  elif name=='release-notes.js':
   blob=patch_notes(blob.decode('utf8')).encode('utf8');modified.add(name)
  e['offset']=str(len(data));e['size']=len(blob)
  if name in modified and 'integrity' in e:
   meta=e['integrity'];meta['hash']=SHA(blob);size=int(meta.get('blockSize',4194304))
   meta['blocks']=[SHA(blob[i:i+size]) for i in range(0,len(blob),size)]
  data.extend(blob)
  if name in modified or name in ['browser-bridge.js','nano-payment-quality-105.js','nano-cash-guide-106.js',
                                   'nano-cash-plan-106.js','nano-payment-ledger-102.js','nano-checkout-choice-104.js']:
   (work/name).parent.mkdir(parents=True,exist_ok=True);(work/name).write_bytes(blob)
 assert modified=={'index.html','package.json','release-notes.js'}
 name='nano-credit-picker-107.js'
 blob=Path('.github/assets/'+name).read_bytes()
 header['files'][name]={'size':len(blob),'offset':str(len(data)),
    'integrity':{'algorithm':'SHA256','hash':SHA(blob),
       'blockSize':4194304,'blocks':[SHA(blob)]}}
 data.extend(blob);(work/name).write_bytes(blob)
 head=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8')
 pad=(len(head)+7)&~3
 final=struct.pack('<4I',4,pad+4,pad,len(head))+head+b'\0'*(pad-4-len(head))+data
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.writestr('payload/app.asar',final)
 with zipfile.ZipFile(target) as z:
  assert SHA(z.read('payload/app.asar'))==SHA(final)
 print(json.dumps({'version':'1.0.107','modified':sorted(modified),'added':name,
 'asarSha256':SHA(final),'zipSha256':SHA(target.read_bytes())}))
if __name__=='__main__':
 source,target,work=map(Path,sys.argv[1:4]);work.mkdir(parents=True,exist_ok=True);build(source,target,work)
