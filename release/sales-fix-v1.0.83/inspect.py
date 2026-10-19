from pathlib import Path
import re
p=Path('/tmp/inspect/src')
def show(label,text,term,before=150,after=4500,index=0):
 hits=list(re.finditer(re.escape(term),text,re.I))
 print('\n### '+label+' '+term+' COUNT '+str(len(hits)))
 if not hits: return
 m=hits[min(index,len(hits)-1)]
 print(text[max(0,m.start()-before):min(len(text),m.start()+after)].replace('\\x20',' '))
def balanced(text,term,max_len=12500):
 hits=list(re.finditer(r'\\b(?:async\\s+)?function\\s+'+re.escape(term)+r'\\s*\\(',text))
 print('\n### FUNC '+term+' '+str(len(hits)))
 if not hits:return
 start=hits[0].start();print(text[start:start+max_len].replace('\\x20',' '))
r=(p/'renderer.js').read_text();b=(p/'browser-bridge.js').read_text();pre=(p/'browser-preload.js').read_text();html=(p/'index.html').read_text()
for func in ['editSale','saveEditedSale','browseQuickEditSaleStep','openSaleDetailsModal','openProductAnalyticsModal','executeSalePayload']:
 balanced(r,func,7000)
for term in ['function editSale','function saveSale','updateSale','saleIdToEdit','editingSaleId','editSaleId','deleteSale','edit-sale','update-sale','get-product-analytics','getProductAnalytics','get-sales','get-sale-details','get-product','get-sales-stats']:
 show('BACKEND',b,term,150,3600)
for term in ['getProductAnalytics','getProducts','processSale','getSaleDetails']:
 show('PRELOAD',pre,term,120,400)
for term in ['openProductAnalyticsModal(','analyticsProductName','onclick="editSale(','salesHistory','id="loginOverlay"','id="loginBtn"']:
 show('HTML',html,term,120,1300)
print('\n### FILES')
for f in p.iterdir():
 if f.is_file() and ('sale' in f.name.lower() or 'database' in f.name.lower() or 'backend' in f.name.lower() or 'api' in f.name.lower() or 'renderer' in f.name.lower()):
  print(f.name,f.stat().st_size)
