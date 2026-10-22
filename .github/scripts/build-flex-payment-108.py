#!/usr/bin/env python3
"""Verified NANO POS 1.0.108 ASAR patch: cashier amount => partial debt or cash change.
Original customer, activation, backup, receipt and inventory code remains intact.
"""
from pathlib import Path
import hashlib,json,struct,sys,zipfile,re
sha=lambda data:hashlib.sha256(data).hexdigest()
BASE='57a53244dd52b596166e5fcbc1627e372f0bde3b0d952a9e69de631cba46a500'
def once(src,old,new):
 count=src.count(old)
 assert count==1,('source_drift',old[:140],count)
 return src.replace(old,new)
def patch_html(src):
 pattern=r'                <div id="nanoCheckoutChoice104" class="grid grid-cols-2 gap-2">.*?\n                </div>'
 replacement='''                <div id="nanoCheckoutChoice104" class="space-y-2">
                    <label for="nanoTenderAmount108" class="block text-sm font-black text-slate-700"
                        data-i18n="nano_received_amount_108">المبلغ الذي قدمه الزبون (د.ج)</label>
                    <input type="number" id="nanoTenderAmount108" step="0.01" min="0"
                        inputmode="decimal" autocomplete="off" placeholder="0.00"
                        class="w-full border-2 border-emerald-200 rounded-xl p-3 text-xl font-black focus:border-emerald-500">
                    <input type="hidden" id="checkoutPaidAmount" value="0">
                    <div id="checkoutChangeUI" hidden>0.00</div>
                    <div id="nanoFlexibleSummary108" role="status" aria-live="polite"
                        class="bg-slate-50 border rounded-xl p-3 text-sm text-slate-700"></div>
                </div>'''
 src,count=re.subn(pattern,replacement,src,flags=re.S)
 assert count==1,('missing_checkout_buttons',count)
 for unwanted in ['onclick="nanoCheckoutPayFull104()"','onclick="nanoOpenCreditPicker107()"','data-i18n="nano_payment_credit_full"']:
  assert unwanted not in src,unwanted
 # Old cash guide refuses payment less than the invoice total; replace it with
 # the unified amount handler. Keep denomination calculator and customer picker.
 src=once(src,'<script defer src="nano-cash-guide-106.js"></script>',
   '<script defer src="nano-flex-core-108.js"></script>\n'
   '  <script defer src="nano-flex-payment-108.js"></script>')
 # legacy button helper no longer needed, avoids another unnecessary startup script
 src=once(src,'<script defer src="nano-checkout-choice-104.js"></script>','')
 assert 'src="nano-split-ui-102.js"' not in src
 return src
def patch_quality(src):
 src=once(src,'!(value===total||value===0)','value>total')
 src=once(src,'if(value===0&&total>0&&!String(c.customerId||\'\').trim())',
   "if(value<total&&!String(c.customerId||'').trim())")
 src=once(src,'!(p===0||p===total)','p>total')
 src=once(src,'if(p===0&&total>0&&!String(get(\'posCustomerSelect\')?.value||\'\').trim()){',
   "if(p<total&&!String(get('posCustomerSelect')?.value||'').trim()){")
 src=once(src,
   """       get('posCustomerSelect')?.focus();return;""",
   """       root.nanoOpenCreditPicker107?.();return;""")
 src=once(src,
   """const due=credit(),method=selected?.selectedOptions?.[0]?.textContent?.trim()||selected?.value||'';""",
   """const due=total>0&&p!==null&&p<total,method=selected?.selectedOptions?.[0]?.textContent?.trim()||selected?.value||'';""")
 src=once(src,
   """detail.textContent=t().method+': '+method+' · '+t().pay+': '+(due?t().credit:t().paid)+' · '+(due?t().creditInfo:t().complete);""",
   """detail.textContent=t().method+': '+method+' · '+t().pay+': '+(due
     ?money(p||0)+' د.ج · '+t().credit+': '+money(total-(p||0))+' د.ج'
     :t().paid)+' · '+(due?t().creditInfo:t().complete);""")
 src=once(src,
   """status.textContent=due&&!String(get('posCustomerSelect')?.value||'').trim()?t().customer:'';""",
   """status.textContent=due&&!String(get('posCustomerSelect')?.value||'').trim()?t().customer:'';""") if False else src
 return src
def patch_credit(src):
 src=once(src,
   """  root.checkoutMarkAsDebt?.();
  const paid=doc.getElementById('checkoutPaidAmount');
  if(paid){paid.value='0';paid.dispatchEvent(new root.Event('input',{bubbles:true}));}
  root.NANO_PAYMENT_QUALITY_105?.render?.();""",
   """  // Preserve the cashier's partial amount. Only the confirmed invoice
  // will post the remaining debt to the selected customer.
  root.NANO_FLEX_108?.render?.();
  root.NANO_PAYMENT_QUALITY_105?.render?.();""")
 return src
def patch_bridge(src):
 src=once(src,"!(__paid105===0||__paid105===__total105)",
   "__paid105>__total105")
 src=once(src,"if(__paid105===0&&__total105>0 &&",
   "if(__paid105<__total105 &&")
 src=once(src,
   """           tenderCents < paidCents) {""",
   """           tenderCents < paidCents ||
           (tenderCents<totalCents?paidCents!==tenderCents:paidCents!==totalCents)) {""")
 return src
def patch_notes(src):
 src=once(src,"const FALLBACK_VERSION = '1.0.107';","const FALLBACK_VERSION = '1.0.108';")
 a=src.index('  const OFFLINE = {');b=src.index('  const TITLES = {',a)
 return src[:a]+"""  const OFFLINE = {
    ar:['تحسينات الدفع: إدخال أي مبلغ نقدي مقدم من الزبون دون زري الدفع الكامل والدين الكامل.',
        'إن كان المبلغ أقل من إجمالي البيع، يسجل الفرق دينًا على زبون محدد أو زبون جديد.',
        'إذا زاد النقد على الإجمالي، يحسب البرنامج الصرف ويعرض الفئات النقدية المقترحة.',
        'تسديدات جزئية آمنة مع حفظ المدفوع والدين والصرف والمخزون دون ازدواج عند إعادة المحاولة.'],
    fr:['Un seul montant reçu, sans boutons paiement intégral ou crédit intégral.',
        'Paiement inférieur au total : le solde est inscrit comme dette du client.',
        'Espèces supérieures au total : monnaie à rendre et coupures suggérées.',
        'Transactions atomiques avec paiements partiels, stock et soldes fiables.'],
    en:['Enter any received amount, with no full-payment or full-credit buttons.',
        'Underpayment records the outstanding balance to a selected or newly created customer.',
        'Cash overpayment displays change due and suggested note/coin denominations.',
        'Partial payments remain idempotent and protect stock and customer balances.']
  };
"""+src[b:]
def build(source,outfile,work):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar'];raw=z.read('payload/app.asar')
 assert sha(raw)==BASE,'official ASAR digest mismatch'
 magic,block,hs,n=struct.unpack_from('<4I',raw);assert magic==4 and block==hs+4
 head=json.loads(raw[16:16+n]);start=8+block
 added=['nano-flex-core-108.js','nano-flex-payment-108.js']
 for f in added:assert f not in head['files']
 members=[]
 def scan(node,p=''):
  for name,e in node.get('files',{}).items():
   if 'files' in e:scan(e,p+name+'/')
   elif 'offset' in e:members.append((p+name,e))
 scan(head);assert len(members)>200
 members.sort(key=lambda x:int(x[1]['offset']))
 updated={'index.html':patch_html,'browser-bridge.js':patch_bridge,'nano-payment-quality-105.js':patch_quality,
          'nano-credit-picker-107.js':patch_credit,'release-notes.js':patch_notes}
 buf=bytearray();changed=set()
 for filename,e in members:
  orig=raw[start+int(e['offset']):start+int(e['offset'])+e['size']]
  assert len(orig)==e['size']
  blob=orig
  if filename in updated:
   blob=updated[filename](orig.decode()).encode();changed.add(filename)
  elif filename=='package.json':
   js=orig.decode();assert json.loads(js)['version']=='1.0.107'
   blob=once(js,'"version": "1.0.107"','"version": "1.0.108"').encode();changed.add(filename)
  e['offset']=str(len(buf));e['size']=len(blob)
  if filename in changed and 'integrity' in e:
   integrity=e['integrity'];integrity['hash']=sha(blob)
   stride=int(integrity.get('blockSize',4194304))
   integrity['blocks']=[sha(blob[i:i+stride]) for i in range(0,len(blob),stride)]
  buf.extend(blob)
  if filename in changed or filename in ['nano-cash-plan-106.js','nano-payment-ledger-102.js']:
   (work/filename).parent.mkdir(parents=True,exist_ok=True);(work/filename).write_bytes(blob)
 assert changed==set(updated)|{'package.json'}
 for filename in added:
  blob=Path('.github/assets/'+filename).read_bytes()
  head['files'][filename]={'size':len(blob),'offset':str(len(buf)),
    'integrity':{'algorithm':'SHA256','hash':sha(blob),
      'blockSize':4194304,'blocks':[sha(blob)]}}
  buf.extend(blob);(work/filename).write_bytes(blob)
 h=json.dumps(head,separators=(',',':'),ensure_ascii=False).encode()
 pad=(len(h)+7)&~3
 final=struct.pack('<4I',4,pad+4,pad,len(h))+h+b'\0'*(pad-4-len(h))+buf
 with zipfile.ZipFile(outfile,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',final)
 print(json.dumps({'version':'1.0.108','asar_sha256':sha(final),'zip_sha256':sha(outfile.read_bytes()),'changed':sorted(changed),'added':added}))
if __name__=='__main__':
 a,b,c=map(Path,sys.argv[1:4]);c.mkdir(parents=True,exist_ok=True);build(a,b,c)
