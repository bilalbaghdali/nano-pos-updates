/* NANO POS digital till total: read-only mirror of the existing #cartTotal. */
(function(root){'use strict';
const d=root.document;if(!d||root.NANO_DIGITAL_TOTAL_172)return;
root.NANO_DIGITAL_TOTAL_172=true;
const NS='http://www.w3.org/2000/svg';
const segments={
  a:'12,5 42,5 48,11 42,17 12,17 6,11',
  b:'49,12 55,18 55,45 49,51 43,45 43,18',
  c:'49,55 55,61 55,88 49,94 43,88 43,61',
  d:'12,91 42,91 48,97 42,103 12,103 6,97',
  e:'5,55 11,61 11,88 5,94 -1,88 -1,61',
  f:'5,12 11,18 11,45 5,51 -1,45 -1,18',
  g:'12,48 42,48 48,54 42,60 12,60 6,54'
};
const digits={'0':'abcdef','1':'bc','2':'abged','3':'abgcd','4':'fgbc',
 '5':'afgcd','6':'afgecd','7':'abc','8':'abcdefg','9':'abfgcd','-':'g'};
const ascii=v=>String(v||'').replace(/[٠-٩]/g,c=>String(c.charCodeAt(0)-1632))
 .replace(/[۰-۹]/g,c=>String(c.charCodeAt(0)-1776)).replace(/٫/g,'.').replace(/٬/g,',');
function el(tag,attrs={}){
 const node=d.createElementNS(NS,tag);
 for(const [key,value] of Object.entries(attrs))node.setAttribute(key,String(value));
 return node;
}
function segmentsFor(value){
 const group=el('g');let offset=0;
 for(const char of value){
   const width=(char==='.'||char===',')?20:58;
   const cell=el('g',{transform:`translate(${offset} 0)`});
   if(char==='.'||char===','){
     cell.appendChild(el('circle',{cx:9,cy:98,r:5,fill:'currentColor'}));
     if(char===',')cell.appendChild(el('path',{d:'M9 102 L4 113',stroke:'currentColor','stroke-width':4}));
   }else if(char===' '){ /* spacing */ }
   else {
     const lit=digits[char]||'';
     for(const [key,points] of Object.entries(segments)){
       cell.appendChild(el('polygon',{points,fill:'currentColor',class:lit.includes(key)?'nano-segment-on':'nano-segment-off'}));
     }
   }
   group.appendChild(cell);offset+=width+4;
 }
 return {group,width:Math.max(1,offset-4)};
}
function setup(){
 const section=d.getElementById('salesSection');
 const total=d.getElementById('cartTotal');
 const row=section?.querySelector('#posSummaryBar .pos-summary-total-row');
 if(!total||!row||d.getElementById('nanoDigitalTotal'))return;
 const screen=d.createElement('div');screen.id='nanoDigitalTotal';screen.className='nano-digital-total';
 screen.setAttribute('aria-hidden','true');
 const frame=d.createElement('div');frame.className='nano-digital-frame';
 const svg=el('svg',{viewBox:'0 0 58 108',preserveAspectRatio:'xMidYMid meet',class:'nano-digital-svg'});
 frame.appendChild(svg);screen.appendChild(frame);
 total.insertAdjacentElement('afterend',screen);
 row.classList.add('nano-digital-enabled');
 let previous=null;
 function refresh(){
   const raw=ascii(total.textContent).replace(/[^0-9.,\-]/g,'').slice(0,20)||'0.00';
   if(raw===previous)return;previous=raw;
   const {group,width}=segmentsFor(raw);
   svg.setAttribute('viewBox',`-3 -3 ${width+6} 114`);
   svg.replaceChildren(group);
   screen.setAttribute('title',raw);
 }
 const observer=new MutationObserver(refresh);
 observer.observe(total,{subtree:true,childList:true,characterData:true});
 refresh();
}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',setup,{once:true});else setup();
})(typeof window!=='undefined'?window:globalThis);
