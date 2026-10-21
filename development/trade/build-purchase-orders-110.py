#!/usr/bin/env python3
"""NANO POS v1.1.0 purchase orders, from verified official 1.0.98 ASAR only.
This builder modifies browser-bridge, index, release notes, version and adds two scripts.
It NEVER rewrites a user's stored data/license/backups."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda x:hashlib.sha256(x).hexdigest()
BASE_ASAR='284f6fb14f6fc006b49de6dab3d6a4d0d305bb865796e6ac52b6a62d8d72ada3'
BRIDGE_SHA='e36f81cd3cb57ca21f282896a1b8d88bdfc866839fe3fb637f83ce02348b17d2'
def once(s,a,b):
 assert s.count(a)==1,('source_drift',a[:115],s.count(a))
 return s.replace(a,b)
def bridge(s):
 s=once(s,'   purchases: [],\n   bundles: [],','   purchases: [],\n   purchase_orders: [],\n   bundles: [],')
 s=once(s,"'products','customers','suppliers','sales','purchases','bundles','promotions',",
        "'products','customers','suppliers','sales','purchases','purchase_orders','bundles','promotions',")
 s=once(s,"   purchases: () => db.purchases || [],","   purchases: () => db.purchases || [],\n   'purchase-orders': () => db.purchase_orders || [],")
 # Forward stable id with remote LAN calls, enabling primary PC server's persistent RPC ledger.
 s=once(s,"body: JSON.stringify({ channel, args })",
        "body: JSON.stringify({ channel, args, operationId: "
        "(['create-purchase-order','confirm-purchase-order-receipt'].includes(channel)"
        "?String(args?.[0]?.operationId||args?.[0]?.receiptId||''):undefined) })")
 anchor="   if (channel === 'get-purchases') {"
 assert s.count(anchor)==1
 handlers=r"""
   // --- Stage 1.1.0: purchase orders are STOCK-NEUTRAL until a verified receipt.
   if (channel === 'get-purchase-orders') return clone(db.purchase_orders || []);
   if (channel === 'create-purchase-order' || channel === 'confirm-purchase-order-receipt') {
     const engine=window.NANO_PURCHASE_ORDER_ENGINE_110;
     if (!engine) return fail('purchase_order_engine_unavailable');
     const payload=args[0]||{};
     let planned;
     try {
       planned=channel==='create-purchase-order'
         ?engine.planOrder(db,payload)
         :engine.planReceipt(db,payload);
     } catch(error) { return fail(error.code || error.message || 'invalid_purchase_order'); }
     if (planned.duplicate) return planned.result;
     // No partial stock/debt writes: all changes are copied, then ONE durable
     // localStorage write is attempted. Any failure restores the old live DB.
     const previous=db;
     try {
       db=planned.snapshot;
       if (planned.purchase) {
         adjustPurchaseStock(planned.purchase.items, 1);
         changeSupplierDebt(planned.purchase.supplier_id, purchaseDebt(planned.purchase));
       }
       db.audit_log=Array.isArray(db.audit_log)?db.audit_log:[];
       db.audit_log.push({
         id:ids(),at:new Date().toISOString(),
         operation:channel,
         record_id:planned.result.purchaseId||planned.result.id,
         after:{
           order_id:payload.orderId||planned.result.id,
           receipt_id:payload.receiptId||null,
           supplier_id:payload.supplierId||planned.purchase?.supplier_id||null,
           total:planned.purchase?.total??null
         }
       });
       localStorage.setItem(KEY,JSON.stringify(db));
     } catch(error) {
       db=previous;
       console.error('[NANO POS] Atomic purchase-order write rejected:',error);
       return fail('purchase_order_write_failed_no_changes');
     }
     try { window.nanoNative?.pcSyncLocalChanged?.({revision:db.revision,at:Date.now()}); } catch {}
     try { window.dispatchEvent(new CustomEvent('nano-pos-data-saved',{detail:{revision:db.revision}})); } catch {}
     return clone(planned.result);
   }

"""
 s=once(s,anchor,handlers+anchor)
 return s
def release_notes(s):
 s=once(s,"const FALLBACK_VERSION = '1.0.98';","const FALLBACK_VERSION = '1.1.0';")
 a=s.index('  const OFFLINE = {');b=s.index('  const TITLES = {',a)
 notes="""  const OFFLINE = {
    ar:['إضافة أوامر شراء مستقلة لا تغير المخزون أو ديون الموردين عند إنشائها.',
        'استلام البضاعة جزئيًا أو كليًا، مع إنشاء فاتورة شراء مرتبطة بكل استلام معتمد.',
        'منع تجاوز الكميات المطلوبة والتكرار، وحفظ المخزون والدين وأمر الشراء في معاملة واحدة.',
        'حماية بيانات المتجر والتفعيل والنسخ الاحتياطية والتحديثات السابقة.'],
    fr:['Bons de commande sans modification de stock ou de dette.',
        'Réception partielle avec facture d’achat associée.',
        'Validation des quantités, anti-duplication et écriture atomique.',
        'Données, activation et sauvegardes préservées.'],
    en:['Purchase orders do not post stock or supplier debt.',
        'Partial or full receipts linked to purchase invoices.',
        'Quantity limits, duplicate protection, and atomic posting.',
        'Existing data, activation, backups and updater retained.']
  };
"""
 return s[:a]+notes+s[b:]
def build(source,target,work):
 with zipfile.ZipFile(source) as z:
  assert z.namelist()==['payload/app.asar']
  raw=z.read('payload/app.asar')
 assert sha(raw)==BASE_ASAR,'unexpected_official_v1.0.98_asar'
 magic,block,contents,n=struct.unpack_from('<4I',raw)
 assert magic==4 and block==contents+4
 header=json.loads(raw[16:16+n])
 for name in ['nano-purchase-order-engine.js','nano-purchase-order-ui.js']:
  assert name not in header['files']
 start=8+block
 nodes=[]
 def traverse(node,prefix=''):
  for name,e in node.get('files',{}).items():
   if 'files' in e:traverse(e,prefix+name+'/')
   elif 'offset' in e:nodes.append((prefix+name,e))
 traverse(header);assert len(nodes)>200
 nodes.sort(key=lambda pair:int(pair[1]['offset']))
 data=bytearray();modified=set()
 for name,e in nodes:
  old=raw[start+int(e['offset']):start+int(e['offset'])+e['size']]
  assert len(old)==e['size']
  if name=='browser-bridge.js':
   assert sha(old)==BRIDGE_SHA,'bridge_source_changed'
   new=bridge(old.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='index.html':
   s=old.decode('utf8')
   s=once(s,'<script src="browser-bridge.js"></script>',
       '<script src="nano-purchase-order-engine.js"></script>\n<script src="browser-bridge.js"></script>')
   s=once(s,'<script defer src="nano-inventory-shortages.js"></script>',
       '<script defer src="nano-inventory-shortages.js"></script>\n  <script defer src="nano-purchase-order-ui.js"></script>')
   new=s.encode('utf8');modified.add(name)
  elif name=='release-notes.js':
   new=release_notes(old.decode('utf8')).encode('utf8');modified.add(name)
  elif name=='package.json':
   src=old.decode('utf8');assert json.loads(src)['version']=='1.0.98'
   new=once(src,'"version": "1.0.98"','"version": "1.1.0"').encode('utf8');modified.add(name)
  else:new=old
  e['offset']=str(len(data));e['size']=len(new)
  if name in modified and 'integrity' in e:
   e['integrity']['hash']=sha(new)
   step=int(e['integrity'].get('blockSize',4194304))
   e['integrity']['blocks']=[sha(new[i:i+step]) for i in range(0,len(new),step)]
  data.extend(new)
  if name in modified:
   (work/name).parent.mkdir(parents=True,exist_ok=True);(work/name).write_bytes(new)
 assert modified=={'index.html','release-notes.js','package.json','browser-bridge.js'}
 for name,src in [('nano-purchase-order-engine.js','development/trade/nano-purchase-order-engine.js'),
                  ('nano-purchase-order-ui.js','development/trade/nano-purchase-order-ui.js')]:
  blob=Path(src).read_bytes()
  header['files'][name]={'size':len(blob),'offset':str(len(data)),
    'integrity':{'algorithm':'SHA256','hash':sha(blob),'blockSize':4194304,'blocks':[sha(blob)]}}
  data.extend(blob);(work/name).write_bytes(blob)
 head=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8')
 pad=(len(head)+7)&~3
 out=struct.pack('<4I',4,pad+4,pad,len(head))+head+b'\0'*(pad-4-len(head))+data
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',out)
 with zipfile.ZipFile(target) as z:assert sha(z.read('payload/app.asar'))==sha(out)
 print(json.dumps({'version':'1.1.0','modified':sorted(modified),
    'added':['nano-purchase-order-engine.js','nano-purchase-order-ui.js'],
    'asar_sha256':sha(out),'patch_sha256':sha(target.read_bytes())}))
if __name__=='__main__':
 src,dst,work=map(Path,sys.argv[1:4]);work.mkdir(parents=True,exist_ok=True)
 build(src,dst,work)
