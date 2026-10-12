const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const money=require('./nano-currency-format.js');
const {decodeLogo,initShopLogo}=require('./shop-logo-window.cjs');
const tiny='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMBAutJS2QAAAAASUVORK5CYII=';
test('currency groups decimal numbers and localizes symbols',()=>{
 assert.equal(money.formatNumber(1234.5,{lang:'fr'}).replace(/\u00a0/g,' '),'1 234,50');
 assert.equal(money.formatNumber(1234.5,{lang:'en'}),'1,234.50');
 assert.equal(money.format(1234.5,{lang:'ar',context:'barcode'}).startsWith('د.ج'),true);
 assert.equal(money.format(12.5,{lang:'ar'}).endsWith('د.ج'),true);
});
test('currency parses arabic digits, thousands separators and invalid values',()=>{
 assert.equal(money.parseAmount('١ ٢٣٤,٥٠'),1234.5);
 assert.equal(money.parseAmount('1,234.50'),1234.5);
 assert.equal(money.parseAmount('1.234,50'),1234.5);
 assert.ok(Number.isNaN(money.parseAmount('غلط')));
});
test('currency custom symbols retained',()=>{
 money.configure({currency:'MAD',position:'before'});
 assert.equal(money.format(2,{lang:'fr'}).startsWith('MAD'),true);
 money.configure({currency:'د.ج',position:'after'});
});
test('shop logo rejects invalid content and oversize',()=>{
 assert.throws(()=>decodeLogo('data:text/html;base64,SGVsbG8='));
 assert.throws(()=>decodeLogo('data:image/jpeg;base64,SGVsbG8='));
 assert.ok(decodeLogo(tiny).length>40);
});
test('shop window logo persists, reloads and removes without changing store data',async()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'nano-logo-test-'));let handler,activeIcon;
 const img={isEmpty:()=>false,getSize:()=>({width:1,height:1}),toPNG:()=>decodeLogo(tiny),resize(){return this}};
 const win={webContents:{},isDestroyed:()=>false,setIcon(v){activeIcon=v}};
 const ipcMain={handle(_name,func){handler=func}};
 const nativeImage={createFromBuffer:()=>img,createFromPath:()=>img};
 const service=initShopLogo({ipcMain,app:{getPath:()=>root},getWindow:()=>win,nativeImage,blankIconPath:'/dev/null'});
 assert.equal((await handler({sender:win.webContents},{dataUrl:tiny})).hasLogo,true);
 assert.ok(fs.existsSync(service.logoPath()));service.restore();assert.ok(activeIcon);
 assert.equal((await handler({sender:win.webContents},{clear:true})).hasLogo,false);
 assert.ok(!fs.existsSync(service.logoPath()));
 assert.equal((await handler({sender:{}},{clear:true})).success,false);
 fs.rmSync(root,{recursive:true,force:true});
});