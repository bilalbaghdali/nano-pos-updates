#!/usr/bin/env python3
"""NANO POS 1.0.105 improvements built only from verified official 1.0.104 ASAR.
Zero database or license migration; no mixed payment or tendered cash reintroduced."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
BASE='fbf0fdc38fac1fec62c49df0f0bba7dc5250a2297b63d4941af60778c1daca02'
def once(s,a,b):
 assert s.count(a)==1,('source_drift',a[:130],s.count(a))
 return s.replace(a,b)
def payment_bridge(s):
 s=once(s,
 "   if (channel === 'process-sale') {\n     // Keep a snapshot",
 """   if (channel === 'process-sale') {
     // For v1.0.105 checkout, an operation identifier is stable across retries and
     // persisted on the sale itself; returning a prior result must NEVER post stock
     // or customer balances twice. Old clients remain backward compatible.
     const __nanoId105=String(args[0]?.checkout?.nanoCheckoutRequestId||'').trim();
     let __nanoSignature105='';
     if(__nanoId105){
       if(!/^n105-[a-z0-9-]{12,110}$/i.test(__nanoId105))
         return fail('معرف تأكيد البيع غير صالح.');
       const __checkout105=args[0]?.checkout||{}, __items105=args[0]?.items;
       if(!Array.isArray(__items105)||!__items105.length)return fail('السلة فارغة.');
       const __money105=value=>{
         const n=Number(value);
         return Number.isFinite(n)&&n>=0&&Number.isSafeInteger(Math.round(n*100)) &&
           Math.abs(n*100-Math.round(n*100))<0.001?Math.round(n*100):null;
       };
       const __total105=__money105(__checkout105.total),
         __paid105=__money105(__checkout105.paidAmount);
       if(__total105===null||__paid105===null||!(__paid105===0||__paid105===__total105))
         return fail('الدفع يجب أن يكون كاملًا أو دينًا كاملًا.');
       const __method105=String(__checkout105.paymentMethod||'cash');
       if(!['cash','card','ccp','cheque','virement','transfer','other'].includes(__method105) ||
          Array.isArray(__checkout105.payments) || __checkout105.__nanoSplit102)
         return fail('طريقة الدفع المختلط غير متاحة.');
       if(__paid105===0&&__total105>0 &&
          !(db.customers||[]).some(c=>String(c.id)===String(__checkout105.customerId)))
         return fail('اختر زبونًا مسجلًا قبل البيع بالدين.');
       // Canonical payload fingerprint (not hash of mutable stock/customer state).
       __nanoSignature105=JSON.stringify({
         items:__items105.map(i=>[String(i.id??''),String(i.batch_id??''),
           Number(i.qty),Number(i.pos_price),Boolean(i.is_custom)]),
         customer:String(__checkout105.customerId??''),total:__total105,
         paid:__paid105,method:__method105,
         discount:Number(__checkout105.discount||0),
         taxPercentage:Number(__checkout105.taxPercentage||0)
       });
       const old=(db.sales||[]).find(s=>s.nano_checkout_operation_id===__nanoId105);
       if(old){
         if(old.nano_checkout_signature!==__nanoSignature105)
           return fail('لا يمكن إعادة استعمال معرف الدفع لعملية مختلفة.');
         return {success:true,id:old.id,saleId:old.id,alreadyProcessed:true,
           paid_amount:old.paid_amount,remaining_amount:old.remaining_amount,
           customerId:old.customer_id};
       }
     }
     // Keep a snapshot""")
 s=once(s,
 "      db.sales.unshift(sale);\n      if (remaining > 0) reviseCustomerBalance(customer.id,remaining);",
 """      if(__nanoId105){
        sale.nano_checkout_operation_id=__nanoId105;
        sale.nano_checkout_signature=__nanoSignature105;
      }
      db.sales.unshift(sale);
      if (remaining > 0) reviseCustomerBalance(customer.id,remaining);""")
 return s
def notes(s):
 s=once(s,"const FALLBACK_VERSION = '1.0.104';","const FALLBACK_VERSION = '1.0.105';")
 a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
 return s[:a]+"""  const OFFLINE = {
    ar:['تحسينات الدفع: ملخص واضح للمبلغ الإجمالي وطريقة الدفع وحالة الدفع الكامل أو الدين.',
        'منع تكرار تأكيد عملية البيع بنفس المعرّف حتى بعد إعادة المحاولة أو انقطاع الاتصال.',
        'التحقق من اختيار زبون مسجل قبل البيع بالدين والتحقق من قيم الدفع قبل تسجيل المخزون.',
        'إبقاء طريقة دفع واحدة دون مبلغ مستلم أو دفع مختلط، والحفاظ على التفعيل والنسخ الاحتياطية.'],
    fr:['Récapitulatif clair du total, mode et statut du paiement.',
        'Opérations idempotentes : un même identifiant ne crée jamais deux ventes.',
        'Validation du client pour vente à crédit et contrôle des montants.',
        'Un seul moyen de paiement, sans montant reçu ni paiement mixte.'],
    en:['Clear payment summary: total, method and full-payment/full-credit status.',
        'Idempotent checkout protects against duplicate sales on retries.',
        'Validate customer account for credit and exact amounts before stock posting.',
        'Keep a single payment method; no cash tender entry or split payments.']
  };
"""+s[b:]
def build(source,target,out):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar'];raw=z.read('payload/app.asar')
 assert H(raw)==BASE,'official ASAR source mismatch'
 magic,block,hs,n=struct.unpack_from('<4I',raw)
 assert magic==4 and block==hs+4
 header=json.loads(raw[16:16+n]);offset=8+block
 assert 'nano-payment-quality-105.js' not in header['files']
 members=[]
 def walk(node,prefix=''):
  for name,e in node.get('files',{}).items():
   if 'files' in e:walk(e,prefix+name+'/')
   elif 'offset' in e:members.append((prefix+name,e))
 walk(header);assert len(members)>200
 members.sort(key=lambda x:int(x[1]['offset']))
 data=bytearray();changed=set()
 for name,e in members:
  content=raw[offset+int(e['offset']):offset+int(e['offset'])+e['size']]
  assert len(content)==e['size']
  if name=='browser-bridge.js':
   content=payment_bridge(content.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='index.html':
   html=content.decode('utf8')
   html=once(html,'<script defer src="nano-checkout-choice-104.js"></script>',
      '<script defer src="nano-checkout-choice-104.js"></script>\\n'
      '  <script defer src="nano-payment-quality-105.js"></script>')
   html=html.replace('</script>\\n','</script>\n')
   assert 'data-i18n="amount_received_label"' not in html
   assert 'src="nano-split-ui-102.js"' not in html
   content=html.encode('utf8');changed.add(name)
  elif name=='release-notes.js':
   content=notes(content.decode('utf8')).encode('utf8');changed.add(name)
  elif name=='package.json':
   src=content.decode('utf8')
   assert json.loads(src)['version']=='1.0.104'
   content=once(src,'"version": "1.0.104"','"version": "1.0.105"').encode('utf8')
   changed.add(name)
  e['offset']=str(len(data));e['size']=len(content)
  if name in changed and 'integrity' in e:
   integ=e['integrity'];integ['hash']=H(content)
   blocksize=int(integ.get('blockSize',4194304))
   integ['blocks']=[H(content[i:i+blocksize]) for i in range(0,len(content),blocksize)]
  data.extend(content)
  if name in changed or name in ('nano-checkout-choice-104.js','nano-payment-ledger-102.js'):
   (out/name).parent.mkdir(parents=True,exist_ok=True)
   (out/name).write_bytes(content)
 assert changed=={'browser-bridge.js','index.html','release-notes.js','package.json'}
 helper='nano-payment-quality-105.js'
 content=Path('.github/assets/'+helper).read_bytes()
 header['files'][helper]={'size':len(content),'offset':str(len(data)),
   'integrity':{'algorithm':'SHA256','hash':H(content),
     'blockSize':4194304,'blocks':[H(content)]}}
 data.extend(content);(out/helper).write_bytes(content)
 meta=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8')
 pad=(len(meta)+7)&~3
 result=struct.pack('<4I',4,pad+4,pad,len(meta))+meta+b'\0'*(pad-4-len(meta))+data
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',result)
 with zipfile.ZipFile(target) as z:assert H(z.read('payload/app.asar'))==H(result)
 print(json.dumps({'version':'1.0.105','modified':sorted(changed),'added':helper,
   'asarSha256':H(result),'patchSha256':H(target.read_bytes())}))
if __name__=='__main__':
 p,q,r=map(Path,sys.argv[1:4]);r.mkdir(parents=True,exist_ok=True);build(p,q,r)
