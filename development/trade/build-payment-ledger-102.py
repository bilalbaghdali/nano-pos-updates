#!/usr/bin/env python3
"""NANO POS v1.0.102 — exact SHA base, sale settlements and split checkout.
No migration or direct editing of shop data, license, backups, or manifest."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
SHA=lambda v:hashlib.sha256(v).hexdigest()
BASE='e787c99a4cec6470d0da92d81356906c5fa18215b6711f8ffbe2fd657e72b82f'
def one(s,a,b):
 assert s.count(a)==1,('source_marker_changed',a[:125],s.count(a))
 return s.replace(a,b)
def patch_bridge(s):
 anchor="  if (channel === 'get-purchases') {"
 settlement=r"""
  // New, idempotent debt payment adapter. Plan on a detached copy, persist it
  // before touching the live cache, and reject any ambiguous or repeated payment.
  if (channel === 'nano-record-settlement-102') {
    try {
      const ledger=window.NANO_PAYMENT_LEDGER_102;
      if(!ledger) return fail('payment_planner_unavailable');
      const planned=ledger.settle(db,args[0]||{});
      if(planned.duplicate)return clone(planned.result);
      localStorage.setItem(KEY,JSON.stringify(planned.next));
      db=planned.next;
      try {window.nanoNative?.pcSyncLocalChanged?.({revision:db.revision,at:Date.now()});}catch{}
      try {window.dispatchEvent(new CustomEvent('nano-pos-data-saved',{detail:{revision:db.revision}}));}catch{}
      return clone(planned.result);
    }catch(e){
      console.error('[NANO POS] verified settlement rejected:',e);
      return fail(e?.code||'payment_commit_failed_no_changes');
    }
  }

"""
 s=one(s,anchor,settlement+anchor)
 anchor="   if (channel === 'process-sale') {"
 s=one(s,anchor,anchor+r"""
     // Keep a snapshot before any sale stock/cash/debt mutation so failed
     // local storage writes cannot leave only part of the sale in live memory.
     const __nanoPriorSale102=clone(db);
     if (Array.isArray(args[0]?.checkout?.payments)) {
       const engine=window.NANO_PAYMENT_LEDGER_102;
       if(!engine)return fail('split_payment_module_unavailable');
       let split;
       try {split=engine.split(String(args[0]?.checkout?.total),
           args[0].checkout.payments,args[0].checkout.customerId);}
       catch(e){return fail(e.code||'invalid_split_payment');}
       args[0]={...args[0],checkout:{...args[0].checkout,
         paidAmount:split.paidAmount,paymentMethod:split.paymentMethod,
         cashTenderedAmount:null,__nanoSplit102:split}};
     }
     if ((args[0]?.items||[]).some(item=>Number(item?.qty)<0))
       return fail('استخدم المرتجعات لتصحيح الكميات بدل بيع بكمية سالبة.');
""")
 s=one(s,"items_count:items.length,items_qty:items.reduce((s,i)=>s+i.quantity,0),payments:[],items };",
  "items_count:items.length,items_qty:items.reduce((s,i)=>s+i.quantity,0),"
  "payments:c.__nanoSplit102?c.__nanoSplit102.payments.map((p,i)=>({id:'NANO-CHK-'+id+'-'+i,"
  "method:p.method,amount:p.amount,date,source:'initial-checkout'})):[],items };")
 old="     db.sales.unshift(sale);\n     if (remaining > 0) reviseCustomerBalance(customer.id,remaining);\n     save();"
 new=r"""     db.sales.unshift(sale);
     if (remaining > 0) reviseCustomerBalance(customer.id,remaining);
     // Write sale, related stock updates and customer balance as one snapshot.
     try {
       const snapshot={...db,revision:Number(db.revision||0)+1};
       localStorage.setItem(KEY,JSON.stringify(snapshot));
       db=snapshot;
       try {window.nanoNative?.pcSyncLocalChanged?.({revision:db.revision,at:Date.now()});}catch{}
       try {window.dispatchEvent(new CustomEvent('nano-pos-data-saved',{detail:{revision:db.revision}}));}catch{}
     } catch(error) {
       db=__nanoPriorSale102;
       console.error('[NANO POS] sale atomic write failed:',error);
       return fail('sale_write_failed_no_changes');
     }"""
 s=one(s,old,new)
 return s
def notes(s):
 s=one(s,"const FALLBACK_VERSION = '1.0.101';","const FALLBACK_VERSION = '1.0.102';")
 a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
 return s[:a]+"""  const OFFLINE = {
    ar:['تفعيل الدفع المختلط والجزئي داخل نافذة تسديد المبيعات الحالية.',
        'حساب المبالغ النقدية والبطاقة وCCP والتحويل والشيك مع منع تجاوز قيمة الفاتورة.',
        'حفظ تفاصيل الدفعات الأولى مع الفاتورة، وحماية بيع جديد من الكتابة الجزئية عند فشل التخزين.',
        'إضافة مسار آمن لتسديد ديون فواتير الزبائن والموردين بمعرّف ثابت لمنع الدفعات المكررة.'],
    fr:['Paiement mixte et partiel dans la fenêtre de caisse.',
        'Répartition carte, espèces, CCP, chèque et virement avec contrôle du total.',
        'Enregistrement des paiements et protection contre les écritures partielles.',
        'Paiements ultérieurs idempotents par identifiant de transaction.'],
    en:['Optional mixed and partial payments inside checkout.',
        'Payment splitting across cash, card, CCP, cheque and bank transfer.',
        'Records individual payment lines and protects sale writes on storage failures.',
        'Idempotent customer and supplier debt settlement API.']
  };
"""+s[b:]
def build(source,target,work):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar'];raw=z.read('payload/app.asar')
 assert SHA(raw)==BASE,'unexpected_official_source'
 magic,block,hs,n=struct.unpack_from('<4I',raw);assert magic==4 and block==hs+4
 head=json.loads(raw[16:16+n]);start=8+block;members=[]
 for filename in ('nano-payment-ledger-102.js','nano-split-ui-102.js'):
  assert filename not in head['files']
 def visit(node,prefix=''):
  for name,entry in node.get('files',{}).items():
   if 'files' in entry:visit(entry,prefix+name+'/')
   elif 'offset' in entry:members.append((prefix+name,entry))
 visit(head);assert len(members)>200
 members.sort(key=lambda x:int(x[1]['offset']))
 data=bytearray();changed=set()
 for name,entry in members:
  blob=raw[start+int(entry['offset']):start+int(entry['offset'])+entry['size']]
  assert len(blob)==entry['size']
  if name=='browser-bridge.js':
   blob=patch_bridge(blob.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='index.html':
   h=blob.decode('utf8')
   h=one(h,'<script defer src="nano-po-shortage-ui-100.js"></script>',
     '<script defer src="nano-payment-ledger-102.js"></script>\n'
     '  <script defer src="nano-split-ui-102.js"></script>\n'
     '  <script defer src="nano-po-shortage-ui-100.js"></script>')
   blob=h.encode('utf8');changed.add(name)
  elif name=='release-notes.js':
   blob=notes(blob.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='package.json':
   old=blob.decode('utf8');assert json.loads(old)['version']=='1.0.101'
   blob=one(old,'"version": "1.0.101"','"version": "1.0.102"').encode('utf8');changed.add(name)
  entry['offset']=str(len(data));entry['size']=len(blob)
  if name in changed and 'integrity' in entry:
   meta=entry['integrity'];meta['hash']=SHA(blob);step=int(meta.get('blockSize',4194304))
   meta['blocks']=[SHA(blob[i:i+step]) for i in range(0,len(blob),step)]
  data.extend(blob)
  if name in changed:(work/name).write_bytes(blob)
 assert changed=={'browser-bridge.js','index.html','release-notes.js','package.json'}
 for name in ['nano-payment-ledger-102.js','nano-split-ui-102.js']:
  blob=Path('development/trade/'+name).read_bytes()
  head['files'][name]={'size':len(blob),'offset':str(len(data)),
    'integrity':{'algorithm':'SHA256','hash':SHA(blob),'blockSize':4194304,'blocks':[SHA(blob)]}}
  data.extend(blob);(work/name).write_bytes(blob)
 packed=json.dumps(head,separators=(',',':'),ensure_ascii=False).encode('utf8')
 pad=(len(packed)+7)&~3
 output=struct.pack('<4I',4,pad+4,pad,len(packed))+packed+b'\0'*(pad-4-len(packed))+data
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',output)
 with zipfile.ZipFile(target) as z:assert SHA(z.read('payload/app.asar'))==SHA(output)
 print(json.dumps({'version':'1.0.102','asar_sha256':SHA(output),'zip_sha256':SHA(target.read_bytes())}))
if __name__=='__main__':
 src,dst,work=map(Path,sys.argv[1:4]);work.mkdir(parents=True,exist_ok=True);build(src,dst,work)
