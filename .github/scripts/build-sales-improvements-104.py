#!/usr/bin/env python3
"""v1.0.104 'تحسينات': remove visible received cash and mixed payment from sale checkout.
Fail-closed byte patch of official 1.0.103 ASAR; preserves all store data, license and ledgers."""
import hashlib,json,struct,sys,zipfile,re
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
BASE='6622d30bf8a95071f97fbf257926d05a53bbade789e770738e88d8c843d3dcaf'
def once(s,a,b):
 assert s.count(a)==1,('source_changed',a[:135],s.count(a))
 return s.replace(a,b)
def html(s):
 # Preserve hidden model input as renderer.js reads it, but remove all received-amount
 # controls from the visible form. Keep explicit full-payment / full-credit actions.
 pat=re.compile(r'\n                <div>\s*<label[^>]*data-i18n="amount_received_label"[^>]*>.*?'
                r'<button[^>]*onclick="checkoutMarkAsDebt\(\)"[^>]*>.*?</button>\s*</div>',re.S)
 replacement='''
                <div id="nanoCheckoutChoice104" class="grid grid-cols-2 gap-2">
                    <input type="hidden" id="checkoutPaidAmount" value="0">
                    <div id="checkoutChangeUI" hidden>0.00</div>
                    <button type="button" onclick="nanoCheckoutPayFull104()"
                        class="py-3 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-300 font-black"
                        data-i18n="nano_payment_full">دفع كامل</button>
                    <button type="button" onclick="checkoutMarkAsDebt()"
                        class="py-3 rounded-xl bg-red-50 text-red-700 border border-red-200 font-black"
                        data-i18n="nano_payment_credit_full">دين كامل</button>
                </div>'''
 s,count=pat.subn(replacement,s)
 assert count==1,('received_amount_html_drift',count)
 # Do not initialize the 2026 mixed-payments overlay/IPC hook.
 s=once(s,'<script defer src="nano-split-ui-102.js"></script>','')
 # Keep existing read-only payment ledger to display historic mixed invoices.
 # Include new tiny helper for the full payment button.
 s=once(s,'<script defer src="nano-payment-ledger-102.js"></script>',
   '<script defer src="nano-payment-ledger-102.js"></script>\n  <script defer src="nano-checkout-choice-104.js"></script>')
 assert s.count('id="checkoutPaidAmount"')==1
 assert 'data-i18n="amount_received_label"' not in s
 return s
def fastpos(s):
 pat=re.compile(r'(?<!function )(?<!\.)\bsetupPayment\(\);')
 count=len(pat.findall(s))
 assert count==1,('fast_pos_setup_drift',count)
 return pat.sub('/* v1.0.104: mixed-payment UI disabled */',s)
def cashchange(s):
 # Keep append-only historic audit modal accessible, but stop creating cashier tendered
 # fields or requiring them to approve a sale.
 s=once(s,'function prepare(payload){',
 '''function prepare(payload){
 // v1.0.104: no tendered-amount requirement in new sales.
 return {ok:true};
''')
 s=once(s,'function init(){',
 '''function init(){
 { const toolbar=get('posToolbar');
   if(toolbar&&!get('nanoCashAuditOpen')){
     const button=d.createElement('button');
     button.type='button';button.id='nanoCashAuditOpen';
     button.className='nano-cash-audit-open';
     button.textContent=T().history;
     button.addEventListener('click',history);
     toolbar.append(button);
   }
 }
 // Keep the history viewer, remove cashier tendered cash input and change panel.
 return;
''')
 return s
def notes(s):
 s=once(s,"const FALLBACK_VERSION = '1.0.103';","const FALLBACK_VERSION = '1.0.104';")
 a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
 return s[:a]+"""  const OFFLINE = {
    ar:['تحسينات: إزالة حقل المبلغ المستلم من شاشة إتمام البيع، مع إزالة حاسبة الصرف الظاهرة.',
        'تحسينات: إزالة خيارات الدفع المختلط والمجزأ من شاشة البيع، والاكتفاء بطريقة دفع واحدة.',
        'الإبقاء على خيار الدفع الكامل أو البيع بالدين الكامل، دون المساس بالديون السابقة.',
        'المحافظة على الفواتير والعمليات التاريخية والتفعيل والنسخ الاحتياطية والتحديث من داخل البرنامج.'],
    fr:['Améliorations : retrait du montant reçu et du calcul de monnaie de la caisse.',
        'Retrait de l’interface de paiement mixte et fractionné ; un seul mode de paiement.',
        'Conservation des options paiement intégral et vente entièrement à crédit.',
        'Factures historiques, données, activation et sauvegardes conservées.'],
    en:['Improvements: remove the received-amount field and cashier change calculator.',
        'Remove mixed/split payments from new checkout; keep a single method.',
        'Preserve full payment or full-credit sales and previous outstanding debts.',
        'Preserve historical invoices, licensing, backups and in-app updates.']
  };
"""+s[b:]
def build(source,target,directory):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar']
  raw=z.read('payload/app.asar')
 assert H(raw)==BASE,'Official ASAR version mismatch'
 magic,block,hs,n=struct.unpack_from('<4I',raw)
 assert magic==4 and block==hs+4
 head=json.loads(raw[16:16+n])
 assert 'nano-checkout-choice-104.js' not in head['files']
 members=[]
 def walk(node,prefix=''):
  for name,entry in node.get('files',{}).items():
   if 'files' in entry:walk(entry,prefix+name+'/')
   elif 'offset' in entry:members.append((prefix+name,entry))
 walk(head);assert len(members)>200
 members.sort(key=lambda v:int(v[1]['offset']))
 data=bytearray();modified=set()
 for name,entry in members:
  raw_slice=raw[8+block+int(entry['offset']):8+block+int(entry['offset'])+entry['size']]
  assert len(raw_slice)==entry['size']
  if name=='index.html':value=html(raw_slice.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='nano-fast-pos.js':value=fastpos(raw_slice.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='nano-cash-change.js':value=cashchange(raw_slice.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='release-notes.js':value=notes(raw_slice.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='package.json':
   s=raw_slice.decode('utf8');assert json.loads(s)['version']=='1.0.103'
   value=once(s,'"version": "1.0.103"','"version": "1.0.104"').encode('utf8');modified.add(name)
  else:value=raw_slice
  entry['offset']=str(len(data));entry['size']=len(value)
  if name in modified and 'integrity' in entry:
   integrity=entry['integrity'];integrity['hash']=H(value)
   stride=int(integrity.get('blockSize',4194304))
   integrity['blocks']=[H(value[i:i+stride]) for i in range(0,len(value),stride)]
  data.extend(value)
  if name in modified:
   (directory/name).parent.mkdir(parents=True,exist_ok=True)
   (directory/name).write_bytes(value)
 assert modified=={'index.html','nano-fast-pos.js','nano-cash-change.js','release-notes.js','package.json'}
 helper='nano-checkout-choice-104.js'
 value=Path('.github/assets/'+helper).read_bytes()
 head['files'][helper]={'size':len(value),'offset':str(len(data)),
    'integrity':{'algorithm':'SHA256','hash':H(value),'blockSize':4194304,'blocks':[H(value)]}}
 data.extend(value);(directory/helper).write_bytes(value)
 metadata=json.dumps(head,separators=(',',':'),ensure_ascii=False).encode('utf8')
 length=(len(metadata)+7)&~3
 output=struct.pack('<4I',4,length+4,length,len(metadata))+metadata+b'\0'*(length-4-len(metadata))+data
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',output)
 with zipfile.ZipFile(target) as z:assert H(z.read('payload/app.asar'))==H(output)
 print(json.dumps({'version':'1.0.104','modified':sorted(modified),'added':helper,
    'asar_sha256':H(output),'zip_sha256':H(target.read_bytes())}))
if __name__=='__main__':
 src,out,directory=map(Path,sys.argv[1:4]);directory.mkdir(parents=True,exist_ok=True)
 build(src,out,directory)
