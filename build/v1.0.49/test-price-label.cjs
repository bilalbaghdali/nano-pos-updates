'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {test}=require('node:test');
const root=__dirname;
const renderer=fs.readFileSync(path.join(root,'checked-renderer.js'),'utf8');
const html=fs.readFileSync(path.join(root,'checked-label-template.html'),'utf8');
const region=renderer.slice(renderer.indexOf('function plLabelFields('),renderer.indexOf('}function ',renderer.indexOf('function plLabelFields(')));
const match=region.match(/'priceText':([^,]*?),'variantsText':/);
assert.ok(match,'Barcode product price expression must exist');
const evaluate=new Function('_0x543bd4','_0x142734','t','return '+match[1]+';');
const value=(price)=>evaluate({price},()=> 'toFixed',(key)=>key==='dzd'?'دج':key);
function label(price){
 const amount=value(price);
 // The label has two separate placeholders: one currency, one numerical amount.
 return html.replace(/{{CURRENCY_TEXT}}/g,'دج').replace(/{{PRICE_TEXT}}/g,amount);
}
test('price value has only numbers and decimals and never a currency symbol',()=>{
 assert.equal(value(3800),'3800.00');
 assert.equal(value(2800.5),'2800.50');
 assert.equal(value(0),'0.00');
 for(const price of [0,0.5,12.25,3800,40000])assert.match(value(price),/^\d+\.\d{2}$/);
});
test('barcode template prints the selected currency exactly once',()=>{
 assert.equal((html.match(/{{CURRENCY_TEXT}}/g)||[]).length,1);
 assert.equal((html.match(/{{PRICE_TEXT}}/g)||[]).length,1);
 const output=label(3800);
 assert.equal((output.match(/دج/g)||[]).length,1,'Duplicated DZD symbol in label!');
 assert.match(output,/<span class="currency">دج<\/span><span class="amount">3800\.00<\/span>/);
});
test('preview and print use same corrected price field generator',()=>{
 const preview=renderer.slice(renderer.indexOf('async function renderPlPreview('),renderer.indexOf('}function ',renderer.indexOf('async function renderPlPreview(')));
 const print=renderer.slice(renderer.indexOf('async function plBuildCells('),renderer.indexOf('}function ',renderer.indexOf('async function plBuildCells(')));
 assert.ok(preview.includes('plLabelFields('));
 assert.ok(print.includes('plLabelFields('));
 assert.ok(preview.includes('fillLabelTemplate('));
 assert.ok(print.includes('fillLabelTemplate('));
});