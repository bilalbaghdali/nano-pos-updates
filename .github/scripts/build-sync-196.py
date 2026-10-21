#!/usr/bin/env python3
"""NANO POS 1.0.96: patch only official v1.0.95 sync paths, refuse source drift."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
BASE='61ebf0d5f4cc36d5486e1ed37b24ee5463c7c0187db5e17ef98864dcc692593f'
EXPECTED={
'sync-operation-guard.cjs':'cd35385f0ee267c56973d871c644aa7296d5dd9fd54ad2e20db2a2454fc986b7',
'mobile-sync-server.cjs':'a0896a8a2c344a18b9ee8aa0d1aeb07e02b708d3b73f67a7f7e0800087c99678',
'pc-sync-service.cjs':'7076dd63c4f83b46259493337eff251bfafaa5c186d258528ee7411828f4ea6e',
}
def once(data,old,new):
    assert data.count(old)==1,(old[:100],data.count(old))
    return data.replace(old,new)
def patch(name,original):
    if name=='sync-operation-guard.cjs':
        return Path('.github/assets/sync-operation-guard-196.cjs').read_bytes()
    s=original.decode('utf8')
    if name=='mobile-sync-server.cjs':
        s=once(s,"const { serve: serveEmbeddedApk } = require('./nano-embedded-apk.cjs');",
            "const { serve: serveEmbeddedApk } = require('./nano-embedded-apk.cjs');\nconst { getSharedOperationGuard } = require('./sync-operation-guard.cjs');")
        s=once(s,'const SYNC_VERSION = 4;','const SYNC_VERSION = 5;')
        s=once(s,'  const dedupe = new Map();',
            "  const operationGuard = getSharedOperationGuard({storeFile: path.join(app.getPath('userData'), 'nano-sync-operation-ledger.json')});")
        a=s.index('  function getDedupe(operationId) {')
        b=s.index('  async function safeRpc(',a)
        s=s[:a]+s[b:]
        s=once(s,"        const operationId = String(body.operationId || '').trim().slice(0, 120);",
                  "        const operationId = String(body.operationId || '').trim();")
        a=s.index('        if (operationId) {\n          const cached = getDedupe(operationId);')
        b=s.index("        logActivity('rpc',",a)
        s=s[:a]+"""        const rpcContext = { ip: req.socket.remoteAddress || '', deviceId: device.id, deviceName: device.name, operationId };
        const authenticatedArgs = channel.startsWith('nano-count-')
          ? [{...(args[0]||{}),__nanoCountOrigin:{origin:'mobile',deviceId:device.id,deviceName:device.name}}]
          : args;
        const result = await operationGuard.call({
          deviceId: 'mobile:' + device.id, operationId, channel, args: authenticatedArgs,
          requireOperationId: true,
          dispatch: (c, payload) => c === 'get-customers'
            ? resolveCustomerRows(dispatchRpc, payload, rpcContext)
            : dispatchRpc(c, payload, rpcContext),
        });
"""+s[b:]
        old="""        const status = error.statusCode || (/not ready/i.test(String(error.message)) ? 503 : 500);
        return send(res, status, { success: false, error: error.message || 'rpc_failed' });"""
        new="""        const status = error.statusCode || (/not ready/i.test(String(error.message)) ? 503 : 500);
        const uncertain = error.code === 'operation_state_uncertain';
        return send(res, status, { success: false, error: error.code || error.message || 'rpc_failed',
          message: uncertain ? 'نتيجة العملية غير مؤكدة. راجع سجل المبيعات والمخزون على الكمبيوتر الرئيسي قبل إعادة المحاولة.' : (error.message || 'rpc_failed'),
          requiresReview: uncertain });"""
        s=once(s,old,new)
    elif name=='pc-sync-service.cjs':
        s=once(s,"const { createOperationGuard } = require('./sync-operation-guard.cjs');",
               "const { getSharedOperationGuard } = require('./sync-operation-guard.cjs');")
        s=once(s,'  const operationGuard = createOperationGuard();',
             "  const operationGuard = getSharedOperationGuard({storeFile: path.join(app.getPath('userData'), 'nano-sync-operation-ledger.json')});")
        s=once(s,'operationGuard.call({deviceId: session.id, operationId:',
             "operationGuard.call({deviceId: 'web:' + session.id, operationId:")
        s=once(s,'operationGuard.call({deviceId: device.id, operationId:',
             "operationGuard.call({deviceId: 'pc:' + device.id, operationId:")
        s=once(s,"} catch (error) { return webJson(res, 500, { success: false, error: 'rpc_failed', message: error.message }); }",
             "} catch (error) { return webJson(res, error.statusCode || 500, { success: false, error: error.code || 'rpc_failed', message: error.message }); }")
        s=once(s,"} catch (error) { return json(res, 500, { success: false, error: 'rpc_failed', message: error.message }); }",
             "} catch (error) { return json(res, error.statusCode || 500, { success: false, error: error.code || 'rpc_failed', message: error.message }); }")
        old="const snapshot = await dispatchRpc('__nano-pc-export-snapshot', []);"
        assert s.count(old)==2,s.count(old)
        s=s.replace(old,"const snapshot = await operationGuard.call({deviceId:'pc:snapshot', channel:'__nano-pc-export-snapshot', args:[], dispatch: dispatchRpc});")
    elif name=='package.json':
        assert json.loads(s)['version']=='1.0.95'
        s=once(s,'"version": "1.0.95"','"version": "1.0.96"')
    else:raise AssertionError('unexpected file')
    return s.encode('utf8')
def build(source,output,tests):
    with zipfile.ZipFile(source) as z:
        assert z.namelist()==['payload/app.asar']
        data=z.read('payload/app.asar')
    assert sha(data)==BASE, 'Not official 1.0.95 ASAR'
    magic,block,contents,n=struct.unpack_from('<4I',data)
    assert magic==4 and block==contents+4
    header=json.loads(data[16:16+n])
    entries=[]
    def walk(node,prefix=''):
        for name,entry in node.get('files',{}).items():
            if 'files' in entry:walk(entry,prefix+name+'/')
            elif 'offset' in entry:entries.append((prefix+name,entry))
    walk(header)
    entries.sort(key=lambda item:int(item[1]['offset']))
    rebuilt=bytearray()
    changed=set()
    for name,entry in entries:
        start=8+block+int(entry['offset'])
        original=data[start:start+entry['size']]
        assert len(original)==entry['size']
        if name in EXPECTED:
            assert sha(original)==EXPECTED[name], 'Source drift: '+name
            content=patch(name,original);changed.add(name)
        elif name=='package.json':
            content=patch(name,original);changed.add(name)
        else:content=original
        entry['offset']=str(len(rebuilt))
        entry['size']=len(content)
        if name in changed and 'integrity' in entry:
            item=entry['integrity'];item['hash']=sha(content)
            size=int(item.get('blockSize',4194304))
            item['blocks']=[sha(content[i:i+size]) for i in range(0,len(content),size)]
        rebuilt.extend(content)
        if name in changed or name in ['nano-customer-contract.cjs','nano-embedded-apk.cjs']:
            dest=tests/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
    assert changed==set(EXPECTED)|{'package.json'}
    raw=json.dumps(header,separators=(',',':'),ensure_ascii=False).encode('utf8')
    capacity=(len(raw)+7)&~3
    output_bytes=struct.pack('<4I',4,capacity+4,capacity,len(raw))+raw+b'\0'*(capacity-4-len(raw))+rebuilt
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload/app.asar',output_bytes)
    with zipfile.ZipFile(output) as z:assert sha(z.read('payload/app.asar'))==sha(output_bytes)
    print(json.dumps({'version':'1.0.96','modified':sorted(changed),'app_asar_sha256':sha(output_bytes),'patch_sha256':sha(output.read_bytes())}))
if __name__=='__main__':
    source,output,tests=sys.argv[1:4]
    directory=Path(tests);directory.mkdir(parents=True,exist_ok=True)
    build(Path(source),Path(output),directory)
