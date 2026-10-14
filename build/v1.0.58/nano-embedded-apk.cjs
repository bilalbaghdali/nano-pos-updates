'use strict';
// NANO POS desktop: serves only the bundled, SHA-256 verified Android APK.
// Read from the application package, never from userData/backups/license folders.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const VERSION = '1.3.7';
const APK_NAME = 'NANO-POS-Mobile-v1.3.7.apk';
const APK_SHA256 = '49503c07f39d941e308005df40b7de3243e1a379704b042ef1f7bd7e2bd6174c';
const APK_PATH = path.join(__dirname, 'downloads', APK_NAME);

function readVerifiedApk() {
  const data = fs.readFileSync(APK_PATH);
  if (data.length < 100000 || data.subarray(0, 2).toString('ascii') !== 'PK') {
    throw new Error('embedded_apk_invalid');
  }
  const digest = crypto.createHash('sha256').update(data).digest('hex');
  if (digest !== APK_SHA256) throw new Error('embedded_apk_checksum_mismatch');
  return data;
}

function status() {
  try {
    const apk = readVerifiedApk();
    return { available: true, local: true, version: VERSION,
      filename: APK_NAME, sha256: APK_SHA256, bytes: apk.length,
      downloadPath: '/nano-mobile.apk' };
  } catch {
    return { available: false, local: true, error: 'embedded_apk_unavailable' };
  }
}

function serve(req, res) {
  let pathname;
  try { pathname = new URL(req.url, 'http://localhost').pathname; }
  catch { return false; }
  if (pathname !== '/nano-mobile.apk' && pathname !== '/api/nano-mobile-apk') return false;

  if (!['GET', 'HEAD'].includes(req.method)) {
    res.writeHead(405, { 'Allow': 'GET, HEAD', 'Cache-Control': 'no-store' });
    res.end();
    return true;
  }

  let apk;
  try { apk = readVerifiedApk(); }
  catch {
    res.writeHead(404, {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'
    });
    res.end(JSON.stringify(status()));
    return true;
  }

  if (pathname === '/api/nano-mobile-apk') {
    const data = Buffer.from(JSON.stringify(status()), 'utf8');
    res.writeHead(200, {
      'Content-Type': 'application/json; charset=utf-8',
      'Content-Length': data.length,
      'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'
    });
    if (req.method === 'HEAD') res.end();
    else res.end(data);
    return true;
  }

  res.writeHead(200, {
    'Content-Type': 'application/vnd.android.package-archive',
    'Content-Disposition': 'attachment; filename="' + APK_NAME + '"',
    'Content-Length': apk.length,
    'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
    'X-Nano-Apk-Sha256': APK_SHA256
  });
  if (req.method === 'HEAD') res.end();
  else res.end(apk);
  return true;
}

function registerIpc({ ipcMain, dialog, app, getWindow }) {
  ipcMain.handle('nano-embedded-mobile-apk-status', () => status());
  ipcMain.handle('nano-save-embedded-mobile-apk', async () => {
    let data;
    try { data = readVerifiedApk(); }
    catch { return { success: false, error: 'bundled_apk_missing_or_invalid' }; }
    const options = {
      title: 'حفظ تطبيق NANO POS Mobile',
      defaultPath: path.join(app.getPath('downloads'), APK_NAME),
      buttonLabel: 'حفظ APK',
      filters: [{ name: 'Android APK', extensions: ['apk'] }]
    };
    const win = getWindow?.();
    const choice = win && !win.isDestroyed()
      ? await dialog.showSaveDialog(win, options)
      : await dialog.showSaveDialog(options);
    if (choice.canceled || !choice.filePath) return { success: false, cancelled: true };
    try {
      await fs.promises.writeFile(choice.filePath, data);
      return { success: true, filename: APK_NAME, savedPath: choice.filePath,
        version: VERSION, sha256: APK_SHA256 };
    } catch {
      return { success: false, error: 'cannot_save_apk' };
    }
  });
}
module.exports = { APK_NAME, APK_SHA256, VERSION, readVerifiedApk, status, serve, registerIpc };
