'use strict';
const assert=require('node:assert/strict');
const test=require('node:test');
const {MIN,normalize,results,identify,fetchMatches}=require('./nano-v140-smart-lookup.js');
const sample=[{id:2,name:'موز طازج'},{id:1,name:'حليب كامل الدسم',barcode:'111'}, {id:3,name:'حليب خالي الدسم',barcode:'222'}, {id:4,name:'القهوة التركية'}];
test('activation threshold exactly four characters',()=>{
 assert.equal(MIN,4);assert.deepEqual(results(sample,'حلي'),[]);
 assert.equal(results(sample,'حليب').length,2);
});
test('contains-match not only name prefixes',()=>assert.equal(results(sample,'كامل')[0].id,1));
test('Arabic diacritics and variants normalize safely',()=>{
 assert.equal(normalize('إِسْمُ الـمَنْتَجِ'), 'اسم المنتج');
 assert.equal(normalize('قهوة'),normalize('قهوه'));
});
test('matching is case-insensitive Unicode and de-duplicates ids',()=>{
 const x=[{id:7,name:'Blue Coffee'},{id:7,name:'blue coffee'},{id:8,name:'BLUE CUP'}];
 assert.equal(results(x,'blue').length,2);
});
test('does not match barcode unless name matches',()=>{
 assert.deepEqual(results(sample,'1111'),[]);
});
test('creation and search fields classify products',()=>{
 for(const id of ['productName','posProductSearchInput','invProductSearch','promoProductSearch','bundleProductSearch','inventorySearch','globalSearch'])
  assert.equal(identify({tagName:'INPUT',id,type:'text',readOnly:false,disabled:false,placeholder:'',getAttribute:()=>''}),'product');
});
test('customer and supplier name fields are eligible; sensitive fields are excluded',()=>{
 const el=(id,type='text')=>({tagName:'INPUT',id,type,readOnly:false,disabled:false,placeholder:'',getAttribute:()=>''});
 assert.equal(identify(el('customerName')),'customer');
 assert.equal(identify(el('supName')),'supplier');
 assert.equal(identify(el('password','password')),null);
 assert.equal(identify({...el('productName'),readOnly:true}),null);
});
test('exactly no result or less than four chars never returns suggestions',async()=>{
 let count=0;const api={getProducts:async()=>{count++;return {items:sample,total:sample.length}}};
 assert.deepEqual(await fetchMatches(api,'product','حلي'),[]);
 assert.equal((await fetchMatches(api,'product','حليب')).length,2);assert.equal(count,2);
});
test('supports paginated product search',async()=>{
 let calls=[];const api={getProducts:async({page,perPage,search})=>{calls.push({page,perPage,search});return{items:page===1?sample:[],total:4}}};
 const found=await fetchMatches(api,'product','حليب');
 assert.equal(found.length,2);assert.equal(calls.length,1);assert.equal(calls[0].search,'حليب');
});
test('customer/supplier searches use their respective database endpoints',async()=>{
 let called=[];const api={getCustomers:async()=>{called.push('customer');return[{id:1,name:'Ahmed Said'}]},getSuppliers:async()=>{called.push('supplier');return[{id:1,name:'Ahmed Trading'}]}};
 assert.equal((await fetchMatches(api,'customer','ahmed')).length,1);
 assert.equal((await fetchMatches(api,'supplier','ahmed')).length,1);
 assert.deepEqual(called,['customer','supplier']);
});