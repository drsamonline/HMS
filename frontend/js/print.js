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

export function createReceivablesAgingPrintPreview(host,{envelope=null,data=null,title="Receivables Aging Ledger"}){
  host.innerHTML="";
  // Batch 91 — the Reports workspace feeds this renderer the print envelope
  // from POST /api/v1/reports/receivables-aging-print-envelope (same shape as
  // the dashboard feed under envelope.data); the dashboard payload stays
  // supported for backward compatibility.
  const src=envelope?.data??data??{};
  const buckets=src?.buckets||[], items=src?.items||[];
  const docTitle=envelope?.title||title;
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Aging Print Preview</strong><span class="print-count">${esc(String(src?.as_of??""))}</span></div><div class="button-row"><button id="aging-print-now">Print Ledger</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(docTitle)}</h1><p class="print-generated">As of: ${esc(String(src?.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="buckets"><div class="print-section-heading"><h2>Aging Buckets</h2></div>`
    +(buckets.length?`<table class="print-table"><thead><tr><th>Bucket</th><th>Invoices</th><th>Outstanding</th></tr></thead><tbody>`
      +buckets.map(b=>`<tr><td>${esc(b.label)}</td><td>${esc(b.invoice_count)}</td><td>${money(b.total_outstanding)}</td></tr>`).join("")
      +`<tr><td><strong>Total</strong></td><td><strong>${esc(src?.invoice_count??0)}</strong></td><td><strong>${money(src?.total_outstanding)}</strong></td></tr>`
      +`</tbody></table>`:'<div class="print-empty">No outstanding invoices</div>')
    +`</section>`
    +`<section class="print-section print-page-break" data-print-section="ledger"><div class="print-section-heading"><h2>Aging Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Invoice</th><th>Patient</th><th>Invoice Date</th><th>Total</th><th>Paid</th><th>Balance Due</th><th>Age (days)</th><th>Bucket</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.invoice_number)}</td><td>${esc(it.patient_name)}${it.patient_number?` — ${esc(it.patient_number)}`:""}</td><td>${esc(String(it.invoice_date||"").slice(0,10))}</td><td>${money(it.total_amount)}</td><td>${money(it.amount_paid)}</td><td>${money(it.balance_due)}</td><td>${esc(it.days_outstanding)}</td><td>${esc(it.bucket_label)}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">Nothing outstanding — the ledger is clear</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#aging-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,src};
}

export function createInvoiceReceiptContinuityPrintPreview(host,{envelope=null,data=null,title="Invoice Receipt Continuity Report"}){
  host.innerHTML="";
  // Batch 92 — the Reports workspace feeds this renderer the print envelope
  // from POST /api/v1/reports/invoice-receipt-continuity-print-envelope (same
  // shape as the dashboard feed under envelope.data); the dashboard payload
  // stays supported for backward compatibility.
  const src=envelope?.data??data??{};
  const issues=src?.issues||[];
  const docTitle=envelope?.title||title;
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Continuity Print Preview</strong><span class="print-count">${esc(String(src?.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="continuity-print-now">Print Report</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(docTitle)}</h1><p class="print-generated">Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Continuity Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Invoices checked</td><td>${esc(src?.invoices_checked??0)}</td></tr>`
    +`<tr><td>Invoices with receipts</td><td>${esc(src?.invoices_with_receipts??0)}</td></tr>`
    +`<tr><td>Invoices missing receipts</td><td>${esc(src?.invoices_missing_receipts??0)}</td></tr>`
    +`<tr><td>Duplicate receipt numbers</td><td>${esc(src?.duplicate_receipt_count??0)}</td></tr>`
    +`<tr><td>Sequence breaks</td><td>${esc(src?.sequence_break_count??0)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="issues"><div class="print-section-heading"><h2>Continuity Issues</h2></div>`
    +(issues.length?`<table class="print-table"><thead><tr><th>Invoice</th><th>Patient</th><th>Issue</th><th>Expected</th><th>Actual</th><th>Missing</th><th>First Receipt</th><th>Last Receipt</th><th>Duplicates</th></tr></thead><tbody>`
      +issues.map(it=>`<tr><td>${esc(it.invoice_number)}</td><td>${esc(it.patient_name)}${it.patient_number?` — ${esc(it.patient_number)}`:""}</td><td>${esc(human(it.gap_type))}</td><td>${esc(it.expected_count)}</td><td>${esc(it.actual_count)}</td><td>${esc(it.missing_count)}</td><td>${esc(it.first_receipt_number??"—")}</td><td>${esc(it.last_receipt_number??"—")}</td><td>${esc((it.duplicate_receipt_numbers||[]).join(", ")||"—")}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No continuity issues detected — the receipt book is consistent</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#continuity-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,src};
}

export function createReceiptNumberingContinuityPrintPreview(host,{envelope=null,data=null,title="Receipt Numbering Continuity Audit"}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const series=payload.series||[];
  const gapped=series.filter(s=>(s.gap_count??0)>0);
  const dupes=series.filter(s=>(s.duplicate_numbers||[]).length>0);
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Receipt Numbering Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="receipt-numbering-print-now">Print Audit</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Audit Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Receipts checked</td><td>${esc(payload.receipts_checked??0)}</td></tr>`
    +`<tr><td>Number series</td><td>${esc(payload.series_count??0)}</td></tr>`
    +`<tr><td>Clean series</td><td>${esc(payload.clean_series_count??0)}</td></tr>`
    +`<tr><td>Total missing numbers</td><td>${esc(payload.total_gap_count??0)}</td></tr>`
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
  return {envelope,data:payload};
}

export function createInvoicePaymentReconciliationPrintPreview(host,{envelope=null,data=null,title="Invoice Payment Reconciliation Ledger"}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const items=payload.items||[];
  const drift=items.filter(it=>it.is_reconciled===false);
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Reconciliation Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="reconciliation-print-now">Print Ledger</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">As of: ${esc(String(payload.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Reconciliation Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Invoices checked</td><td>${esc(payload.invoices_checked??0)}</td></tr>`
    +`<tr><td>Paid invoices</td><td>${esc(payload.paid_invoices??0)}</td></tr>`
    +`<tr><td>Partially paid invoices</td><td>${esc(payload.partially_paid_invoices??0)}</td></tr>`
    +`<tr><td>Unpaid invoices</td><td>${esc(payload.unpaid_invoices??0)}</td></tr>`
    +`<tr><td>Total billed</td><td>${money(payload.total_billed)}</td></tr>`
    +`<tr><td>Total paid</td><td>${money(payload.total_paid)}</td></tr>`
    +`<tr><td>Total outstanding</td><td>${money(payload.total_outstanding)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="ledger"><div class="print-section-heading"><h2>Reconciliation Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Invoice</th><th>Patient</th><th>Date</th><th>Total</th><th>Paid</th><th>Balance Due</th><th>Stored Status</th><th>Derived Status</th><th>Receipts</th><th>Reconciled</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.invoice_number)}</td><td>${esc(it.patient_name)}${it.patient_number?` — ${esc(it.patient_number)}`:""}</td><td>${esc(String(it.invoice_date||"").slice(0,10))}</td><td>${money(it.total_amount)}</td><td>${money(it.amount_paid)}</td><td>${money(it.balance_due)}</td><td>${esc(human(it.stored_payment_status))}</td><td>${esc(human(it.derived_payment_status))}</td><td>${esc(it.receipt_count)}</td><td>${it.is_reconciled?"✓":"✗ drift"}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No invoices to reconcile</div>')
    +`</section>`
    +`<section class="print-section" data-print-section="drift"><div class="print-section-heading"><h2>Status Drift Detail</h2></div>`
    +(drift.length?`<table class="print-table"><thead><tr><th>Invoice</th><th>Patient</th><th>Stored Status</th><th>Derived Status</th><th>Total</th><th>Paid</th><th>Balance Due</th></tr></thead><tbody>`
      +drift.map(it=>`<tr><td>${esc(it.invoice_number)}</td><td>${esc(it.patient_name)}</td><td>${esc(human(it.stored_payment_status))}</td><td>${esc(human(it.derived_payment_status))}</td><td>${money(it.total_amount)}</td><td>${money(it.amount_paid)}</td><td>${money(it.balance_due)}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No status drift detected — every invoice reconciles with the payment ledger.</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#reconciliation-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}
export function createCollectionSummaryPrintPreview(host,{envelope=null,data=null,title=""}={}){
  const payload=envelope?.data??data??{};
  const heading=title||envelope?.title||"Collection Summary by Patient";
  host.innerHTML="";
  const items=payload?.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Collection Summary Print Preview</strong><span class="print-count">${esc(String(payload?.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="collection-summary-print-now">Print Summary</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(heading)}</h1><p class="print-generated">As of: ${esc(String(payload?.as_of??"\u2014"))} \u00b7 Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Collection Summary Headlines</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Invoices checked</td><td>${esc(payload?.invoices_checked??0)}</td></tr>`
    +`<tr><td>Patients checked</td><td>${esc(payload?.patients_checked??0)}</td></tr>`
    +`<tr><td>Patients with outstanding</td><td>${esc(payload?.patients_with_outstanding??0)}</td></tr>`
    +`<tr><td>Total billed</td><td>${money(payload?.total_billed)}</td></tr>`
    +`<tr><td>Total collected</td><td>${money(payload?.total_collected)}</td></tr>`
    +`<tr><td>Total outstanding</td><td>${money(payload?.total_outstanding)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="patients"><div class="print-section-heading"><h2>Per-Patient Collection Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Patient</th><th>Invoices</th><th>Paid</th><th>Partial</th><th>Unpaid</th><th>Billed</th><th>Collected</th><th>Outstanding</th><th>Last Payment</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.patient_name)}${it.patient_number?` \u2014 ${esc(it.patient_number)}`:""}</td><td>${esc(it.invoice_count)}</td><td>${esc(it.paid_invoice_count)}</td><td>${esc(it.partial_invoice_count)}</td><td>${esc(it.unpaid_invoice_count)}</td><td>${money(it.total_billed)}</td><td>${money(it.total_collected)}</td><td>${money(it.outstanding)}</td><td>${esc(String(it.last_payment_date||"").slice(0,10)||"\u2014")}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No patient collections to summarise</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#collection-summary-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}

export function createPaymentMethodSummaryPrintPreview(host,{envelope=null,data=null,title="Payment Method Collection Summary"}={}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const items=payload.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Payment Method Summary Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="payment-method-summary-print-now">Print Summary</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">As of: ${esc(String(payload.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Collection Headlines</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Invoices checked</td><td>${esc(payload.invoices_checked??0)}</td></tr>`
    +`<tr><td>Receipts scanned</td><td>${esc(payload.receipts_scanned??0)}</td></tr>`
    +`<tr><td>Methods reported</td><td>${esc(payload.methods_reported??0)}</td></tr>`
    +`<tr><td>Total collected</td><td>${money(payload.total_collected)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="methods"><div class="print-section-heading"><h2>Per-Method Collection Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Method</th><th>Receipts</th><th>Invoices</th><th>Gross Received</th><th>Collected</th><th>Share %</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(human(it.payment_method))}</td><td>${esc(it.receipt_count)}</td><td>${esc(it.invoice_count)}</td><td>${money(it.gross_received)}</td><td>${money(it.collected)}</td><td>${esc(it.share_of_total)}%</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No payments recorded in this scan window</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#payment-method-summary-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}
export function createInvoiceOverpaymentPrintPreview(host,{envelope=null,data=null,title="Invoice Overpayment Ledger"}={}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const items=payload.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Overpayment Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="overpayment-print-now">Print Ledger</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">As of: ${esc(String(payload.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Overpayment Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Invoices overpaid</td><td>${esc(payload.invoices_overpaid??0)}</td></tr>`
    +`<tr><td>Total billed (overpaid invoices)</td><td>${money(payload.total_billed)}</td></tr>`
    +`<tr><td>Total paid (unclamped)</td><td>${money(payload.total_paid_raw)}</td></tr>`
    +`<tr><td>Total overpaid</td><td>${money(payload.total_overpaid)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="ledger"><div class="print-section-heading"><h2>Overpayment Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Invoice</th><th>Patient</th><th>Date</th><th>Total Billed</th><th>Paid (Unclamped)</th><th>Overpaid</th><th>Receipts</th><th>Stored Status</th><th>Derived Status</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.invoice_number)}</td><td>${esc(it.patient_name)}${it.patient_number?` — ${esc(it.patient_number)}`:""}</td><td>${esc(String(it.invoice_date||"").slice(0,10))}</td><td>${money(it.total_amount)}</td><td>${money(it.total_paid_raw)}</td><td>${money(it.overpaid_amount)}</td><td>${esc(it.receipt_count)}</td><td>${esc(human(it.stored_payment_status))}</td><td>${esc(human(it.derived_payment_status))}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No overpaid invoices detected in this scan window.</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#overpayment-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}

export function createPaymentMethodOverpaymentPrintPreview(host,{envelope=null,data=null,title="Payment Method Overpayment Breakdown"}={}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const items=payload.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Method Overpayment Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="method-overpayment-print-now">Print Breakdown</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">As of: ${esc(String(payload.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Overpayment Breakdown Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Invoices checked</td><td>${esc(payload.invoices_checked??0)}</td></tr>`
    +`<tr><td>Receipts scanned</td><td>${esc(payload.receipts_scanned??0)}</td></tr>`
    +`<tr><td>Methods reported</td><td>${esc(payload.methods_reported??0)}</td></tr>`
    +`<tr><td>Methods with overpayment</td><td>${esc(payload.methods_with_overpayment??0)}</td></tr>`
    +`<tr><td>Total gross received</td><td>${money(payload.total_gross)}</td></tr>`
    +`<tr><td>Total collected</td><td>${money(payload.total_collected)}</td></tr>`
    +`<tr><td>Total overpaid</td><td>${money(payload.total_overpaid)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="methods"><div class="print-section-heading"><h2>Per-Method Overpayment Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Method</th><th>Receipts</th><th>Invoices</th><th>Gross Received</th><th>Collected</th><th>Share %</th><th>Overpaid</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(human(it.payment_method))}</td><td>${esc(it.receipt_count)}</td><td>${esc(it.invoice_count)}</td><td>${money(it.gross_received)}</td><td>${money(it.collected)}</td><td>${esc(it.share_of_total)}%</td><td>${money(it.overpaid)}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No payments recorded in this scan window</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#method-overpayment-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}

export function createInvoiceSettlementAuditPrintPreview(host,{envelope=null,data=null,title="Invoice Settlement Audit"}={}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const items=payload.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Settlement Audit Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="settlement-audit-print-now">Print Audit</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">As of: ${esc(String(payload.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Settlement Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Invoices audited</td><td>${esc(payload.total_invoices??0)}</td></tr>`
    +`<tr><td>Cleared</td><td>${esc(payload.cleared_count??0)}</td></tr>`
    +`<tr><td>Unsettled</td><td>${esc(payload.unsettled_count??0)}</td></tr>`
    +`<tr><td>Total billed</td><td>${money(payload.total_billed)}</td></tr>`
    +`<tr><td>Total collected</td><td>${money(payload.total_collected)}</td></tr>`
    +`<tr><td>Total outstanding</td><td>${money(payload.total_outstanding)}</td></tr>`
    +`<tr><td>Total overpaid</td><td>${money(payload.total_overpaid)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="ledger"><div class="print-section-heading"><h2>Settlement Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Invoice</th><th>Patient</th><th>Date</th><th>Billed</th><th>Settled</th><th>Outstanding</th><th>Overpaid</th><th>Payments</th><th>Refunds</th><th>Status</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.invoice_number)}</td><td>${esc(it.patient_name)}${it.patient_number?` — ${esc(it.patient_number)}`:""}</td><td>${esc(String(it.invoice_date||"").slice(0,10))}</td><td>${money(it.total_amount)}</td><td>${money(it.settled_amount)}</td><td>${money(it.outstanding_amount)}</td><td>${money(it.overpayment_amount)}</td><td>${esc(it.payment_count)}</td><td>${esc(it.refund_count)}</td><td>${esc(human(it.derived_payment_status))}${it.is_cleared?" · Cleared":""}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No invoices found in this scan window.</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#settlement-audit-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}

export function createRefundAuditPrintPreview(host,{envelope=null,data=null,title="Refund Processing Audit"}={}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const items=payload.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Refund Audit Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="refund-audit-print-now">Print Audit</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">As of: ${esc(String(payload.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Refund Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Refunds scanned</td><td>${esc(payload.total_refunds??0)}</td></tr>`
    +`<tr><td>Processed</td><td>${esc(payload.processed_count??0)}</td></tr>`
    +`<tr><td>Drifted</td><td>${esc(payload.drifted_count??0)}</td></tr>`
    +`<tr><td>Total refunded</td><td>${money(payload.total_refunded)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="ledger"><div class="print-section-heading"><h2>Refund Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Receipt</th><th>Datetime</th><th>Method</th><th>Refund</th><th>Invoice</th><th>Net Paid</th><th>Remarks</th><th>State</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.receipt_number)}</td><td>${esc(String(it.payment_datetime||"").slice(0,16).replace("T"," "))}</td><td>${esc(human(it.payment_method))}</td><td>${money(it.refund_amount)}</td><td>${esc(it.invoice_number??"—")}</td><td>${it.invoice_net_paid==null?"—":money(it.invoice_net_paid)}</td><td>${it.has_remarks?"Yes":"No"}</td><td>${it.processing_complete?"Complete":"Drifted"}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No refund entries found in this scan window.</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#refund-audit-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}

export function createDischargeAuditPrintPreview(host,{envelope=null,data=null,title="Discharge Audit Ledger"}={}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const items=payload.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Discharge Audit Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="discharge-audit-print-now">Print Audit</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">As of: ${esc(String(payload.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Discharge Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Discharges audited</td><td>${esc(payload.total_discharges??0)}</td></tr>`
    +`<tr><td>Reconciled</td><td>${esc(payload.reconciled_count??0)}</td></tr>`
    +`<tr><td>Drifted</td><td>${esc(payload.drift_count??0)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="ledger"><div class="print-section-heading"><h2>Discharge Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Discharge</th><th>Datetime</th><th>Patient</th><th>Admission</th><th>Ward / Bed</th><th>Admission Discharged</th><th>Bed Freed</th><th>Hours Since</th><th>State</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.discharge_number)}</td><td>${esc(String(it.discharge_datetime||"").slice(0,16).replace("T"," "))}</td><td>${esc(it.patient_name)}${it.patient_number?` — ${esc(it.patient_number)}`:""}</td><td>${esc(it.admission_number)}</td><td>${esc(it.ward??"—")}${it.bed_number?` / ${esc(it.bed_number)}`:""}</td><td>${it.admission_discharged?"Yes":"No"}</td><td>${it.bed_freed?"Yes":"No"}</td><td>${esc(it.hours_since_discharge)}</td><td>${it.is_reconciled?"Reconciled":"Drifted"}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No discharges found in this scan window.</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#discharge-audit-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}

export function createOPDQueueSummaryPrintPreview(host,{envelope=null,data=null,title="OPD Queue Daily Summary"}={}){
  host.innerHTML="";
  const payload=envelope?.data??data??{};
  const items=payload.items||[];
  const shell=document.createElement("div"); shell.className="print-preview-shell";
  shell.innerHTML=`<div class="print-toolbar no-print"><div><strong>Queue Summary Print Preview</strong><span class="print-count">${esc(String(payload.as_of??"").slice(0,10))}</span></div><div class="button-row"><button id="queue-summary-print-now">Print Summary</button></div></div>`
    +`<article class="print-document"><header class="print-header"><div class="print-brand">HHMS</div><div><h1>${esc(envelope?.title||title)}</h1><p class="print-generated">As of: ${esc(String(payload.as_of??"—"))} · Generated: ${esc(new Date().toLocaleString())}</p></div></header><main>`
    +`<section class="print-section" data-print-section="summary"><div class="print-section-heading"><h2>Queue Summary</h2></div>`
    +`<table class="print-table"><tbody>`
    +`<tr><td>Days reported</td><td>${esc(payload.days_reported??0)}</td></tr>`
    +`<tr><td>Total tokens</td><td>${esc(payload.total_tokens??0)}</td></tr>`
    +`<tr><td>Open backlog</td><td>${esc(payload.total_open??0)}</td></tr>`
    +`</tbody></table></section>`
    +`<section class="print-section print-page-break" data-print-section="days"><div class="print-section-heading"><h2>Per-Day Queue Ledger</h2></div>`
    +(items.length?`<table class="print-table"><thead><tr><th>Queue Date</th><th>Tokens</th><th>Waiting</th><th>In Consultation</th><th>Completed</th><th>Cancelled</th><th>Open</th></tr></thead><tbody>`
      +items.map(it=>`<tr><td>${esc(it.queue_date)}</td><td>${esc(it.total_tokens)}</td><td>${esc(it.waiting)}</td><td>${esc(it.in_consultation)}</td><td>${esc(it.completed)}</td><td>${esc(it.cancelled)}</td><td>${esc(it.open_token_count)}</td></tr>`).join("")
      +`</tbody></table>`:'<div class="print-empty">No queue days found in this scan window.</div>')
    +`</section></main></article>`;
  host.appendChild(shell);
  $("#queue-summary-print-now",shell).addEventListener("click",()=>window.print());
  return {envelope,data:payload};
}
