from pathlib import Path
import struct,json,hashlib,re,copy

src=Path('payload/app.asar')
out=Path('payload/app-v1.0.33.asar')
controller=Path('../tools/.tmp-controller-v1.0.33.js').read_text(encoding='utf-8')

with src.open('rb') as f:
    f.read(4); hs=struct.unpack('<I',f.read(4))[0]; hb=f.read(hs); sl=struct.unpack('<I',hb[4:8])[0]
    header=json.loads(hb[8:8+sl].decode('utf-8')); base=8+hs; blob=f.read()

files=[]
def walk(node,pre=''):
    for name,m in node.get('files',{}).items():
        q=f'{pre}/{name}' if pre else name
        if 'files' in m: walk(m,q)
        else: files.append((q,m))
walk(header)
original={q:blob[int(m['offset']):int(m['offset'])+int(m['size'])] for q,m in files}
modified={}
def get_text(path): return (modified.get(path,original[path])).decode('utf-8')
def set_text(path,text): modified[path]=text.encode('utf-8')

def patch_print_engine(path):
    s=get_text(path)
    mapping={
      'template1':('ar','invoice_template_premium_ar.html'),
      'template1_ar':('ar','invoice_template_premium_ar.html'),
      'template4':('ar','invoice_template_premium_ar.html'),
      'template1_fr':('fr','invoice_template_premium_fr.html'),
      'template5':('fr','invoice_template_premium_fr.html'),
      'template1_en':('en','invoice_template_premium_en.html'),
      'template6':('en','invoice_template_premium_en.html'),
      'template3':('en','invoice_template_premium_en.html'),
    }
    for key,(lang,fn) in mapping.items():
        pat=re.compile(r"('"+re.escape(key)+r"':\{'tplName':)(.*?)(,'lang':'"+lang+r"','design':(?:_0x300b1a\([^)]*\)|'design1')\})")
        s,n=pat.subn(lambda m:m.group(1)+repr(fn)+m.group(3),s,count=1)
        if n!=1: raise RuntimeError(f'{path}: mapping {key} count={n}')
    set_text(path,s)
for p in ['print-engine.js','mobile/www/print-engine.js']: patch_print_engine(p)

def patch_renderer(path):
    s=get_text(path)
    a=s.find('async function printInvoice'); b=s.find('let _printMenuContext',a)
    if a<0 or b<0: raise RuntimeError(path+' boundaries')
    f=s[a:b]
    if f.count("t('piece')")!=1: raise RuntimeError(path+' piece leak')
    f=f.replace("t('piece')","_0x5f4c24('piece')",1)
    old="['toLocaleDateString']('fr-FR')"
    if f.count(old)!=1: raise RuntimeError(path+' date locale')
    f=f.replace(old,"['toLocaleDateString'](_0x2d3485==='ar'?'ar-DZ':_0x2d3485==='en'?'en-US':'fr-FR')",1)
    set_text(path,s[:a]+f+s[b:])
for p in ['renderer.js','mobile/www/renderer.js']: patch_renderer(p)

for p in ['document-print-preview.js','mobile/www/document-print-preview.js']: set_text(p,controller)

s=get_text('pc-sync-ui.js')
old="const host=document.getElementById('nanoPcSyncPanel'); if(!host)return;"
new="const host=document.getElementById('nanoPcSyncPanel'); if(!host)return;const active=document.activeElement;if(active&&host.contains(active)&&/INPUT|TEXTAREA|SELECT/.test(active.tagName))return;"
if s.count(old)!=1: raise RuntimeError('pc sync anchor')
set_text('pc-sync-ui.js',s.replace(old,new,1))

for p in ['app-config.js','browser-ui.css','browser-ui.js','index.html','package-lock.json','package.json']:
    s=get_text(p)
    if '1.0.32' not in s: raise RuntimeError('version missing '+p)
    set_text(p,s.replace('1.0.32','1.0.33'))

new_header=copy.deepcopy(header); new_nodes={}
def walk2(node,pre=''):
    for name,m in node.get('files',{}).items():
        q=f'{pre}/{name}' if pre else name
        if 'files' in m: walk2(m,q)
        else:new_nodes[q]=m
walk2(new_header)

parts=[]; offset=0
for q,_ in files:
    data=modified.get(q,original[q]); m=new_nodes[q]
    m['offset']=str(offset); m['size']=len(data)
    integ=m.get('integrity') or {}; bs=int(integ.get('blockSize') or 4194304)
    integ['algorithm']='SHA256'; integ['hash']=hashlib.sha256(data).hexdigest(); integ['blockSize']=bs
    integ['blocks']=[hashlib.sha256(data[i:i+bs]).hexdigest() for i in range(0,len(data),bs)]
    m['integrity']=integ
    parts.append(data); offset+=len(data)

js=json.dumps(new_header,separators=(',',':'),ensure_ascii=False).encode('utf-8')
pad=(-len(js))%4
string_pickle=struct.pack('<I',len(js))+js+b'\0'*pad
header_pickle=struct.pack('<I',len(string_pickle))+string_pickle
out.write_bytes(struct.pack('<I',4)+struct.pack('<I',len(header_pickle))+header_pickle+b''.join(parts))
sha=hashlib.sha256(out.read_bytes()).hexdigest()
print('app.asar sha256',sha)
if sha!='0d0022d87d8211f468aade66a3f7840f28a2982a90f030a13041ede521253819':
    raise RuntimeError('unexpected sha '+sha)
out.replace(src)
