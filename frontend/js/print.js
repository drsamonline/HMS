const $=(s,r=document)=>r.querySelector(s);
const esc=v=>String(v??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[c]));
const human=k=>String(k||"").replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());

function valueMarkup(v){
  if(v===null||v===undefined||v==="") return '<span class="print-empty">—</span>';
  if(Array.isArray(v)){
    if(!v.length) return '<span class="print-empty">No records</span>';
    return `<div class="print-list">${v.map((x,i)=>`<div class="print-list-item"><div class="print-index">${i+1}</div><div class="print-value">${valueMarkup(x)}</div></div>`).join("")}</div>`;
  }
  if(typeof v==="object"){
    const rows=Object.entries(v).map(([k,val])=>`<div class="print-field"><dt>${esc(human(k))}</dt><dd>${valueMarkup(val)}</dd></div>`).join("");
    return `<dl class="print-fields">${rows}</dl>`;
  }
  return `<span>${esc(v)}</span>`;
}

function sectionMarkup(section,label,data){
  return `<section class="print-section" data-print-section="${esc(section)}"><div class="print-section-heading"><h2>${esc(label)}</h2></div>${valueMarkup(data)}</section>`;
}

function buildSectionMap(report){
  return new Map((report?.sections||[]).map(section=>[section, report?.data?.[section]]));
}

export function createPrintPreview(host,{manifest,envelope,title="HHMS Clinical Report",patientLabel=""}){
  host.innerHTML="";
  const sections=(manifest?.sections||[]).filter(x=>x.available!==false);
  const data=envelope?.data||{};
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Print Preview</strong><span id="print-count" class="print-count"></span></div><div class="button-row"><button id="print-select-all" class="secondary">Select All</button><button id="print-clear-all" class="secondary">Clear All</button><button id="print-now">Print Selected</button></div></div><div class="print-selector no-print"></div><article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(title)}</h1><p>${esc(patientLabel)}</p><p class="print-generated">Generated: ${esc(new Date().toLocaleString())}</p></div></header><main id="print-pages"></main></article>`;
  host.appendChild(shell);
  const selector=$(".print-selector",shell), pages=$("#print-pages",shell);
  sections.forEach(sec=>{
    const label=sec.label||human(sec.section), item=document.createElement("label"); item.className="print-select-item";
    item.innerHTML=`<input type="checkbox" value="${esc(sec.section)}" checked><span><strong>${esc(label)}</strong><small>${esc(sec.page_group||"Clinical")}</small></span>`; selector.appendChild(item);
    const node=document.createElement("div"); node.dataset.section=sec.section; node.innerHTML=sectionMarkup(sec.section,label,data[sec.section]);
    if(sec.page_break_before) node.classList.add("print-page-break"); pages.appendChild(node);
  });
  const selected=()=>new Set([...selector.querySelectorAll("input:checked")].map(x=>x.value));
  const apply=()=>{const keep=selected();[...pages.children].forEach(node=>node.hidden=!keep.has(node.dataset.section));$("#print-count",shell).textContent=`${keep.size} section(s) selected`;};
  selector.addEventListener("change",apply);
  $("#print-select-all",shell).addEventListener("click",()=>{selector.querySelectorAll("input").forEach(x=>x.checked=true);apply()});
  $("#print-clear-all",shell).addEventListener("click",()=>{selector.querySelectorAll("input").forEach(x=>x.checked=false);apply()});
  $("#print-now",shell).addEventListener("click",()=>{apply();if(!selected().size){window.alert("Select at least one section to print.");return;}window.print();});
  apply(); return {apply,selected};
}

export function createBatchPrintPreview(host,{reports=[],title="HHMS Batch Clinical Reports"}){
  host.innerHTML="";
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Batch Print Preview</strong><span id="batch-print-count" class="print-count"></span></div><div class="button-row"><button id="batch-select-all" class="secondary">Select All</button><button id="batch-clear-all" class="secondary">Clear All</button><button id="batch-print">Print Selected Cases</button></div></div><div class="print-batch-selector no-print"></div><article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(title)}</h1><p class="print-generated">Generated: ${esc(new Date().toLocaleString())}</p></div></header><main id="batch-print-pages"></main></article>`;
  host.appendChild(shell);
  const selector=$(".print-batch-selector",shell), pages=$("#batch-print-pages",shell);
  reports.forEach((entry,index)=>{
    const report=entry.report||entry, id=String(report.case_record_id||entry.case_record_id||index), label=entry.case_number||`Case ${id}`;
    const item=document.createElement("label"); item.className="print-select-item"; item.innerHTML=`<input type="checkbox" value="${esc(id)}" checked><span><strong>${esc(label)}</strong><small>Patient ID ${esc(report.patient_id||entry.patient_id||"")}</small></span>`; selector.appendChild(item);
    const wrap=document.createElement("div"); wrap.className="batch-report-sheet"; wrap.dataset.caseId=id;
    wrap.innerHTML=`<div class="batch-case-heading"><h2>${esc(label)}</h2><p>Patient ID: ${esc(report.patient_id||entry.patient_id||"")}</p></div>`;
    for(const [section,data] of Object.entries(report.data||{})) wrap.insertAdjacentHTML("beforeend",sectionMarkup(section,human(section),data));
    pages.appendChild(wrap);
  });
  const selected=()=>new Set([...selector.querySelectorAll("input:checked")].map(x=>x.value));
  const apply=()=>{const keep=selected();[...pages.children].forEach(node=>node.hidden=!keep.has(node.dataset.caseId));$("#batch-print-count",shell).textContent=`${keep.size} case(s) selected`;};
  selector.addEventListener("change",apply);
  $("#batch-select-all",shell).addEventListener("click",()=>{selector.querySelectorAll("input").forEach(x=>x.checked=true);apply()});
  $("#batch-clear-all",shell).addEventListener("click",()=>{selector.querySelectorAll("input").forEach(x=>x.checked=false);apply()});
  $("#batch-print",shell).addEventListener("click",()=>{apply();if(!selected().size){window.alert("Select at least one case to print.");return;}window.print();});
  apply(); return {apply,selected};
}

export function clearPrintPreview(host){ if(host) host.innerHTML=""; }

const money=v=>{const n=Number(v);return Number.isFinite(n)?n.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}):esc(v??"—")};

export function createInvoicePrintPreview(host,{envelope,title=""}){
  host.innerHTML="";
  const data=envelope?.data||{};
  const inv=data.invoice||{}, patient=data.patient||{};
  const items=data.items||[], receipts=data.receipts||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Invoice Print Preview</strong><span class="print-count">${esc(envelope?.invoice_number||"")}</span></div><div class="button-row"><button id="invoice-print-now">Print Invoice</button></div></div><article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(title||envelope?.title||"Invoice")}</h1><p>${esc([patient.first_name,patient.last_name].filter(Boolean).join(" ")||"")}${patient.patient_number?` — ${esc(patient.patient_number)}`:""}</p><p class="print-generated">Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="invoice"><div class="print-section-heading"><h2>Invoice Details</h2></div><dl class="print-fields">`
    +`<div class="print-field"><dt>Invoice Number</dt><dd>${esc(inv.invoice_number??"")}</dd></div>`
    +`<div class="print-field"><dt>Invoice Date</dt><dd>${esc(inv.invoice_date?String(inv.invoice_date).slice(0,10):"")}</dd></div>`
    +`<div class="print-field"><dt>Payment Status</dt><dd>${esc(human(data.payment_status))}</dd></div>`
    +`<div class="print-field"><dt>Remarks</dt><dd>${valueMarkup(inv.remarks)}</dd></div>`
    +`</dl></section>`
    +`<section class="print-section" data-print-section="items"><div class="print-section-heading"><h2>Line Items</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>#</th><th>Type</th><th>Description</th><th>Qty</th><th>Unit Price</th><th>Line Total</th></tr></thead><tbody>`
      +items.map((it,i)=>`<tr><td>${i+1}</td><td>${esc(human(it.item_type))}</td><td>${esc(it.description)}</td><td>${esc(it.quantity)}</td><td>${money(it.unit_price)}</td><td>${money(it.line_total)}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No line items</div>')
    +`</section>`
    +`<section class="print-section" data-print-section="totals"><div class="print-section-heading"><h2>Totals</h2></div><dl class="print-fields">`
    +`<div class="print-field"><dt>Total Amount</dt><dd>${money(data.total_amount)}</dd></div>`
    +`<div class="print-field"><dt>Amount Paid</dt><dd>${money(data.amount_paid)}</dd></div>`
    +`<div class="print-field"><dt>Balance Due</dt><dd>${money(data.balance_due)}</dd></div>`
    +`</dl></section>`
    +`<section class="print-section print-page-break" data-print-section="receipts"><div class="print-section-heading"><h2>Receipts</h2></div>`
    +(receipts.length?`<table class="print-table"><thead><tr><th>Receipt</th><th>Date</th><th>Method</th><th>Reference</th><th>Amount</th></tr></thead><tbody>`
      +receipts.map(r=>`<tr><td>${esc(r.receipt_number)}</td><td>${esc(String(r.payment_datetime||"").slice(0,10))}</td><td>${esc(human(r.payment_method))}</td><td>${esc(r.transaction_reference??"—")}</td><td>${money(r.amount_paid)}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No payments recorded</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#invoice-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope};
}

export function createReceivablesAgingPrintPreview(host,{data,title="Receivables Aging Ledger"}){
  host.innerHTML="";
  const buckets=data?.buckets||[], items=data?.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Aging Print Preview</strong><span class="print-count">${esc(String(data?.as_of??""))}</span></div><div class="button-row"><button id="aging-print-now">Print Ledger</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(title)}</h1><p class="print-generated">As of: ${esc(String(data?.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="buckets"><div class="print-section-heading"><h2>Aging Buckets</h2></div>`
    +(buckets.length?`<table class="print-table"><thead><tr><th>Bucket</th><th>Invoices</th><th>Outstanding</th></tr></thead><tbody>`
      +buckets.map(b=>`<tr><td>${esc(b.label)}</td><td>${esc(b.invoice_count)}</td><td>${money(b.total_outstanding)}</td></tr>`).join("")
      +`<tr><td><strong>Total</strong></td><td><strong>${esc(data?.invoice_count??0)}</strong></td><td><strong>${money(data?.total_outstanding)}</strong></td></tr>`
      +`</tbody></table>`:'<div class="print-empty">No outstanding invoices</div>')
    +`</section>`
    +`<section class="print-section print-page-break" data-print-section="ledger"><div class="print-section-heading"><h2>Aging Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Invoice</th><th>Patient</th><th>Invoice Date</th><th>Total</th><th>Paid</th><th>Balance Due</th><th>Age (days)</th><th>Bucket</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.invoice_number)}</td><td>${esc(it.patient_name)}${it.patient_number?` — ${esc(it.patient_number)}`:""}</td><td>${esc(String(it.invoice_date||"").slice(0,10))}</td><td>${money(it.total_amount)}</td><td>${money(it.amount_paid)}</td><td>${money(it.balance_due)}</td><td>${esc(it.days_outstanding)}</td><td>${esc(it.bucket_label)}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">Nothing outstanding — the ledger is clear</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#aging-print-now",shell).addEventListener("click",()=>window.print());
  return {data};
}

export function createInvoiceReceiptContinuityPrintPreview(host,{data,title="Invoice Receipt Continuity Report"}){
  host.innerHTML="";
  const issues=data?.issues||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Continuity Print Preview</strong><span class="print-count">${esc(String(data?.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="continuity-print-now">Print Report</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(title)}</h1><p class="print-generated">Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Continuity Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Invoices checked</td><td>${esc(data?.invoices_checked??0)}</td></tr>`
    +`<tr><td>Invoices with receipts</td><td>${esc(data?.invoices_with_receipts??0)}</td></tr>`
    +`<tr><td>Invoices missing receipts</td><td>${esc(data?.invoices_missing_receipts??0)}</td></tr>`
    +`<tr><td>Duplicate receipt numbers</td><td>${esc(data?.duplicate_receipt_count??0)}</td></tr>`
    +`<tr><td>Sequence breaks</td><td>${esc(data?.sequence_break_count??0)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="issues"><div class="print-section-heading"><h2>Continuity Issues</h2></div>`
    +(issues.length?`<table class="print-table"><thead><tr><th>Invoice</th><th>Patient</th><th>Issue</th><th>Expected</th><th>Actual</th><th>Missing</th><th>First Receipt</th><th>Last Receipt</th><th>Duplicates</th></tr></thead><tbody>`
      +issues.map(it=>`<tr><td>${esc(it.invoice_number)}</td><td>${esc(it.patient_name)}${it.patient_number?` — ${esc(it.patient_number)}`:""}</td><td>${esc(human(it.gap_type))}</td><td>${esc(it.expected_count)}</td><td>${esc(it.actual_count)}</td><td>${esc(it.missing_count)}</td><td>${esc(it.first_receipt_number??"—")}</td><td>${esc(it.last_receipt_number??"—")}</td><td>${esc((it.duplicate_receipt_numbers||[]).join(", ")||"—")}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No continuity issues detected — the receipt book is consistent</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#continuity-print-now",shell).addEventListener("click",()=>window.print());
  return {data};
}

export function createReceiptNumberingContinuityPrintPreview(host,{data,title="Receipt Numbering Continuity Audit"}){
  host.innerHTML="";
  const series=data?.series||[];
  const gapped=series.filter(s=>(s.gap_count??0)>0);
  const dupes=series.filter(s=>(s.duplicate_numbers||[]).length>0);
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Receipt Numbering Print Preview</strong><span class="print-count">${esc(String(data?.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="receipt-numbering-print-now">Print Audit</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(title)}</h1><p class="print-generated">Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Audit Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Receipts checked</td><td>${esc(data?.receipts_checked??0)}</td></tr>`
    +`<tr><td>Number series</td><td>${esc(data?.series_count??0)}</td></tr>`
    +`<tr><td>Clean series</td><td>${esc(data?.clean_series_count??0)}</td></tr>`
    +`<tr><td>Total missing numbers</td><td>${esc(data?.total_gap_count??0)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section" data-print-section="series"><div class="print-section-heading"><h2>Receipt Series Summary</h2></div>`
    +(series.length?`<table class="print-table"><thead><tr><th>Series Prefix</th><th>First</th><th>Last</th><th>Expected</th><th>Actual</th><th>Gaps</th><th>Duplicates</th></tr></thead><tbody>`
      +series.map(s=>`<tr><td>${esc(s.prefix)}</td><td>${esc(s.first_number)}</td><td>${esc(s.last_number)}</td><td>${esc(s.expected_count)}</td><td>${esc(s.actual_count)}</td><td>${esc(s.gap_count)}</td><td>${esc((s.duplicate_numbers||[]).join(", ")||"—")}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No receipt numbers recorded yet</div>')
    +`</section>`
    +`<section class="print-section print-page-break" data-print-section="missing"><div class="print-section-heading"><h2>Missing Numbers Detail</h2></div>`
    +(gapped.length?gapped.map(s=>`<h3>Series ${esc(s.prefix)} (${esc(s.gap_count)} missing)</h3><p class="print-generated">${esc((s.missing_numbers||[]).join(", "))}</p>`).join(""):'<div class="print-empty">No numbering gaps detected.</div>')
    +`</section>`
    +`<section class="print-section" data-print-section="duplicates"><div class="print-section-heading"><h2>Duplicate Receipt Numbers</h2></div>`
    +(dupes.length?`<table class="print-table"><thead><tr><th>Series Prefix</th><th>Duplicated Numbers</th></tr></thead><tbody>`
      +dupes.map(s=>`<tr><td>${esc(s.prefix)}</td><td>${esc((s.duplicate_numbers||[]).join(", "))}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No duplicate receipt numbers detected.</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#receipt-numbering-print-now",shell).addEventListener("click",()=>window.print());
  return {data};
}
