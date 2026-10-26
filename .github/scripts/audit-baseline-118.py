#!/usr/bin/env python3
import json,re,struct,sys,zipfile
from pathlib import Path
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def unpack_asar(raw):
    magic,block,hs,n=struct.unpack_from('<4I',raw)
    assert magic==4 and block==hs+4, (magic,block,hs)
    tree=json.loads(raw[16:16+n]); start=8+block
    files={}
    def walk(node,prefix=''):
        for name,e in node.get('files',{}).items():
            p=prefix+name
            if 'files' in e: walk(e,p+'/')
            elif 'offset' in e and 'size' in e:
                a=start+int(e['offset']); files[p]=raw[a:a+int(e['size'])]
    walk(tree)
    return tree,files
def main(zip_path, output):
    with zipfile.ZipFile(zip_path) as z:
        assert z.namelist()==['payload/app.asar']
        tree,files=unpack_asar(z.read('payload/app.asar'))
    text={}
    for p,b in files.items():
        if p.endswith(('.js','.cjs','.mjs','.html','.json','.css')) and len(b)<12_000_000:
            try: text[p]=b.decode('utf-8')
            except UnicodeDecodeError: pass
    full='\n'.join(text.values())
    # Export root-level app code to a short-lived CI artifact so patches can target the verified source.
    source_dir=Path('source-audit')
    source_dir.mkdir(parents=True,exist_ok=True)
    selected=[]
    for p,b in files.items():
        if '/' not in p and (p.endswith(('.js','.html','.json','.css'))):
            out=source_dir/p
            out.write_bytes(b)
            selected.append((p,len(b)))
    print(f'Exported {len(selected)} root-level source files for inspection; no customer database or backup files are included.')
    package=json.loads(files['package.json'].decode())
    sections=[
      ('Update/Integrity',['autoUpdater','sha256','checkForUpdates','update-config','patch','rollback','checksum','integrity','app-update']),
      ('Backup/Restore',['backup','restore','MEGA','exportData','importData','backupData','restoreData','safeStorage','activation']),
      ('Checkout/Barcode',['cartItemsList','barcode','addToCart','saleInvoice','checkout','scanBarcode','speechSynthesis','cart']),
      ('Debt/Payments',['debt','payment','partial','credit','change','customerPayments','paymentHistory','dueDate']),
      ('Inventory/Purchase',['inventory','lowStock','shortage','supplier','purchaseOrder','stockAlert','minStock','purchase']),
      ('Login/Performance/Touch',['login','currentUser','DOMContentLoaded','renderHome','touchstart','pointerdown','loading','debounce','cache']),
      ('Reports/Export',['report','profit','expense','xlsx','Excel','jsPDF','PDF','slowMoving','turnover','salesReport'])
    ]
    lines=[f"Package version: {package.get('version')}",f"ASAR files: {len(files)}",f"Text source files inspected: {len(text)}"]
    lines.append("Relevant JS/UI files:")
    for p,s in text.items():
        if any(k in p.lower() for k in ('main','renderer','preload','backup','update','database','report','invoice')):
            lines.append(f" - {p} ({len(s)} chars)")
    lines.append("")
    for label,needles in sections:
        lines.append(f"## {label}")
        for needle in needles:
            count=len(re.findall(re.escape(needle),full,re.I))
            if count:
                lines.append(f"{needle}: {count}")
                for p,s in text.items():
                    m=re.search(re.escape(needle),s,re.I)
                    if m:
                        a=max(0,m.start()-180);b=min(len(s),m.end()+280)
                        excerpt=re.sub(r'\s+',' ',s[a:b]).strip()
                        lines.append(f"  {p}: {excerpt[:470]}")
                        break
            else:
                lines.append(f"{needle}: 0")
    report='\n'.join(lines)+'\n'
    Path(output).write_text(report,encoding='utf-8')
    print(report)
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('audit-baseline-118.py BASE.zip OUTPUT.txt')
    main(sys.argv[1],sys.argv[2])
