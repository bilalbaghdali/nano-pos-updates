'use strict';
// Keep the executable icon independent of the merchant's own brand.
const fs = require('node:fs');
const path = require('node:path');
const LOGO_FILE = 'shop-caption-logo.png';
const MAX_SIZE = 2 * 1024 * 1024;
function decodeLogo(dataUrl) {
  if (typeof dataUrl !== 'string' || dataUrl.length > MAX_SIZE * 1.4 + 100) throw Error('Invalid shop logo');
  const match = /^data:image\/(png|jpeg);base64,([A-Za-z0-9+/]+={0,2})$/.exec(dataUrl);
  if (!match) throw Error('Only PNG and JPEG shop logos are supported');
  const bytes = Buffer.from(match[2], 'base64');
  if (!bytes.length || bytes.length > MAX_SIZE) throw Error('Shop logo exceeds 2 MB');
  const png = bytes.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a','hex'));
  const jpeg = bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
  if ((match[1] === 'png' && !png) || (match[1] === 'jpeg' && !jpeg)) throw Error('Invalid image signature');
  return bytes;
}
function initShopLogo({ipcMain, app, getWindow, nativeImage, blankIconPath}) {
  const logoPath = () => path.join(app.getPath('userData'), LOGO_FILE);
  const baseIcon = () => nativeImage.createFromPath(blankIconPath);
  const applyImage = bytes => {
    const window = getWindow();
    if (!window || window.isDestroyed?.()) return false;
    const img = bytes ? nativeImage.createFromBuffer(bytes) : baseIcon();
    if (img.isEmpty()) throw Error('Invalid shop logo');
    if (img.getSize().width > 4096 || img.getSize().height > 4096) throw Error('Image dimensions exceed limit');
    // Electron controls the native window icon. Windows may retain a titlebar gutter.
    window.setIcon(bytes ? img.resize({width:64,height:64}) : img);
    return true;
  };
  const restore = () => {
    const dest = logoPath();
    if (fs.existsSync(dest)) {
      try { applyImage(fs.readFileSync(dest));return; } catch(e){ console.warn('[NANO POS] shop caption logo restore failed:',e.message); }
    }
    try { applyImage(null); } catch(e) { console.warn(e.message); }
  };
  ipcMain.handle('nano-shop-caption-logo',async (event,payload={})=>{
    if (!event.sender || event.sender !== getWindow()?.webContents) return {success:false,error:'Invalid window'};
    const dest = logoPath();
    if (payload?.clear === true) {
      // Clear only the native titlebar image, never the stored shop settings logo.
      try { fs.unlinkSync(dest); } catch(e) { if(e.code!=='ENOENT') throw e; }
      applyImage(null);
      return {success:true,hasLogo:false};
    }
    const bytes = decodeLogo(payload?.dataUrl);
    const image = nativeImage.createFromBuffer(bytes);
    if (image.isEmpty() || image.getSize().width>4096 || image.getSize().height>4096) throw Error('Invalid logo dimensions');
    const out = image.toPNG();
    if (out.length > 12 * 1024 * 1024) throw Error('Converted logo too large');
    const temp = dest+'.tmp';
    try { fs.writeFileSync(temp,out,{mode:0o600});fs.renameSync(temp,dest); }
    finally { try {fs.unlinkSync(temp);}catch{} }
    applyImage(out);
    return {success:true,hasLogo:true};
  });
  return {restore,logoPath};
}
module.exports = { decodeLogo, initShopLogo };