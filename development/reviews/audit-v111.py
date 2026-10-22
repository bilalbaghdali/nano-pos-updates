#!/usr/bin/env python3
"""Read-only static audit of official NANO POS v1.0.111 ASAR.
Report counts and module names; NO passwords, credentials or business records.
"""
import json,hashlib,struct,zipfile,re,collections,datetime,os
from pathlib import Path
p=Path('source/NANO-POS-Patch-1.0.110-to-1.0.111-INVOICE-FA.zip')
manifest=json.loads(Path('nano-pos-update.json').read_text('utf8'))
assert manifest['version']=='1.0.111' and manifest['published']
assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['patches'][0]['sha256']
with zipfile.ZipFile(p) as z:
 assert z.namelist()==['payload/app.asar']
 raw=z.read('payload/app.asar')
assert hashlib.sha256(raw).hexdigest()==manifest['patches'][0]['appAsarSha256']
magic,b,hs,n=struct.unpack_from('<4I',raw);assert magic==4 and b==hs+4
tree=json.loads(raw[16:16+n]);start=8+b
entries=[]
def walk(node,prefix=''):
 for name,e in node['files'].items():
  if 'files' in e:walk(e,prefix+name+'/')
  else:entries.append((prefix+name,e))
walk(tree)
def blob(path):
 e=tree['files']
 for part in path.split('/'):e=e['files'][part] if 'files' in e else e[part]
 return raw[start+int(e['offset']):start+int(e['offset'])+e['size']]
def txt(path):return blob(path).decode('utf8')
files={k:int(v['size']) for k,v in entries}
ext=collections.Counter(Path(k).suffix.lower() for k in files)
priority=sorted([(k,v) for k,v in files.items() if v>=120*1024 and
 Path(k).suffix.lower() in ['.js','.cjs','.css','.html']],key=lambda t:-t[1])[:30]
i=txt('index.html')
script_tags=list(re.finditer(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>',i,re.I))
script_data=[{'src':m.group(1),'defer':bool(re.search(r'\bdefer\b',m.group(0),re.I)),
              'async':bool(re.search(r'\basync\b',m.group(0),re.I))} for m in script_tags]
script_src=[x['src'].split('/')[-1] for x in script_data]
duplicates=sorted([v for v,c in collections.Counter(script_src).items() if c>1])
candidates=[
 'browser-bridge.js','renderer.js','main.js','main.cjs','pc-sync-service.cjs',
 'mobile-sync-server.cjs','document-print-preview.js','nano-blue-print-110.js',
 'nano-invoice-layout-111.js','nano-invoice-sequence-111.js',
 'nano-payment-ledger-102.js','nano-sales-safe-195.js','nano-stock-forecast-198.js',
 'nano-mega-connect.js','nano-backup.js','updater-manager.js',
]
signals={
 'data_localstorage_save':r'localStorage\.setItem\(KEY,JSON\.stringify',
 'sale_atomic_snapshot':r'const snapshot=\{\.\.\.db,revision:',
 'sale_duplicate_request_token':r'nano_checkout_operation_id',
 'sale_cash_tender_record':r'cash_tendered_amount',
 'invoice_sequence_record':r'invoice_counters',
 'invoice_saved_number':r'invoice_number',
 'sale_edit':r'editSaleId',
 'event_dispatched':r'nano-pos-data-saved',
 'password_default':r'DEFAULT_PASSWORD',
 'password_plain_comparison':r'\.password\s*===|password\s*!==',
 'password_hashing':r'argon2|bcrypt|scrypt|pbkdf2',
 'innerHTML_assignments':r'\.innerHTML\s*=',
 'api_print_invoice':r'printInvoice',
 'print_preview':r'NanoDocumentPreview',
 'megasupport':r'mega',
 'license':r'license',
 'local_storage':r'localStorage',
 'websocket':r'WebSocket',
 'data_sync':r'pcSyncLocalChanged',
 'pdf':r'exportPdf|doExportPdf',
 'activity_audit':r'audit_log|sale_edit_audit',
 'operations_ledger':r'operationGuard',
 'csp_meta':r'Content-Security-Policy',
 'update_sha256':r'sha256|SHA-256',
}
matches={}
for path in candidates:
 if path not in files:continue
 try:s=txt(path)
 except:continue
 matches[path]={key:len(re.findall(rx,s,re.I)) for key,rx in signals.items() if re.search(rx,s,re.I)}
# Known actual downloaded HTML (not all stylesheet sources).
markup=i[:17000]
visibility={
 'index_script_total':len(script_data),
 'index_deferred_script_count':sum(v['defer'] for v in script_data),
 'index_async_script_count':sum(v['async'] for v in script_data),
 'index_script_dupes':duplicates,
 'loaded_dynamic_invoice_modules':{x:x in script_src for x in ['nano-blue-print-110.js','nano-invoice-layout-111.js','nano-invoice-sequence-111.js','document-print-preview.js']},
 'receipt_template_count':len([n for n in files if 'receipt_template' in n and n.endswith('.html')]),
 'invoice_template_count':len([n for n in files if 'invoice_template' in n and n.endswith('.html')]),
}
# Detect whether the actual platform has structured persistent files rather than browser storage.
root_script=[name for name in files if name in ['main.js','main.cjs','pc-sync-service.cjs','mobile-sync-server.cjs']]
auth_security={}
for path in ['browser-bridge.js','pc-sync-service.cjs','mobile-sync-server.cjs','main.cjs','main.js']:
 if path not in files:continue
 s=txt(path)
 auth_security[path]={
  'sha256':hashlib.sha256(blob(path)).hexdigest(),
  'crypto_usage':len(re.findall(r'\bcrypto\.|require\([\'"](?:node:)?crypto[\'"]\)',s)),
  'default_username_marker': 'DEFAULT_USERNAME' in s,
  'default_password_marker': 'DEFAULT_PASSWORD' in s,
  'plaintext_password_checks':len(re.findall(r'password\s*===|password\s*!==|\.password\s*===|\.password\s*!==',s)),
  'scrypt_bcrypt_argon':bool(re.search(r'argon2|bcrypt|scrypt|pbkdf2',s,re.I)),
  'auth_token':bool(re.search(r'Bearer|authorization|authentication|session',s,re.I)),
  'JSON_snapshot_storage':bool(re.search(r'localStorage\.setItem\(KEY,JSON\.stringify',s)),
  'file_write':bool(re.search(r'writeFileSync|writeFile\(',s)),
  'remote_web_proxy':bool(re.search(r'REMOTE_WEB|/nano-web/snapshot',s)),
 }
report={
 'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source':{'repo':'bilalbaghdali/nano-pos-updates','release':'v1.0.111',
   'official_asar_sha256':hashlib.sha256(raw).hexdigest(),
   'official_zip_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},
 'package':{'name':json.loads(txt('package.json')).get('name'),
   'version':json.loads(txt('package.json')).get('version'),
   'dependencies':list(json.loads(txt('package.json')).get('dependencies',{}).keys())},
 'archive':{'file_count':len(entries),'asar_bytes':len(raw),'extension_counts':ext,'large_files':priority,
   'selected_native_services':root_script},
 'index':visibility,
 'signal_counts_by_module':matches,
 'security_architecture_signals':auth_security,
}
out=Path('development/reviews/nano-pos-v111-static-review.json')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print('Verified official ASAR; static, read-only; '+str(len(entries))+' files; report saved '+str(out.stat().st_size)+' bytes')
