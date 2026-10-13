#!/usr/bin/env python3
"""Small fail-closed patch for customer lookup in v1.0.53's authoritative mobile RPC."""

def patch_files(get, put):
    server = get('mobile-sync-server.cjs')
    anchor = "const crypto = require('node:crypto');"
    assert server.count(anchor) == 1, 'Unexpected mobile server import layout'
    server=server.replace(anchor,anchor+"\nconst { resolveCustomerRows } = require('./nano-customer-contract.cjs');",1)
    anchor = "const result = await dispatchRpc(channel, args, { ip: req.socket.remoteAddress || '', deviceId: device.id, deviceName: device.name, operationId });"
    assert server.count(anchor) == 1, 'Unexpected mobile customer RPC location'
    updated = """const rpcContext = { ip: req.socket.remoteAddress || '', deviceId: device.id, deviceName: device.name, operationId };
        const result = channel === 'get-customers'
          ? await resolveCustomerRows(dispatchRpc, args, rpcContext)
          : await dispatchRpc(channel, args, rpcContext);"""
    server=server.replace(anchor,updated,1)
    # Ensure the existing permissions check remains before snapshot-assisted reads.
    i=server.index('if (!permissionAllowed(device, channel))')
    j=server.index('resolveCustomerRows(dispatchRpc, args, rpcContext)')
    assert i<j, 'Paired-device customer permissions must be checked before fallback'
    put('mobile-sync-server.cjs',server)

    sync = get('mobile/www/mobile-sync-bridge.js')
    old = """    return body.result;
  }

  async function flushQueue()"""
    new = """    if (channel === 'get-customers') {
      const result = body.result;
      const rows = Array.isArray(result) ? result
        : (Array.isArray(result?.customers) ? result.customers
        : (Array.isArray(result?.rows) ? result.rows
        : (Array.isArray(result?.data?.customers) ? result.data.customers : null)));
      if (!rows) {
        const error = new Error('استجابة قائمة الزبائن من الكمبيوتر غير مكتملة؛ يرجى المحاولة مجددًا.');
        error.code = 'CUSTOMER_LIST_INVALID';
        throw error;
      }
      return rows;
    }
    return body.result;
  }

  async function flushQueue()"""
    assert sync.count(old)==1, 'Unexpected mobile sync response layout'
    sync=sync.replace(old,new,1)
    put('mobile/www/mobile-sync-bridge.js',sync)

    front = get('mobile/www/nano-mobile-credit.js')
    old = """    const list = await window.api.getCustomers();
    if (!Array.isArray(list)) throw new Error('لم تصل قائمة الزبائن من الكمبيوتر.');
    customers = list.filter(x => isValidId(x?.id));"""
    new = """    let response;
    try {
      response = await window.api.getCustomers();
    } catch (error) {
      const code = String(error?.code || 'CUSTOMER_LIST_FETCH_ERROR');
      console.warn('[NANO Mobile] Cannot load customer rows from primary PC', code);
      // Never replace an inaccessible authoritative list with stale local records.
      throw new Error('تعذر جلب بيانات الزبائن من الكمبيوتر. تأكد من اتصال الهاتف وصلاحية قسم الزبائن، ثم أعد المحاولة.');
    }
    const list = Array.isArray(response) ? response
      : (Array.isArray(response?.customers) ? response.customers
      : (Array.isArray(response?.rows) ? response.rows : null));
    if (!list) throw new Error('لم تصل قائمة زبائن صالحة من الكمبيوتر؛ لم يتم اعتماد أي بيع بالدين.');
    customers = list.filter(x => x && typeof x === 'object' && isValidId(x.id));"""
    assert front.count(old)==1, 'Unexpected customer-picker fetch implementation'
    front=front.replace(old,new,1)
    put('mobile/www/nano-mobile-credit.js',front)