/* NANO POS 1.0.111 — durable annual sales invoice number generator.
 * Assign only during the same atomic sale transaction. Existing invoices never renumber.
 */
(function(root){
 'use strict';
 const PREFIX='FA';
 const PATTERN=/^FA-(20\d{2})-(\d{2,})$/;
 function next(db,date){
   if(!db||!Array.isArray(db.sales))throw Error('invalid_sales_database');
   const year=new Date(date).getFullYear();
   if(!Number.isInteger(year)||year<2020||year>9999)throw Error('invalid_invoice_year');
   const records=db.invoice_counters||{};
   const years=records.sales||{};
   let highest=Number(years[String(year)]||0);
   if(!Number.isSafeInteger(highest)||highest<0)throw Error('invalid_invoice_counter');
   for(const sale of db.sales){
     const match=PATTERN.exec(String(sale?.invoice_number||''));
     if(match&&Number(match[1])===year){
       const num=Number(match[2]);
       if(!Number.isSafeInteger(num)||num<1)throw Error('invalid_existing_invoice_number');
       if(num>highest)highest=num;
     }
   }
   if(highest>=Number.MAX_SAFE_INTEGER)throw Error('invoice_sequence_overflow');
   const sequence=highest+1;
   const number=PREFIX+'-'+year+'-'+String(sequence).padStart(2,'0');
   if(db.sales.some(s=>s.invoice_number===number))throw Error('duplicate_invoice_number');
   return {number,year,sequence};
 }
 function commit(db,planned){
   if(!db||!planned||!PATTERN.test(planned.number))throw Error('invalid_invoice_plan');
   if(db.sales.some(s=>s.invoice_number===planned.number))throw Error('duplicate_invoice_number');
   db.invoice_counters={...(db.invoice_counters||{}),
     sales:{...(db.invoice_counters?.sales||{}),[String(planned.year)]:planned.sequence}};
   return planned.number;
 }
 const api=Object.freeze({next,commit,PATTERN});
 root.NANO_INVOICE_SEQUENCE_111=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
