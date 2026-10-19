'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require('/tmp/ui-test/node_modules/jsdom');
const root=process.argv[2];if(!root)throw Error('Source dir needed');
const sleep=t=>new Promise(resolve=>setTimeout(resolve,t));
async function testDatabase(){
 const dom=new JSDOM('<html><body></body></html>',{url:'http://localhost:4210',runScripts:'outside-only'});
 const w=dom.window;w.structuredClone=global.structuredClone;
 w.NANO_CONFIG={distribution:{cleanBusinessDataOnFirstRun:false},login:{username:'admin',password:'test'}};
 w.nanoLicense={access:async()=>({allowed:true}),installationId:()=> 'test'};
 const data={
   users:[{id:1,username:'admin',password:'test',role:'Admin'}],
   products:[
     {id:1,name:'Milk',barcode:'111',stock:0,min_stock:4,batches:[{stock:0}]},
     {id:2,name:'Bread',barcode:'222',stock:2,min_stock:5,batches:[{stock:2}]},
     {id:3,name:'Yogurt',barcode:'333',stock:5,min_stock:1,batches:[{stock:5,expiry_date:'2020-01-01'}]},
     {id:4,name:'Rice',barcode:'444',stock:20,min_stock:3,batches:[{stock:20,expiry_date:'2099-01-01'}]},
     {id:5,name:'Eggs',barcode:'555',stock:8,min_stock:2,batches:[{stock:8,expiry_date: new Date(Date.now()+5*86400000).toISOString().slice(0,10)}]},
     {id:6,name:'Bad date',barcode:'666',stock:4,batches:[{stock:4,expiry_date:'2026-99-99'}]}
   ],
   promotions:[{id:40,name:'Offer',end_date:new Date(Date.now()+2*86400000).toISOString().slice(0,10)}]
 };
 w.localStorage.setItem('lumina-browser-data-v1',JSON.stringify(data));
 w.eval(fs.readFileSync(root+'/browser-bridge.js','utf8'));
 const ipc=w.__browserElectron?.ipcRenderer?.invoke;assert.equal(typeof ipc,'function');
 let result=await ipc('get-notifications');
 assert.equal(result.outOfStock.length,1,'No real out of stock');
 assert.equal(result.outOfStock[0].id,1);
 assert.equal(result.lowStock.length,1,'No low stock');
 assert.equal(result.expired.length,1,'No expired');
 assert.equal(result.expiringSoon.length,1,'No approaching expiry');
 assert.equal(result.promotionsEnding.length,1,'No ending promotion');
 assert.equal(result.outOfStock[0].barcode,'111');
 const observed=[];w.addEventListener('nano-pos-data-saved',()=>observed.push(1));
 const update=await ipc('update-product',2,{min_stock:1});
 assert.equal(update.success,true,'Inventory update did not persist');
 result=await ipc('get-notifications');
 assert.equal(result.lowStock.length,0,'Low-stock alert was not updated');
 assert(observed.length,'No refresh event after saved inventory change');
 dom.window.close();
 console.log('PASS: real out-of-stock, low stock, expiry, promotions, live saved-data update');
 return {outOfStock:[{id:1,name:'Milk',barcode:'111',stock:0}],lowStock:[{id:2,name:'Bread',barcode:'222',stock:2,minimum:5}],
 expired:[{id:3,name:'Yogurt',barcode:'333',expiry_date:'2020-01-01'}],expiringSoon:[],promotionsEnding:[]};
}
async function testUI(response){
 const html='<html lang="ar"><head></head><body><button id="notificationToggle"></button><span id="notifBadge" class="hidden"></span>'+
  '<div id="notificationsDropdown" class="hidden"><button onclick="fetchNotifications()">Refresh</button><div id="notificationsContent"></div></div>'+
  '<section id="productsSection" class="hidden"></section><input id="inventorySearch"></body></html>';
 const dom=new JSDOM(html,{url:'http://localhost:4300/',runScripts:'outside-only'});
 const w=dom.window,d=w.document;
 let searches=0;d.getElementById('inventorySearch').addEventListener('keyup',()=>searches++);
 w.navigate=section=>{d.getElementById(section)?.classList.remove('hidden')};
 w.toggleNotifications=()=>d.getElementById('notificationsDropdown').classList.add('hidden');
 w.api={getNotifications:async()=>response};
 w.eval(fs.readFileSync(root+'/nano-notifications.js','utf8'));
 d.dispatchEvent(new w.Event('DOMContentLoaded'));
 const list=await w.NANO_NOTIFICATIONS_182.refresh(true);
 assert.equal(list.length,3,'Alert count incorrect');
 assert.equal(d.querySelectorAll('.nano-alert-item').length,3);
 assert.equal(d.querySelector('.nano-alert-count').textContent,'3');
 const first=d.querySelector('.nano-alert-item');first.click();
 assert.equal(d.getElementById('inventorySearch').value,'111');
 assert(searches>0,'Click did not search for selected item');
 assert(!d.getElementById('productsSection').classList.contains('hidden'));
 response.outOfStock.length=0;response.lowStock.length=0;response.expired.length=0;
 await w.NANO_NOTIFICATIONS_182.refresh(true);
 assert(d.getElementById('notifBadge').classList.contains('hidden'));
 assert(d.getElementById('notificationsContent').textContent.includes('لا توجد'));
 dom.window.close();
 console.log('PASS: live badge count, safe UI, product navigation, empty alert state');
}
async function testFallback(){
 const js=fs.readFileSync(root+'/nano-notifications.js','utf8');
 const dom=new JSDOM('<html><head></head><body><button id="notificationToggle"></button><span id="notifBadge"></span><div id="notificationsDropdown"><div id="notificationsContent"></div></div></body></html>',
 {url:'http://localhost:4400',runScripts:'outside-only'});
 const w=dom.window;let pages=0;
 w.api={getNotifications:async()=>[],getProducts:async({page})=>{pages++;return {items:page===1?[{id:1,name:'Absent',barcode:'X',stock:0}]:[],total:1};}};
 w.eval(js);w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
 const list=await w.NANO_NOTIFICATIONS_182.refresh(true);
 assert.equal(list.length,1);assert.equal(pages,1);
 dom.window.close();
 console.log('PASS: safe fallback to product API when older provider returns empty array');
}
(async()=>{const source=await testDatabase();await testUI(source);await testFallback();})().catch(e=>{console.error(e);process.exitCode=1});
